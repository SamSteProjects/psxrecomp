"""Internal V6 bindings persist and pack through normal Build; no group UI claim."""
from copy import deepcopy
from hashlib import sha256
import struct
import json
import shutil
import subprocess
from pathlib import Path
import tomllib
import unittest
import zipfile
from unittest.mock import patch
from importer.core import _pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_face_ledger import append_vector_ledger,append_group_ledger,replay_face_ledger
from importer.model_primitives import inspect_model_primitives
from sdk.model_face_addition import base_content
from sdk.project import ProjectService
from sdk.build import build_project
import test_model_growth_normal_build as fixtures


class GroupBuildTests(unittest.TestCase):
    def test_primitive_browser_source_and_reference_users_accept_authored_groups(self):
        import test_model_editors_allocated_vectors as editor_fixtures
        from sdk import model_vertex_users,model_normal_users
        helper=editor_fixtures.AllocatedEditorTests();self.addCleanup(helper.doCleanups)
        p,asset=helper.fixture();binding=deepcopy(p.model_overrides[asset])
        original=p._model_source(asset);base=base_content(p,asset,original,binding)
        _,audit=replay_face_ledger(base,binding['ledger']);donor=audit['faces'][0]['face_id']
        candidate,ledger,_=append_group_ledger(base,binding['ledger'],[dict(
            group_id='group://authored/00000000-0000-4000-8000-000000000077',donor_face_id=donor,
            faces=[dict(face_id='face://authored/00000000-0000-4000-8000-000000000077',donor_face_id=donor,
                fields=dict(vertices=[5,6,0,1],normal_indices=[4,5,4,5]))])])
        binding.update(ledger=ledger,asset_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate))
        (p.root/'Authored'/'Models'/(binding['asset_sha256']+'.tmd')).write_bytes(candidate)
        p.model_overrides[asset]=binding
        source=p.model_primitive_source(asset)
        self.assertEqual(source['vector_growth'],[dict(object_index=0,vertices=3,normals=3)])
        index=source['authored_faces'][0][-1]['current_index']
        fields=source['objects'][0]['primitives'][index]
        edits=[dict(object_index=0,primitive_index=index,vertices=[6,5,0,1],normal_indices=[5,4,5,4],uvs=fields['uvs'])]
        review=p.preview_model_primitives(asset,edits,source['effective_sha256'],'a'*64)
        for module,vector in ((model_vertex_users,5),(model_normal_users,4)):
            report=module.inspect(p,asset,0,vector,source['effective_sha256'],'a'*64)
            self.assertEqual(report['vector_origin'],'allocated')
            self.assertIsNone(report['retail_coordinates'])
            self.assertIn(index,{r['primitive_index'] for r in report['current_users']})
        node=shutil.which('node')
        if node:
            for key in ('preview','current_preview'):review[key]['semantic_id']=asset
            script="""import {decodeModelPrimitives,decodeModelPrimitivePreview} from './integrations/legaia/editor/model-primitives.js';
let input='';for await(const chunk of process.stdin)input+=chunk;
const {source,review,edits}=JSON.parse(input);
const context={projectPath:'C:/private/project',sceneId:'scene://fixture',mode:'edit',sourceKey:source.project_source_key};
const decoded=decodeModelPrimitives(source,source.asset_id,context);
decodeModelPrimitivePreview(review,decoded,context,edits);
"""
            result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(dict(source=source,review=review,edits=edits)),
                text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
            self.assertEqual(result.returncode,0,result.stderr)
        p.set_model_primitives(asset,edits,source['effective_sha256'],'a'*64,review['proposed_sha256'])
        self.assertEqual(p.model_overrides[asset]['ledger']['schema_version'],'legaia.model-face-addition-ledger.v6')

    def test_internal_v6_binding_existing_edit_history_persistence_and_exact_build(self):
        helper=fixtures.ModelGrowthNormalBuildTests();self.addCleanup(helper.doCleanups)
        p,asset,*_=helper.fixture();binding=deepcopy(p.model_overrides[asset])
        original=p._model_source(asset,p.active_scene)
        base=base_content(p,asset,original,binding)
        current=p.read_model_replacement(asset,binding);nv=struct.unpack_from('<I',current,16)[0]
        current,ledger,audit=append_vector_ledger(base,binding['ledger'],[
            dict(object_index=0,kind='vertices',vectors=[[100,200,300]])])
        donor=audit['faces'][0]['face_id'];corners=inspect_model_primitives(current)['objects'][0]['primitives'][0]['corner_count']
        current,ledger,audit=append_group_ledger(base,ledger,[dict(
            group_id='group://authored/00000000-0000-4000-8000-000000000099',donor_face_id=donor,
            faces=[dict(face_id='face://authored/00000000-0000-4000-8000-000000000099',
                donor_face_id=donor,fields={'vertices':[nv,0,1,2][:corners]})])])
        binding.update(ledger=ledger,asset_sha256=sha256(current).hexdigest(),byte_length=len(current))
        (p.root/'Authored'/'Models'/(binding['asset_sha256']+'.tmd')).write_bytes(current)
        p.model_overrides[asset]=binding
        self.assertEqual(p.read_model_replacement(asset,binding),current)
        p.set_model_vector(asset,0,'vertices',nv,[71,19,-3],sha256(current).hexdigest())
        final=p.read_model_replacement(asset,p.model_overrides[asset])
        self.assertEqual(p.model_overrides[asset]['ledger']['schema_version'],'legaia.model-face-addition-ledger.v6')
        self.assertEqual(replay_face_ledger(base,p.model_overrides[asset]['ledger'])[1]['allocated_group_count'],1)
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),current)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),final)
        from sdk import model_materials
        from contextlib import nullcontext
        with patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()):
            catalog=model_materials.snapshot(p,asset)
            group_index=catalog['authored_groups'][0][0]['current_index']
            semi=catalog['objects'][0]['groups'][group_index]['semi_transparent']
            edits=[dict(kind='group',object_index=0,group_index=group_index,values={'semi_transparent':not semi})]
            candidate,review=model_materials.prepare(p,asset,edits,sha256(final).hexdigest(),'a'*64)
            model_materials.apply(p,asset,edits,sha256(final).hexdigest(),'a'*64,review['review_key'])
            self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
            final=candidate
        p.save();saved=deepcopy(p.model_overrides[asset])
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.read_model_replacement(asset,saved),final)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            replacement=decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement']
        archive=_archive(replacement);carrier=archive.read_entry(archive.entry(1))
        descriptor=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size)
        start,_=_pack_ranges(pack)[1]
        self.assertEqual(pack[start:start+len(final)],final)
        self.assertEqual(p.model_overrides[asset],saved)


if __name__=='__main__':unittest.main()
