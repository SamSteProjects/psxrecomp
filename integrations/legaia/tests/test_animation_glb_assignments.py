"""Assigned pose interchange preserves imported channel ownership and Build data."""
import base64
from copy import deepcopy
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
from importer.core import decompress_lzs
from importer.pipeline import _disc_context, import_scene
from importer.scene_animation import load_scene_actor_animation_catalog
from sdk.actor_animation import review
from sdk.animation_glb import export_clip, preview_import, apply_import, pose_import
from sdk.build import build_project
from sdk.project import ProjectService, ProjectError, digest
from test_animation_glb_workflow import shifted
from test_model_primitive_workflow import http_server

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class AssignedAnimationGlb(unittest.TestCase):
 def test_assigned_clip_and_appearance_roundtrip_keep_distinct_owners(self):
  root=Path('local-output/sdk-20260909');root.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(prefix='assigned-animation-',dir=root) as directory:
   project=ProjectService(Path(directory));project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town0b'),os.environ['LEGAIA_DISC_BIN'])
   subject='scene://town0b/actors/man-p1/0019';owner='scene://town0b/actors/man-p1/0049';clip='animation://town0b/scene-anm/0012'
   imported=digest(project.imports);options=project.animation_authoring_options(subject);channel=project.animation_channel_values(subject,0,0)
   existing=dict(animation_id=options['binding']['semantic_id'],source_record_sha256=options['binding']['source_record']['record_sha256'],edits=[dict(frame_index=0,object_index=0,translation={'x':channel['retail']['translation']['x']^1})])
   project.command(dict(type='set_animation_channels',entity_id=subject,value=existing))
   assignment=review(project,subject,clip);project.command(dict(type='set_actor_animation',**{k:assignment[k] for k in ('entity_id','animation_asset_id','source_key','review_key')}))
   animation,asset,binding=export_clip(project,subject,15)
   self.assertEqual(binding['schema_version'],'legaia.animation-glb-binding.v2');self.assertEqual(binding['channel_owner_entity_id'],owner);self.assertEqual(binding['model_source_entity_id'],subject);self.assertEqual(binding['animation_id'],clip);self.assertEqual(animation['entity_id'],subject)
   project.command(dict(type='set_actor_appearance',entity_id=subject,donor_entity_id=owner))
   self.assertEqual(export_clip(project,subject,15)[2]['model_source_entity_id'],owner)
   with http_server(project) as (_,post):
    status,exported=post('/api/animation-glb-export',dict(entity_id=subject,clip_fps=15));self.assertEqual(status,200,exported)
    original=base64.b64decode(exported['glb_base64']);self.assertEqual(preview_import(project,subject,original,exported['binding'])['changed_axes'],0)
    edited=shifted(original);binding=exported['binding']
    before=deepcopy(project.overrides);history=len(project.undo_stack);report=preview_import(project,subject,edited,binding)
    self.assertEqual(report['changed_axes'],1);self.assertEqual(report['ownership']['channel_owner_entity_id'],owner);self.assertEqual(project.overrides,before)
    self.assertEqual(pose_import(project,subject,edited,binding)[0]['entity_id'],subject)
    for key in ('channel_owner_entity_id','model_source_entity_id'):
     bad=dict(binding,**{key:subject})
     with self.assertRaisesRegex(ProjectError,'binding differs'):preview_import(project,subject,edited,bad)
    body=dict(entity_id=subject,glb_base64=base64.b64encode(edited).decode(),binding=binding)
    status,pose=post('/api/animation-glb-pose-preview',body);self.assertEqual(status,200,pose);self.assertEqual(pose['animation']['entity_id'],subject);self.assertEqual(pose['animation']['source_clip_id'],clip)
    with self.assertRaises(ProjectError):apply_import(project,subject,edited,binding,'0'*64)
    apply_import(project,subject,edited,binding,report['review_key']);after=deepcopy(project.overrides)
    self.assertEqual(len(project.undo_stack),history+1);self.assertEqual(after[subject],before[subject]);self.assertEqual(after[owner]['AnimationChannels']['animation_id'],clip)
    project.undo();self.assertEqual(project.overrides,before);project.redo();self.assertEqual(project.overrides,after);project.save();reopened=ProjectService.open(project.root)
    self.assertEqual(reopened.overrides,after);self.assertEqual(digest(reopened.imports),imported)
    with self.assertRaisesRegex(ProjectError,'binding differs'):preview_import(project,subject,edited,binding)
    with _disc_context(project.disc_path):
     catalog=load_scene_actor_animation_catalog(project.disc_path,'town0b');expected,_=catalog.authored_bank({id:parts['AnimationChannels'] for id,parts in after.items() if 'AnimationChannels' in parts})
    built=build_project(reopened)
    with zipfile.ZipFile(built['path']) as package:
     actual=decompress_lzs(package.read('assets/town0b-animation.lzs'),len(expected))[0]
    self.assertEqual(actual,expected);self.assertEqual(project.overrides[subject]['AnimationChannels'],existing)

if __name__=='__main__':unittest.main()
