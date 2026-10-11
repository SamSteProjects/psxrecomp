from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
from importer.core import ImportError
from importer.worldmap_scripted_export import group_metadata,scripted_group_ids
from sdk.project import ProjectError
from sdk.worldmap_scripted_export import export


class ScriptedGroupExportTests(TestCase):
 def test_canonical_membership_and_scripted_kind_ownership(self):
  ids=[f'placement://authored/00000000-0000-4000-8000-{i:012x}' for i in range(1,34)]
  meta=dict(authored_scripted_placements=[dict(placement_id=i) for i in ids[:2]],authored_decorations=[dict(placement_id=ids[2])])
  held=deepcopy(meta)
  with patch('importer.worldmap_scripted_export.qualify_source',return_value=meta):
   result=group_metadata({},'a'*64,ids[:2]);self.assertEqual(result['selected_placement_ids'],ids[:2])
   result['selected_placement_ids'].clear();self.assertEqual(meta,held)
   for bad in [ids[2:3],ids[:1]+ids[2:3]]:
    with self.assertRaisesRegex(ImportError,'ownership'):group_metadata({},'a'*64,bad)
  for bad in [[],ids[:2][::-1],[ids[0],ids[0]],ids,[True],['foreign'],None]:
   with self.assertRaises(ImportError):scripted_group_ids(bad)
  returned=scripted_group_ids(ids[:32]);returned.clear();self.assertEqual(len(ids),33)

 def test_malformed_or_mixed_scope_refuses_before_read_and_write(self):
  identifier='placement://authored/00000000-0000-4000-8000-000000000001'
  with patch('sdk.worldmap_scripted_export.inspect',side_effect=AssertionError('must not read')),patch('sdk.worldmap_scripted_export.write_encoded_glb',side_effect=AssertionError('must not write')):
   for ids in [[],[True],[identifier,identifier],['foreign']]:
    with self.assertRaises(ImportError):export(None,'map01','a'*64,'selected-authored',placement_ids=ids)
   for scope,entity,ids in [('ground',None,[identifier]),('selected-authored','foreign',[identifier]),('selected-authored',None,None),('selected',None,None)]:
    with self.assertRaises(ProjectError):export(None,'map01','a'*64,scope,entity,ids)
