from copy import deepcopy
import unittest
from importer.scene_export import encode_scene_glb, select_scene_export_instance
from importer.core import ImportError
from test_importer_export import preview, parse_glb
from test_animation_clip_export import values

class SceneExportTests(unittest.TestCase):
    def test_shared_geometry_preserves_instance_transform_and_source(self):
        model=preview()
        scene={'schema':'legaia.scene-preview.v1','coordinate_system':'editor_field_y_up_source_units',
               'scene_id':'scene://synthetic','source_key':'verified',
               'assets':[{'geometry_key':'one','preview':model}], 'entities':[]}
        for i in range(2):
            scene['entities'].append({'entity_id':f'actor-{i}','renderable':True,'geometry_key':'one',
              'model_to_scene':[0,0,1,10+i*100, 0,-1,0,20, -1,0,0,30, 0,0,0,1]})
        before=deepcopy(scene);raw,audit=encode_scene_glb(scene);doc,binary=parse_glb(raw)
        self.assertEqual(scene,before);self.assertEqual(audit['entity_count'],2)
        self.assertEqual(len(doc['meshes']),1)
        for index,root in enumerate(doc['scenes'][0]['nodes']):
            parent=doc['nodes'][root];child=doc['nodes'][parent['children'][0]]
            self.assertEqual(child['mesh'],0)
            positions=values(doc,binary,doc['meshes'][0]['primitives'][0]['attributes']['POSITION'])
            for x,y,z in positions:
                m=parent['matrix'];world=[sum(m[c*4+r]*v for c,v in enumerate([x,y,z,1])) for r in range(3)]
                self.assertEqual(world,[z+10+index*100,y+20,-x+30])
        selected=select_scene_export_instance(scene,'actor-1')
        selected_raw,selected_audit=encode_scene_glb(selected)
        selected_doc,_=parse_glb(selected_raw)
        self.assertEqual(selected_audit['export_scope'],'selected-instance')
        self.assertEqual(selected_audit['selected_entity_id'],'actor-1')
        self.assertEqual(len(selected_doc['scenes'][0]['nodes']),1)
        self.assertEqual(selected_doc['nodes'][0]['matrix'],doc['nodes'][doc['scenes'][0]['nodes'][1]]['matrix'])
        self.assertEqual(scene,before)
        for identifier in ('missing','',None):
            with self.assertRaises(ImportError):select_scene_export_instance(scene,identifier)
        empty=deepcopy(scene);empty['assets']=[]
        for entity in empty['entities']:entity['renderable']=False
        with self.assertRaises(ImportError):encode_scene_glb(empty)
        scene['entities'][1]['geometry_key']='missing'
        with self.assertRaises(ImportError):encode_scene_glb(scene)
