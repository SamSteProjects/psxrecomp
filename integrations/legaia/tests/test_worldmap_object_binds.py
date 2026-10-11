from copy import deepcopy
import struct
from unittest import TestCase
from pathlib import Path
import tempfile
from urllib.request import urlopen

from importer.core import ImportError
from importer.worldmap_object_binds import resolve_object_bind


def fixture(counts=(2,0,0)):
    base=0x2b+6
    data=bytearray(base+4+18)
    struct.pack_into('<3h',data,0x22,*counts)
    data[0x28:0x2b]=(4).to_bytes(3,'little')
    data[0x2b:0x2e]=(0).to_bytes(3,'little')
    data[0x2e:0x31]=(2).to_bytes(3,'little')
    data[base:base+4]=bytes([0,5,0,7])
    def hit(table,index,record):
        return dict(semantic_id=f'trigger://map01/{table}/{index}',
            table_source=table,table_kind=1,record_index=index,
            encoded=dict(tile_x=8,tile_z=9,record_index=record,gate=0))
    return bytes(data),dict(assets=[hit('fallback',0,1),hit('primary',0,0)])


class WorldObjectBindTests(TestCase):
    def test_http_module_delivery_and_exact_request_fields(self):
        from sdk.project import ProjectService
        from test_project_workflow import synthetic_scene
        from test_model_primitive_workflow import http_server
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.import_metadata(synthetic_scene())
            held=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
            with http_server(p) as (server,post):
                with urlopen(f'http://127.0.0.1:{server.server_address[1]}/worldmap-object-bind.js') as response:
                    self.assertIn(b'qualifyWorldObjectBind',response.read())
                for body in ({},{'scene':'map01','source_key':'0'*64,'entity_id':'foreign'},
                             {'scene':'map01','source_key':'0'*64,'entity_id':'foreign','extra':True}):
                    self.assertEqual(post('/api/worldmap-object-bind',body)[0],400)
            self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)

    def test_primary_precedence_header_and_immutable_inputs(self):
        man,catalog=fixture();before=deepcopy(catalog)
        r=resolve_object_bind(catalog,man,8,9)
        self.assertEqual(r['status'],'resolved_source_header')
        self.assertEqual(r['encoded_animation_selector'],5)
        self.assertEqual(r['man_record']['flat_record_index'],0)
        self.assertEqual(r['shadowed_trigger_ids'],['trigger://map01/fallback/0'])
        self.assertEqual(r['animation_clip'],'not_resolved')
        self.assertEqual(catalog,before)
        self.assertEqual(resolve_object_bind(catalog,man,7,9)['status'],'no_source_bind')

    def test_fallback_flat_partition_and_header_refusals(self):
        man,catalog=fixture((1,1,0));catalog['assets']=catalog['assets'][:1]
        r=resolve_object_bind(catalog,man,8,9)
        self.assertEqual(r['status'],'unsupported_header_partition')
        self.assertIsNone(r['encoded_animation_selector'])
        for kind in ('index','alias','header','section'):
            with self.subTest(kind=kind):
                man,catalog=fixture();data=bytearray(man)
                if kind=='index':catalog['assets'][1]['encoded']['record_index']=9
                if kind=='alias':data[0x2e:0x31]=bytes(3)
                if kind=='header':data[0x31]=1
                if kind=='section':data[0x2b:0x2e]=(4).to_bytes(3,'little')
                with self.assertRaises(ImportError):resolve_object_bind(catalog,bytes(data),8,9)
        for col,row in ((True,9),(-1,9),(8,128)):
            with self.assertRaises(ImportError):resolve_object_bind(catalog,man,col,row)
