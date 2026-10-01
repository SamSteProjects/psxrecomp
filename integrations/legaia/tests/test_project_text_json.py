"""Atomic, source-bound external text files preserve editor state and MAN spans."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError, canonical
from test_importer_dialogue_authoring import fixture, ACTOR
from test_project_workflow import synthetic_scene
from importer.core import ImportError

class TextJSONTests(unittest.TestCase):
    def test_complete_file_preview_atomic_history_clear_and_noop(self):
        context,_=fixture(b"\x1fHello\x5e\x2dWorld\0")
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            p.command(dict(type='set_transform',entity_id=ACTOR,position={'x':128}))
            with patch.object(p,'_dialogue_context',return_value=context):
                source=p.dialogue_json_source(ACTOR);before=deepcopy(p.overrides);history=len(p.undo_stack)
                self.assertEqual(p.import_dialogue_json(ACTOR,canonical(source))['change_count'],0)
                self.assertEqual(len(p.undo_stack),history)
                document=deepcopy(source);document['runs'][0]['text']='OK';document['runs'][1]['text']='Next'
                self.assertEqual(p.preview_dialogue_json(ACTOR,canonical(document))['change_count'],2)
                self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),history)
                p.import_dialogue_json(ACTOR,canonical(document));self.assertEqual(len(p.undo_stack),history+1)
                authored=deepcopy(p.overrides);self.assertEqual(p.overrides[ACTOR]['Transform'],before[ACTOR]['Transform'])
                p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(p.overrides,authored)
                with self.assertRaisesRegex(ProjectError,'stale'):
                    p.import_dialogue_json(ACTOR,canonical(document))
                clear=p.dialogue_json_source(ACTOR)
                for run in clear['runs']:run['text']=None
                p.import_dialogue_json(ACTOR,canonical(clear));self.assertEqual(p.overrides,before)
            restored=ProjectService.open(p.save());self.assertEqual(restored.overrides,before)

    def test_rejected_files_never_change_history_or_overrides(self):
        context,_=fixture(b"\x1fHello\0")
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            with patch.object(p,'_dialogue_context',return_value=context):
                source=p.dialogue_json_source(ACTOR);before=deepcopy(p.state())
                mutations=[lambda d:d.update(owner_id='other'),lambda d:d.update(decoded_man_sha256='0'*64),
                    lambda d:d.update(authored_state_sha256='0'*64),lambda d:d.update(extra=True),
                    lambda d:d['runs'].clear(),lambda d:d['runs'].append(deepcopy(d['runs'][0])),
                    lambda d:d['runs'][0].update(byte_length=True),lambda d:d['runs'][0].update(retail_text='Wrong'),
                    lambda d:d['runs'][0].update(text='Longer'),lambda d:d['runs'][0].update(text='^'),lambda d:d['runs'][0].update(text='|'),
                    lambda d:d['runs'][0].update(text=3),lambda d:d['runs'][0].update(run_id='bad')]
                for mutate in mutations:
                    document=deepcopy(source);mutate(document)
                    with self.assertRaises((ProjectError,ImportError)):p.import_dialogue_json(ACTOR,canonical(document))
                    self.assertEqual(p.state(),before);self.assertEqual(p.undo_stack,[])
                for content in (b'',b'x',b'{"x":1,"x":2}',b'{"x":NaN}',bytes(1024*1024+1)):
                    with self.assertRaises(ProjectError):p.preview_dialogue_json(ACTOR,content)
                p.mode='live'
                with self.assertRaisesRegex(ProjectError,'Edit mode'):p.import_dialogue_json(ACTOR,canonical(source))

if __name__=='__main__':unittest.main()
