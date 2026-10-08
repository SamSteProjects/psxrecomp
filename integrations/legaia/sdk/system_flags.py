"""Reviewed project-local system selector bindings, separate from word flags."""
from copy import deepcopy
import hashlib
import re
from importer.core import ImportError as RetailImportError
from importer.system_flag_authoring import SystemFlagAuthoringContext, validate_system_flag_values
from .project import ProjectError, digest

COMPONENT = 'ScriptSystemFlags'
SCHEMA = 'legaia.system-flag-authoring.v1'


def validate(project, owner, value):
    project._dialogue_document(owner)
    if (not isinstance(value, dict) or set(value) != {'entries'}
            or not isinstance(value['entries'], dict) or not 1 <= len(value['entries']) <= 1024):
        raise ProjectError('System selector component requires a bounded nonempty entry collection')
    prefix = 'script://' + owner.removeprefix('scene://') + '/system-flag/'
    for identity, fields in value['entries'].items():
        if not isinstance(identity, str) or re.fullmatch(re.escape(prefix) + r'[0-9a-f]{4}', identity) is None:
            raise ProjectError('System selector binding must belong to the source owner')
        try:
            validate_system_flag_values(fields)
        except RetailImportError as exc:
            raise ProjectError(str(exc)) from exc
    return deepcopy(value)


def _prepare(project, owner):
    from .script_branches import state_key
    document = project._dialogue_document(owner)
    if document['scene']['semantic_id'] != project.active_scene:
        raise ProjectError('System selector inspection requires the active imported scene')
    key = state_key(project)
    source = project._dialogue_context(owner)
    context = SystemFlagAuthoringContext(source)
    options = context.options(owner)
    offset, record, entry = source.verified_record(owner)
    components = deepcopy(project.overrides.get(owner, {}))
    if COMPONENT in components:
        validate(project, owner, components[COMPONENT])
    return key, source, context, options, offset, record, entry, components


def _compose(source, owner, components):
    from importer.branch_authoring import BranchAuthoringContext
    from .script_branches import _compose as compose_operands
    plain = compose_operands(source, owner, components)
    branches = BranchAuthoringContext(source, system_selectors=components.get(COMPONENT, {}).get('entries', {}))
    current, _ = branches.patch_composed(plain, components.get('ScriptBranches', {}).get('entries', {}))
    return current, branches.inspect_owner(owner, current)


def snapshot(project, owner):
    from .script_branches import state_key
    key, source, context, options, offset, record, entry, components = _prepare(project, owner)
    current, report = _compose(source, owner, components)
    native = current[offset:offset + len(record)]
    entries = components.get(COMPONENT, {}).get('entries', {})
    targets = []
    for target in options['targets']:
        pc = target['pc']
        targets.append(dict(target, authored_values=deepcopy(entries.get(target['semantic_id'])),
                            current_index=((native[pc] & 15) << 8) | native[pc + 1]))
    if set(entries) - {t['semantic_id'] for t in targets}:
        raise ProjectError('Saved system selectors are absent from the qualified source')
    if key != state_key(project):
        raise ProjectError('System selector source changed during inspection')
    return dict(schema_version=SCHEMA, owner_id=owner, state_key=key,
                source_record_sha256=hashlib.sha256(record).hexdigest(),
                current_record_sha256=hashlib.sha256(native).hexdigest(),
                targets=targets, current_report=report, supported=bool(targets),
                reason=options['reason'], limitations=options['limitations'], gameplay_verified=False)


def review(project, owner, operand, value):
    from .script_branches import state_key
    if value is not None:
        try:
            validate_system_flag_values(value)
        except RetailImportError as exc:
            raise ProjectError(str(exc)) from exc
    key, source, context, options, offset, record, entry, components = _prepare(project, owner)
    target = next((t for t in options['targets'] if t['semantic_id'] == operand), None)
    if target is None:
        raise ProjectError('Select a source-qualified system selector')
    before, current_report = _compose(source, owner, components)
    proposed = deepcopy(components)
    entries = deepcopy(proposed.get(COMPONENT, {}).get('entries', {}))
    if value is None:
        entries.pop(operand, None)
    else:
        entries[operand] = deepcopy(value)
    if entries:
        proposed[COMPONENT] = validate(project, owner, {'entries': entries})
        context.patch(entries)
    else:
        proposed.pop(COMPONENT, None)
    after, proposed_report = _compose(source, owner, proposed)
    current_record = before[offset:offset + len(record)]
    proposed_record = after[offset:offset + len(record)]
    differences = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    if any(i not in (offset + target['pc'], offset + target['pc'] + 1) for i in differences):
        raise ProjectError('Reviewed system selector changed an unrelated MAN byte')
    proof = dict(owner_id=owner, operand_id=operand, value=deepcopy(value), state_key=key,
                 source_record_sha256=hashlib.sha256(record).hexdigest(),
                 current_record_sha256=hashlib.sha256(current_record).hexdigest(),
                 proposed_record_sha256=hashlib.sha256(proposed_record).hexdigest(), proposed=proposed)
    if key != state_key(project):
        raise ProjectError('System selector source changed during Review')
    return dict(schema_version=SCHEMA, **proof, review_key=digest(proof),
                current_report=current_report, proposed_report=proposed_report,
                changed_decoded_byte_offsets=differences, no_op=components == proposed,
                native_bytes_changed=before != after, project_changed=False, gameplay_verified=False)


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'operand_id', 'value', 'review_key'}:
        raise ProjectError('System selector Apply requires only reviewed identities, value and key')
    result = review(project, command['entity_id'], command['operand_id'], command['value'])
    if command['review_key'] != result['review_key']:
        raise ProjectError('System selector inputs changed; review again')
    if result['no_op']:
        raise ProjectError('Reviewed system selector does not change authored state')
    owner = command['entity_id']
    before = deepcopy(project.overrides.get(owner))
    after = result['proposed'] or None
    if after is None:
        project.overrides.pop(owner, None)
    else:
        project.overrides[owner] = deepcopy(after)
    project.undo_stack.append(dict(entity_id=owner, before=before, after=deepcopy(after)))
    project.redo_stack.clear()


def merge_patch(baseline, working, patched, changes, expected, previous):
    """Check complete two-byte receipts and disjoint composition independently."""
    from .build import BuildError
    if not isinstance(patched, bytes) or len(patched) != len(baseline) or len(working) != len(baseline):
        raise BuildError('System selector patch changed MAN length')
    occupied = {i for c in previous for i in range(c['decoded_byte_offset'], c['decoded_byte_offset'] + c.get('byte_length', 1))}
    allowed, audited = set(), set()
    for target in expected.values():
        at = target['decoded_byte_offset']
        if type(at) is not int or not 0 <= at <= len(baseline) - 2:
            raise BuildError('System selector span escapes the source MAN')
        span = set(range(at, at + 2))
        if span & (occupied | allowed) or working[at:at + 2] != baseline[at:at + 2]:
            raise BuildError('System selector patch overlaps another authored MAN span')
        allowed.update(span)
    result = bytearray(working)
    seen = set()
    for change in changes:
        identity = change.get('system_flag_id')
        target = expected.get(identity)
        at = change.get('decoded_byte_offset')
        if target is None or identity in seen:
            raise BuildError('System selector audit has missing or duplicate identity')
        index = validate_system_flag_values(target['requested_values'])
        desired = bytes(((baseline[target['decoded_byte_offset']] & 0xF0) | (index >> 8), index & 255))
        if (at != target['decoded_byte_offset'] or change.get('byte_length') != 2
                or change.get('owner_id') != target['owner_id'] or change.get('pc') != target['pc']
                or change.get('mnemonic') != target['mnemonic'] or change.get('target_context') is not None
                or change.get('field') != 'system_flag_index'
                or change.get('source_record_sha256') != target['source_record_sha256']
                or change.get('source_decoded_man_sha256') != hashlib.sha256(baseline).hexdigest()
                or change.get('before_hex') != baseline[at:at + 2].hex()
                or change.get('after_hex') != patched[at:at + 2].hex()
                or change.get('before_index') != target['values']['index'] or change.get('after_index') != index
                or patched[at:at + 2] != desired):
            raise BuildError('System selector audit differs from source or requested bytes')
        seen.add(identity); audited.update(range(at, at + 2)); result[at:at + 2] = desired
    for identity, target in expected.items():
        at = target['decoded_byte_offset']; index = validate_system_flag_values(target['requested_values'])
        desired = bytes(((baseline[at] & 0xF0) | (index >> 8), index & 255))
        if patched[at:at + 2] != desired or (desired != baseline[at:at + 2] and identity not in seen):
            raise BuildError('System selector requested change is missing from the audit')
    if any(a != b and i not in audited for i, (a, b) in enumerate(zip(baseline, patched))):
        raise BuildError('System selector patch changed an unaudited MAN byte')
    return bytes(result)
