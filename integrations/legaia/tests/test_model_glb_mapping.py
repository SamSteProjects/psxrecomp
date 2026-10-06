"""Explicit model ownership remains source-qualified and Review choice-bound."""
from copy import deepcopy
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import patch
import unittest
from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_glb import export_model_glb, import_model_glb
from sdk.model_glb import preview_import, apply_import
from sdk.project import ProjectError
from test_model_glb import synthetic, rewrite


def external(doc, binary):
    for index,node in enumerate(doc['nodes']):
        node.pop('extras',None);node['name']=f'External part {index}'


class ModelObjectMapping(unittest.TestCase):
    def setUp(self):
        self.source=synthetic(((0x22,), (0x22,)))
        self.glb,self.profile=export_model_glb(self.source,decode_tmd(self.source))
        self.external=rewrite(self.glb,external)

    def test_unlabelled_external_meshes_roundtrip_and_native_material_faces_agree(self):
        with self.assertRaises(ImportError):import_model_glb(self.source,self.external,self.profile)
        candidate,_=import_model_glb(self.source,self.external,self.profile,object_node_indices=[0,1])
        self.assertEqual(candidate,self.source)
        from sdk.model_glb_material_selection import _face_rows
        for material in range(2):
            self.assertEqual(_face_rows(self.source,self.glb,material),_face_rows(self.source,self.external,material,[0,1]))

    def test_reordered_external_nodes_and_hierarchy_bake_same_native_edit(self):
        def edit(doc,binary):
            external(doc,binary)
            doc['nodes'][1]['translation']=[3,-4,5]
        original=rewrite(self.glb,edit)
        expected,_=import_model_glb(self.source,original,self.profile,object_node_indices=[0,1])
        def reordered(doc,binary):
            doc['nodes'].reverse()
            doc['nodes'].append(dict(name='Parent',children=[0,1],scale=[1,1,1]))
            doc['scenes'][0]['nodes']=[2]
        candidate,_=import_model_glb(self.source,rewrite(original,reordered),self.profile,object_node_indices=[1,0])
        self.assertNotEqual(candidate,self.source);self.assertEqual(candidate,expected)

    def test_invalid_incomplete_duplicate_detached_conflicting_and_unmapped_nodes_reject(self):
        for mapping in ([],[0],[0,0],[0,2],[0,1024],[0,True],[0,1.0],(0,1)):
            with self.subTest(mapping=mapping),self.assertRaises(ImportError):
                import_model_glb(self.source,self.external,self.profile,object_node_indices=mapping)
        with self.assertRaises(ImportError):
            import_model_glb(self.source,self.glb,self.profile,object_node_indices=[1,0])
        def extra(doc,binary):doc['nodes'].append(dict(name='Unowned mesh',mesh=0));doc['scenes'][0]['nodes'].append(2)
        with self.assertRaises(ImportError):
            import_model_glb(self.source,rewrite(self.external,extra),self.profile,object_node_indices=[0,1])
        def detached(doc,binary):doc['scenes'][0]['nodes']=[0]
        with self.assertRaises(ImportError):
            import_model_glb(self.source,rewrite(self.external,detached),self.profile,object_node_indices=[0,1])

    def test_review_binds_mapping_even_when_native_bytes_are_identical(self):
        asset='asset://town01/models/scene-tmd/0000'
        binding=dict(schema_version='legaia.model-glb-binding.v1',asset_id=asset,scene_id='scene://town01',
                     source_sha256=sha256(self.source).hexdigest(),effective_sha256=sha256(self.source).hexdigest(),
                     project_source_key='a'*64,profile=self.profile)
        snapshot=dict(binding=binding,retail=self.source,effective=self.source,glb=self.glb)
        def translate(doc,binary):
            external(doc,binary)
            for node in doc['nodes']:node['translation']=[1,0,0]
        content=rewrite(self.glb,translate)
        choices=[dict(deepcopy(binding),external_object_nodes=m) for m in ([0,1],[1,0])]
        publications=[];project=SimpleNamespace(set_model_replacement=lambda asset,candidate:publications.append(candidate))
        with patch('sdk.model_glb._snapshot',side_effect=lambda *a:deepcopy(snapshot)),patch('sdk.model_glb._current'):
            reviews=[preview_import(project,asset,content,b) for b in choices]
            self.assertEqual(reviews[0]['proposed_sha256'],reviews[1]['proposed_sha256'])
            self.assertNotEqual(reviews[0]['review_key'],reviews[1]['review_key'])
            with self.assertRaises(ProjectError):apply_import(project,asset,content,choices[1],reviews[0]['review_key'])
            self.assertEqual(publications,[])
            apply_import(project,asset,content,choices[1],reviews[1]['review_key']);self.assertEqual(len(publications),1)
            with self.assertRaises(ProjectError):preview_import(project,asset,content,dict(binding,external_object_nodes=None))


if __name__=='__main__':unittest.main()
