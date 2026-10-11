from hashlib import sha256
from copy import deepcopy
from unittest import TestCase
from pathlib import Path
import tempfile
from urllib.request import urlopen
from importer.core import ImportError
from importer.worldmap_object_script import inspect_object_script


class WorldObjectScriptTests(TestCase):
    def test_http_module_delivery_and_exact_read_only_request(self):
        from sdk.project import ProjectService
        from test_project_workflow import synthetic_scene
        from test_model_primitive_workflow import http_server
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.import_metadata(synthetic_scene());held=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
            with http_server(p) as (server,post):
                with urlopen(f'http://127.0.0.1:{server.server_address[1]}/worldmap-object-script.js') as response:
                    self.assertIn(b'qualifyWorldObjectScript',response.read())
                body=dict(scene='map01',source_key='0'*64,entity_id='foreign')
                for bad in ({},body,{**body,'extra':True}):self.assertEqual(post('/api/worldmap-object-script',bad)[0],400)
            self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)

    def test_header_entry_unknown_stop_and_source_immutability(self):
        payload=bytes([1,10,20,0,0x21,0])
        bind=dict(status='resolved_source_header',man_record=dict(partition=0,record_index=2,
            flat_record_index=2,byte_offset=3,byte_length=len(payload),sha256=sha256(payload).hexdigest(),header=dict(byte_length=4)))
        held=deepcopy(bind);man=bytes(3)+payload
        r=inspect_object_script(bind,man,'map01')
        self.assertEqual(r['entry_pc'],4);self.assertEqual(r['graph']['entry_pc'],4)
        self.assertEqual(r['graph']['instructions'][0]['mnemonic'],'NOP')
        self.assertEqual(r['graph']['instructions'][0]['byte_offset'],7)
        self.assertEqual(r['graph']['status'],'partial');self.assertTrue(r['graph']['opaque_regions'])
        self.assertEqual(r['runtime_execution'],'not_asserted');self.assertEqual(bind,held)
        for mutate in (lambda b:b.update(status='no_source_bind'),lambda b:b['man_record'].update(partition=1),lambda b:b['man_record']['header'].update(byte_length=3),lambda b:b['man_record'].update(sha256='0'*64)):
            bad=deepcopy(bind);mutate(bad)
            with self.assertRaises(ImportError):inspect_object_script(bad,man,'map01')
