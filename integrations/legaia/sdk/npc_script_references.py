"""Recorded retail script donors for authored NPCs, never generated/live scripts."""
import re

from importer.pipeline import REFERENCE_COMMIT
from .project import ProjectError, digest


def evidence(draft, record, scene):
    donor = draft['donor_entity_id']
    match = re.fullmatch(r'scene://([A-Za-z0-9_-]+)/actors/man-p1/([0-9]{4})', donor)
    source = record.get('source_record')
    target = 'script://' + donor.removeprefix('scene://')
    if (not match or scene != 'scene://' + match[1] or draft['scene_id'] != scene or
            record.get('id') != target or record.get('semantic_id') != target or
            record.get('script_id') != target or record.get('kind') != 'script' or
            record.get('asset_kind') != 'script' or record.get('actor_semantic_id') != donor or
            record.get('owner_semantic_id') != donor or type(record.get('partition')) is not int or record['partition'] != 1 or
            record.get('reference_commit') != REFERENCE_COMMIT or not isinstance(source, dict) or
            type(source.get('partition')) is not int or source['partition'] != 1 or
            type(source.get('record_index')) is not int or not 0 <= source['record_index'] <= 511 or source['record_index'] != int(match[2])):
        raise ProjectError('NPC script donor differs from its source catalog identity')
    if record.get('status') == 'unavailable':
        return None
    if (record.get('status') not in ('decoded_supported_paths', 'partial') or
            not isinstance(source.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', source['sha256']) or
            type(source.get('byte_offset')) is not int or not 0 <= source['byte_offset'] < 4 * 1024 * 1024 or
            type(source.get('byte_length')) is not int or not 1 <= source['byte_length'] <= 4 * 1024 * 1024 - source['byte_offset'] or
            type(source.get('record_alias_count')) is not int or not 1 <= source['record_alias_count'] <= 512 or
            source.get('byte_coordinate_space') not in ('decoded_lzs_descriptor', 'raw_man_payload')):
        raise ProjectError('NPC script donor has invalid source record evidence')
    return dict(donor_entity_id=donor, source_record_sha256=source['sha256'],
                reference_commit=REFERENCE_COMMIT, record_index=source['record_index'],
                byte_offset=source['byte_offset'], byte_length=source['byte_length'],
                byte_coordinate_space=source['byte_coordinate_space'],
                authored_draft_sha256=digest(draft), script_status=record['status'])
