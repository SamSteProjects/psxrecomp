"""Relative source-record transforms with complete shared ownership and atomic history."""
from copy import deepcopy
import json
import re
from .project import ProjectError, digest
from .worldmap_placement_files import SCHEMA, prepare, review as review_file
from .worldmap_placements import owner, values


def arguments(record_ids, delta, shared_record):
    if not isinstance(record_ids, list) or not 1 <= len(record_ids) <= 128 or any(not isinstance(i, str) or not re.fullmatch('[0-9]{4}', i) or int(i) >= 512 for i in record_ids) or record_ids != sorted(set(record_ids)):
        raise ProjectError('Batch placement requires 1..128 canonical unique source record IDs')
    if not isinstance(delta, dict) or set(delta) != {'x', 'y', 'z', 'yaw_units'} or any(type(delta[a]) is not int or not -65535 <= delta[a] <= 65535 for a in ('x', 'y', 'z')) or type(delta['yaw_units']) is not int or not -4095 <= delta['yaw_units'] <= 4095 or type(shared_record) is not bool:
        raise ProjectError('Batch placement requires integer offset/yaw deltas and explicit shared-record consent')


def review(project, scene, key, record_ids, delta, shared_record):
    arguments(record_ids, delta, shared_record)
    _, source, records, _, _, binding, _, _ = prepare(project, scene, key)
    entries = {}
    for identifier in record_ids:
        row = records.get(identifier)
        if not row or not row['writable']:
            raise ProjectError('Batch contains an unavailable or incomplete source record')
        if row['source_cell_count'] > 1 and not shared_record:
            raise ProjectError('Batch requires consent to edit every cell of each shared source record')
        current = row['current_values']
        proposed = values(dict(offset={a: current['offset'][a] + delta[a] for a in ('x', 'y', 'z')},
                               yaw_units=(current['yaw_units'] + delta['yaw_units']) % 4096))
        shared = True if row['source_cell_count'] > 1 else (binding or {}).get('entries', {}).get(identifier, {}).get('shared_record', False)
        entries[identifier] = dict(values=proposed, source_record_sha256=row['source_record_sha256'], shared_record=shared)
    content = json.dumps(dict(schema_version=SCHEMA, scene=scene, source_record=source, entries=entries))
    result = review_file(project, scene, key, content)
    result.update(schema_version='legaia.worldmap-placement-batch-review.v1', record_ids=list(record_ids), delta=deepcopy(delta), shared_record=shared_record)
    result['review_key'] = digest(result)
    return result


def apply(project, command):
    if set(command) != {'type', 'scene', 'source_key', 'record_ids', 'delta', 'shared_record', 'review_key'} or command['type'] != 'transform_worldmap_records':
        raise ProjectError('Batch placement Apply requires exact reviewed source records and deltas')
    result = review(project, command['scene'], command['source_key'], command['record_ids'], command['delta'], command['shared_record'])
    if command['review_key'] != result['review_key']:
        raise ProjectError('Batch placement review changed; review again')
    if result['no_op']:
        return
    identifier = owner(command['scene'])
    if result['after'] is None:
        project.overrides.pop(identifier, None)
    else:
        project.overrides[identifier] = deepcopy(result['after'])
    project.undo_stack.append(dict(entity_id=identifier, before=result['before'], after=deepcopy(result['after'])))
    project.redo_stack.clear()
