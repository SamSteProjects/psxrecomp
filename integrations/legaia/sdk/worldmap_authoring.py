"""Global source-bound landmark authoring, distinct from field/world transforms."""
from copy import deepcopy
import hashlib
from pathlib import Path
import re

from .project import ProjectError, digest

OWNER = 'worldmap://legaia/menu'
COMPONENT = 'WorldMapMenu'
SCHEMA = 'legaia.worldmap-authoring.v1'
FIELDS = ('name_index', 'discovery_flag_index', 'destination_scene_id',
          'menu_position.x', 'menu_position.y')


def state_key(project):
    from .build import authored_state_key
    stamp = None
    if project.disc_path:
        try:
            stat = Path(project.disc_path).stat()
            stamp = [stat.st_size, stat.st_mtime_ns]
        except OSError:
            pass
    return digest(dict(authored=authored_state_key(project), mode=project.mode,
                       active_scene=project.active_scene, disc_stamp=stamp))


def _hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def validate_values(value):
    if (not isinstance(value, dict) or set(value) != {'name_index', 'discovery_flag_index',
            'destination_scene_id', 'menu_position'} or not isinstance(value['menu_position'], dict)
            or set(value['menu_position']) != {'x', 'y'}):
        raise ProjectError('World-map landmark requires existing name, discovery index, destination and menu X/Y')
    fields = [(value['name_index'], 0, 15), (value['discovery_flag_index'], 32, 287),
              (value['destination_scene_id'], 0, 65535),
              (value['menu_position']['x'], 0, 255), (value['menu_position']['y'], 0, 255)]
    if any(type(number) is not int or not low <= number <= high for number, low, high in fields):
        raise ProjectError('World-map landmark fields exceed their encoded source domains')
    return deepcopy(value)


def validate(project, owner, value):
    if (owner != OWNER or not isinstance(value, dict) or set(value) != {
            'source_executable_sha256', 'source_disc_sha256', 'entries'}
            or not _hash(value['source_executable_sha256']) or not _hash(value['source_disc_sha256'])
            or not isinstance(value['entries'], dict) or not 1 <= len(value['entries']) <= 63):
        raise ProjectError('World-map overrides require a bounded global menu and immutable executable/disc bindings')
    identities = {doc['source']['disc_identity'] for doc in project.imports.values()}
    if identities != {'sha256:' + value['source_disc_sha256']}:
        raise ProjectError('World-map override does not belong to the project retail disc')
    for identifier, entry in value['entries'].items():
        if not isinstance(identifier, str) or not re.fullmatch(re.escape(OWNER) + r'/placements/[0-9]{4}', identifier):
            raise ProjectError('World-map override requires original stable placement identities')
        validate_values(entry)
    return deepcopy(value)


def _context(project):
    if not project.disc_path or not project.imports:
        raise ProjectError('Import a scene from the user-owned retail disc before editing world-map landmarks')
    from importer.worldmap_authoring import load_worldmap_authoring_context
    context = load_worldmap_authoring_context(project.disc_path)
    options = context.options()
    if {doc['source']['disc_identity'] for doc in project.imports.values()} != {
            'sha256:' + options['source_record']['disc_sha256']}:
        raise ProjectError('World-map source differs from the imported project retail identity')
    components = project.overrides.get(OWNER)
    if components is not None and (not isinstance(components, dict) or set(components) != {COMPONENT}):
        raise ProjectError('Global world-map owner accepts only the source-bound menu component')
    binding = (components or {}).get(COMPONENT)
    if binding is not None:
        validate(project, OWNER, binding)
        if (binding['source_executable_sha256'] != options['source_executable_sha256']
                or binding['source_disc_sha256'] != options['source_record']['disc_sha256']):
            raise ProjectError('World-map executable source changed; restore or reimport the matching source')
    return context, options, binding


def _values(row):
    return dict(name_index=row['name_index'], discovery_flag_index=row['discovery_flag_index'],
                destination_scene_id=row['destination_scene_id'], menu_position=deepcopy(row['menu_position']))


def _snapshot(project, context, options, binding):
    entries = (binding or {}).get('entries', {})
    current, _ = context.patch(entries)
    destinations = {row['destination_scene_id']: row['destination_source_label']
                    for row in options['allowed_destinations']}
    placements = []
    for row in options['placements']:
        retail = row.get('values') or _values(row)
        authored = entries.get(row['semantic_id'])
        effective = authored or retail
        placements.append(dict(semantic_id=row['semantic_id'], record_index=row['record_index'],
            retail_values=deepcopy(retail), authored_value=deepcopy(authored), current_values=deepcopy(effective),
            retail_destination_label=destinations.get(retail['destination_scene_id']),
            current_destination_label=destinations.get(effective['destination_scene_id']), writable=True, reason=None))
    return dict(schema_version=SCHEMA, source_key=state_key(project), source_record=deepcopy(options['source_record']),
        current_executable_sha256=hashlib.sha256(current).hexdigest(), names=deepcopy(options['names']),
        field_evidence=deepcopy(options['field_evidence']),
        destinations=[dict(id=identifier, label=label) for identifier, label in sorted(destinations.items())],
        placements=placements, limitations=deepcopy(options.get('limitations', [])), gameplay_verified=False), current


def snapshot(project):
    context, options, binding = _context(project)
    return _snapshot(project, context, options, binding)[0]


def _field(values, field):
    for part in field.split('.'):
        values = values[part]
    return values


def review(project, entity_id, values):
    if project.mode != 'edit':
        raise ProjectError('World-map landmark authoring requires Edit mode')
    context, options, before = _context(project)
    result, current = _snapshot(project, context, options, before)
    rows = {row['semantic_id']: row for row in result['placements']}
    if not isinstance(entity_id, str) or entity_id not in rows:
        raise ProjectError('Select an original source-qualified world-map landmark')
    row = rows[entity_id]
    if values is not None:
        values = validate_values(values)
    proposed = values if values is not None else row['retail_values']
    entries = deepcopy((before or {}).get('entries', {}))
    if proposed == row['retail_values']:
        entries.pop(entity_id, None)
    else:
        entries[entity_id] = deepcopy(proposed)
    after = dict(source_executable_sha256=options['source_executable_sha256'],
        source_disc_sha256=options['source_record']['disc_sha256'], entries=entries) if entries else None
    candidate, _ = context.patch(entries)
    offset = options['source_record']['table_file_offset'] + row['record_index'] * 6
    changed = [dict(file_offset=i, before_byte=a, after_byte=b)
               for i, (a, b) in enumerate(zip(current, candidate)) if a != b]
    if any(not offset <= change['file_offset'] < offset + 6 for change in changed):
        raise ProjectError('Landmark review changed another source row')
    current_hash, proposed_hash = hashlib.sha256(current).hexdigest(), hashlib.sha256(candidate).hexdigest()
    proof = dict(source_key=result['source_key'], source_hash=options['source_executable_sha256'],
                 current_hash=current_hash, proposed_hash=proposed_hash, entity_id=entity_id,
                 values=values, component=after)
    fields = [dict(field=field, before=_field(row['current_values'], field), after=_field(proposed, field))
              for field in FIELDS if _field(row['current_values'], field) != _field(proposed, field)]
    result['review'] = dict(review_key=digest(proof), entity_id=entity_id, values=deepcopy(values),
        no_op=before == after, proposed_values=deepcopy(proposed),
        proposed_destination_label=next((item['label'] for item in result['destinations']
                                        if item['id'] == proposed['destination_scene_id']), None),
        audit=dict(scope='worldmap-menu-record-only', changed_fields=fields, changed_bytes=changed,
                   file_offset=offset, byte_length=6, source_executable_sha256=options['source_executable_sha256'],
                   current_executable_sha256=current_hash, candidate_executable_sha256=proposed_hash))
    return result, after


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'values', 'review_key'}:
        raise ProjectError('World-map Apply requires only the reviewed source row, values and key')
    report, binding = review(project, command['entity_id'], command['values'])
    if command['review_key'] != report['review']['review_key']:
        raise ProjectError('World-map source or authored state changed; review again')
    if report['review']['no_op']:
        raise ProjectError('Reviewed world-map values do not change authored state')
    before = deepcopy(project.overrides.get(OWNER))
    after = {COMPONENT: binding} if binding else None
    if after:
        project.overrides[OWNER] = after
    else:
        project.overrides.pop(OWNER, None)
    project.undo_stack.append(dict(entity_id=OWNER, before=before, after=deepcopy(after)))
    project.redo_stack.clear()
