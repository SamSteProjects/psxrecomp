from copy import deepcopy
import unittest
from importer.animation_glb import import_animation_glb
from importer.core import ImportError
from test_animation_glb import document,encode,record,changed_key
from test_animation_glb_node_identity import rename_and_reorder
class ObjectMapping(unittest.TestCase):
 def fixture(self):
  frames=[[([i*12,3,-2],[i*8,0,0]) for i in range(3)]]*3
  doc,payload=document(frames);external=rename_and_reorder(doc)
  for n in external['nodes']:n.pop('extras',None)
  return record(frames),doc,external,payload
 def test_untagged_external_rig_maps_exact_source_objects(self):
  source,doc,external,payload=self.fixture()
  with self.assertRaises(ImportError):import_animation_glb(source,encode(external,payload),fps=15)
  actual,report=import_animation_glb(source,encode(external,payload),fps=15,object_node_indices=[2,1,0])
  self.assertEqual(actual,source);self.assertEqual(report['external_object_nodes'],[2,1,0])
 def test_mapped_external_track_edits_match_exported_track_bytes(self):
  source,doc,external,payload=self.fixture();payload=changed_key(doc,payload,'translation',1,[31,-3,-2],obj=2)
  expected,a=import_animation_glb(source,encode(doc,payload),fps=15)
  actual,b=import_animation_glb(source,encode(external,payload),fps=15,object_node_indices=[2,1,0])
  self.assertEqual(actual,expected);self.assertEqual(a['changes'],b['changes'])
 def test_mapping_bounds_unique_count_and_preserved_identity_reject(self):
  source,doc,external,payload=self.fixture()
  for mapping in [[],[0,1],[0,1,1],[0,1,3],[True,1,2],['0',1,2],[-1,1,2],[10**400,1,2],{},[0,1,2,3]]:
   with self.subTest(mapping=mapping):
    with self.assertRaises(ImportError):import_animation_glb(source,encode(external,payload),fps=15,object_node_indices=mapping)
  with self.assertRaisesRegex(ImportError,'conflicts'):import_animation_glb(source,encode(doc,payload),fps=15,object_node_indices=[2,1,0])
