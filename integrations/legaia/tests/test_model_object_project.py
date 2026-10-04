"""Actual object clone review/history/persistence and normal synthetic Build."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tomllib
import unittest
import zipfile
from unittest.mock import patch
from importer.core import _pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from sdk import model_object_allocation
from sdk.project import ProjectService,ProjectError
from sdk.build import build_project
from test_model_object_ledger import clone_request
import test_model_growth_normal_build as fixtures


class ObjectProjectTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.ModelGrowthNormalBuildTests();self.addCleanup(helper.doCleanups)
        p,asset,*_=helper.fixture()
        self.enterContext(patch('sdk.model_object_allocation.source_key',return_value='a'*64))
        return p,asset

    def test_command_review_identity_one_history_step_reopen_and_build(self):
        p,asset=self.fixture();source=model_object_allocation.source(p,asset,'a'*64)
        self.assertEqual(len(source['native_objects']),len(source['objects']))
        self.assertEqual(sum(group['primitive_count'] for group in source['native_objects'][0]['groups']),len(source['objects'][0]['primitives']))
        request=clone_request(source['topology'],source['object_identities'][0],100)
        requests=[request];state=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        files=set((p.root/'Authored'/'Models').iterdir());before=p.read_model_replacement(asset,p.model_overrides[asset])
        base=deepcopy(p.model_overrides[asset]['base_binding'])
        report=model_object_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        changed=deepcopy(requests);changed[0]['object_id']=changed[0]['object_id'].replace('000000000064','000000000065')
        other=model_object_allocation.review(p,asset,changed,source['effective_sha256'],'a'*64)
        self.assertEqual(other['proposed_sha256'],report['proposed_sha256']);self.assertNotEqual(other['review_key'],report['review_key'])
        for key in ('0'*64,other['review_key']):
            with self.assertRaises(ProjectError):p.apply_model_object_allocations(asset,requests,source['effective_sha256'],'a'*64,key)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        p.apply_model_object_allocations(asset,requests,source['effective_sha256'],'a'*64,report['review_key'])
        final=p.read_model_replacement(asset,p.model_overrides[asset])
        self.assertEqual(sha256(final).hexdigest(),report['proposed_sha256'])
        self.assertEqual(p.model_overrides[asset]['base_binding'],base)
        self.assertEqual(len(p.undo_stack),len(state[1])+1)
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),final)
        p.save();saved=deepcopy(p.model_overrides[asset])
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.read_model_replacement(asset,saved),final)
            self.assertEqual(model_object_allocation.source(reopened,asset,'a'*64)['topology'],report['topology'])
        state=deepcopy((p._document(),p.undo_stack,p.redo_stack));out=build_project(p)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)
        with zipfile.ZipFile(out['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            replacement=decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement']
        archive=_archive(replacement);carrier=archive.read_entry(archive.entry(1));descriptor=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size);start,_=_pack_ranges(pack)[1]
        self.assertEqual(pack[start:start+len(final)],final)

    def test_stale_publication_no_mutation_and_exact_donor_coverage(self):
        p,asset=self.fixture();source=model_object_allocation.source(p,asset,'a'*64)
        requests=[clone_request(source['topology'],source['object_identities'][0],100)]
        report=model_object_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        state=deepcopy((p._document(),p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        with patch('sdk.scene_preview.source_key',return_value='0'*64):
            with self.assertRaises(ProjectError):p.apply_model_object_allocations(asset,requests,source['effective_sha256'],'a'*64,report['review_key'])
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        with self.assertRaises(ProjectError):model_object_allocation.review(p,asset,requests,'0'*64,'a'*64)

    def test_HTTP_exact_review_fields_stale_and_repeated_apply(self):
        from test_model_primitive_workflow import http_server
        p,asset=self.fixture()
        with http_server(p) as (server,post),patch.object(server,'state',return_value={'applied':True}):
            status,source=post('/api/model-object-allocation-source',dict(asset_id=asset,source_key='a'*64))
            self.assertEqual(status,200)
            requests=[clone_request(source['topology'],source['object_identities'][0],100)]
            body=dict(asset_id=asset,source_key='a'*64,expected_sha256=source['effective_sha256'],requests=requests)
            state=deepcopy((p._document(),p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
            status,report=post('/api/model-object-allocation-preview',body);self.assertEqual(status,200)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)
            self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
            for changes in (dict(extra=True),dict(source_key='0'*64),dict(expected_sha256='0'*64),dict(requests=[]),
                    dict(requests=requests*65),dict(requests=[dict(requests[0],extra=True)]),
                    dict(requests=[dict(requests[0],object_id=True)]),dict(requests=[dict(requests[0],groups=[])])):
                self.assertEqual(post('/api/model-object-allocation-preview',{**body,**changes})[0],400)
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)
            self.assertEqual(post('/api/model-object-allocation',{**body,'review_key':'0'*64})[0],400)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)
            self.assertEqual(post('/api/model-object-allocation',{**body,'review_key':report['review_key']})[0],200)
            state=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            self.assertEqual(post('/api/model-object-allocation',{**body,'review_key':report['review_key']})[0],400)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)


if __name__=='__main__':unittest.main()
