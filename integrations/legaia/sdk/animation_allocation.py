"""Reviewed allocation of persistent rigid clips; native delivery remains separate."""
from copy import deepcopy
from hashlib import sha256
from uuid import UUID

from importer.animation import animation_record_ranges, decode_animation_record
from importer.animation_allocation import allocate_animation_record, append_animation_record_payloads
from importer.animation_authoring import replace_animation_record
from importer.pipeline import _disc_context
from importer.scene_animation import load_scene_actor_animation_catalog
from .project import ProjectError, digest
from .scene_preview import source_key
from .animation_record_ledger import SCHEMA, validate, reconstruct, verify_witnesses, publish, compose


def prepare_record_allocation(project, entity_id, source_frame_indices, edits,
                              expected_source_key):
    """Resolve a donor through actor/model evidence and review one new record.

    Current shared channel contributions are composed before copying frames.
    The preview neither publishes a component nor allocates files/history.
    """
    if project.mode != 'edit':
        raise ProjectError('Animation record allocation review requires Edit mode')
    document = project.imports.get(project.active_scene)
    actor = next((item for item in (document or {}).get('actors', [])
                  if item['semantic_id'] == entity_id), None)
    if actor is None:
        raise ProjectError('Animation allocation requires an imported actor in the active scene')
    if 'ActorAllocatedAnimation' in project.overrides.get(entity_id,{}):
        raise ProjectError('Allocating from an assigned allocated clip is not implemented; clear its assignment before capturing an imported clip')
    key = source_key(project)
    if not key or expected_source_key != key:
        raise ProjectError('Animation allocation source is stale; review the current scene')
    with _disc_context(project.disc_path):
        model_source = actor
        if any(name in project.overrides.get(entity_id, {}) for name in ('ActorAppearance', 'ActorAnimation')):
            from .actor_animation import source_actor
            model_source = project.appearance_source_actor(entity_id, verify_disc=True)
            actor = source_actor(project, entity_id, verify_disc=True)
        options = project.animation_authoring_options(actor['semantic_id'])
        binding = options['binding']
        catalog = load_scene_actor_animation_catalog(project.disc_path, document['scene']['name'])
        retail, provenance = catalog.source_bank()
        owners = {item['semantic_id']: deepcopy(project.overrides[item['semantic_id']]['AnimationChannels'])
                  for item in document['actors']
                  if 'AnimationChannels' in project.overrides.get(item['semantic_id'], {})}
        effective, _ = catalog.authored_bank(owners)
        identity_hash = digest(dict(project_source_key=key, entity_id=entity_id,
            donor_animation_id=binding['semantic_id'], source_frame_indices=source_frame_indices, edits=edits))
        record_id = str(UUID(bytes=bytes.fromhex(identity_hash)[:16], version=4))
        start,end = animation_record_ranges(retail)[binding['source_record']['record_index']]
        donor, captured = retail[start:end], effective[start:end]
        _, differences = replace_animation_record(donor,sha256(donor).hexdigest(),captured)
        donor_edits = {}
        for row in differences:
            field, axis = row['field'].split('.')
            edit = donor_edits.setdefault((row['frame_index'],row['object_index']),
                dict(frame_index=row['frame_index'],object_index=row['object_index']))
            edit.setdefault(field,{})[axis] = row['after_value']
        record, _ = allocate_animation_record(captured,sha256(captured).hexdigest(),source_frame_indices,edits)
        decoded = decode_animation_record(donor)
        entry = dict(record_id=record_id,entity_id=entity_id,channel_owner_entity_id=actor['semantic_id'],
            model_source_entity_id=model_source['semantic_id'],donor_animation_id=binding['semantic_id'],
            donor_asset_id=binding['asset_semantic_id'],donor_record_sha256=sha256(donor).hexdigest(),
            effective_donor_record_sha256=sha256(captured).hexdigest(),donor_frame_count=decoded['frame_count'],
            object_count=decoded['bone_count'],donor_edits=list(donor_edits.values()),
            source_frame_indices=deepcopy(source_frame_indices),edits=deepcopy(edits),record_sha256=sha256(record).hexdigest())
        ledger = deepcopy(project.overrides.get(project.active_scene,{}).get('AnimationRecords'))
        if ledger is not None:
            validate(project,project.active_scene,ledger)
            verify_witnesses(ledger,catalog)
            payloads = reconstruct(retail,ledger)
            if any(row['record_id'] == record_id for row in ledger['records']):
                raise ProjectError('Animation identity is already reserved in this ledger')
            if payloads:
                effective, _ = append_animation_record_payloads(effective,sha256(effective).hexdigest(),payloads)
        else:
            ledger = dict(schema_version=SCHEMA,source_scene_id=project.active_scene,
                source_bank_sha256=sha256(retail).hexdigest(),revision=0,records=[],removed_record_ids=[])
        ledger['records'].append(entry)
        ledger['revision'] += 1
        validate(project,project.active_scene,ledger)
        candidate, allocation = append_animation_record_payloads(effective,sha256(effective).hexdigest(),
            [dict(record_id=record_id,record=record)])
    if source_key(project) != key:
        raise ProjectError('Project changed while verifying animation allocation')
    report = dict(schema_version='legaia.animation-record-allocation-review.v2',
        entity_id=entity_id, scene_id=project.active_scene, project_source_key=key,
        animation_id=f"animation://{document['scene']['name']}/authored-record/{record_id}",
        donor_animation_id=binding['semantic_id'],
        channel_owner_entity_id=actor['semantic_id'], model_source_entity_id=model_source['semantic_id'],
        donor_asset_id=binding['asset_semantic_id'], source_bank=deepcopy(provenance),
        retail_bank_sha256=sha256(retail).hexdigest(), effective_bank_sha256=sha256(effective).hexdigest(),
        candidate_bank_sha256=sha256(candidate).hexdigest(), allocation=allocation,
        project_changed=False, gameplay_verified=False,
        proposed_ledger=ledger,
        capabilities=dict(review=True, apply=True, build=True, actor_assignment=False),
        limitations=['Qualified compressed and raw streaming ANM carriers support normal Build relocation; final source, carrier and package readback are required.',
                     'The frame sequence has no verified retail rate or runtime clip-selection evidence.',
                     'Existing shared clip edits are copied into the new record; existing records remain unchanged.'])
    report['review_key'] = digest(report)
    return candidate, report


def preview_record_allocation(project, entity_id, source_frame_indices, edits, expected_source_key):
    return prepare_record_allocation(project, entity_id, source_frame_indices, edits, expected_source_key)[1]


def allocation_options(project, entity_id, expected_source_key):
    if project.mode != 'edit':
        raise ProjectError('Animation allocation requires Edit mode')
    document = project.imports.get(project.active_scene)
    actor = next((a for a in (document or {}).get('actors',[]) if a['semantic_id'] == entity_id),None)
    key = source_key(project)
    if actor is None or not key or key != expected_source_key:
        raise ProjectError('Animation allocation requires the current imported actor and scene source')
    model_source = actor
    with _disc_context(project.disc_path):
        if any(name in project.overrides.get(entity_id,{}) for name in ('ActorAppearance','ActorAnimation')):
            from .actor_animation import source_actor
            model_source = project.appearance_source_actor(entity_id,verify_disc=True)
            actor = source_actor(project,entity_id,verify_disc=True)
        options = project.animation_authoring_options(actor['semantic_id'])
        binding = options['binding']
        ledger = project.overrides.get(project.active_scene,{}).get('AnimationRecords')
        if ledger is not None:
            validate(project,project.active_scene,ledger,verify_disc=True)
        catalog = load_scene_actor_animation_catalog(project.disc_path,document['scene']['name'])
        catalog.source_bank()
        delivery = True
    used = sum(len(row['source_frame_indices'])*row['object_count'] for row in (ledger or {}).get('records',[]))
    remaining = 4096-used
    maximum = min(512,remaining//binding['bone_count'])
    if len((ledger or {}).get('records',[])) >= 64 or (ledger or {}).get('revision',0) >= 64:
        maximum = 0
    if source_key(project) != key:
        raise ProjectError('Project changed while loading animation allocation options')
    return dict(schema_version='legaia.animation-record-allocation-options.v1',entity_id=entity_id,
        scene_id=project.active_scene,project_source_key=key,donor_animation_id=binding['semantic_id'],
        channel_owner_entity_id=actor['semantic_id'],model_source_entity_id=model_source['semantic_id'],
        donor_asset_id=binding['asset_semantic_id'],donor_frame_count=binding['frame_count'],
        object_count=binding['bone_count'],maximum_frame_count=maximum,
        remaining_channel_count=remaining,remaining_record_count=64-len((ledger or {}).get('records',[])),
        build_available=delivery,gameplay_verified=False)


def pose_record_allocation(project, entity_id, source_frame_indices, edits, expected_source_key, review_key):
    candidate,report = prepare_record_allocation(project,entity_id,source_frame_indices,edits,expected_source_key)
    if report['review_key'] != review_key:
        raise ProjectError('Animation pose differs from the reviewed allocation; review again')
    entry = report['proposed_ledger']['records'][-1]
    row = report['allocation']['allocated_records'][0]
    start,end = animation_record_ranges(candidate)[row['record_index']]
    decoded = decode_animation_record(candidate[start:end])
    document = project.imports[project.active_scene]
    asset = next(a for a in document['assets']['models'] if a['semantic_id'] == entry['donor_asset_id'])
    actor = next(a for a in document['actors'] if a['semantic_id'] == entry['channel_owner_entity_id'])
    with _disc_context(project.disc_path):
        catalog = load_scene_actor_animation_catalog(project.disc_path,document['scene']['name'])
        # The donor supplies the evidenced object/channel prefix. The new record
        # is unassigned; do not label its ordinal as an existing MAN association.
        index = int(entry['donor_animation_id'].rsplit('/',1)[1])
        animation = catalog._animation_preview(actor,asset,index,decoded)
    donor_source = animation['source_record']
    animation.update(semantic_id=report['animation_id'],entity_id=entity_id,actor_semantic_id=entity_id,
        clip_id='allocation-preview',label='Proposed allocated clip',representation='allocation_preview',
        source_clip_id=entry['donor_animation_id'],proposal=report,
        source_record=dict(source_kind='authored_animation_record',record_id=entry['record_id'],
            record_sha256=entry['record_sha256'],bank_sha256=report['candidate_bank_sha256'],
            record_index=row['record_index'],byte_offset=start,byte_length=end-start,
            byte_coordinate_space='proposed_native_scene_anm_bank',donor_source=donor_source),
        association=dict(kind='reviewed_donor_channel_prefix_for_unassigned_allocated_clip',runtime_assigned=False,
            donor_animation_id=entry['donor_animation_id'],channel_owner_entity_id=entry['channel_owner_entity_id'],
            model_source_entity_id=entry['model_source_entity_id'],active_object_indices=list(range(decoded['bone_count']))))
    if source_key(project) != expected_source_key:
        raise ProjectError('Project changed during allocated animation pose preview')
    return animation,deepcopy(asset)


def apply_command(project, command):
    if set(command) != {'type','entity_id','source_frame_indices','edits','expected_source_key','review_key'}:
        raise ProjectError('Animation allocation Apply requires the exact reviewed request')
    candidate, report = prepare_record_allocation(project,command['entity_id'],command['source_frame_indices'],
                                                 command['edits'],command['expected_source_key'])
    if command['review_key'] != report['review_key']:
        raise ProjectError('Animation allocation changed after review; review again')
    # Reconstruct the complete prospective ledger independently, before publishing.
    composed, _ = compose(project,project.active_scene,ledger=report['proposed_ledger'])
    if composed != candidate:
        raise ProjectError('Animation ledger replay differs from the reviewed bank')
    publish(project,project.active_scene,report['proposed_ledger'])


def record_library(project, scene_id, expected_source_key):
    """Verify saved captures before exposing their stable identities to the editor."""
    key = source_key(project)
    if project.mode != 'edit' or scene_id != project.active_scene or not key or key != expected_source_key:
        raise ProjectError('Allocated clip library requires the current editable scene source')
    ledger = project.overrides.get(scene_id,{}).get('AnimationRecords')
    records = []
    delivery = False
    if ledger is not None:
        validate(project,scene_id,ledger,verify_disc=True)
        with _disc_context(project.disc_path):
            catalog=load_scene_actor_animation_catalog(project.disc_path,project.imports[scene_id]['scene']['name'])
            catalog.source_bank()
            delivery=True
        for entry in ledger['records']:
            records.append(dict(record_id=entry['record_id'],
                animation_id=f"animation://{project.imports[scene_id]['scene']['name']}/authored-record/{entry['record_id']}",
                entity_id=entry['entity_id'],channel_owner_entity_id=entry['channel_owner_entity_id'],
                model_source_entity_id=entry['model_source_entity_id'],donor_asset_id=entry['donor_asset_id'],
                donor_animation_id=entry['donor_animation_id'],record_sha256=entry['record_sha256'],
                frame_count=len(entry['source_frame_indices']),object_count=entry['object_count'],
                active=entry['record_id'] not in ledger['removed_record_ids'],runtime_assigned=False))
    if source_key(project) != key:
        raise ProjectError('Project changed while loading allocated clips')
    return dict(schema_version='legaia.animation-record-library.v1',scene_id=scene_id,
        project_source_key=key,revision=(ledger or {}).get('revision',0),records=records,
        activation_available=(ledger or {}).get('revision',0)<64,
        build_available=delivery,gameplay_verified=False)


def pose_saved_record(project, scene_id, record_id, expected_source_key):
    library = record_library(project,scene_id,expected_source_key)
    row = next((item for item in library['records'] if item['record_id'] == record_id),None)
    if row is None:
        raise ProjectError('Saved clip preview requires a retained record identity')
    ledger = deepcopy(project.overrides[scene_id]['AnimationRecords'])
    # Retired clips remain inspectable, without assigning a native bank ordinal
    # or silently restoring them in the project.
    ledger['removed_record_ids'] = []
    from .animation_record_ledger import verified_source
    source,catalog = verified_source(project,scene_id)
    payload = next(item['record'] for item in reconstruct(source,ledger) if item['record_id'] == record_id)
    entry = next(item for item in ledger['records'] if item['record_id'] == record_id)
    document = project.imports[scene_id]
    asset = next(item for item in document['assets']['models'] if item['semantic_id'] == entry['donor_asset_id'])
    actor = next(item for item in document['actors'] if item['semantic_id'] == entry['channel_owner_entity_id'])
    with _disc_context(project.disc_path):
        animation = catalog._animation_preview(actor,asset,
            int(entry['donor_animation_id'].rsplit('/',1)[1]),decode_animation_record(payload))
    donor_source = animation['source_record']
    animation.update(semantic_id=row['animation_id'],entity_id=entry['entity_id'],actor_semantic_id=entry['entity_id'],
        clip_id='allocated-record',label='Saved allocated clip',representation='allocated_record',
        source_clip_id=entry['donor_animation_id'],saved_record=deepcopy(row),
        source_record=dict(source_kind='authored_animation_record',record_id=record_id,
            record_sha256=entry['record_sha256'],byte_length=len(payload),
            byte_coordinate_space='retained_native_animation_record',donor_source=donor_source),
        association=dict(kind='captured_donor_channel_prefix_for_unassigned_allocated_clip',runtime_assigned=False,
            channel_owner_entity_id=entry['channel_owner_entity_id'],model_source_entity_id=entry['model_source_entity_id'],
            active_object_indices=list(range(entry['object_count']))))
    if source_key(project) != expected_source_key:
        raise ProjectError('Project changed during saved clip pose preview')
    return animation,deepcopy(asset)


def prepare_record_activation(project, scene_id, record_id, active, expected_source_key):
    if project.mode != 'edit' or scene_id != project.active_scene:
        raise ProjectError('Animation record activation requires the active scene in Edit mode')
    key = source_key(project)
    if not key or key != expected_source_key:
        raise ProjectError('Animation record activation source is stale; review again')
    ledger = deepcopy(project.overrides.get(scene_id,{}).get('AnimationRecords'))
    validate(project,scene_id,ledger)
    if type(active) is not bool or not isinstance(record_id,str) or not any(row['record_id'] == record_id for row in ledger['records']):
        raise ProjectError('Animation activation requires a retained record identity and exact boolean')
    was_active = record_id not in ledger['removed_record_ids']
    if active == was_active:
        raise ProjectError('Animation record activation has no effective change')
    if not active and any(components.get('ActorAllocatedAnimation',{}).get('scene_id')==scene_id
            and components.get('ActorAllocatedAnimation',{}).get('record_id')==record_id
            for components in project.overrides.values()):
        raise ProjectError('Allocated clip is still assigned to an actor; clear its initial assignment before retirement')
    if active:
        ledger['removed_record_ids'].remove(record_id)
    else:
        ledger['removed_record_ids'].append(record_id)
    ledger['revision'] += 1
    candidate, allocation = compose(project,scene_id,ledger=ledger)
    if source_key(project) != key:
        raise ProjectError('Project changed during animation record activation review')
    report = dict(schema_version='legaia.animation-record-activation-review.v1',scene_id=scene_id,
        record_id=record_id,active=active,project_source_key=key,
        candidate_bank_sha256=sha256(candidate).hexdigest(),allocation=allocation,
        proposed_ledger=ledger,project_changed=False,gameplay_verified=False)
    report['review_key'] = digest(report)
    return candidate,report


def apply_activation_command(project, command):
    if set(command) != {'type','scene_id','record_id','active','expected_source_key','review_key'}:
        raise ProjectError('Animation activation Apply requires the exact reviewed request')
    _, report = prepare_record_activation(project,command['scene_id'],command['record_id'],
                                         command['active'],command['expected_source_key'])
    if report['review_key'] != command['review_key']:
        raise ProjectError('Animation activation changed after review; review again')
    publish(project,command['scene_id'],report['proposed_ledger'])
