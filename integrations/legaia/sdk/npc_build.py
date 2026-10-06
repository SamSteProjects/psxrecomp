"""Qualified NPC candidates for fixed-span overlays or compressed/raw MAN relocation.

This establishes serialization only, without claiming guest actor allocation,
spawn scheduling or acceptance of opaque script paths.
"""
from copy import copy, deepcopy
from hashlib import sha256
import re
import struct

from importer.core import ImportError, parse_scene_table, decompress_lzs
from importer.lzs_optimal import MAX_OPTIMAL_BYTES, compress_lzs_optimal
from importer.prot_layout import locate_physical_span
from importer.serialization import compress_lzs
from .build import authored_state_key
from .draft_build import _prepare_draft_scene
from .project import ProjectError
from .actor_capacity import actor_pool_assessment

MAX_CANDIDATE_BYTES = 4 * 1024 * 1024
MAX_PROT_BYTES = 256 * 1024 * 1024

# Shared author-facing scope; this is not a readiness verdict for any project.
NORMAL_BUILD_SCOPE_NOTE = (
    'Normal Build supports source-qualified compressed and raw streaming MAN NPC candidates. '
    'Compressed candidates can use fixed-span overlays or qualified capacity-growth relocation; '
    'raw streaming candidates use qualified relocation. Source, allocation, composition and actor-pool '
    'checks still apply. Use Review Build to assess the current complete authored project; '
    'serialization support does not establish runtime spawning, scheduling or gameplay.')


def _public(value):
    """Audit metadata only: keep semantic evidence, never payloads/private paths."""
    if isinstance(value, dict):
        return {key: _public(item) for key, item in value.items()
                if not key.startswith('_') and not isinstance(item, bytes) and
                not any(word in key.lower() for word in ('path', 'directory'))}
    if isinstance(value, (list, tuple)):
        return [_public(item) for item in value if not isinstance(item, bytes)]
    return deepcopy(value)


def prepare_npc_overlays(project, scene_id, archive, *,managed_model_ids=()):
    """Caller delegates only model IDs carried by its qualified growth requests."""
    if (project.mode != 'edit' or not project.disc_path or not isinstance(scene_id, str) or
            not re.fullmatch(r'scene://[A-Za-z0-9_-]{1,128}', scene_id) or scene_id not in project.imports):
        raise ProjectError('NPC Build requires an imported source scene and disc in Edit mode')
    before = authored_state_key(project)
    if (not isinstance(managed_model_ids,(list,tuple,set)) or len(managed_model_ids)>4096 or
            any(not isinstance(identifier,str) or identifier not in project.model_overrides for identifier in managed_model_ids) or
            len(set(managed_model_ids))!=len(managed_model_ids)):
        raise ProjectError('NPC model delivery handoff requires bounded unique authored model identities')
    delegated=set(managed_model_ids)
    document = project.imports[scene_id]
    view = copy(project)
    view.overrides = {owner: deepcopy(value) for owner, value in project.overrides.items()
                      if owner == scene_id or isinstance(owner, str) and owner.startswith(scene_id + '/')}
    view.actor_drafts = {owner: deepcopy(value) for owner, value in project.actor_drafts.items()
                         if value.get('scene_id') == scene_id}
    view.model_overrides = {owner: deepcopy(value) for owner, value in project.model_overrides.items()
                            if value.get('source_scene_id') == scene_id and owner not in delegated}
    view.texture_overrides = {owner: deepcopy(value) for owner, value in project.texture_overrides.items()
                              if value.get('source_scene_id') == scene_id}
    if not 1 <= len(view.actor_drafts) <= 128:
        raise ProjectError('NPC Build requires 1..128 saved drafts in the source scene')
    prot, audit = _prepare_draft_scene(view, sorted(view.actor_drafts)[0], defer_rebuild=True, scene_id=scene_id,animation_growth_managed=True)
    audit['managed_model_ids']=sorted(identifier for identifier in delegated if project.model_overrides[identifier]['source_scene_id']==scene_id)
    if not isinstance(prot, bytes) or not 0 < len(prot) <= MAX_PROT_BYTES or len(prot) != archive.node.size:
        raise ProjectError('NPC Build source PROT exceeds bounds or differs from the archive')
    current_prot = archive.image.read_user(archive.node.extent_lba, 0, archive.node.size, archive.node.size)
    if prot != current_prot or sha256(prot).hexdigest() != audit.get('source_prot_sha256'):
        raise ProjectError('NPC Build candidate source archive changed')
    if {doc['source']['disc_identity'] for doc in project.imports.values()} != {'sha256:' + audit['source_disc_sha256']}:
        raise ProjectError('NPC Build candidate disc differs from imported source identity')
    request = audit.get('_rebuild_request')
    if isinstance(request,dict) and 'chunk_header_offset' in request:
        return _prepare_streaming_candidate(project,view,scene_id,archive,prot,audit,request,before)
    if (not isinstance(request, dict) or set(request) != {'entry_index', 'table_offset', 'source_man_sha256', 'candidate'} or
            type(request['entry_index']) is not int or type(request['table_offset']) is not int):
        raise ProjectError('NPC Build requires one qualified compressed MAN carrier')
    candidate = request['candidate']
    if not isinstance(candidate, bytes) or not 0 < len(candidate) <= MAX_CANDIDATE_BYTES:
        raise ProjectError('NPC Build candidate MAN exceeds the decoded source budget')
    entry = archive.entry(request['entry_index'])
    span = locate_physical_span(archive, entry.start_lba * archive.SECTOR)
    if span['entry_index'] != request['entry_index'] or span['offset_within_span'] != 0:
        raise ProjectError('NPC Build compressed MAN has no unique physical owner')
    container = prot[span['byte_offset']:span['byte_offset'] + span['byte_length']]
    table_offset = request['table_offset']
    table = parse_scene_table(container, request['entry_index'], table_offset)
    descriptors = [] if table is None else [row for row in table.descriptors if row.type_byte == 3 and row.size]
    if len(descriptors) != 1:
        raise ProjectError('NPC Build requires exactly one source MAN descriptor')
    descriptor = descriptors[0]
    table_end = table_offset + 8 + 8 * len(table.descriptors)
    if any(not table_end <= table_offset + row.data_offset <= len(container) for row in table.descriptors):
        raise ProjectError('NPC Build descriptor payload exceeds its source carrier')
    if sum(row.data_offset == descriptor.data_offset for row in table.descriptors) != 1:
        raise ProjectError('NPC Build MAN source payload is aliased')
    start = table_offset + descriptor.data_offset
    end = min([table_offset + row.data_offset for row in table.descriptors if row.data_offset > descriptor.data_offset] + [len(container)])
    original, consumed = decompress_lzs(container[start:end], descriptor.size)
    if sha256(original).hexdigest() != request['source_man_sha256']:
        raise ProjectError('NPC Build decoded MAN source changed')
    audit['actor_pool_evidence'] = actor_pool_assessment(archive, candidate)
    encoded = compress_lzs(candidate)
    greedy_size = len(encoded)
    strategy = 'greedy_lzs'
    if len(encoded) > consumed and len(candidate) <= MAX_OPTIMAL_BYTES:
        encoded = compress_lzs_optimal(candidate)
        strategy = 'bounded_optimal_lzs'
    if len(encoded) > consumed:
        return _prepare_compressed_candidate(project,view,scene_id,audit,request,before,span,container,descriptor.index,consumed)
    if decompress_lzs(encoded, len(candidate)) != (candidate, len(encoded)):
        raise ProjectError('NPC Build candidate compression failed independent exact readback')
    original_span = container[start:start + consumed]
    replacement = encoded + original_span[len(encoded):]
    word_offset = table_offset + 8 + descriptor.index * 8
    size_word = struct.pack('<I', (3 << 24) | len(candidate))
    rebuilt = bytearray(container)
    rebuilt[start:start + consumed] = replacement
    rebuilt[word_offset:word_offset + 4] = size_word
    reopened = parse_scene_table(bytes(rebuilt), request['entry_index'], table_offset)
    if (reopened is None or len(rebuilt) != len(container) or
            [(row.type_byte, row.data_offset, row.size) for row in reopened.descriptors] !=
            [(row.type_byte, row.data_offset, len(candidate) if row.index == descriptor.index else row.size) for row in table.descriptors] or
            decompress_lzs(rebuilt[start:end], len(candidate))[0] != candidate):
        raise ProjectError('NPC Build fixed carrier failed descriptor/MAN readback')
    allowed = set(range(start, start + consumed)) | set(range(word_offset, word_offset + 4))
    if any(a != b and at not in allowed for at, (a, b) in enumerate(zip(container, rebuilt))):
        raise ProjectError('NPC Build altered bytes outside its original owned stream and size word')
    for row in table.descriptors:
        if row.index == descriptor.index:
            continue
        at = table_offset + row.data_offset
        stop = min([table_offset + other.data_offset for other in table.descriptors if other.data_offset > row.data_offset] + [len(container)])
        if at < start + consumed and start < stop or at < word_offset + 4 and word_offset < stop or container[at:stop] != rebuilt[at:stop]:
            raise ProjectError('NPC Build MAN writes overlap another source descriptor payload')
    # Equal-span model/animation/MAP/texture patches are emitted by the parent
    # normal Build. Qualify disjoint ownership here without emitting duplicates.
    for patch in audit.get('_asset_patches', []):
        if (type(patch.get('offset')) is not int or not isinstance(patch.get('payload'), bytes) or
                not 0 <= patch['offset'] <= len(prot) or patch['offset'] + len(patch['payload']) > len(prot) or
                sha256(prot[patch['offset']:patch['offset'] + len(patch['payload'])]).hexdigest() != patch.get('expected_sha256')):
            raise ProjectError('NPC Build composed asset span is invalid')
        at, stop = patch['offset'], patch['offset'] + len(patch['payload'])
        for local, payload in ((start, replacement), (word_offset, size_word)):
            owned = span['byte_offset'] + local
            if at < owned + len(payload) and owned < stop:
                raise ProjectError('NPC Build source MAN span overlaps composed asset output')
    scene = document['scene']['name']
    base = archive.node.extent_lba * 2048 + span['byte_offset']
    overlays = []
    for local, payload, old, suffix in ((start, replacement, original_span, 'man.lzs'),
                                       (word_offset, size_word, container[word_offset:word_offset + 4], 'man-size.bin')):
        overlays.append(dict(scene=scene, offset=base + local, size=len(payload),
            expected_sha256=sha256(old).hexdigest(), sha256=sha256(payload).hexdigest(), payload=payload,
            file=f'assets/{scene}-npc-{suffix}', decoded_before_sha256=sha256(original).hexdigest(),
            decoded_after_sha256=sha256(candidate).hexdigest(), source_kind='source-man-donor-append-candidate'))
    edits = []
    for row in audit['actor']['drafts']:
        draft_id = row['draft_id']
        edits.append(dict(scene=scene, semantic_id=draft_id, field='npc.appended_record', before_value=None,
            after_value=row['record_index'], scope='source-man-donor-append-candidate',
            donor_entity_id=view.actor_drafts[draft_id]['donor_entity_id'], source_counts=deepcopy(row.get('partition_counts_before')),
            candidate_counts=deepcopy(row.get('partition_counts_after')), changes=_public(row)))
    for family, changes in audit.items():
        if family.endswith('_changes') and changes:
            count = len(changes) if isinstance(changes, (list, dict)) else 1
            edits.append(dict(scene=scene, semantic_id=scene_id, field='npc.composed.' + family,
                before_value=None, after_value=count, scope='source-man-draft-composed-overrides', composition_changes=_public(changes)))
    metadata = dict(schema_version='legaia.npc-fixed-span-build.v1', scene_id=scene_id, authored_state_key=before, draft_audit=_public(audit),
        physical_owner=deepcopy(span), descriptor_index=descriptor.index,
        compression=dict(strategy=strategy, greedy_encoded_size=greedy_size, original_encoded_size=consumed,
                         new_encoded_size=len(encoded), decoded_size_before=len(original), decoded_size_after=len(candidate)),
        validation=dict(exact_man_readback=True, unchanged_descriptor_offsets=True, unchanged_other_payloads=True,
                        unchanged_physical_carrier_size=True, no_disc_relocation=True),
        gameplay_verified=False, allocation_verified=False, spawn_scheduling_verified=False,
        opaque_script_paths_verified=False)
    if project.mode != 'edit' or authored_state_key(project) != before:
        raise ProjectError('Project build inputs changed during fixed-span NPC preparation')
    return overlays, edits, metadata


def _prepare_streaming_candidate(project,view,scene_id,archive,prot,audit,request,before):
    from importer.streaming_man import grow_streaming_man
    if (set(request)!={'entry_index','chunk_header_offset','source_man_sha256','candidate'} or
            type(request['entry_index']) is not int or type(request['chunk_header_offset']) is not int or
            not isinstance(request['candidate'],bytes) or not 0<len(request['candidate'])<=MAX_CANDIDATE_BYTES):
        raise ProjectError('Streaming NPC Build requires a bounded qualified MAN growth request')
    entry=archive.entry(request['entry_index']);span=locate_physical_span(archive,entry.start_lba*2048)
    if span['entry_index']!=request['entry_index'] or span['offset_within_span']!=0:
        raise ProjectError('Streaming NPC Build has no unique physical owner')
    carrier=prot[span['byte_offset']:span['byte_offset']+span['byte_length']]
    _,native=grow_streaming_man(carrier,sha256(carrier).hexdigest(),request['chunk_header_offset'],request['source_man_sha256'],request['candidate'])
    audit['actor_pool_evidence']=actor_pool_assessment(archive,request['candidate'])
    return _relocation_metadata(project,view,scene_id,audit,before,span,native,request,'streaming')


def _prepare_compressed_candidate(project,view,scene_id,audit,request,before,span,container,descriptor_index,consumed):
    from importer.core import parse_man
    from importer.man_container import encode_man_candidate
    parse_man(request['candidate'])
    _,native=encode_man_candidate(container,sha256(container).hexdigest(),request['table_offset'],
        request['source_man_sha256'],request['candidate'],allow_growth=True)
    native['original_consumed_size']=consumed
    native['original_consumed_span_exceeded']=True
    native['strategy']='relocated_greedy_lzs'
    return _relocation_metadata(project,view,scene_id,audit,before,span,native,
        dict(request,descriptor_index=descriptor_index),'compressed')


def _relocation_metadata(project,view,scene_id,audit,before,span,native,request,carrier_kind):
    scene=view.imports[scene_id]['scene']['name'];edits=[]
    for row in audit['actor_changes' if carrier_kind=='streaming' else 'actor']['drafts']:
        identifier=row['draft_id']
        edits.append(dict(scene=scene,semantic_id=identifier,field='npc.appended_record',before_value=None,
            after_value=row['record_index'],scope='source-man-donor-append-candidate',
            donor_entity_id=view.actor_drafts[identifier]['donor_entity_id'],changes=_public(row)))
    for family,changes in audit.items():
        if family.endswith('_changes') and changes:
            edits.append(dict(scene=scene,semantic_id=scene_id,field='npc.composed.'+family,before_value=None,
                after_value=len(changes) if isinstance(changes,(list,dict)) else 1,
                scope='source-man-draft-composed-overrides',composition_changes=_public(changes)))
    metadata=dict(schema_version=f'legaia.npc-{carrier_kind}-growth-build.v1',scene_id=scene_id,
        authored_state_key=before,draft_audit=_public(audit),physical_owner=deepcopy(span),
        native_growth=_public(native),validation=dict(exact_man_readback=True,qualified_carrier_kind=carrier_kind,
            **({'terminated_chunk_chain':True} if carrier_kind=='streaming' else {'lz_decode_round_trip':True})),
        gameplay_verified=False,allocation_verified=False,spawn_scheduling_verified=False,opaque_script_paths_verified=False,
        _relocation_request=dict(kind=carrier_kind+'-man',**request))
    if project.mode!='edit' or authored_state_key(project)!=before:
        raise ProjectError('Project build inputs changed during NPC relocation preparation')
    return [],edits,metadata
