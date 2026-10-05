"""Atomic source trigger-cell translation; no payload or activation semantics."""
from copy import deepcopy
from hashlib import sha256
from importer.core import ImportError
from importer.trigger_authoring import patch_field_triggers
from .project import ProjectError, digest
from .trigger_cells import _context, _check_current, _indexed, _cells


def review(project, scene, trigger_ids, delta, action='translate'):
    if project.mode != 'edit' or scene != project.active_scene or scene not in project.imports:
        raise ProjectError('Trigger group requires the active imported scene in Edit mode')
    if (not isinstance(trigger_ids, list) or not 1 <= len(trigger_ids) <= 128 or
            any(not isinstance(item, str) for item in trigger_ids) or len(set(trigger_ids)) != len(trigger_ids)):
        raise ProjectError('Choose 1..128 unique primary trigger identities')
    if (action not in ('translate', 'retail') or not isinstance(delta, dict) or set(delta) != {'x','z'} or
            any(type(delta[axis]) is not int or not -255 <= delta[axis] <= 255 for axis in ('x','z')) or
            action == 'retail' and any(delta.values())):
        raise ProjectError('Trigger group requires integer X/Z offsets in -255..255; Retail requires zero offsets')
    identifiers = sorted(trigger_ids)
    context = _context(project, scene)
    imported, current = _indexed(context['imported']), _indexed(context['current'])
    if any(identifier not in imported or identifier not in current for identifier in identifiers):
        raise ProjectError('Trigger group includes an absent, fallback or cross-scene source row')
    edits = {row['trigger_id']: deepcopy(row) for row in (context['authored'] or {}).get('edits', [])}
    rows = []
    for identifier in identifiers:
        original, existing = imported[identifier], current[identifier]
        before = _cells(existing)
        proposed = _cells(original) if action == 'retail' else {
            'tile_x': before['tile_x'] + delta['x'], 'tile_z': before['tile_z'] + delta['z']}
        if any(not 0 <= value <= 255 for value in proposed.values()):
            raise ProjectError('Trigger group would leave byte-coordinate bounds; no cells changed')
        if proposed == _cells(original):
            edits.pop(identifier, None)
        else:
            edits[identifier] = dict(trigger_id=identifier, **proposed)
        rows.append(dict(trigger_id=identifier, source=deepcopy(original),
                         layers=dict(imported=_cells(original), current=before, proposed=proposed)))
    binding = dict(source_sha256=context['source_hash'], edits=[edits[k] for k in sorted(edits)])
    try:
        patched, audit = patch_field_triggers(context['original'], context['source_hash'], context['name'], binding['edits'])
    except ImportError as error:
        raise ProjectError(str(error)) from error
    result = dict(schema_version='legaia.trigger-group-review.v1', read_only=True,
                  project_source_key=context['project_key'], scene_id=scene,
                  trigger_ids=identifiers, delta=deepcopy(delta), action=action, rows=rows,
                  value=binding, audit=audit, proposed_map_sha256=sha256(patched).hexdigest(),
                  project_change=context['authored'] != (binding if binding['edits'] else None),
                  changed_cell_count=sum(row['layers']['current'] != row['layers']['proposed'] for row in rows),
                  scope='source-MAP-trigger-cell-only', height_status='unknown',
                  activation='not_evaluated', gameplay_verified=False)
    result['review_key'] = digest(result)
    _check_current(project, context)
    return result


def apply(project, command):
    if (not isinstance(command, dict) or set(command) != {'type','scene_id','trigger_ids','delta','action','review_key'} or
            command['type'] != 'apply_trigger_group' or not isinstance(command['review_key'], str)):
        raise ProjectError('Trigger group Apply requires exact reviewed identities, offset, action and key')
    report = review(project, command['scene_id'], command['trigger_ids'], command['delta'], command['action'])
    if report['review_key'] != command['review_key']:
        raise ProjectError('Trigger group changed since review')
    if report['project_change']:
        project.command(dict(type='set_trigger_cells' if report['value']['edits'] else 'clear_trigger_cells',
                             entity_id=report['scene_id'], **({'value':deepcopy(report['value'])} if report['value']['edits'] else {})))
    return report
