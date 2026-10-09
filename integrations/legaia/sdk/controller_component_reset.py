"""Reviewed removal of one authored controller component, with atomic history."""
from copy import deepcopy
from hashlib import sha256
from .controller_components import CONTROLLER_COMPONENTS
from .controller_system_flags import prepare, compose, state_key
from .controller_source_report import controller_report
from .project import ProjectError, digest
from importer.core import ImportError as RetailImportError


def review(project, owner, component):
    if not isinstance(component, str) or component not in CONTROLLER_COMPONENTS:
        raise ProjectError('Choose a supported controller component to reset')
    try:
        key, context, offset, record, entry, components, current, _ = prepare(project, owner)
        authored = components.get(component)
        if authored is None:
            raise ProjectError('Controller component has no authored entries to reset')
        proposed = deepcopy(components)
        del proposed[component]
        candidate = compose(context, owner, proposed)
        changed = [i for i, (a, b) in enumerate(zip(current, candidate)) if a != b]
        if len(candidate) != len(current) or any(not offset <= i < offset+len(record) for i in changed):
            raise ProjectError('Controller component reset changed unrelated MAN bytes')
        proof = dict(owner_id=owner, component=component, state_key=key,
                     source_record_sha256=sha256(record).hexdigest(),
                     current_record_sha256=sha256(current[offset:offset+len(record)]).hexdigest(),
                     proposed_record_sha256=sha256(candidate[offset:offset+len(record)]).hexdigest(),
                     authored=deepcopy(authored), proposed=proposed)
        source_report = controller_report(owner, context._man, offset, record, entry, context._source)
        current_report = controller_report(owner, current, offset, record, entry, context._source,
                                          components.get('ControllerSystemFlags', {}).get('entries', {}))
        proposed_report = controller_report(owner, candidate, offset, record, entry, context._source,
                                           proposed.get('ControllerSystemFlags', {}).get('entries', {}))
    except RetailImportError as exc:
        raise ProjectError(str(exc)) from exc
    if key != state_key(project):
        raise ProjectError('Controller component source changed during reset Review')
    return dict(schema_version='legaia.controller-component-reset.v1', **proof,
                review_key=digest(proof), removed_operand_ids=sorted(authored['entries']),
                removed_operand_count=len(authored['entries']),
                changed_decoded_byte_offsets=changed, native_bytes_changed=bool(changed),
                source_report=source_report, current_report=current_report, proposed_report=proposed_report,
                project_changed=False, gameplay_verified=False)


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'component', 'review_key'} or command['type'] != 'reset_controller_component':
        raise ProjectError('Controller component reset requires exact reviewed inputs')
    result = review(project, command['entity_id'], command['component'])
    if result['review_key'] != command['review_key']:
        raise ProjectError('Controller component source changed; review reset again')
    owner = command['entity_id']
    before = deepcopy(project.overrides[owner])
    after = deepcopy(result['proposed']) or None
    if after is None:
        del project.overrides[owner]
    else:
        project.overrides[owner] = after
    project.undo_stack.append(dict(entity_id=owner, before=before, after=deepcopy(after)))
    project.redo_stack.clear()
