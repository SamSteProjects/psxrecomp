import os,struct,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from importer.player_battle import _sources,table,assemble,discover,preview
from importer.assets import decode_tmd
from importer.core import decompress_lzs,ImportError,validate_metadata_only
from sdk.project import ProjectService
from sdk.project_assets import source_key
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerBattleTests(unittest.TestCase):
    def test_every_descriptor_selection_preserves_source_objects(self):
        disc=os.environ['LEGAIA_DISC_BIN'];digest,sources=_sources(disc);catalog=discover(disc);validate_metadata_only(catalog);self.assertEqual([m['preview_summary']['objects'] for m in catalog['models']],[17,18,17,19]);checked=0
        for index,_,_,raw in sources:
            for r in table(raw):
                ids=[0]*5;ids[r['section_index']]=r['item_id'];g,a=assemble(raw,ids);self.assertEqual(a['sections'][r['section_index']]['record_index'],r['record_index']);parts={}
                for selected in a['sections']:
                    at=selected['byte_offset'];n=struct.unpack_from('<I',raw,at)[0];d,_=decompress_lzs(raw[at+4:at+selected['byte_length']],n);frame=struct.unpack_from('<I',d)[0];count=struct.unpack_from('<I',d,frame+20)[0];ds=struct.unpack_from('<I',d,frame+8)[0];end=frame+24+count*28+((ds-count*28-9)//4)*4;parts[selected['record_index']]=decode_tmd(d[frame+12:end])
                for obj,origin in zip(g['objects'],a['object_sources']):
                    p=parts[origin['record_index']];source=p['objects'][origin['source_object_index']];self.assertEqual(obj['vertex_count'],source['vertex_count']);self.assertEqual(g['vertices'][obj['vertex_start']:obj['vertex_start']+obj['vertex_count']],p['vertices'][source['vertex_start']:source['vertex_start']+source['vertex_count']]);self.assertEqual(obj['triangle_count'],source['triangle_count'])
                    for j in range(obj['triangle_count']):
                        ti=obj['triangle_start']+j;si=source['triangle_start']+j;self.assertEqual([v-obj['vertex_start'] for v in g['triangles'][ti]],[v-source['vertex_start'] for v in p['triangles'][si]]);self.assertEqual(g['triangle_uvs'][ti],p['triangle_uvs'][si]);self.assertEqual(g['triangle_colors'][ti],p['triangle_colors'][si]);self.assertEqual(g['materials'][g['triangle_materials'][ti]],p['materials'][p['triangle_materials'][si]])
                checked+=1
            default,_=assemble(raw,[0]*5);fallback,a=assemble(raw,[255]*5);self.assertEqual(default,fallback);self.assertTrue(all(s['fallback'] for s in a['sections']))
            for offset in [0,table(raw)[0]['descriptor_offset']+4,table(raw)[0]['descriptor_offset']+8]:
                bad=bytearray(raw);bad[offset:offset+4]=b'\xff'*4
                with self.assertRaises(ImportError):table(bytes(bad))
            with self.assertRaises(ImportError):table(raw+b'neighbor')
        self.assertEqual(checked,152)
        for args in [(catalog['models'][0]['semantic_id'],'0'*64,[0]*5),('foreign',catalog['source_key'],[0]*5),(catalog['models'][0]['semantic_id'],catalog['source_key'],[True]*5)]:
            with self.assertRaises(ImportError):preview(disc,*args)

    def test_project_http_is_read_only_and_source_guarded(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];context=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));held=deepcopy((p._document(),p.undo_stack))
            with http_server(p) as (_,post):
                status,r=post('/api/player-battle-resources',context);self.assertEqual(status,200)
                args=dict(context,asset_id=r['catalog']['models'][0]['semantic_id'],catalog_source_key=r['catalog']['source_key'],equipped=[0]*5);self.assertEqual(post('/api/player-battle-preview',args)[0],200)
                for change in [dict(expected_source_key='0'*64),dict(catalog_source_key='0'*64),dict(asset_id='foreign'),dict(equipped=[True]*5),dict(equipped=[0]*4),dict(extra=True)]:self.assertEqual(post('/api/player-battle-preview',dict(args,**change))[0],400)
            self.assertEqual((p._document(),p.undo_stack),held)
