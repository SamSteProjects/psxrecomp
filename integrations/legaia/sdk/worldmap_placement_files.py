"""Sparse source-bound placement metadata; never cell/model/script or Retail payload transfer."""
from copy import deepcopy
from hashlib import sha256
import json
import re
from .project import ProjectError, digest
from .script_operand_files import parse_json
from .worldmap_authoring import state_key
from .worldmap_placements import COMPONENT, context, owner, values, patch

SCHEMA = 'legaia.worldmap-placement-file.v1'
MAX_BYTES = 262144


def parse(content):
    value = parse_json(content, max_bytes=MAX_BYTES)
    if not isinstance(value, dict) or set(value) != {'schema_version', 'scene', 'source_record', 'entries'} or value['schema_version'] != SCHEMA:
        raise ProjectError('Unsupported placement file schema or fields')
    owner(value['scene'])
    source = value['source_record']
    if not isinstance(source, dict) or set(source) != {'scene', 'source_disc_sha256', 'source_map_sha256', 'source_floor_lut_sha256'} or source['scene'] != value['scene'] or any(not isinstance(source[k], str) or not re.fullmatch('[0-9a-f]{64}', source[k]) for k in source if k != 'scene'):
        raise ProjectError('Placement file requires exact immutable kingdom source hashes')
    entries = value['entries']
    if not isinstance(entries, dict) or len(entries) > 512:
        raise ProjectError('Placement file exceeds its record budget')
    for identifier, entry in entries.items():
        if not re.fullmatch('[0-9]{4}', identifier) or int(identifier) >= 512:
            raise ProjectError('Placement file record index is invalid')
        if entry is None:
            continue
        if not isinstance(entry, dict) or set(entry) != {'values', 'shared_record', 'source_record_sha256'} or type(entry['shared_record']) is not bool or not isinstance(entry['source_record_sha256'], str) or not re.fullmatch('[0-9a-f]{64}', entry['source_record_sha256']):
            raise ProjectError('Placement file requires bounded values, original record hash and explicit shared scope')
        values(entry['values'])
    return value


def prepare(project, scene, key):
    if project.mode != 'edit' or key != state_key(project):
        raise ProjectError('Placement file requires current Edit source inputs')
    return context(project, scene)


def export_file(project, scene, key):
    _, source, _, _, _, binding, _, _ = prepare(project, scene, key)
    value = dict(schema_version=SCHEMA, scene=scene, source_record=deepcopy(source), entries=deepcopy((binding or {}).get('entries', {})))
    parse(json.dumps(value))
    if project.mode != 'edit' or key != state_key(project):
        raise ProjectError('Placement source changed during export')
    return value


def review(project, scene, key, content):
    value = parse(content)
    if value['scene'] != scene:
        raise ProjectError('Placement file belongs to another kingdom')
    raw, source, records, _, floor, binding, current, _ = prepare(project, scene, key)
    if value['source_record'] != source:
        raise ProjectError('Placement file differs from the original kingdom source')
    entries = deepcopy((binding or {}).get('entries', {}))
    rows = []
    for identifier, entry in sorted(value['entries'].items()):
        row = records.get(identifier)
        if not row or not row['writable']:
            raise ProjectError('Placement file targets an unavailable or incomplete source record')
        if entry is not None and entry['source_record_sha256'] != row['source_record_sha256']:
            raise ProjectError('Placement file original record hash changed')
        proposed = row['retail_values'] if entry is None else entry['values']
        if proposed == row['retail_values']:
            entries.pop(identifier, None)
        else:
            entries[identifier] = deepcopy(entry)
        rows.append(dict(record_id=identifier, current_values=deepcopy(row['current_values']), proposed_values=deepcopy(proposed),
                         source_record_sha256=row['source_record_sha256'], affected_source_entities=[p['entity_id'] for p in row['placements']]))
    candidate, _, _ = patch(raw, records, entries, scene=scene, floor=floor)
    before = deepcopy(project.overrides.get(owner(scene)))
    after = {COMPONENT: dict(source, entries=entries)} if entries else None
    result = dict(schema_version='legaia.worldmap-placement-file-review.v1', scene=scene, source_key=key,
                  source_record=deepcopy(source), current_map_sha256=sha256(current).hexdigest(), candidate_map_sha256=sha256(candidate).hexdigest(),
                  records=rows, changed_bytes=[dict(byte_offset=i, before_byte=a, after_byte=b) for i, (a, b) in enumerate(zip(current, candidate)) if a != b],
                  before=before, after=after, no_op=before == after, project_changed=False, gameplay_verified=False)
    if project.mode != 'edit' or key != state_key(project):
        raise ProjectError('Placement inputs changed during file review')
    result['review_key'] = digest(dict(report=result, file=value))
    return result


def apply(project, command):
    if set(command) != {'type', 'scene', 'source_key', 'content', 'review_key'} or command['type'] != 'import_worldmap_placement_file':
        raise ProjectError('Placement file import accepts only reviewed source-bound metadata')
    result = review(project, command['scene'], command['source_key'], command['content'])
    if command['review_key'] != result['review_key']:
        raise ProjectError('Placement file or project changed; review again')
    if result['no_op']:
        return
    identifier = owner(command['scene'])
    if result['after'] is None:
        project.overrides.pop(identifier, None)
    else:
        project.overrides[identifier] = deepcopy(result['after'])
    project.undo_stack.append(dict(entity_id=identifier, before=result['before'], after=deepcopy(result['after'])))
    project.redo_stack.clear()
