"""Authored trigger edges retain Retail references and qualify actual MAP/P2 sources."""
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import os
import tempfile
import unittest
from sdk.project import ProjectService,ProjectError,digest
from sdk.resources import refresh_resource_catalog
from sdk.trigger_scripts import review,apply
from sdk.asset_references import assemble,assemble_project,inspect,inspect_project
from importer.pipeline import import_scene

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class EffectiveTriggerReferences(unittest.TestCase):
    def test_retail_and_effective_edges_active_project_inverse_and_undo(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'vell'),os.environ['LEGAIA_DISC_BIN'])
            catalog=refresh_resource_catalog(p);row=next(r for r in catalog['records'] if r['kind']=='trigger' and r.get('table_source')=='primary' and r.get('table_kind')==1 and r.get('encoded',{}).get('gate')==1)
            before=assemble(p,catalog,row['id']);retail=next(e for e in before['outgoing'] if e['kind']=='field_trigger_script_reference');initial=review(p,row['id']);target=next(t for t in initial['targets'] if t['script_id']!=retail['target_id']);proposed=review(p,row['id'],target['script_id']);apply(p,dict(type='apply_trigger_scripts',trigger_id=row['id'],script_id=target['script_id'],action='set',review_key=proposed['review_key']))
            state=deepcopy(p._document());report=inspect(p,row['id']);effective=next(e for e in report['outgoing'] if e['kind']=='effective_field_trigger_script_reference')
            self.assertEqual(next(e for e in report['outgoing'] if e['kind']=='field_trigger_script_reference'),retail)
            self.assertEqual(effective['layer'],'effective');self.assertEqual(effective['target_id'],target['script_id']);self.assertEqual(effective['runtime_binding'],'not_asserted')
            proof=effective['trigger_reference_evidence'];binding=effective['trigger_binding_evidence']
            self.assertEqual(proof['trigger_source_record_sha256'],row['source_record']['sha256']);self.assertEqual(proof['script_source_record_sha256'],target['source_sha256']);self.assertEqual(binding['component_sha256'],digest(p.overrides[p.active_scene]['TriggerScripts']));self.assertEqual(binding['target_byte_offset'],row['source_record']['byte_offset']+2)
            inverse=inspect(p,target['script_id']);self.assertIn(effective,inverse['incoming']);project=inspect_project(p,row['id']);self.assertIn(effective,project['outgoing']);self.assertEqual(p._document(),state)
            for mutate in (lambda c:c['records'].remove(next(r for r in c['records'] if r['id']==target['script_id'])),lambda c:next(r for r in c['records'] if r['id']==target['script_id'])['source_record'].update(sha256='0'*64),lambda c:next(r for r in c['records'] if r['id']==row['id'])['source_record'].update(sha256='0'*64)):
                bad=deepcopy(catalog);mutate(bad)
                with self.assertRaises(ProjectError):assemble(p,bad,row['id'])
            self.assertEqual(p._document(),state);p.undo();self.assertFalse(any(e['kind']=='effective_field_trigger_script_reference' for e in inspect(p,row['id'])['outgoing']))
