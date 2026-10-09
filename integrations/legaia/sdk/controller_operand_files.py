"""Source-bound controller operand transfer; no instruction or runtime transfer."""
from copy import deepcopy
from hashlib import sha256
import json
from .project import ProjectError, digest
from .controller_components import CONTROLLER_COMPONENTS
from .controller_system_flags import prepare, compose, state_key, validate_components, scene_document
from .controller_snapshots import snapshot
from .script_operand_files import parse_json
from importer.core import ImportError as RetailImportError

SCHEMA = 'legaia.controller-operand-file.v1'


def parse(content):
    value = parse_json(content)
    fields = {'schema_version', 'scene_id', 'owner_id', 'source_import_sha256', 'source_record_sha256', 'components'}
    if not isinstance(value, dict) or set(value) != fields or value['schema_version'] != SCHEMA:
        raise ProjectError('Unsupported controller operand file fields or schema')
    for name in ('source_import_sha256', 'source_record_sha256'):
        if not isinstance(value[name], str) or len(value[name]) != 64 or any(c not in '0123456789abcdef' for c in value[name]):
            raise ProjectError('Controller operand file requires immutable source hashes')
    if any(not isinstance(value[name], str) or len(value[name]) > 512 for name in ('scene_id', 'owner_id')):
        raise ProjectError('Controller operand file requires structural scene ownership')
    components = value['components']
    if not isinstance(components, dict) or set(components)-CONTROLLER_COMPONENTS:
        raise ProjectError('Unsupported controller operand component')
    total = 0
    for component in components.values():
        if not isinstance(component, dict) or set(component) != {'entries'} or not isinstance(component['entries'], dict) or not component['entries']:
            raise ProjectError('Controller operand component requires nonempty entries')
        total += len(component['entries'])
        if any(len(identifier) > 512 or not (entry is None or isinstance(entry, dict)) for identifier, entry in component['entries'].items()):
            raise ProjectError('Controller operand entry requires values or null to inherit Retail')
    if total > 256:
        raise ProjectError('Controller operand file is limited to 256 entries')
    return value


def review(project, owner, content):
    value = parse(content)
    if value['owner_id'] != owner:
        raise ProjectError('Controller operand file belongs to another owner')
    key, context, offset, record, _, components, current, _ = prepare(project, owner)
    document = scene_document(project, owner)
    record_hash = sha256(record).hexdigest()
    if value['scene_id'] != project.active_scene or value['source_import_sha256'] != digest(document) or value['source_record_sha256'] != record_hash:
        raise ProjectError('Controller operand file differs from immutable imported source')
    before = deepcopy(project.overrides.get(owner))
    workspace = snapshot(project, owner, key)
    proposed = deepcopy(components)
    rows = []
    for family, supplied in sorted(value['components'].items()):
        targets = {target['semantic_id']: target for target in workspace['families'][family]['targets']}
        entries = deepcopy(proposed.get(family, {}).get('entries', {}))
        for identifier, fields in sorted(supplied['entries'].items()):
            target = targets.get(identifier)
            if target is None:
                raise ProjectError('Controller operand file contains an unqualified source target')
            if fields is not None:
                validate_components(project, owner, {family:dict(source_record_sha256=record_hash, entries={identifier:fields})})
            previous = deepcopy(entries.get(identifier))
            if fields is None or fields == target['values']:
                entries.pop(identifier, None)
            else:
                entries[identifier] = deepcopy(fields)
            actual = deepcopy(entries.get(identifier))
            rows.append(dict(component=family, operand_id=identifier, before=previous, after=actual, changed=previous != actual))
        if entries:
            proposed[family] = dict(source_record_sha256=record_hash, entries=entries)
        else:
            proposed.pop(family, None)
    try:
        if proposed:
            validate_components(project, owner, proposed)
        candidate = compose(context, owner, proposed)
    except RetailImportError as exc:
        raise ProjectError(str(exc)) from exc
    changed = [i for i, (a, b) in enumerate(zip(current, candidate)) if a != b]
    if len(current) != len(candidate) or any(not offset <= i < offset+len(record) for i in changed):
        raise ProjectError('Controller operand transfer changed unrelated MAN bytes')
    if key != state_key(project) or before != project.overrides.get(owner):
        raise ProjectError('Controller project changed during operand file Review')
    after = deepcopy(proposed) or None
    proof = dict(owner_id=owner, state_key=key, file=value, before=before, after=after)
    return dict(schema_version='legaia.controller-operand-review.v1', owner_id=owner, scene_id=value['scene_id'],
                state_key=key, source_import_sha256=value['source_import_sha256'], source_record_sha256=record_hash,
                current_record_sha256=sha256(current[offset:offset+len(record)]).hexdigest(),
                proposed_record_sha256=sha256(candidate[offset:offset+len(record)]).hexdigest(),
                before=before, after=after, entries=rows, change_count=sum(row['changed'] for row in rows),
                changed_decoded_byte_offsets=changed, native_bytes_changed=bool(changed), no_op=before == after,
                review_key=digest(proof), project_changed=False, gameplay_verified=False)


def export_file(project, owner):
    key, _, _, record, _, components, _, _ = prepare(project, owner)
    value = dict(schema_version=SCHEMA, scene_id=project.active_scene, owner_id=owner,
                source_import_sha256=digest(scene_document(project, owner)), source_record_sha256=sha256(record).hexdigest(),
                components={family:dict(entries=deepcopy(value['entries'])) for family, value in sorted(components.items())})
    parse(json.dumps(value))
    if key != state_key(project):
        raise ProjectError('Controller project changed during operand export')
    return value


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'content', 'review_key'} or command['type'] != 'import_controller_operand_file':
        raise ProjectError('Controller operand import requires exact reviewed inputs')
    result = review(project, command['entity_id'], command['content'])
    if command['review_key'] != result['review_key']:
        raise ProjectError('Controller operand file or project changed; review again')
    if result['no_op']:
        return
    owner = command['entity_id']
    if result['after'] is None:
        project.overrides.pop(owner, None)
    else:
        project.overrides[owner] = deepcopy(result['after'])
    project.undo_stack.append(dict(entity_id=owner, before=deepcopy(result['before']), after=deepcopy(result['after'])))
    project.redo_stack.clear()
