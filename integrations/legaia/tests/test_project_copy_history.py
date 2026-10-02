"""Copy discovery records saved metadata changes without promising input integrity."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError,canonical
from sdk.project_copy import review,create_copy
from sdk.project_copy_history import list_copies
from test_project_workflow import synthetic_scene


class ProjectCopyHistory(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.p=ProjectService(Path(self.directory.name));self.p.import_metadata(synthetic_scene());self.p.save()
    def copy(self,name='Saved copy'):
        return create_copy(self.p,name,review(self.p)['review_key'])
    def test_fresh_service_lists_current_name_and_changed_saved_metadata_without_writes(self):
        p=self.p;created=self.copy();before={str(f):f.read_bytes() for f in p.root.rglob('*') if f.is_file()}
        reopened=ProjectService.open(p.root);listing=list_copies(reopened);row=listing['copies'][0]
        self.assertEqual(row['status'],'recorded_copy');self.assertEqual(row['saved_metadata_state'],'matches_creation')
        self.assertEqual(row['current_inputs_validation'],'not_checked')
        self.assertEqual(before,{str(f):f.read_bytes() for f in p.root.rglob('*') if f.is_file()})
        clone=ProjectService.open(Path(created['copied_project']));clone.name='Edited copy';clone.save()
        row=list_copies(reopened)['copies'][0];self.assertEqual(row['name'],'Edited copy');self.assertEqual(row['creation_name'],'Saved copy')
        self.assertEqual(row['saved_metadata_state'],'changed_since_creation');self.assertFalse(reopened.dirty)
        self.assertEqual(json.loads((clone.root/'copy-report.json').read_bytes()),created)
    def test_incomplete_foreign_and_unsafe_inventory_are_unavailable(self):
        p=self.p;created=self.copy();folder=Path(created['copied_project']);receipt=folder/'copy-report.json';receipt_bytes=receipt.read_bytes()
        for change in [{'source_project':'elsewhere'},{'copied_project':'elsewhere'},{'retail_disc_included':True},{'files':[{'path':'../outside','sha256':'f'*64,'byte_length':1}]}]:
            receipt.write_bytes(canonical({**created,**change}));self.assertEqual(list_copies(p)['copies'][0]['status'],'incomplete_or_invalid')
        receipt.write_bytes(receipt_bytes);empty=p.root/'ProjectCopies'/('project-'+'f'*32);empty.mkdir()
        row=next(row for row in list_copies(p)['copies'] if row['id']==empty.name);self.assertEqual(row['saved_metadata_state'],'unavailable')
        (folder/'project.legaia.json').write_bytes(b'corrupt');self.assertEqual(list_copies(p)['copies'][0]['status'],'incomplete_or_invalid')
    def test_list_does_not_claim_authored_file_integrity(self):
        p=self.p;created=self.copy();folder=Path(created['copied_project']);imported=next((folder/'Imported').iterdir());imported.write_bytes(b'corrupt')
        row=list_copies(p)['copies'][0];self.assertEqual(row['status'],'recorded_copy');self.assertEqual(row['current_inputs_validation'],'not_checked')
        with self.assertRaises(ProjectError):ProjectService.open(folder)
    def test_bounds_identity_order_mode_and_reparse(self):
        p=self.p;self.copy('A');self.copy('B')
        listing=list_copies(p);self.assertEqual([x['id'] for x in listing['copies']],sorted(x['id'] for x in listing['copies']))
        with patch('sdk.project_copy_history.MAX_COPIES',1):
            listing=list_copies(p);self.assertTrue(listing['truncated']);self.assertEqual(len(listing['copies']),1)
        with patch('sdk.project_copy_history.MAX_ENTRIES',1):self.assertTrue(list_copies(p)['truncated'])
        with patch('sdk.project_copy_history.MAX_RESPONSE',1):
            with self.assertRaisesRegex(ProjectError,'2 MiB'):list_copies(p)
        with patch('sdk.build_history.MAX_METADATA',1):
            self.assertTrue(all(row['status']=='incomplete_or_invalid' for row in list_copies(p)['copies']))
        p.mode='live'
        with self.assertRaises(ProjectError):list_copies(p)
        p.mode='edit'
        with patch('sdk.project_copy_history._guard_output',side_effect=ProjectError('reparse')):
            with self.assertRaisesRegex(ProjectError,'reparse'):list_copies(p)
    def test_stale_source_during_listing_rejects(self):
        from sdk.project_copy_history import _entry
        p=self.p;self.copy()
        def drift(*args):result=_entry(*args);p.name='Changed';return result
        with patch('sdk.project_copy_history._entry',side_effect=drift):
            with self.assertRaisesRegex(ProjectError,'changed while'):list_copies(p)
    def test_http_empty_body_only_and_normal_open_validation(self):
        import threading
        from urllib.error import HTTPError
        from urllib.request import Request,urlopen
        from sdk.server import EditorServer
        created=self.copy();server=EditorServer(('127.0.0.1',0),ProjectService.open(self.p.root));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def post(route,body):
            request=Request(f'http://127.0.0.1:{server.server_port}{route}',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            with urlopen(request,timeout=10) as response:return json.load(response)
        try:
            with self.assertRaises(HTTPError) as error:post('/api/project/copies',{'path':'outside'})
            self.assertEqual(error.exception.code,400);error.exception.close()
            listing=post('/api/project/copies',{});self.assertEqual(listing['copies'][0]['path'],created['copied_project'])
            folder=Path(created['copied_project']);next((folder/'Imported').iterdir()).write_bytes(b'corrupt')
            with self.assertRaises(HTTPError) as error:post('/api/project/open',{'path':created['copied_project']})
            self.assertEqual(error.exception.code,400);error.exception.close();self.assertEqual(server.project.root,self.p.root)
        finally:server.shutdown();server.server_close();thread.join(timeout=10)
