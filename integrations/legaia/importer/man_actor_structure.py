"""Structural MAN actor append prototype, not a verified script relocation.

Existing partition indices and record bytes are retained. Adding a table entry
shifts payload addresses by three bytes; absolute script references are not
rewritten here, so callers must not package this as gameplay-ready content.
"""
from hashlib import sha256
import struct
from .core import ImportError, parse_man
from .man_layout import read_man_layout, resolve_spawn_record
from .script_inspection import inspect_record


def actor_context_reference_status(partition0_count: int, record_index: int) -> dict:
    """Describe encoded target limits, without claiming allocation success."""
    if any(type(v) is not int or not 0 <= v <= 32767 for v in (partition0_count, record_index)):
        raise ImportError('Actor context indices must be nonnegative signed-header integers')
    context_id = partition0_count+record_index
    status = ('outside_byte_target_range' if context_id > 255 else
              'reserved_reference_target' if context_id in (0xF8, 0xFB) else
              'byte_target_representable')
    return dict(script_context_id=context_id, cross_context_target_status=status,
                reserved_targets_known=[0xF8, 0xFB], allocation_verified=False)


def append_actor_candidate(source: bytes, expected_sha256: str, donor_record_index: int,
                           *, position: dict | None = None):
    """Append donor and repair reached opcode44 references; not build-ready."""
    from .script_reindex import inspect_spawn_reindex, spawn_index_map, reindex_spawn_operands
    structural, audit = append_actor_donor(source, expected_sha256, donor_record_index)
    inventory = inspect_spawn_reindex(source, structural)
    if any(row['coverage'] == 'rejected' for row in inventory['records']):
        raise ImportError('Actor candidate has rejected script reindex records')
    layout = read_man_layout(structural)
    lookup = {(r['partition'], r['record_index']): r for r in layout['records']}
    output, changes = bytearray(structural), []
    for row in inventory['records']:
        span = lookup[(row['partition'], row['record_index'])]
        for change in row['changes']:
            offset = span['byte_offset']+change['byte_offset']
            if output[offset] != change['before']:
                raise ImportError('Actor candidate operand preimage mismatch')
            output[offset] = change['after']
            changes.append(dict(partition=row['partition'], record_index=row['record_index'],
                                byte_offset=offset, before=change['before'], after=change['after']))
    # A cloned donor may itself contain global spawn references.
    span = lookup[(1, audit['record_index'])]
    record = structural[span['byte_offset']:span['byte_offset']+span['byte_length']]
    replacement, donor_changes = reindex_spawn_operands(
        record, sha256(record).hexdigest(), 1+record[0]*2+4,
        spawn_index_map(source, structural))
    output[span['byte_offset']:span['byte_offset']+span['byte_length']] = replacement
    for change in donor_changes['changes']:
        changes.append(dict(partition=1, record_index=audit['record_index'],
                            byte_offset=span['byte_offset']+change['byte_offset'],
                            before=change['before'], after=change['after']))
    result = bytes(output)
    if len(result) != len(structural) or read_man_layout(result) != layout:
        raise ImportError('Actor candidate rewrite changed structural layout')
    placement_changes = []
    if position is not None:
        from .serialization import patch_man_positions
        result, placement_changes = patch_man_positions(
            result, 'authored-candidate', {audit['record_index']: position})
        if read_man_layout(result) != layout:
            raise ImportError('Candidate placement changed structural layout')
    audit.update(structural_result_sha256=audit['result_sha256'],
                 result_sha256=sha256(result).hexdigest(),
                 existing_record_bytes_preserved=not any(r['changes'] for r in inventory['records']),
                 reached_spawn_changes=changes, script_coverage=inventory,
                 authored_placement_changes=placement_changes,
                 build_ready=False)
    return result, audit


def append_actor_donor(source: bytes, expected_sha256: str, donor_record_index: int):
    """Clone an evidenced partition1 actor into a structural candidate.

    This source-bound entry point deliberately accepts no client-supplied script
    bytes. It still does not establish spawn scheduling or script relocation.
    """
    if not isinstance(source, bytes) or sha256(source).hexdigest() != expected_sha256:
        raise ImportError('Actor donor source hash mismatch')
    if type(donor_record_index) is not int:
        raise ImportError('Actor donor index must be an integer')
    layout = read_man_layout(source)
    donor = next((actor for actor in parse_man(source).actors
                  if actor.record_index == donor_record_index), None)
    if donor is None:
        raise ImportError('Actor donor must identify an existing partition1 actor')
    aliases = [record for record in layout['records']
               if record['byte_offset'] == donor.byte_offset]
    if len(aliases) != 1:
        raise ImportError('Actor donor record is aliased across partition entries')
    result, audit = append_actor_structure(
        source, expected_sha256,
        source[donor.byte_offset:donor.byte_offset+donor.byte_length])
    audit['donor'] = dict(partition=1, record_index=donor.record_index,
                         byte_offset=donor.byte_offset, byte_length=donor.byte_length,
                         model_index=donor.model_index, animation_id=donor.animation_id,
                         world_x=donor.world_x, world_z=donor.world_z)
    audit['spawn_scheduling_verified'] = False
    audit['context_reference'] = actor_context_reference_status(
        layout['partition_counts'][0], audit['record_index'])
    audit['reference_spawn_rule'] = dict(
        evidence='pinned engine-core/src/field_channels.rs::spawn_channels',
        setup_function='FUN_8003AEB0', allocator_function='FUN_8003A1E4',
        script_context_id=layout['partition_counts'][0]+audit['record_index'],
        entry_pc=1+donor.local_count*2+4,
        status='reference_evidence_not_runtime_verified')
    audit['global_record_index_rewrite_required'] = True
    audit['shifted_global_index_range'] = dict(
        partition=2, first_before=sum(layout['partition_counts'][:2]),
        count=layout['partition_counts'][2], delta=1)
    record = source[donor.byte_offset:donor.byte_offset+donor.byte_length]
    graph = inspect_record(record, 1+donor.local_count*2+4)
    # Metadata only: never embed proprietary instructions/dialogue in an audit.
    audit['donor_script_inspection'] = dict(
        status=graph['status'],
        instruction_count=len(graph['instructions']),
        dialogue_count=len(graph['dialogues']),
        opaque_byte_count=sum(region['length'] for region in graph['opaque_regions']),
        stop_count=len(graph['stops']),
        camera_apply_jump_count=sum(row['mnemonic'] == 'CAMERA_APPLY_JUMP'
                                    for row in graph['instructions']),
        explicit_spawn_count=sum(row['mnemonic'] == 'SPAWN_RECORD'
                                 for row in graph['instructions']),
        spawn_references=[dict(pc=row['pc'],
                               **resolve_spawn_record(layout, row['operands']['global_record_index']))
                          for row in graph['instructions']
                          if row['mnemonic'] == 'SPAWN_RECORD'],
        interpretation='Supported paths only; not a relocation or spawn-safety proof')
    return result, audit


def append_actor_structure(source: bytes, expected_sha256: str, actor_record: bytes):
    if not isinstance(source, bytes) or sha256(source).hexdigest() != expected_sha256:
        raise ImportError('Actor append source hash mismatch')
    layout = read_man_layout(source)
    counts = layout['partition_counts']
    if not 1 <= counts[1] < 255:
        raise ImportError('Actor append requires an existing bounded partition1')
    if not isinstance(actor_record, bytes) or not 6 <= len(actor_record) <= 65536 or 1+actor_record[0]*2+4 >= len(actor_record):
        raise ImportError('New actor record requires a bounded placement header and script bytes')
    section = layout['sections'][0]['byte_offset']
    if any(r['byte_offset']+r['byte_length'] > section for r in layout['records']):
        raise ImportError('Actor append requires all records before section data')
    base = layout['data_region_offset']
    insertion = 0x2b + (counts[0]+counts[1])*3
    section_relative = section-base+len(actor_record)
    if section_relative > 0xffffff:
        raise ImportError('MAN section offset exceeds u24 capacity')
    header = bytearray(source[:0x2b])
    struct.pack_into('<h',header,0x24,counts[1]+1)
    header[0x28:0x2b] = section_relative.to_bytes(3,'little')
    result = bytes(header) + source[0x2b:insertion] + (section-base).to_bytes(3,'little') + source[insertion:base] + source[base:section] + actor_record + source[section:]
    rebuilt = read_man_layout(result)
    if len(result) != len(source)+3+len(actor_record):
        raise ImportError('Structural append size did not roundtrip')
    lookup = {(r['partition'],r['record_index']):r for r in rebuilt['records']}
    for old in layout['records']:
        new = lookup[(old['partition'],old['record_index'])]
        if source[old['byte_offset']:old['byte_offset']+old['byte_length']] != result[new['byte_offset']:new['byte_offset']+new['byte_length']]:
            raise ImportError('Structural append altered an existing record')
    if source[section:] != result[rebuilt['sections'][0]['byte_offset']:]:
        raise ImportError('Structural append altered trailing sections')
    actor = next(a for a in parse_man(result).actors if a.record_index == counts[1])
    if actor.byte_length != len(actor_record):
        raise ImportError('New actor record bounds did not roundtrip')
    return result, dict(record_index=counts[1], byte_offset=actor.byte_offset,
                        byte_length=actor.byte_length, payload_address_delta=3,
                        source_sha256=expected_sha256,
                        result_sha256=sha256(result).hexdigest(),
                        actor_record_sha256=sha256(actor_record).hexdigest(),
                        source_byte_length=len(source), result_byte_length=len(result),
                        partition_counts_before=counts,
                        partition_counts_after=rebuilt['partition_counts'],
                        existing_record_bytes_preserved=True, script_relocation_verified=False,
                        external_decoded_size_update_required=True)
