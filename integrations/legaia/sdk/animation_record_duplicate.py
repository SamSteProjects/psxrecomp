"""Reviewed independent copies of retained native clips; assignments stay intact."""
from copy import deepcopy
from hashlib import sha256
from uuid import UUID

from .animation_record_ledger import compose, publish, validate
from .project import ProjectError, digest
from .scene_preview import source_key


def prepare(project, scene_id, record_id, expected_source_key):
    key = source_key(project)
    if project.mode != 'edit' or scene_id != project.active_scene or not key or key != expected_source_key:
        raise ProjectError('Clip duplication requires the current editable scene source')
    ledger = deepcopy(project.overrides.get(scene_id, {}).get('AnimationRecords'))
    validate(project, scene_id, ledger)
    source = next((row for row in ledger['records'] if row['record_id'] == record_id), None)
    if source is None:
        raise ProjectError('Clip duplication requires an existing retained identity')
    # Both compositions freshly reconstruct every frozen donor and opaque native
    # field. The duplicate reuses that exact recipe, not current shared edits.
    before, _ = compose(project, scene_id, ledger=ledger)
    identity = digest(dict(operation='duplicate_retained_animation', scene_id=scene_id,
                           record_id=record_id, project_source_key=key))
    new_id = str(UUID(bytes=bytes.fromhex(identity)[:16], version=4))
    if any(row['record_id'] == new_id for row in ledger['records']):
        raise ProjectError('Duplicate clip identity is already reserved')
    duplicate = dict(deepcopy(source), record_id=new_id)
    ledger['records'].append(duplicate)
    ledger['revision'] += 1
    validate(project, scene_id, ledger)
    candidate, native = compose(project, scene_id, ledger=ledger)
    allocated = next(row for row in native['allocated_records'] if row['record_id'] == new_id)
    if allocated['candidate_record_sha256'] != source['record_sha256']:
        raise ProjectError('Duplicate native clip differs from its retained source')
    if source_key(project) != key:
        raise ProjectError('Project changed during retained clip duplication')
    report = dict(schema_version='legaia.animation-record-duplicate-review.v1',
                  scene_id=scene_id, record_id=record_id, project_source_key=key,
                  source_entry=deepcopy(source), duplicate_entry=duplicate,
                  source_active=record_id not in ledger['removed_record_ids'],
                  effective_bank_sha256=sha256(before).hexdigest(),
                  candidate_bank_sha256=sha256(candidate).hexdigest(),
                  proposed_ledger=ledger, project_changed=False, gameplay_verified=False,
                  assignments_changed=False)
    report['review_key'] = digest(report)
    return candidate, report


def apply(project, command):
    if set(command) != {'type', 'scene_id', 'record_id', 'expected_source_key', 'review_key'}:
        raise ProjectError('Duplicate Apply requires the exact reviewed scene, clip and source')
    _, report = prepare(project, command['scene_id'], command['record_id'], command['expected_source_key'])
    if command['review_key'] != report['review_key']:
        raise ProjectError('Clip duplication changed after Review; review again')
    publish(project, command['scene_id'], report['proposed_ledger'])
    return report
