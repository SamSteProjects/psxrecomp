from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from importer.scene_controller import REFERENCE_COMMIT
from sdk.project import ProjectService, ProjectError
from sdk.asset_references import assemble, assemble_project
from test_project_workflow import synthetic_scene


def controller():
    return dict(id='script://fixture/controllers/man-p1/0000', semantic_id='script://fixture/controllers/man-p1/0000',
        kind='controller', asset_kind='controller', scene_id='scene://fixture', owner_scene_id='scene://fixture',
        read_only=True, runtime_binding='not_asserted', reference_commit=REFERENCE_COMMIT, local_count=0, entry_pc=5,
        source_record=dict(disc_identity='sha256:'+'a'*64,iso_file='PROT.DAT',prot_entry=12,prot_entry_name='fixture',
            record_kind='man_partition_1_scene_controller',record_index=0,byte_coordinate_space='decoded_man_payload',
            byte_offset=100,byte_length=12,containing_decoded_size=150,sha256='b'*64))


class ControllerReferences(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.p=ProjectService(Path(directory.name));document=synthetic_scene()
        document['source']['disc_identity']='sha256:'+'a'*64;self.p.import_metadata(document)
        self.catalog=dict(scene_id='scene://fixture',source_key='c'*64,records=[controller()],limitations=[])

    def test_source_ownership_and_reverse_navigation_are_detached(self):
        before=deepcopy(self.p._document())
        report=assemble(self.p,self.catalog,controller()['id'])
        edge=report['incoming'][0]
        self.assertEqual((edge['source_id'],edge['target_id'],edge['kind'],edge['layer']),
            ('scene://fixture',controller()['id'],'scene_entry_controller_source','decoded'))
        self.assertEqual(edge['controller_source_evidence']['execution'],'not_asserted')
        self.assertEqual(edge['source_catalog_key'],'c'*64)
        self.assertEqual(report['outgoing'],[])
        scene=assemble(self.p,self.catalog,'scene://fixture')
        self.assertIn(edge,scene['outgoing'])
        project=assemble_project(self.p,{'scene://fixture':self.catalog},controller()['id'])
        self.assertEqual(project['incoming'][0]['controller_source_evidence'],edge['controller_source_evidence'])
        edge['controller_source_evidence']['source_record']['sha256']='changed'
        self.assertEqual(self.catalog['records'][0]['source_record']['sha256'],'b'*64)
        self.assertEqual(before,self.p._document())

    def test_mismatched_ownership_and_source_bounds_refuse(self):
        bad=deepcopy(self.catalog);bad['records'].append(deepcopy(bad['records'][0]))
        with self.assertRaises(ProjectError):assemble(self.p,bad,controller()['id'])
        for field,value in [('owner_scene_id','scene://foreign'),('scene_id','scene://foreign'),('entry_pc',6),
                            ('local_count',True),('read_only',False),('reference_commit','0'*40)]:
            bad=deepcopy(self.catalog);bad['records'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ProjectError):assemble(self.p,bad,controller()['id'])
        for field,value in [('disc_identity','sha256:'+'d'*64),('record_index',1),('byte_offset',150),
                            ('byte_length',51),('prot_entry',True),('prot_entry_name','foreign'),('sha256','bad')]:
            bad=deepcopy(self.catalog);bad['records'][0]['source_record'][field]=value
            with self.subTest(field=field),self.assertRaises(ProjectError):assemble(self.p,bad,controller()['id'])
