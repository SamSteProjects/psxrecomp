"""Private pack interchange: original source positions, crops and API guards."""
import base64,json,os,struct,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.battle_character_resources import resources,animations,preview,pose,export
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class BattlePackExportTests(unittest.TestCase):
    def test_glb_source_pixels_positions_and_refusals(self):
        from importer.texture_png import decode_png
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];key=source_key(p);context=dict(expected_project_path=str(p.root),expected_source_key=key);r=resources(p,**context);an=animations(p,**context);held=deepcopy((p._document(),p.undo_stack))
            with http_server(p) as (_,post):
                for slot,model in enumerate(r['catalog']['models']):
                    raw=preview(p,**context,asset_id=model['semantic_id'],catalog_source_key=r['catalog']['source_key'],palette_index=0)['preview']
                    for selected in ([False,True] if slot<3 else [False]):
                        clip=an['catalog']['clips'][slot*9] if slot<3 else None;frame=clip['frame_count']-1 if clip else None
                        args=dict(context,model_id=model['semantic_id'],model_source_key=r['catalog']['source_key'],animation_id=clip['semantic_id'] if selected else None,animation_source_key=an['catalog']['source_key'] if selected else None,frame_index=frame if selected else None)
                        status,value=post('/api/battle-pack-export',args);self.assertEqual(status,200,value)
                        content=base64.b64decode(value['glb_base64']);self.assertEqual(len(content),value['audit']['byte_length']);self.assertEqual(value['audit']['posed'],selected)
                        length=struct.unpack_from('<I',content,12)[0];doc=json.loads(content[20:20+length]);binary=content[28+length:]
                        self.assertNotIn('skins',doc);self.assertNotIn('animations',doc)
                        vertices=pose(p,**context,model_id=model['semantic_id'],animation_id=clip['semantic_id'],model_source_key=r['catalog']['source_key'],animation_source_key=an['catalog']['source_key'],frame_index=frame)['geometry']['vertices'] if selected else raw['vertices']
                        corners=0
                        for node in doc['nodes']:
                            if 'mesh' not in node:continue
                            obj=node['extras']['source_object']
                            for prim in doc['meshes'][node['mesh']]['primitives']:
                                a=doc['accessors'][prim['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0);positions=list(struct.iter_unpack('<3f',binary[offset:offset+a['count']*12]))
                                tris=[t for t in range(obj['triangle_start'],obj['triangle_start']+obj['triangle_count']) if raw['triangle_materials'][t]==prim['material']]
                                expected=[]
                                for t in tris:
                                    for c in (0,2,1):
                                        x,y,z=vertices[raw['triangles'][t][c]];expected.append((x,-y,z))
                                self.assertEqual(len(positions),len(expected));corners+=len(positions)
                                for actual,target in zip(positions,expected):
                                    for a,b in zip(actual,target):self.assertAlmostEqual(a,b,delta=0.0002)
                        self.assertEqual(corners,len(raw['triangles'])*3)
                        matched=[t for t in raw['textures'] if t['status']=='address_match'];self.assertEqual(len(doc.get('images',[])),len(matched))
                        for image,t in zip(doc.get('images',[]),matched):
                            v=doc['bufferViews'][image['bufferView']];png=decode_png(binary[v['byteOffset']:v['byteOffset']+v['byteLength']]);self.assertEqual(png['rgba'],base64.b64decode(t['rgba_base64']))
                for change in [dict(extra=True),dict(expected_source_key='0'*64),dict(model_source_key='0'*64),dict(model_id='foreign'),dict(animation_id=None,animation_source_key='0'*64),dict(frame_index=True)]:
                    self.assertEqual(post('/api/battle-pack-export',dict(args,**change))[0],400)
                selected_args=dict(args,model_id=r['catalog']['models'][0]['semantic_id'],animation_id=an['catalog']['clips'][0]['semantic_id'],animation_source_key=an['catalog']['source_key'],frame_index=0)
                for change in [dict(frame_index=True),dict(frame_index=999),dict(animation_source_key='0'*64),dict(animation_id=an['catalog']['clips'][9]['semantic_id'])]:
                    self.assertEqual(post('/api/battle-pack-export',dict(selected_args,**change))[0],400)
            self.assertEqual((p._document(),p.undo_stack),held)
