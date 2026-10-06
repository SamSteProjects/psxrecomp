"""Camera metadata persistence and source safety independent of game inputs."""
from copy import deepcopy
from pathlib import Path
import json
import math
import tempfile
import unittest
import struct
from hashlib import sha256
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError, digest
from sdk.scene_views import review_key
from sdk.build import authored_state_key
from sdk.scene_preview import source_key
import test_actor_placement_batch as fixture

DISPLAY = dict(camera=dict(projection='orthographic',yaw=0,pitch=math.pi/2,distance=1000,target=dict(x=2880,y=-64,z=5440)),representation='retail',layers=dict(actors=True,scenery=True,ground=False))

class SceneViewTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.p=fixture.ActorPlacementBatchTests().project(self.directory.name);self.p.save()
    def create(self,name='Wall',display=None):
        p=self.p;p.command(dict(type='create_scene_view',scene_id=p.active_scene,import_sha256=digest(p.imports[p.active_scene]),name=name,display=deepcopy(DISPLAY if display is None else display)))
        return next(row for row in p.scene_views.values() if row['name']==name.strip())
    def cmd(self,kind,row,**fields):
        return dict(type=kind,view_id=row['id'],review_key=review_key(self.p,row),**fields)
    def test_metadata_history_save_open_and_no_game_input_changes(self):
        p=self.p;inputs=(deepcopy(p.imports),deepcopy(p.overrides),authored_state_key(p),source_key(p));row=self.create(' Wall ')
        self.assertEqual(row['display'],DISPLAY);self.assertTrue(p.dirty);self.assertIn('Saved scene views',p.unsaved_sections)
        self.assertEqual((p.imports,p.overrides,authored_state_key(p),source_key(p)),inputs)
        self.assertEqual(p.state()['scene_views'][0]['review_key'],review_key(p,row))
        p.undo();self.assertFalse(p.scene_views);self.assertFalse(p.dirty);p.redo()
        opened=ProjectService.open(p.save());self.assertEqual(opened.scene_views,p.scene_views);self.assertFalse(opened.dirty);self.assertFalse(opened.undo_stack)
    def test_review_crud_noop_and_atomic_rejection(self):
        p=self.p;row=self.create();stale=self.cmd('delete_scene_view',row)
        p.command(self.cmd('rename_scene_view',row,name='Other'));row=p.scene_views[row['id']];depth=len(p.undo_stack)
        p.command(self.cmd('rename_scene_view',row,name='Other'));self.assertEqual(len(p.undo_stack),depth)
        with self.assertRaises(ProjectError):p.command(stale)
        new=deepcopy(DISPLAY);new['camera']['target']['x']=3000;p.command(self.cmd('update_scene_view',row,display=new));self.assertEqual(p.scene_views[row['id']]['display'],new)
        p.undo();self.assertEqual(p.scene_views[row['id']],row);p.redo();row=p.scene_views[row['id']]
        p.command(self.cmd('delete_scene_view',row));self.assertFalse(p.scene_views);p.undo();self.assertEqual(p.scene_views[row['id']],row)
    def test_front_and_side_orthographic_views_persist_without_game_changes(self):
        p=self.p;game=(deepcopy(p.overrides),authored_state_key(p),source_key(p))
        for name,yaw in [('Front',0),('Side',math.pi/2)]:
            d=deepcopy(DISPLAY);d['camera'].update(pitch=0,yaw=yaw)
            row=self.create(name,d)
            perspective=deepcopy(d);perspective['camera']['projection']='perspective'
            with self.assertRaises(ProjectError):p.command(self.cmd('update_scene_view',row,display=perspective))
            self.assertEqual(p.scene_views[row['id']]['display'],d)
        self.assertEqual((p.overrides,authored_state_key(p),source_key(p)),game)
        opened=ProjectService.open(p.save());self.assertEqual(opened.scene_views,p.scene_views)
        self.assertTrue(all(v['display']['camera']['pitch']==0 for v in opened.scene_views.values()))
    def test_invalid_camera_layers_source_names_and_live_reject(self):
        p=self.p
        bad=[]
        for key,value in [('pitch',-.001),('pitch',float('nan')),('distance',19),('distance',float('inf')),('yaw',True),('projection','unknown'),('target',dict(x=0,y=None,z=1))]:
            d=deepcopy(DISPLAY);d['camera'][key]=value;bad.append(d)
        d=deepcopy(DISPLAY);d['layers']['actors']=1;bad.append(d)
        d=deepcopy(DISPLAY);d['runtime']={};bad.append(d)
        for d in bad:
            with self.assertRaises(ProjectError):self.create(display=d)
            self.assertFalse(p.scene_views);self.assertFalse(p.undo_stack)
        for name in ['', 'x'*81]:
            with self.assertRaises(ProjectError):self.create(name)
        row=self.create()
        with self.assertRaises(ProjectError):self.create('wall')
        cmd=dict(type='create_scene_view',scene_id=p.active_scene,import_sha256='stale',name='New',display=DISPLAY)
        with self.assertRaises(ProjectError):p.command(cmd)
        p.mode='live'
        with self.assertRaises(ProjectError):p.command(self.cmd('delete_scene_view',row))
    def test_reimport_guard_survives_delete_history_and_reopen(self):
        p=self.p;row=self.create();changed=deepcopy(p.imports[p.active_scene]);changed['actors'][0]['imported_transform']['position']['x']=192
        with self.assertRaisesRegex(ProjectError,'scene views'):p.import_metadata(changed)
        p.command(self.cmd('delete_scene_view',row))
        with self.assertRaisesRegex(ProjectError,'scene views'):p.import_metadata(changed)
        p.undo();opened=ProjectService.open(p.save())
        with self.assertRaisesRegex(ProjectError,'scene views'):opened.import_metadata(changed)
    def test_visibility_grid_history_and_portable_reopen(self):
        p=self.p;actor=p.imports[p.active_scene]['actors'][0]['semantic_id']
        d=deepcopy(DISPLAY);d.update(grid=False,visibility=dict(hidden_entity_ids=[actor],isolated_entity_id=None,map_sha256=None))
        game=(deepcopy(p.imports),deepcopy(p.overrides),authored_state_key(p),source_key(p));row=self.create(display=d)
        self.assertEqual(row['display'],d);p.undo();self.assertFalse(p.scene_views);p.redo()
        opened=ProjectService.open(p.save());self.assertEqual(opened.scene_views,p.scene_views)
        self.assertEqual((p.imports,p.overrides,authored_state_key(p),source_key(p)),game)
        replacement=deepcopy(d);replacement['visibility']=dict(hidden_entity_ids=[],isolated_entity_id=actor,map_sha256=None);replacement['grid']=True
        p.command(self.cmd('update_scene_view',row,display=replacement));p.undo();self.assertEqual(p.scene_views[row['id']]['display'],d);p.redo();self.assertEqual(p.scene_views[row['id']]['display'],replacement)
    def test_static_visibility_source_membership_and_map_binding(self):
        p=self.p;source=bytearray(0x10000);struct.pack_into('<H',source,0x8002,0x2004);source=bytes(source)
        prefix='environment://'+p.active_scene.removeprefix('scene://')+'/field-map/'
        d=deepcopy(DISPLAY);d.update(grid=True,visibility=dict(hidden_entity_ids=[prefix+'ground'],isolated_entity_id=prefix+'decorations/00001',map_sha256=sha256(source).hexdigest()))
        with patch.object(p,'_environment_source',return_value=source):row=self.create(display=d)
        self.assertEqual(ProjectService.open(p.save()).scene_views,p.scene_views)
        before=deepcopy((p.scene_views,p.undo_stack,p.redo_stack));bad=deepcopy(d);bad['visibility']['map_sha256']='a'*64
        with patch.object(p,'_environment_source',return_value=source),self.assertRaisesRegex(ProjectError,'source MAP'):p.command(self.cmd('update_scene_view',row,display=bad))
        bad=deepcopy(d);bad['visibility']['isolated_entity_id']=prefix+'decorations/00002'
        with patch.object(p,'_environment_source',return_value=source),self.assertRaisesRegex(ProjectError,'static source'):p.command(self.cmd('update_scene_view',row,display=bad))
        self.assertEqual((p.scene_views,p.undo_stack,p.redo_stack),before)
    def test_visibility_invalid_requests_are_atomic(self):
        p=self.p;actor=p.imports[p.active_scene]['actors'][0]['semantic_id'];base=deepcopy(DISPLAY);base.update(grid=False,visibility=dict(hidden_entity_ids=[actor],isolated_entity_id=None,map_sha256=None))
        for mutate in [lambda d:d.update(grid=1),lambda d:d['visibility'].update(hidden_entity_ids=[actor,actor]),lambda d:d['visibility'].update(isolated_entity_id=actor),lambda d:d['visibility'].update(hidden_entity_ids=['actor://unknown']),lambda d:d['visibility'].update(map_sha256='a'*64),lambda d:d['visibility'].update(runtime_address=4096),lambda d:d.update(visibility=None)]:
            bad=deepcopy(base);mutate(bad)
            with self.assertRaises(ProjectError):self.create(display=bad)
            self.assertFalse(p.scene_views);self.assertFalse(p.undo_stack)

    def test_malformed_saved_views_and_legacy_project(self):
        p=self.p;path=p.save();raw=json.loads(path.read_text(encoding='utf-8'));self.assertNotIn('scene_views',raw);self.assertEqual(ProjectService.open(path).scene_views,{})
        row=self.create();p.save();raw=json.loads(path.read_text(encoding='utf-8'));raw['scene_views'][row['id']]['display']['camera']['target']['y']=None;path.write_text(json.dumps(raw),encoding='utf-8')
        with self.assertRaises(ProjectError):ProjectService.open(path)

    def test_group_isolation_history_and_exact_portable_metadata(self):
        p=self.p;ids=sorted(row['semantic_id'] for row in p.imports[p.active_scene]['actors'])
        d=deepcopy(DISPLAY);d['visibility']=dict(hidden_entity_ids=[],isolated_entity_ids=ids,map_sha256=None)
        inputs=(deepcopy(p.imports),deepcopy(p.overrides),authored_state_key(p),source_key(p))
        row=self.create('Group',d);self.assertEqual(row['display'],d)
        p.undo();self.assertFalse(p.scene_views);p.redo();self.assertEqual(ProjectService.open(p.save()).scene_views,p.scene_views)
        self.assertEqual((p.imports,p.overrides,authored_state_key(p),source_key(p)),inputs)
        for mutation in (lambda v:v.update(isolated_entity_id=ids[0]),lambda v:v.update(isolated_entity_ids=[]),lambda v:v.update(isolated_entity_ids=ids[::-1]),lambda v:v.update(isolated_entity_ids=ids*65),lambda v:v.update(isolated_entity_ids=[ids[0],ids[0]]),lambda v:v.update(hidden_entity_ids=[ids[0]]),lambda v:v.update(isolated_entity_ids=['authored-actor://unproven'])):
            bad=deepcopy(d);mutation(bad['visibility']);before=deepcopy((p.scene_views,p.undo_stack,p.redo_stack))
            with self.assertRaises(ProjectError):p.command(self.cmd('update_scene_view',row,display=bad))
            self.assertEqual((p.scene_views,p.undo_stack,p.redo_stack),before)

    def test_mixed_group_requires_each_static_instance_and_exact_map(self):
        p=self.p;actor=p.imports[p.active_scene]['actors'][0]['semantic_id'];prefix='environment://'+p.active_scene.removeprefix('scene://')+'/field-map/'
        source=bytearray(0x10000);struct.pack_into('<H',source,0x8002,0x2004);source=bytes(source)
        d=deepcopy(DISPLAY);d['visibility']=dict(hidden_entity_ids=[prefix+'ground'],isolated_entity_ids=sorted([actor,prefix+'decorations/00001']),map_sha256=sha256(source).hexdigest())
        with patch.object(p,'_environment_source',return_value=source):row=self.create('Mixed',d)
        for ids in ([actor,prefix+'decorations/00002'],[actor,'environment://foreign/field-map/ground']):
            bad=deepcopy(d);bad['visibility']['isolated_entity_ids']=sorted(ids)
            with patch.object(p,'_environment_source',return_value=source),self.assertRaises(ProjectError):p.command(self.cmd('update_scene_view',row,display=bad))
        self.assertEqual(p.scene_views[row['id']]['display'],d)

    def test_npc_visibility_deleted_metadata_reopens_and_undo_restores_identity(self):
        p=self.p;actor=p.imports[p.active_scene]['actors'][0]['semantic_id']
        p.command(dict(type='create_actor_draft',donor_entity_id=actor,position=dict(x=64,z=64),name='Visible draft'))
        npc=next(iter(p.actor_drafts));d=deepcopy(DISPLAY);d['representation']='authored';d['visibility']=dict(hidden_entity_ids=[actor],isolated_entity_id=npc,map_sha256=None)
        inputs=(deepcopy(p.imports),deepcopy(p.overrides),deepcopy(p.actor_drafts),authored_state_key(p));row=self.create('NPC',d)
        self.assertEqual((p.imports,p.overrides,p.actor_drafts,authored_state_key(p)),inputs)
        self.assertEqual(ProjectService.open(p.save()).scene_views,p.scene_views)
        retail=deepcopy(d);retail['representation']='retail'
        with self.assertRaisesRegex(ProjectError,'Authored scene'):self.create('Retail NPC',retail)
        p.command(dict(type='delete_actor_draft',entity_id=npc));saved_views=deepcopy(p.scene_views)
        opened=ProjectService.open(p.save());self.assertEqual(opened.scene_views,saved_views);self.assertFalse(opened.actor_drafts)
        before=deepcopy((p.scene_views,p.undo_stack,p.redo_stack))
        with self.assertRaisesRegex(ProjectError,'unavailable'):p.command(self.cmd('update_scene_view',row,display=d))
        with self.assertRaisesRegex(ProjectError,'unavailable'):self.create('Missing NPC',d)
        self.assertEqual((p.scene_views,p.undo_stack,p.redo_stack),before)
        p.undo();self.assertEqual(p.actor_drafts,inputs[2]);self.assertEqual(p.scene_views,saved_views)
        mixed=deepcopy(d);mixed['visibility']=dict(hidden_entity_ids=[],isolated_entity_ids=sorted([actor,npc]),map_sha256=None)
        p.command(self.cmd('update_scene_view',row,display=mixed));self.assertEqual(ProjectService.open(p.save()).scene_views,p.scene_views)

    def test_npc_visibility_foreign_scene_rejects_without_metadata_mutation(self):
        p=self.p;actor=p.imports[p.active_scene]['actors'][0]['semantic_id'];p.command(dict(type='create_actor_draft',donor_entity_id=actor,position=dict(x=64,z=64),name='Other scene'))
        npc=next(iter(p.actor_drafts));p.actor_drafts[npc]['scene_id']='scene://other'
        d=deepcopy(DISPLAY);d['representation']='authored';d['visibility']=dict(hidden_entity_ids=[],isolated_entity_id=npc,map_sha256=None)
        before=deepcopy((p.scene_views,p.undo_stack))
        with self.assertRaises(ProjectError):self.create('Foreign',d)
        self.assertEqual((p.scene_views,p.undo_stack),before)

if __name__=='__main__':unittest.main()
