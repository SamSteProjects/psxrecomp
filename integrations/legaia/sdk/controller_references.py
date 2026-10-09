"""Retail scene/controller ownership, without inferring script execution."""
from copy import deepcopy
from importer.scene_controller import REFERENCE_COMMIT
from .project import ProjectError


def controller_source_evidence(record, scene, document):
    source = record.get('source_record')
    name = document['scene']['name']
    integer = lambda value, low, high: type(value) is int and low <= value <= high
    hash_value = lambda value: isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)
    expected = {'disc_identity','iso_file','prot_entry','prot_entry_name','record_kind','record_index',
                'byte_coordinate_space','byte_offset','byte_length','containing_decoded_size','sha256'}
    if (record.get('id') != f'script://{name}/controllers/man-p1/0000'
        or record.get('semantic_id') != record.get('id') or document['scene']['semantic_id'] != scene
        or record.get('kind') != 'controller' or record.get('asset_kind') != 'controller'
        or record.get('owner_scene_id') != scene or record.get('scene_id') != scene
        or record.get('read_only') is not True or record.get('runtime_binding') != 'not_asserted'
        or record.get('reference_commit') != REFERENCE_COMMIT
        or not isinstance(source, dict) or set(source) != expected
        or not isinstance(source['disc_identity'], str) or source['disc_identity'] != document['source']['disc_identity']
        or not source['disc_identity'].startswith('sha256:') or not hash_value(source['disc_identity'][7:])
        or source['iso_file'] != 'PROT.DAT' or source['prot_entry_name'] != name
        or not integer(source['prot_entry'], 0, 65535)
        or source['record_kind'] != 'man_partition_1_scene_controller' or type(source['record_index']) is not int or source['record_index'] != 0
        or source['byte_coordinate_space'] != 'decoded_man_payload'
        or not integer(source['containing_decoded_size'], 1, 4*1024*1024)
        or not integer(source['byte_offset'], 0, source['containing_decoded_size']-1)
        or not integer(source['byte_length'], 1, min(65536, source['containing_decoded_size']-source['byte_offset']))
        or not hash_value(source['sha256']) or not integer(record.get('local_count'), 0, 255)
        or not integer(record.get('entry_pc'), 5, source['byte_length']-1)
        or record['entry_pc'] != 1 + record['local_count']*2 + 4):
        raise ProjectError('Controller scene ownership differs from its Retail source record')
    return dict(source_record=deepcopy(source), entry_pc=record['entry_pc'], local_count=record['local_count'],
                reference_commit=REFERENCE_COMMIT, relationship='retail_scene_entry_record', execution='not_asserted')
