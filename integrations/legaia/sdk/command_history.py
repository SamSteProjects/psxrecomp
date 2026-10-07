"""Read-only views of the project's session Undo/Redo records."""
from copy import deepcopy
from .project import ProjectError, canonical, digest

PAGE_SIZE = 50
MAX_RECORD_BYTES = 8 * 1024 * 1024


def source_key(project):
    return digest(dict(project=str(project.root), document=project._document(),
                       saved=project.saved_digest, undo=project.undo_stack, redo=project.redo_stack))


def listing(project, offset=0):
    if type(offset) is not int or offset < 0:
        raise ProjectError('History offset must be a nonnegative integer')
    total = len(project.undo_stack) + len(project.redo_stack)
    if offset > total:
        raise ProjectError('History offset exceeds current session records')
    rows = []
    # Stack order is explicit: newest applied first, then next redo first.
    position = 0
    for branch, stack in (('undo', project.undo_stack), ('redo', project.redo_stack)):
        for index in range(len(stack) - 1, -1, -1):
            if offset <= position < offset + PAGE_SIZE:
                entry = stack[index]
                rows.append(dict(branch=branch, index=index, record_key=digest(entry),
                                 recorded_target=entry.get('target'),
                                 recorded_owners={key: deepcopy(entry[key]) for key in
                                     ('entity_id', 'asset_id', 'template_id', 'bookmark_id',
                                      'group_id', 'view_id', 'selection_set_id', 'source_entity_ids')
                                     if key in entry}, byte_length=len(canonical(entry))))
            position += 1
    result = dict(schema_version='legaia.command-history.v1', source_key=source_key(project),
                read_only=True, session_only=True, total=total, offset=offset,
                page_size=PAGE_SIZE, records=rows,
                next_offset=offset + len(rows) if offset + len(rows) < total else None)
    if len(canonical(result)) > MAX_RECORD_BYTES:
        raise ProjectError('History page exceeds the 8 MiB inspection limit')
    return result


def inspect_record(project, key, branch, index, record_key):
    if not isinstance(key, str) or key != source_key(project):
        raise ProjectError('Session history changed; refresh before inspecting a record')
    if branch not in ('undo', 'redo') or type(index) is not int or index < 0:
        raise ProjectError('Invalid session history selector')
    stack = project.undo_stack if branch == 'undo' else project.redo_stack
    if index >= len(stack) or record_key != digest(stack[index]):
        raise ProjectError('Session history record no longer matches')
    entry = stack[index]
    if len(canonical(entry)) > MAX_RECORD_BYTES:
        raise ProjectError('History record exceeds the 8 MiB inspection limit')
    return dict(schema_version='legaia.command-history-record.v1', source_key=key,
                read_only=True, branch=branch, index=index, record_key=record_key,
                record=deepcopy(entry))
