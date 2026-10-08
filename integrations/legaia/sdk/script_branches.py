"""Source-qualified field branch review; imported facts never become editable state."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import re

from importer.core import ImportError as RetailImportError
from .project import ProjectError, digest

COMPONENT = 'ScriptBranches'
SCHEMA = 'legaia.script-branches.v1'
OPERANDS = {
    'Dialogue': ('dialogue_authoring', 'DialogueAuthoringContext', 'runs'),
    'Transitions': ('transition_authoring', 'TransitionAuthoringContext', 'entries'),
    'ScriptMovement': ('movement_authoring', 'MovementAuthoringContext', 'entries'),
    'ScriptFacing': ('facing_authoring', 'FacingAuthoringContext', 'entries'),
    'ScriptFlags': ('flag_authoring', 'FlagAuthoringContext', 'entries'),
    'ScriptSystemFlags': ('system_flag_authoring', 'SystemFlagAuthoringContext', 'entries'),
    'ScriptWaits': ('wait_authoring', 'WaitAuthoringContext', 'entries'),
    'ScriptEffectColors': ('effect_color_authoring', 'EffectColorAuthoringContext', 'entries'),
    'ScriptModelSelectors': ('model_selector_authoring', 'ModelSelectorAuthoringContext', 'entries'),
}


def state_key(project) -> str:
    from .build import authored_state_key
    stamp = None
    if project.disc_path:
        try:
            stat = Path(project.disc_path).stat()
            stamp = [stat.st_size, stat.st_mtime_ns]
        except OSError:
            pass
    return digest({'authored': authored_state_key(project), 'scene': project.active_scene,
                   'mode': project.mode, 'disc_stamp': stamp})


def validate(project, owner, value):
    project._dialogue_document(owner)
    if not isinstance(value, dict) or set(value) != {'entries'} or not isinstance(value['entries'], dict) or not 1 <= len(value['entries']) <= 1024:
        raise ProjectError('Script branches require a bounded nonempty destination collection')
    prefix = 'script://' + owner.removeprefix('scene://') + '/branch/'
    for identifier, target in value['entries'].items():
        if not isinstance(identifier, str) or not re.fullmatch(re.escape(prefix) + r'[0-9a-f]{4}', identifier):
            raise ProjectError('Branch identity does not belong to this imported script owner')
        if not isinstance(target, dict) or set(target) != {'target_pc'} or type(target['target_pc']) is not int or not 0 <= target['target_pc'] <= 32767:
            raise ProjectError('Branch target must be an integer record PC from 0 to 32767')
    return deepcopy(value)


def _context(project, owner):
    from importer.branch_authoring import BranchAuthoringContext
    document = project._dialogue_document(owner)
    if document['scene']['semantic_id'] != project.active_scene:
        raise ProjectError('Branch inspection requires the active imported scene')
    source = project._dialogue_context(owner)
    return source, BranchAuthoringContext(source, system_selectors=project.overrides.get(owner, {}).get('ScriptSystemFlags', {}).get('entries', {}))


def _compose(source, owner, components):
    """Reuse each writer's retail qualification before applying branch words last."""
    import importlib
    original = source._man
    current = bytearray(original)
    for component, (module, class_name, collection) in OPERANDS.items():
        entries = components.get(component, {}).get(collection, {})
        if not entries:
            continue
        context = source if component == 'Dialogue' else getattr(importlib.import_module('importer.' + module), class_name)(source)
        candidate, _ = context.patch(entries, original=original)
        if len(candidate) != len(original):
            raise ProjectError('Branch flow composition requires unchanged MAN record lengths')
        for offset, (before, after) in enumerate(zip(original, candidate)):
            mask = before ^ after
            if mask and (current[offset] ^ before) & mask:
                raise ProjectError('Script operand edits overlap while composing the current flow')
            current[offset] = (current[offset] & ~mask) | (after & mask)
    return bytes(current)


def _layers(project, owner, source, context, options):
    components = project.overrides.get(owner, {})
    plain = _compose(source, owner, components)
    if COMPONENT in components:
        validate(project, owner, components[COMPONENT])
    branches = components.get(COMPONENT, {}).get('entries', {})
    current, _ = context.patch_composed(plain, branches)
    current_report = context.inspect_owner(owner, current)
    from importer.script_inspection import _instruction
    offset, record, _ = source.verified_record(owner)
    effective_record = current[offset:offset+len(record)]
    targets = []
    for row in options.get('targets', []):
        authored = deepcopy(branches.get(row['semantic_id']))
        target = row.get('target_pc', row.get('values', {}).get('target_pc'))
        targets.append({**deepcopy(row), 'target_pc': target, 'authored_value': authored,
                        'current_target_pc': authored['target_pc'] if authored is not None else target,
                        'successors': _instruction(record, row['pc'])['successors'],
                        'current_successors': _instruction(effective_record, row['pc'])['successors']})
    return plain, current, current_report, targets


def snapshot(project, owner):
    source, context = _context(project, owner)
    options = context.options(owner)
    original_report = options.get('inspection') or context.inspect_owner(owner)
    result = {'schema_version': SCHEMA, 'owner_id': owner, 'state_key': state_key(project),
              'source_record_sha256': hashlib.sha256(source.verified_record(owner)[1]).hexdigest(),
              'source_report': original_report, 'current_report': None, 'targets': [],
              'destinations': deepcopy(options.get('destinations', [])), 'supported': options.get('supported', False),
              'reason': options.get('reason'), 'limitations': deepcopy(options.get('limitations', [])),
              'gameplay_verified': False}
    try:
        _, _, current, targets = _layers(project, owner, source, context, options)
        result.update(current_report=current, targets=targets)
    except (ProjectError, RetailImportError, ValueError) as exc:
        result.update(supported=False, reason=str(exc))
    return result


def review(project, owner, branch_id, value):
    if project.mode != 'edit':
        raise ProjectError('Branch authoring requires Edit mode')
    source, context = _context(project, owner)
    options = context.options(owner)
    allowed = {row['semantic_id']: row for row in options.get('targets', [])}
    if not isinstance(branch_id, str) or branch_id not in allowed:
        raise ProjectError('Branch is not uniquely qualified by the verified source: ' + str(options.get('reason') or branch_id))
    if value is not None:
        validate(project, owner, {'entries': {branch_id: value}})
    plain, current, current_report, targets = _layers(project, owner, source, context, options)
    before = deepcopy(project.overrides.get(owner, {}).get(COMPONENT))
    entries = deepcopy((before or {}).get('entries', {}))
    retail = allowed[branch_id].get('target_pc', allowed[branch_id].get('values', {}).get('target_pc'))
    if value is None or value['target_pc'] == retail:
        entries.pop(branch_id, None)
    else:
        entries[branch_id] = deepcopy(value)
    proposed_value = {'entries': entries} if entries else None
    candidate, audit = context.patch_composed(plain, entries)
    proposed = context.inspect_owner(owner, candidate)
    current_pcs = {row['pc'] for row in current_report['instructions'] + current_report['dialogues']}
    proposed_pcs = {row['pc'] for row in proposed['instructions'] + proposed['dialogues']}
    key = state_key(project)
    proof = {'state_key': key, 'owner_id': owner, 'branch_id': branch_id, 'value': value,
             'source_sha256': hashlib.sha256(source._man).hexdigest(),
             'current_sha256': hashlib.sha256(current).hexdigest(),
             'candidate_sha256': hashlib.sha256(candidate).hexdigest(), 'component': proposed_value}
    # Compare current and proposed bytes, including a reset that removes all overrides.
    offset, original_record, _ = source.verified_record(owner)
    changed = [offset + i for i, (a, b) in enumerate(zip(current[offset:offset+len(original_record)], candidate[offset:offset+len(original_record)])) if a != b]
    row = allowed[branch_id]
    target_before = next(item['current_target_pc'] for item in targets if item['semantic_id'] == branch_id)
    delta = [{'owner_id': owner, 'branch_id': branch_id, 'pc': row['pc'], 'mnemonic': row['mnemonic'],
              'field': 'script.branch_target', 'scope': 'script-branch-target-only',
              'before': target_before, 'after': value['target_pc'] if value is not None else retail,
              'changed_byte_offsets': changed, 'byte_offset': row.get('decoded_byte_offset', offset + row['operand_pc']),
              'byte_length': 2, 'source_record_sha256': hashlib.sha256(original_record).hexdigest(),
              'candidate_record_sha256': hashlib.sha256(candidate[offset:offset+len(original_record)]).hexdigest()}] if changed else []
    result = {'schema_version': SCHEMA, 'owner_id': owner, 'state_key': key,
              'source_record_sha256': hashlib.sha256(original_record).hexdigest(),
              'source_report': options.get('inspection') or context.inspect_owner(owner),
              'current_report': current_report, 'targets': targets, 'destinations': options['destinations'],
              'supported': True, 'reason': None, 'limitations': options.get('limitations', []),
              'gameplay_verified': False,
              'review': {'review_key': digest(proof), 'branch_id': branch_id, 'value': deepcopy(value),
                         'no_op': before == proposed_value, 'audit': delta, 'source_audit': audit,
                         'proposed_report': proposed, 'newly_unreachable_source_pcs': sorted(current_pcs - proposed_pcs),
                         'newly_reached_source_pcs': sorted(proposed_pcs - current_pcs)}}
    return result, proposed_value


def apply(project, command):
    if set(command) != {'type', 'entity', 'branch_id', 'value', 'review_key'}:
        raise ProjectError('Branch Apply requires only reviewed owner, source identity, destination and key')
    result, value = review(project, command['entity'], command['branch_id'], command['value'])
    if command['review_key'] != result['review']['review_key']:
        raise ProjectError('Script source or authored state changed; review the branch again')
    if result['review']['no_op']:
        raise ProjectError('Reviewed branch destination does not change the authored state')
    owner = command['entity']
    before = deepcopy(project.overrides.get(owner))
    after = deepcopy(before or {})
    if value:
        after[COMPONENT] = value
    else:
        after.pop(COMPONENT, None)
    after = after or None
    if after is None:
        project.overrides.pop(owner, None)
    else:
        project.overrides[owner] = after
    project.undo_stack.append({'entity_id': owner, 'before': before, 'after': deepcopy(after)})
    project.redo_stack.clear()
