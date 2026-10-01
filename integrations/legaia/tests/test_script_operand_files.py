import json,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError,digest
from importer.core import ImportError as RetailImportError
from sdk.script_operand_files import parse,review,export_file,SCHEMA
from test_project_workflow import synthetic_scene
from test_importer_dialogue_authoring import fixture,ACTOR

class OperandFiles(unittest.TestCase):
 def test_source_bound_multi_component_atomic_roundtrip_and_stale_rejection(self):
  context,_=fixture(b'\x23\0\x80\x2e\xe2\x4a\1\1\x4c\x50\xef\0\x3f\0\0\x06town01\1\2\3opaque')
  from importer.movement_authoring import MovementAuthoringContext
  from importer.flag_authoring import FlagAuthoringContext
  from importer.wait_authoring import WaitAuthoringContext
  from importer.model_selector_authoring import ModelSelectorAuthoringContext
  from importer.transition_authoring import TransitionAuthoringContext
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.disc_path='fixture.bin'
   kinds={'ScriptMovement':(MovementAuthoringContext(context),{'x':128}),'ScriptFlags':(FlagAuthoringContext(context),{'bit':3}),'ScriptWaits':(WaitAuthoringContext(context),{'duration_ticks':512}),'ScriptModelSelectors':(ModelSelectorAuthoringContext(context),{'model_selector_signed':-1}),'Transitions':(TransitionAuthoringContext(context),{'entry_x_encoded':4})}
   components={kind:{'entries':{ctx.options(ACTOR)['targets' if kind!='Transitions' else 'transitions'][0]['semantic_id']:values}} for kind,(ctx,values) in kinds.items()}
   file=dict(schema_version=SCHEMA,scene_id=p.active_scene,source_import_sha256=digest(p.imports[p.active_scene]),owner_id=ACTOR,components=components);content=json.dumps(file)
   with patch('importer.pipeline._disc_context'),patch('sdk.resources._verify'),patch.object(ProjectService,'_dialogue_context',return_value=context):
    before=deepcopy(p.overrides);report=review(p,ACTOR,content);self.assertEqual(p.overrides,before);self.assertEqual(p.undo_stack,[]);self.assertEqual(report['change_count'],5)
    p.command(dict(type='import_script_operands',entity_id=ACTOR,content=content,review_key=report['review_key']));self.assertEqual(len(p.undo_stack),1);self.assertEqual(p.overrides[ACTOR],components)
    self.assertEqual(export_file(p,ACTOR),file);self.assertEqual(ProjectService.open(p.save()).overrides,p.overrides)
    p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(p.overrides[ACTOR],components)
    same=review(p,ACTOR,content);p.command(dict(type='import_script_operands',entity_id=ACTOR,content=content,review_key=same['review_key']));self.assertEqual(len(p.undo_stack),1)
    p.undo();p.overrides[ACTOR]={'Transform':{'position':{'x':64}}}
    with self.assertRaises(ProjectError):p.command(dict(type='import_script_operands',entity_id=ACTOR,content=content,review_key=report['review_key']))
    before=deepcopy(p.overrides);bad=deepcopy(file);bad['components']['Transitions']['entries'][next(iter(components['Transitions']['entries']))]={'entry_x_encoded':True}
    with self.assertRaises((ProjectError,RetailImportError)):review(p,ACTOR,json.dumps(bad))
    self.assertEqual(p.overrides,before)
    for mutate in [lambda f:f.update(source_import_sha256='a'*64),lambda f:f.update(owner_id='other'),lambda f:f['components'].update(Unknown={'entries':{'x':{'bit':1}}})]:
     bad=deepcopy(file);mutate(bad)
     with self.assertRaises(ProjectError):review(p,ACTOR,json.dumps(bad))
     self.assertEqual(p.overrides,before)
 def test_strict_file_boundary(self):
  for text in ['{}','{"x":1,"x":2}','{"a":NaN}',' '*65537,'[]']:
   with self.assertRaises(ProjectError):parse(text)

if __name__=='__main__':unittest.main()
