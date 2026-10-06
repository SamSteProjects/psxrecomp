"""The complete 512-face import survives replay and normal native packaging."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json, shutil, subprocess, tomllib, unittest, zipfile
from unittest.mock import patch
from importer.core import ImportError, _pack_ranges, parse_scene_assets, decompress_lzs
from importer.model_face_addition import MAX_NEW_FACES
from importer.model_primitives import inspect_model_primitives
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from sdk import model_mesh_append
from sdk.project import ProjectService, ProjectError
from sdk.build import build_project
import test_model_mesh_append as fixtures


def mesh(count):
    # Every triangle owns three distinct vertices; no shared-index shortcut.
    positions=[point for i in range(count) for point in
               ([i*3,0,0],[i*3+1,0,0],[i*3,1,0])]
    return fixtures.glb(positions=positions,indices=list(range(count*3)))


class MeshCapacityTests(unittest.TestCase):
    def test_exact_limit_replacement_history_replay_editor_and_normal_build(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture()
        p.model_overrides.pop(asset) # Start with Retail; fixture has an earlier addition.
        source=model_mesh_append.source(p,asset,'a'*64)
        donor=source['topology']['faces'][0]['face_id']
        original=p._model_source(asset);before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        self.assertEqual(MAX_NEW_FACES,512)
        with self.assertRaises((ImportError,ProjectError)):
            model_mesh_append.prepare(p,asset,mesh(513),donor,source['effective_sha256'],'a'*64,new_group=True,replace_group=True)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        content=mesh(512)
        candidate,_,review=model_mesh_append.prepare(p,asset,content,donor,source['effective_sha256'],'a'*64,new_group=True,replace_group=True)
        self.assertEqual(review['topology']['authored_face_count'],512)
        self.assertEqual(review['topology']['allocated_vector_count'],1536)
        script="""import {decodeMeshAppendReview} from './integrations/legaia/editor/model-mesh-append.js';
import assert from 'node:assert/strict';let input='';for await(const c of process.stdin)input+=c;
const {review,source,donor}=JSON.parse(input);
decodeMeshAppendReview(review,source,donor,review.geometry.glb_sha256,true,true);
const bad=structuredClone(review);bad.topology.authored_face_count=513;
assert.throws(()=>decodeMeshAppendReview(bad,source,donor,review.geometry.glb_sha256,true,true));"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],
            input=json.dumps(dict(review=review,source=source,donor=donor)),text=True,capture_output=True,
            cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)
        p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,review['review_key'],new_group=True,replace_group=True)
        self.assertEqual(len(p.undo_stack),len(before[1])+1)
        self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
        native=inspect_model_primitives(candidate)
        self.assertEqual(sum(len(o['primitives']) for o in native['objects']),512)
        p.undo();self.assertEqual(p._document(),before[0]);p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        output=build_project(p)
        with zipfile.ZipFile(output['path']) as package:
            entry=tomllib.loads(package.read('manifest.toml').decode())['disc_relocation'][0]
            archive=_archive(decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));descriptor=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(candidate)],candidate)
        self.assertEqual(p._model_source(asset),original)


if __name__=='__main__':unittest.main()
