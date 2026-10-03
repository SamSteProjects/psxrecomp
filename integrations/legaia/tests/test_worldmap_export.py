"""Source-seed world GLBs preserve geometry, confidence and one Y conversion."""
from copy import deepcopy
from pathlib import Path
import base64,struct,tempfile,unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.worldmap_export import adapt_worldmap_scene,encode_worldmap_glb
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_export import export
from sdk.worldmap_authoring import state_key
from test_importer_export import preview,parse_glb,read_accessor
from test_project_workflow import synthetic_scene

KEY='a'*64
GROUND='scene://map01/worldmap/ground'
SEED='scene://map01/worldmap/placements/00af'

def fixture():
    model=preview();texture=model['textures'][0];texture['rgba']=base64.b64decode(texture.pop('rgba_base64'))
    ground=deepcopy(model);ground['coordinate_system']='retail_field_y_down'
    identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
    entities=[dict(entity_id=GROUND,asset_id='asset://map01/worldmap/walk-ground',source_position=dict(x=0,y=0,z=0),source_to_world=identity,placement_scope='source_ground',runtime_visibility='not_evaluated',runtime_resting_position='unknown',renderable=True)]
    for i in range(2):
        entities.append(dict(entity_id=SEED if i==0 else 'scene://map01/worldmap/placements/01fa',asset_id='asset://map01/worldmap/models/0001',source_position=dict(x=10+i*100,y=20,z=30),source_to_world=[0,0,-1,0,0,1,0,0,1,0,0,0,10+i*100,20,30,1],placement_scope='source_spawn_seed',runtime_visibility='not_evaluated',runtime_resting_position='unknown',renderable=True,source_record_sha256='b'*64))
    graph=dict(schema_version='legaia.worldmap-scene-graph.v1',coordinate_system='retail_field_y_down',matrix_convention='column-major-affine',assets=[dict(asset_id='asset://map01/worldmap/walk-ground',preview=ground,source_record={}),dict(asset_id='asset://map01/worldmap/models/0001',preview=model,source_record=dict(decoded_member_sha256='c'*64))],entities=entities,coverage=dict(candidate_count=2,resolved_count=2,rendered_count=2,unresolved_count=0),metrics=dict(asset_count=2,entity_count=3,stored_triangle_count=2,drawn_triangle_count=3,texture_output_bytes=32),limitations=['Source spawn seeds, not runtime resting poses.'])
    return dict(schema_version='legaia.worldmap-geometry.v2',scene='map01',semantic_id='asset://map01/worldmap/walk-ground',source_record=dict(disc_sha256='0'*64,map_sha256='d'*64),scene_graph=graph,limitations=['Ground source only.'])


class WorldmapExportTests(unittest.TestCase):
    def test_shared_mesh_yaw_translation_one_reflection_uv_color_and_provenance(self):
        source=fixture();before=deepcopy(source);raw,audit=encode_worldmap_glb(source,KEY);doc,binary=parse_glb(raw)
        self.assertEqual(source,before);self.assertEqual(len(doc['meshes']),2)
        roots=doc['scenes'][0]['nodes'];meshes=[]
        for i,root in enumerate(roots[1:]):
            node=doc['nodes'][root];child=doc['nodes'][node['children'][0]];meshes.append(child['mesh']);primitive=doc['meshes'][child['mesh']]['primitives'][0]
            positions=read_accessor(doc,binary,primitive['attributes']['POSITION'])
            self.assertEqual(positions,[(0,0,0),(0,-2,0),(2,0,0)])
            for point in positions:
                m=node['matrix'];world=[sum(m[c*4+r]*v for c,v in enumerate(list(point)+[1])) for r in range(3)]
                self.assertEqual(world,[point[2]+10+i*100,point[1]-20,-point[0]+30])
            self.assertEqual(read_accessor(doc,binary,primitive['attributes']['COLOR_0']),[(1,1,1)]*3)
            self.assertEqual(read_accessor(doc,binary,primitive['attributes']['TEXCOORD_0']),[(.25,.25),(.25,.75),(.75,.25)])
            self.assertEqual(node['extras']['runtime_resting_position'],'unknown')
            self.assertEqual(node['extras']['runtime_visibility'],'not_evaluated')
        self.assertEqual(meshes[0],meshes[1]);self.assertEqual(len(doc['images']),2)
        self.assertEqual(doc['extras']['worldmap_source']['source_record'],source['source_record'])
        self.assertEqual(audit['worldmap_source']['coverage'],source['scene_graph']['coverage'])

    def test_ground_and_selected_seed_keep_original_world_transform(self):
        source=fixture();full,_=encode_worldmap_glb(source,KEY);doc,_=parse_glb(full)
        for scope,entity_id,root_index in [('ground',None,0),('selected',GROUND,0),('selected',SEED,1)]:
            raw,audit=encode_worldmap_glb(source,KEY,scope,entity_id);selected,_=parse_glb(raw)
            self.assertEqual(len(selected['scenes'][0]['nodes']),1)
            self.assertEqual(selected['nodes'][0]['matrix'],doc['nodes'][doc['scenes'][0]['nodes'][root_index]]['matrix'])
            self.assertEqual(audit['worldmap_source']['scope'],scope);self.assertEqual(len(selected['meshes']),1)
        for scope,entity_id in [('unknown',None),('ground',SEED),('selected',None),('selected','missing')]:
            with self.assertRaises(ImportError):adapt_worldmap_scene(source,KEY,scope,entity_id)

    def test_invalid_source_graph_matrix_identity_range_confidence_and_counts(self):
        for mutation in ('matrix','position','duplicate','runtime','range','indices','metrics','sourcehash'):
            with self.subTest(mutation=mutation):
                source=fixture();graph=source['scene_graph']
                if mutation=='matrix':graph['entities'][1]['source_to_world'][3]=1
                elif mutation=='position':graph['entities'][1]['source_position']['y']=21
                elif mutation=='duplicate':graph['entities'][2]['entity_id']=SEED
                elif mutation=='runtime':graph['entities'][1]['runtime_resting_position']='known'
                elif mutation=='range':graph['assets'][1]['preview']['vertices'][0][0]=1000001
                elif mutation=='indices':graph['assets'][1]['preview']['triangles'][0][2]=3
                elif mutation=='metrics':graph['metrics']['drawn_triangle_count']=2
                else:graph['assets'][1]['source_record']['decoded_member_sha256']='bad'
                with self.assertRaises(ImportError):encode_worldmap_glb(source,KEY)

    def test_sdk_exports_only_private_files_and_rejects_stale_before_write(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));document=synthetic_scene();document['source']['disc_identity']='sha256:'+'0'*64;p.import_metadata(document);p.disc_path='synthetic.bin';p.save();source=fixture()
            source['source_record']['disc_sha256']=p.imports[p.active_scene]['source']['disc_identity'].removeprefix('sha256:')
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.selected));key=state_key(p)
            with patch('sdk.worldmap_export.load_worldmap_geometry',return_value=source) as loader:
                result=export(p,'map01',key,'selected',SEED)
                self.assertEqual(Path(result['path']).read_bytes(),base64.b64decode(result['glb_base64']))
                self.assertEqual(Path(result['path']).parent,p.root/'Exports');self.assertFalse(result['project_changed'])
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack,p.selected),before)
                loader.reset_mock()
                with patch('sdk.worldmap_export.write_encoded_glb') as writer:
                    with self.assertRaises(ProjectError):export(p,'map01','stale','ground')
                    loader.assert_not_called();writer.assert_not_called()
                def drift(*args):p.name='Changed';return source
                with patch('sdk.worldmap_export.load_worldmap_geometry',side_effect=drift),patch('sdk.worldmap_export.write_encoded_glb') as writer:
                    with self.assertRaises(ProjectError):export(p,'map01',key,'ground')
                    writer.assert_not_called()
                key=state_key(p);wrong=deepcopy(source);wrong['source_record']['disc_sha256']='f'*64
                with patch('sdk.worldmap_export.load_worldmap_geometry',return_value=wrong),patch('sdk.worldmap_export.write_encoded_glb') as writer:
                    with self.assertRaises(ProjectError):export(p,'map01',key,'ground')
                    writer.assert_not_called()
                def encode_drift(*args):
                    raw,audit=encode_worldmap_glb(*args);p.name='Post-encode drift';return raw,audit
                with patch('sdk.worldmap_export.encode_worldmap_glb',side_effect=encode_drift),patch('sdk.worldmap_export.write_encoded_glb') as writer:
                    with self.assertRaises(ProjectError):export(p,'map01',key,'ground')
                    writer.assert_not_called()


if __name__=='__main__':unittest.main()
