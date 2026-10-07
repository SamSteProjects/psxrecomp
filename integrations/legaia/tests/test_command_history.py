"""Focused session-history checks; no runtime or retail input required."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from sdk.project import ProjectService, ProjectError
from sdk.command_history import listing, inspect_record
from test_project_workflow import synthetic_scene


class CommandHistory(unittest.TestCase):
    def test_record_inspection_undo_redo_save_and_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            p = ProjectService(Path(directory)); p.import_metadata(synthetic_scene()); p.save()
            entity = synthetic_scene()['actors'][0]['semantic_id']
            p.command(dict(type='set_transform', entity_id=entity, position=dict(x=125)))
            before = deepcopy((p._document(), p.undo_stack, p.redo_stack))
            report = listing(p); row = report['records'][0]
            detail = inspect_record(p, report['source_key'], row['branch'], row['index'], row['record_key'])
            self.assertEqual(detail['record'], p.undo_stack[-1])
            detail['record']['after'].clear()
            self.assertEqual(before, (p._document(), p.undo_stack, p.redo_stack))
            p.undo()
            with self.assertRaises(ProjectError):
                inspect_record(p, report['source_key'], row['branch'], row['index'], row['record_key'])
            self.assertEqual(listing(p)['records'][0]['branch'], 'redo')
            p.redo(); p.save(); self.assertEqual(listing(p)['total'], 1)
            self.assertEqual(listing(ProjectService.open(p.root))['total'], 0)

    def test_pagination_exact_metadata_and_bad_selectors(self):
        with tempfile.TemporaryDirectory() as directory:
            p = ProjectService(Path(directory))
            p.undo_stack = [dict(target='project_name', before=str(i), after=str(i+1)) for i in range(53)]
            p.redo_stack = [dict(entity_id='entity://unknown', before=None, after={'unknown': True})]
            report = listing(p); self.assertEqual(len(report['records']), 50)
            self.assertEqual(report['next_offset'], 50)
            tail = listing(p, 50); self.assertEqual(len(tail['records']), 4)
            self.assertIsNone(tail['records'][-1]['recorded_target'])
            self.assertEqual(tail['records'][-1]['recorded_owners'], {'entity_id':'entity://unknown'})
            for offset in (True, -1, 55, '0'):
                with self.assertRaises(ProjectError): listing(p, offset)
            row = report['records'][0]
            for branch, index, key in [('wrong',0,row['record_key']),('undo',True,row['record_key']),('undo',999,row['record_key']),('undo',row['index'],'bad')]:
                with self.assertRaises(ProjectError): inspect_record(p,report['source_key'],branch,index,key)
            self.assertEqual(listing(p,54)['records'], [])

    def test_oversized_detail_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            p = ProjectService(Path(directory)); p.undo_stack=[dict(before=None,after='x'*(8*1024*1024))]
            report=listing(p);row=report['records'][0]
            with self.assertRaisesRegex(ProjectError,'8 MiB'):
                inspect_record(p,report['source_key'],row['branch'],row['index'],row['record_key'])


if __name__ == '__main__': unittest.main()
