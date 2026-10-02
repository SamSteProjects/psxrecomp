"""Independent editable snapshots preserve current inputs without saving the source."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
from sdk.project_copy import review, create_copy
from sdk.export_snapshot import capture_export_inputs
from test_project_workflow import synthetic_scene


class ProjectCopy(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.p=ProjectService(Path(self.directory.name));self.p.import_metadata(synthetic_scene());self.p.save()
        self.actor='scene://fixture/actors/man-p1/0001'

    def test_dirty_inputs_history_and_independent_edit_save(self):
        p=self.p;saved=(p.root/'project.legaia.json').read_bytes()
        p.command(dict(type='set_transform',entity_id=self.actor,position={'x':128}))
        p.command(dict(type='create_actor_template',entity_id=self.actor,name='Experiment'))
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.saved_digest))
        r=review(p);result=create_copy(p,'  Branch \U0001f680  ',r['review_key'])
        self.assertTrue(r['source_dirty']);self.assertTrue(result['readback_verified'])
        self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack,p.saved_digest))
        self.assertEqual(saved,(p.root/'project.legaia.json').read_bytes())
        clone=ProjectService.open(Path(result['copied_project']))
        expected=deepcopy(p._document());expected['name']='Branch \U0001f680'
        self.assertEqual(clone._document(),expected);self.assertFalse(clone.dirty)
        self.assertEqual(clone.undo_stack,[]);self.assertEqual(clone.redo_stack,[])
        clone.command(dict(type='set_transform',entity_id=self.actor,position={'x':192}));clone.save()
        self.assertEqual(p.overrides[self.actor]['Transform']['position']['x'],128)
        self.assertEqual(saved,(p.root/'project.legaia.json').read_bytes())
        self.assertEqual(json.loads((clone.root/'copy-report.json').read_bytes()),result)
        self.assertFalse((clone.root/'Builds').exists())

    def test_stale_non_build_metadata_rejects_before_output(self):
        p=self.p;p.command(dict(type='set_transform',entity_id=self.actor,position={'x':128}));p.save();r=review(p)
        p.command(dict(type='create_actor_template',entity_id=self.actor,name='New template'))
        with self.assertRaisesRegex(ProjectError,'changed since'):create_copy(p,'Copy',r['review_key'])
        self.assertFalse((p.root/'ProjectCopies').exists())
        p.undo();r=review(p);p.active_scene=None
        with self.assertRaisesRegex(ProjectError,'changed since'):create_copy(p,'Copy',r['review_key'])
        self.assertFalse((p.root/'ProjectCopies').exists())

    def test_only_referenced_authored_files_copied_and_tamper_rejects(self):
        from test_importer_textures import tim
        p=self.p;payload=tim();key=sha256(payload).hexdigest()
        folder=p.root/'Authored/Textures';folder.mkdir(parents=True)
        (folder/(key+'.tim')).write_bytes(payload);(folder/('f'*64+'.tim')).write_bytes(b'unreferenced')
        p.texture_overrides['texture://fixture/0']={'asset_sha256':key,'byte_length':len(payload),'format':'tim','source_scene_id':p.active_scene}
        r=review(p);result=create_copy(p,'Texture copy',r['review_key']);clone=ProjectService.open(Path(result['copied_project']))
        self.assertEqual(clone.read_texture_replacement(clone.texture_overrides['texture://fixture/0']),payload)
        self.assertFalse((clone.root/'Authored/Textures'/('f'*64+'.tim')).exists())
        (folder/(key+'.tim')).write_bytes(b'x'*len(payload))
        with self.assertRaisesRegex(ProjectError,'digest'):create_copy(p,'Reject',r['review_key'])
        self.assertEqual(len(list((p.root/'ProjectCopies').iterdir())),1)

    def test_model_drafts_views_selections_and_source_reference_preserved(self):
        import struct
        from test_importer_assets import model
        from test_scene_views import DISPLAY
        from sdk.project import digest
        p=self.p;p.disc_path='C:/private/source.bin'
        scene=synthetic_scene();second=deepcopy(scene['actors'][0]);second['semantic_id']='scene://fixture/actors/man-p1/0002';scene['actors'].append(second);p.import_metadata(scene)
        p.command(dict(type='create_actor_draft',donor_entity_id=self.actor,position={'x':128,'z':256},name='Resident'))
        p.command(dict(type='create_scene_view',scene_id=p.active_scene,import_sha256=digest(p.imports[p.active_scene]),name='Wall',display=deepcopy(DISPLAY)))
        p.command(dict(type='create_actor_selection_set',scene_id=p.active_scene,import_sha256=digest(p.imports[p.active_scene]),name='Actors',actor_ids=[self.actor,second['semantic_id']]))
        source=model();payload=bytearray(source);start=12+struct.unpack_from('<I',source,12)[0];struct.pack_into('<h',payload,start,20);payload=bytes(payload)
        key=sha256(payload).hexdigest();asset='asset://fixture/model/0';folder=p.root/'Authored/Models';folder.mkdir(parents=True);(folder/(key+'.tmd')).write_bytes(payload)
        p.model_overrides[asset]=dict(asset_sha256=key,source_sha256=sha256(source).hexdigest(),byte_length=len(payload),source_scene_id=p.active_scene,format='tmd-shape')
        with patch.object(ProjectService,'_model_source',return_value=source):
            r=review(p);result=create_copy(p,'Complete copy',r['review_key']);clone=ProjectService.open(Path(result['copied_project']))
            self.assertEqual(clone.read_model_replacement(asset,clone.model_overrides[asset]),payload)
        self.assertEqual(clone.disc_path,p.disc_path)
        for field in ['actor_drafts','scene_views','actor_selection_sets','model_overrides']:
            self.assertEqual(getattr(clone,field),getattr(p,field))
        self.assertFalse(result['retail_disc_included'])

    def test_names_modes_and_capture_limits_reject_before_output(self):
        p=self.p;r=review(p)
        for name in ['',True,'x'*121,'a\nb','\ud800']:
            with self.assertRaises(ProjectError):create_copy(p,name,r['review_key'])
        with patch('sdk.project_copy.MAX_BYTES',1):
            with self.assertRaisesRegex(ProjectError,'byte limit'):review(p)
        with patch('sdk.project_copy.MAX_FILES',1):
            with self.assertRaisesRegex(ProjectError,'file limit'):review(p)
        p.mode='live'
        with self.assertRaisesRegex(ProjectError,'Edit mode'):review(p)
        self.assertFalse((p.root/'ProjectCopies').exists())

    def test_drift_during_capture_and_copy_withholds_completion_report(self):
        p=self.p;original=capture_export_inputs
        def drift(*args,**kwargs):
            captured=original(*args,**kwargs);p.name+=' changed';return captured
        with patch('sdk.project_copy.capture_export_inputs',side_effect=drift):
            with self.assertRaisesRegex(ProjectError,'metadata changed'):review(p)
        r=review(p);original_open=ProjectService.open
        def open_and_drift(path):
            clone=original_open(path);p.name+=' changed';return clone
        with patch('sdk.project_copy.ProjectService.open',side_effect=open_and_drift):
            with self.assertRaisesRegex(ProjectError,'no completion report'):create_copy(p,'Copy',r['review_key'])
        folders=list((p.root/'ProjectCopies').iterdir());self.assertEqual(len(folders),1)
        self.assertFalse((folders[0]/'copy-report.json').exists())

    def test_reparse_output_rejected_without_following_link(self):
        import stat
        from types import SimpleNamespace
        p=self.p;r=review(p);original=Path.lstat
        def linked(path,*args,**kwargs):
            if path.name=='ProjectCopies':return SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=0x400)
            return original(path,*args,**kwargs)
        with patch('pathlib.Path.lstat',linked):
            with self.assertRaisesRegex(ProjectError,'reparse'):create_copy(p,'Copy',r['review_key'])
        self.assertFalse((p.root/'ProjectCopies').exists())

    def test_empty_project_and_unique_destinations(self):
        p=ProjectService(self.p.root/'blank');r=review(p)
        a=create_copy(p,'First',r['review_key']);b=create_copy(p,'Second',r['review_key'])
        self.assertNotEqual(a['copied_project'],b['copied_project'])
        self.assertFalse((p.root/'project.legaia.json').exists())
        self.assertEqual(ProjectService.open(Path(a['copied_project'])).imports,{})

    def test_http_whitelist_copy_and_dirty_open_guard(self):
        import threading
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        from sdk.server import EditorServer
        p=self.p;p.command(dict(type='set_transform',entity_id=self.actor,position={'x':128}))
        server=EditorServer(('127.0.0.1',0),p);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def post(route,body):
            request=Request(f'http://127.0.0.1:{server.server_port}{route}',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            with urlopen(request,timeout=10) as response:return json.load(response)
        try:
            for route,body in [('/api/project/copy-review',{'path':'outside'}),('/api/project/copy',{'name':'Copy','review_key':'bad','output':'outside'})]:
                with self.assertRaises(HTTPError) as error:post(route,body)
                self.assertEqual(error.exception.code,400);error.exception.close()
            r=post('/api/project/copy-review',{});created=post('/api/project/copy',{'name':'HTTP copy','review_key':r['review_key']})
            self.assertIs(server.project,p);self.assertTrue(p.dirty);self.assertEqual(len(p.undo_stack),1)
            with self.assertRaises(HTTPError) as error:post('/api/project/open',{'path':created['copied_project']})
            self.assertEqual(error.exception.code,400);error.exception.close()
            p.undo();post('/api/project/open',{'path':created['copied_project']})
            self.assertEqual(server.project.overrides[self.actor]['Transform']['position']['x'],128)
            self.assertFalse(server.project.dirty)
        finally:server.shutdown();server.server_close();thread.join(timeout=10)
