"""Gate-1 MAP relationships qualify source records without executing a trigger."""
from copy import deepcopy
from pathlib import Path
import os
import struct
import tempfile
import unittest

from importer.core import ProtEntry
from importer.field_map import _decode
from importer.script_catalog import _catalog
from sdk.asset_references import assemble, assemble_project, inspect
from sdk.project import ProjectService, ProjectError, digest
from test_importer_dialogue_authoring import fixture
from test_project_workflow import synthetic_scene

DISC = '0' * 64


def table(rows):
    block = bytearray(0x2000)
    struct.pack_into('<hh', block, 6, 18, len(rows))
    for index, row in enumerate(rows):
        block[18 + index*4:22 + index*4] = bytes(row)
    return bytes(block)


def decoded_catalog():
    data = bytearray(0x12000)
    data[0x10000:] = table([(8, 9, 0, 1), (8, 9, 0, 1), (4, 5, 0, 0), (6, 7, 255, 1)])
    maps = _decode('fixture', DISC, ProtEntry(1, 100, 8, 36), bytes(data),
                   (ProtEntry(2, 136, 8, 8), table([(8, 9, 0, 1), (3, 4, 1, 7)])))[0]
    # Give P2 a separate bounded record rather than the fixture's P0 alias.
    _, original = fixture()
    region = 0x2B + 12
    section = int.from_bytes(original[0x28:0x2B], 'little')
    p2 = bytes(4) + b'\x24'
    man = bytearray(original[:region + section] + p2 + original[region + section:])
    man[0x34:0x37] = section.to_bytes(3, 'little')
    man[0x28:0x2B] = (section + len(p2)).to_bytes(3, 'little')
    scripts = _catalog(bytes(man), 'fixture', dict(disc=dict(sha256=DISC, serial='SCUS-94254'),
                       iso_file='PROT.DAT', prot_entry_index=3, compressed_stream_offset=32,
                       compressed_bytes_consumed=len(man)), set())
    records = []
    for asset in maps['assets'] + [row for row in scripts['assets'] if row['asset_kind']=='script' and row['partition']==2]:
        asset = deepcopy(asset)
        asset.update(id=asset['semantic_id'], kind=asset['asset_kind'], scene_id='scene://fixture', layer='derived')
        records.append(asset)
    return dict(scene_id='scene://fixture', source_key='a'*64, records=records, limitations=['Decoded source records only.'])


class TriggerAssetReferences(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = ProjectService(Path(temporary.name))
        document = synthetic_scene()
        document['source']['disc_identity'] = 'sha256:'+DISC
        self.project.import_metadata(document)
        self.catalog = decoded_catalog()
        self.script_id = 'script://fixture/scripts/man-p2/0000'
        self.trigger_id = 'trigger://fixture/field-map/primary/kind-1/0000'

    def test_primary_fallback_duplicate_rows_have_distinct_detached_source_edges(self):
        before = deepcopy((self.catalog, self.project.imports, self.project.overrides, self.project.undo_stack))
        report = assemble(self.project, self.catalog, self.script_id)
        links = [row for row in report['incoming'] if row['kind']=='field_trigger_script_reference']
        self.assertEqual([row['source_id'] for row in links], [
            'trigger://fixture/field-map/fallback/kind-1/0000',
            'trigger://fixture/field-map/primary/kind-1/0000',
            'trigger://fixture/field-map/primary/kind-1/0001'])
        self.assertEqual(report['coverage']['unresolved_reference_count'], 3)
        source_script = next(row for row in self.catalog['records'] if row['id']==self.script_id)
        for edge in links:
            trigger = next(row for row in self.catalog['records'] if row['id']==edge['source_id'])
            self.assertEqual(edge['trigger_reference_evidence'], dict(
                trigger_source_record_sha256=trigger['source_record']['sha256'],
                script_source_record_sha256=source_script['source_record']['sha256'], table_source=trigger['table_source'],
                table_kind=1, trigger_row_index=trigger['record_index'], partition_two_record_index=0, gate=1,
                reachability='not_evaluated'))
            self.assertEqual(edge['layer'], 'decoded')
            self.assertEqual(edge['runtime_binding'], 'not_asserted')
            self.assertEqual(edge['source_catalog_key'], self.catalog['source_key'])
            self.assertEqual(edge['source_import_sha256'], digest(self.project.imports[self.project.active_scene]))
            self.assertNotIn('pc', edge)
            self.assertEqual(edge['id'], digest({key:value for key,value in edge.items() if key!='id'}))
        trigger = assemble(self.project, self.catalog, self.trigger_id)
        self.assertEqual({row['kind'] for row in trigger['outgoing']}, {'field_map_table_source','field_trigger_script_reference'})
        report['incoming'][0]['trigger_reference_evidence']['gate'] = 0
        self.assertEqual((self.catalog, self.project.imports, self.project.overrides, self.project.undo_stack), before)

    def test_absent_ambiguous_and_unbounded_targets_stay_unresolved(self):
        mutations = [
            lambda rows: rows.remove(next(row for row in rows if row['id']==self.script_id)),
            lambda rows: rows.append(deepcopy(next(row for row in rows if row['id']==self.script_id))),
            lambda rows: next(row for row in rows if row['id']==self.script_id)['source_record'].update(record_alias_count=2),
            lambda rows: next(row for row in rows if row['id']==self.script_id).update(status='unavailable', source_record={
                **next(row for row in rows if row['id']==self.script_id)['source_record'],
                'record_alias_count':None, 'byte_offset':None, 'byte_length':None, 'sha256':None}),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                bad = deepcopy(self.catalog)
                mutation(bad['records'])
                report = assemble(self.project, bad, self.trigger_id)
                self.assertEqual([row['kind'] for row in report['outgoing']], ['field_map_table_source'])
                self.assertEqual(report['coverage']['unresolved_reference_count'], 6)
                self.assertNotIn('script://fixture/scripts/man-p2/0255', {row['id'] for row in report['nodes']})

    def test_conflicting_source_identity_bounds_hash_and_disc_reject(self):
        trigger_mutations = [
            lambda row: row.update(semantic_id='trigger://fixture/field-map/primary/kind-1/0001'),
            lambda row: row.update(table_source='fallback'),
            lambda row: row.update(table_kind=True),
            lambda row: row.update(record_index=True),
            lambda row: row.update(scene_id='scene://other'),
            lambda row: row.update(reference_commit='b'*40),
            lambda row: row['encoded'].update(tile_x=9),
            lambda row: row['encoded'].update(tile_x=256),
            lambda row: row['encoded'].update(record_index=True),
            lambda row: row['script_reference'].update(partition=0),
            lambda row: row['script_reference'].update(index_space='flat_man'),
            lambda row: row['script_reference'].pop('index_space'),
            lambda row: row['script_reference'].update(record_index=1),
            lambda row: row['source_record'].update(sha256='b'*64),
            lambda row: row['source_record']['disc'].update(sha256='b'*64),
            lambda row: row['source_record'].update(record_index=1),
            lambda row: row['source_record'].update(table_source='fallback'),
            lambda row: row['source_record'].update(prot_entry_name='other'),
            lambda row: row['source_record'].update(byte_length=8),
            lambda row: row['source_record'].update(byte_offset=0x12000),
            lambda row: row['source_record'].update(containing_span_byte_length=0x4000),
        ]
        script_mutations = [
            lambda row: row.update(semantic_id='script://fixture/scripts/man-p2/0001'),
            lambda row: row.update(partition=1),
            lambda row: row.update(owner_semantic_id='scene://other/scripts/man-p2/0000'),
            lambda row: row.update(actor_semantic_id='scene://fixture/actors/man-p1/0000'),
            lambda row: row.update(reference_commit='b'*40),
            lambda row: row['source_record']['disc'].update(sha256='b'*64),
            lambda row: row['source_record'].update(partition=1),
            lambda row: row['source_record'].update(record_index=1),
            lambda row: row['source_record'].update(prot_entry_name='other'),
            lambda row: row['source_record'].update(byte_coordinate_space='runtime_memory'),
            lambda row: row['source_record'].update(byte_length=0),
            lambda row: row['source_record'].update(sha256='invalid'),
            lambda row: row['source_record'].update(byte_offset=4*1024*1024),
        ]
        for identity, mutations in ((self.trigger_id,trigger_mutations),(self.script_id,script_mutations)):
            for mutation in mutations:
                with self.subTest(identity=identity,mutation=mutation):
                    bad = deepcopy(self.catalog)
                    mutation(next(row for row in bad['records'] if row['id']==identity))
                    with self.assertRaises(ProjectError):
                        assemble(self.project, bad, self.trigger_id)
        duplicate = deepcopy(self.catalog)
        duplicate['records'].append(deepcopy(next(row for row in duplicate['records'] if row['id']==self.trigger_id)))
        with self.assertRaises(ProjectError):
            assemble(self.project, duplicate, self.trigger_id)

    def test_raw_man_variant_and_project_scope_keep_same_source_scene(self):
        second = synthetic_scene()
        second['source']['disc_identity'] = 'sha256:'+DISC
        second['scene'] = dict(semantic_id='scene://other', name='other')
        second['actors'][0]['semantic_id'] = 'scene://other/actors/man-p1/0001'
        self.project.import_metadata(second)
        self.project.active_scene = 'scene://fixture'
        source = next(row for row in self.catalog['records'] if row['id']==self.script_id)['source_record']
        source['byte_coordinate_space'] = 'raw_man_payload'
        before = deepcopy((self.project.imports,self.project.overrides,self.project.active_scene,self.project.undo_stack))
        report = assemble_project(self.project, {'scene://fixture':self.catalog,
            'scene://other':dict(scene_id='scene://other',source_key='b'*64,records=[],limitations=[])}, self.trigger_id)
        edge = next(row for row in report['outgoing'] if row['kind']=='field_trigger_script_reference')
        self.assertEqual(edge['scene_id'], 'scene://fixture')
        self.assertEqual(edge['source_catalog_key'], self.catalog['source_key'])
        self.assertEqual(edge['trigger_reference_evidence']['partition_two_record_index'], 0)
        for node in report['nodes']:
            self.assertEqual(node['scene_ids'], ['scene://fixture'])
            self.assertEqual(node['navigable_scene_ids'], ['scene://fixture'])
        self.assertEqual((self.project.imports,self.project.overrides,self.project.active_scene,self.project.undo_stack), before)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailTriggerAssetReferences(unittest.TestCase):
    def test_fresh_gate_one_rows_link_to_unique_catalog_p2_sources(self):
        from importer.pipeline import import_scene
        from sdk.resources import refresh_resource_catalog
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.disc_path = os.environ['LEGAIA_DISC_BIN']
            project.import_metadata(import_scene(project.disc_path,'town01'))
            catalog = refresh_resource_catalog(project)
            triggers = [row for row in catalog['records'] if row['kind']=='trigger' and row.get('table_kind')==1 and row.get('encoded',{}).get('gate')==1]
            self.assertTrue(triggers)
            before = deepcopy((project.imports,project.overrides,project.undo_stack,project.active_scene))
            fresh = inspect(project,triggers[0]['id'])
            self.assertIn('field_trigger_script_reference',{row['kind'] for row in fresh['outgoing']})
            for trigger in triggers:
                report = assemble(project,catalog,trigger['id'])
                links = [row for row in report['outgoing'] if row['kind']=='field_trigger_script_reference']
                self.assertEqual(len(links),1)
                expected = 'script://town01/scripts/man-p2/'+str(trigger['encoded']['record_index']).zfill(4)
                self.assertEqual(links[0]['target_id'],expected)
                self.assertEqual(links[0]['trigger_reference_evidence']['trigger_source_record_sha256'],trigger['source_record']['sha256'])
                self.assertEqual(links[0]['runtime_binding'],'not_asserted')
            self.assertEqual((project.imports,project.overrides,project.undo_stack,project.active_scene),before)


if __name__=='__main__':
    unittest.main()
