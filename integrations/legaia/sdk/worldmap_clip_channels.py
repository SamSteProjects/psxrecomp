"""Reviewed native clip channels without invented placed-model associations."""
from base64 import b64decode, b64encode
from copy import copy, deepcopy
from hashlib import sha256

from importer.worldmap_animation_authoring import patch_world_animation_bank
from .project import ProjectError, digest
from .worldmap_animation_channels import inspect
from .worldmap_animation_binding import COMPONENT, SCHEMA, owner, normalize, verify
from .worldmap_placement_allocation import _fresh


def review(project, animation_id, source_key, edits, shared_record):
    if shared_record is not True:
        raise ProjectError('Native clip edits require explicit shared-record consent')
    source = inspect(project, animation_id, source_key)
    record = source['record']; scene = record['source_scene']; span = record['source_record']
    retail = b64decode(source['retail_bank_base64'], validate=True)
    current = b64decode(source['current_bank_base64'], validate=True)
    _, audit = patch_world_animation_bank(retail, source['retail_bank_sha256'], span['record_index'], span['sha256'], edits)
    identifier = owner(scene); before = deepcopy(project.overrides.get(identifier))
    binding = deepcopy(source['binding']) or dict(schema_version=SCHEMA, scene=scene,
        source_disc_sha256=span['disc_sha256'], source_bank_sha256=source['retail_bank_sha256'], entries={})
    index = f"{span['record_index']:04d}"; rows = normalize(audit)
    if rows:
        binding['entries'][index] = dict(source_record_sha256=span['sha256'], edits=rows)
    else:
        binding['entries'].pop(index, None)
    after = {COMPONENT: binding} if binding['entries'] else None
    view = copy(project); view.overrides = deepcopy(project.overrides)
    if after: view.overrides[identifier] = after
    else: view.overrides.pop(identifier, None)
    _, proposed, _, _, _ = verify(view, scene)
    start = span['byte_offset']; end = start+span['byte_length']
    if current[:start] != proposed[:start] or current[end:] != proposed[end:]:
        raise ProjectError('Native clip proposal changed a neighboring Current record')
    result = dict(schema_version='legaia.world-clip-channel-review.v1', source=source,
        edits=deepcopy(edits), binding=deepcopy(binding) if after else None, shared_record=True,
        proposed_bank_base64=b64encode(proposed).decode('ascii'), proposed_bank_sha256=sha256(proposed).hexdigest(),
        proposed_record_sha256=sha256(proposed[start:end]).hexdigest(),
        changed_bytes=[dict(byte_offset=i, before_byte=a, after_byte=b) for i,(a,b) in enumerate(zip(current,proposed)) if a!=b],
        project_change=before!=after, read_only=True, project_changed=False, gameplay_verified=False)
    result['review_key'] = digest(result)
    _fresh(project, source_key)
    return result


def apply(project, command):
    fields = {'type','animation_id','source_key','edits','shared_record','review_key'}
    if not isinstance(command,dict) or set(command)!=fields or command['type']!='set_world_clip_channels':
        raise ProjectError('Native clip Apply requires exact reviewed source and channels')
    result = review(project, **{k:command[k] for k in fields-{'type','review_key'}})
    if result['review_key'] != command['review_key']:
        raise ProjectError('Native clip Review changed; Review and Preview again')
    if not result['project_change']: return result
    identifier = owner(result['source']['record']['source_scene']); before = deepcopy(project.overrides.get(identifier))
    after = {COMPONENT:deepcopy(result['binding'])} if result['binding'] else None
    _fresh(project, command['source_key'])
    if after: project.overrides[identifier]=after
    else: project.overrides.pop(identifier,None)
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)))
    project.redo_stack.clear()
    return result
