from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from sdk.project import ProjectService, ProjectError
from sdk.project_changes import review, inspect, save_reviewed
from test_project_workflow import synthetic_scene


class ProjectChanges(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.p=ProjectService(Path(self.directory.name));self.p.import_metadata(synthetic_scene());self.p.save()
        self.entity=synthetic_scene()['actors'][0]['semantic_id']

    def test_exact_review_inspection_save_history_and_reopen(self):
        p=self.p;imported=deepcopy(p.imports);p.command(dict(type='set_transform',entity_id=self.entity,position=dict(x=125)))
        before=deepcopy((p._document(),p.saved_document,p.undo_stack,p.redo_stack));files={f:f.read_bytes() for f in p.root.rglob('*') if f.is_file()}
        report=review(p);self.assertEqual(report['total'],1);row=report['records'][0];self.assertEqual(row['section'],'authored');self.assertEqual(row['change'],'added')
        detail=inspect(p,report['source_key'],row['section'],row['owner_id'],row['record_key']);self.assertFalse(detail['saved_present']);self.assertEqual(detail['current'],p.overrides[self.entity])
        detail['current'].clear();self.assertEqual(before,(p._document(),p.saved_document,p.undo_stack,p.redo_stack));self.assertEqual(files,{f:f.read_bytes() for f in files})
        save_reviewed(p,report['source_key']);self.assertFalse(p.dirty);self.assertEqual(review(p)['total'],0);self.assertEqual(len(p.undo_stack),1)
        p.undo();self.assertTrue(p.dirty);self.assertEqual(review(p)['records'][0]['change'],'removed');p.redo();self.assertFalse(p.dirty)
        reopened=ProjectService.open(p.root);self.assertEqual(review(reopened)['total'],0);self.assertEqual(p.imports,imported)

    def test_stale_save_and_inspection_refuse_without_writing(self):
        p=self.p;report=review(p);saved=(p.root/'project.legaia.json').read_bytes();p.name='Changed'
        with self.assertRaises(ProjectError):save_reviewed(p,report['source_key'])
        with self.assertRaises(ProjectError):inspect(p,report['source_key'],'name',None,'0'*64)
        self.assertEqual((p.root/'project.legaia.json').read_bytes(),saved)

    def test_retained_source_dirty_sections_and_type_exactness(self):
        p=self.p
        for field,label in [('model_sources','Retained model inputs'),('animation_sources','Retained animation inputs')]:
            setattr(p,field,{'source://fixture':{'test':True}});self.assertIn(label,p.unsaved_sections);self.assertIn(field,{row['section'] for row in review(p)['records']});setattr(p,field,{})
        p.name=1;p._mark_saved();p.name=True;self.assertEqual(review(p)['records'][0]['section'],'name')

    def test_pagination_unknown_values_missing_and_bad_offsets(self):
        p=self.p;p.actor_templates={f'fixture-{i}':{'unknown':None} for i in range(53)}
        self.assertEqual(review(p)['next_offset'],50);tail=review(p,50);self.assertEqual(len(tail['records']),3)
        row=tail['records'][0];value=inspect(p,tail['source_key'],row['section'],row['owner_id'],row['record_key']);self.assertEqual(value['current'],{'unknown':None})
        for offset in (True,-1,54,'0'):
            with self.assertRaises(ProjectError):review(p,offset)
        with self.assertRaises(ProjectError):inspect(p,tail['source_key'],row['section'],row['owner_id'],'bad')

    def test_new_project_snapshot_and_tampered_snapshot(self):
        p=ProjectService(self.p.root/'new');r=review(p);self.assertFalse(r['saved_snapshot_present']);self.assertTrue(r['dirty']);self.assertIn('actor_templates',{row['section'] for row in r['records']})
        self.p.saved_document['name']='tampered'
        with self.assertRaises(ProjectError):review(self.p)

    def test_detail_size_bound_refuses_without_mutation(self):
        p=self.p;p.actor_templates={'fixture':{'unknown':'x'*(8*1024*1024)}}
        report=review(p);row=report['records'][0];key=report['source_key']
        with self.assertRaisesRegex(ProjectError,'8 MiB'):inspect(p,key,row['section'],row['owner_id'],row['record_key'])
        self.assertEqual(review(p)['source_key'],key)


if __name__=='__main__':unittest.main()
