"""Full V7 geometry retains only evidenced channels in coordinated scene sampling."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess
import struct
import unittest
from unittest.mock import patch
from importer.assets import decode_tmd
from importer.model_authoring import preview_model_shape
from importer.model_face_ledger import create_face_ledger,append_object_ledger,replay_face_ledger
from importer.model_object_ledger import source_objects
from sdk.project import ProjectError
from sdk.scene_preview import source_key
from test_model_primitives import synthetic
from test_model_object_ledger import clone_request
import test_scene_animation as fixtures


class AuthoredObjectSceneAnimationTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.SceneAnimationTests();helper.setUp();self.addCleanup(helper.doCleanups)
        native=bytearray(synthetic(((0x10,),),count=1));start=12+struct.unpack_from('<I',native,12)[0]
        for index,xyz in enumerate(([0,0,0],[10,0,0],[0,10,0],[20,0,0],[0,20,0])):
            struct.pack_into('<3h',native,start+index*8,*xyz)
        original=bytes(native);ledger=create_face_ledger(original)
        _,audit=replay_face_ledger(original,ledger)
        candidate,ledger,_=append_object_ledger(original,ledger,[clone_request(audit,next(iter(source_objects(original).values())),100)])
        binding=dict(format='tmd-face-addition-v1',asset_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),ledger=ledger)
        raw=decode_tmd(original)
        raw['animation']=dict(frame_count=2,asset_semantic_id=helper.asset_id,source_clip_id='animation://fixture/scene-anm/0001')
        raw['frames']=[dict(frame_index=i,posed=True,coordinate_system='retail_psx_actor_local_y_down',
            object_transforms=[dict(object_index=0,rotation_psx=[0,0,i*1024],translation=[i*20,0,0])]) for i in range(2)]
        clip=preview_model_shape(raw,candidate,binding)
        scene=helper.scene();baseline=deepcopy(clip);baseline['vertices']=deepcopy(clip['frames'][0]['vertices'])
        baseline['posed']=True;baseline['normal_source']={key:baseline.pop(key) for key in ('triangle_normals','normal_preview')}
        scene['assets'][0]['preview']=baseline
        return helper,scene,clip

    def test_complete_geometry_normal_prefix_and_browser_sampling(self):
        helper,scene,clip=self.fixture();before=deepcopy((scene,clip,helper.project._document()))
        report=helper.prepare(scene,lambda *args:clip);track=report['tracks'][0]
        self.assertEqual(track['pose_scope'],dict(kind='existing_channel_prefix',object_count=2,posed_object_count=1,
            unposed_object_indices=[1],unposed_vertex_start=5))
        self.assertEqual(track['frames'][0][5:],track['frames'][1][5:])
        self.assertNotEqual(track['frames'][0][:5],track['frames'][1][:5])
        self.assertEqual(track['normal_pose']['source']['pose_scope'],track['pose_scope'])
        self.assertEqual((scene,clip,helper.project._document()),before)
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        context=dict(projectPath=str(helper.project.root),sceneId=helper.project.active_scene,mode='edit',
            sourceKey=source_key(helper.project),sceneSourceKey=scene['source_key'],representation='authored',ready=True,canStart=True)
        script="""import assert from 'node:assert/strict';
import {decodeSceneAnimation,sceneAnimationSamples} from './integrations/legaia/editor/scene-animation.js';
import {rigidFrameNormals} from './integrations/legaia/editor/source-normal-view.js';
let data='';for await(const chunk of process.stdin)data+=chunk;const {report,context,clip}=JSON.parse(data);
const decoded=decodeSceneAnimation(report,context),samples=sceneAnimationSamples(decoded,1),source=decoded.tracks[0].normal_pose.source;
assert.deepEqual(samples[0].normal_preview.triangle_normals[1],source.triangle_normals[1]);
assert.ok(Math.abs(samples[0].normal_preview.triangle_normals[0][0][1]-4096)<1e-6);
const modelNormals=rigidFrameNormals(clip,clip.frames[1]);assert.deepEqual(modelNormals.triangle_normals,samples[0].normal_preview.triangle_normals);
for(const mutate of [c=>c.unposed_object_indices=[0],c=>c.pose_scope='unknown',c=>c.frames[1].object_transforms.push({object_index:1,rotation_psx:[0,0,0],translation:[0,0,0]})]){const bad=structuredClone(clip);mutate(bad);assert.throws(()=>rigidFrameNormals(bad,bad.frames[1]));}
for(const mutate of [r=>r.tracks[0].pose_scope.unposed_object_indices=[0],r=>r.tracks[0].frames[1][5][0]++,r=>r.tracks[0].normal_pose.source.pose_scope.unposed_vertex_start++,r=>r.tracks[0].normal_pose.frames[1].object_transforms.push({object_index:1,rotation_psx:[0,0,0],translation:[0,0,0]})]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeSceneAnimation(bad,context));}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(dict(report=report,context=context,clip=clip)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_scope_and_forged_channels_reject_even_without_normal_budget(self):
        helper,scene,clip=self.fixture()
        with patch('sdk.scene_animation.MAX_FRAME_NORMAL_CORNERS',0):
            track=helper.prepare(scene,lambda *args:clip)['tracks'][0]
            self.assertNotIn('normal_pose',track);self.assertEqual(track['pose_scope']['unposed_object_indices'],[1])
            for mutate in (lambda c:c['frames'][1]['vertices'][5].__setitem__(0,999),
                    lambda c:c['frames'][1]['object_transforms'].append(dict(object_index=1,rotation_psx=[0,0,0],translation=[0,0,0])),
                    lambda c:c.__setitem__('unposed_object_indices',[0]),lambda c:c.pop('pose_scope'),
                    lambda c:c['frames'][1]['object_transforms'].__setitem__(0,None),
                    lambda c:c['frames'][1]['object_transforms'][0]['rotation_psx'].__setitem__(0,0.5)):
                bad=deepcopy(clip);mutate(bad)
                with self.assertRaises(ProjectError):helper.prepare(scene,lambda *args:bad)


if __name__=='__main__':unittest.main()
