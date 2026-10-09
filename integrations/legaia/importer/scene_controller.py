"""Bound the Retail scene-entry controller without treating it as a placed actor."""
from hashlib import sha256
from .core import ImportError, parse_man
from .man_source import read_man_source
from .pipeline import _disc_context, _bounded_scene_range, REFERENCE_COMMIT
from .script_inspection import inspect_record, MAX_RECORD_BYTES


def controller_record(man, scene):
    parsed = parse_man(man, scene)
    if parsed.partition_counts[1] < 1:
        raise ImportError('Scene has no partition-1 controller')
    total = sum(parsed.partition_counts)
    base = 43 + total * 3
    starts = [base + int.from_bytes(man[43+i*3:46+i*3], 'little') for i in range(total)]
    section = base + int.from_bytes(man[40:43], 'little')
    if any(not base <= start < section <= len(man) for start in starts):
        raise ImportError('Scene controller record table exceeds the record region')
    start = starts[parsed.partition_counts[0]]
    if starts.count(start) != 1:
        raise ImportError('Scene controller has aliased record ownership')
    end = min([p for p in starts if p > start] + [section])
    record = man[start:end]
    entry = 1 + record[0] * 2 + 4
    if not 0 < len(record) <= MAX_RECORD_BYTES or entry >= len(record):
        raise ImportError('Scene controller prefix or script entry exceeds its record')
    return start, record, entry


def inspect_scene_controller(disc, scene):
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        carrier = read_man_source(archive, start, end, scene)
        offset, record, entry = controller_record(carrier.payload, scene)
        identity = f'script://{scene}/controllers/man-p1/0000'
        return dict(schema_version='legaia.scene-controller-inspection.v1', scene_id=f'scene://{scene}',
                    semantic_id=identity, read_only=True, representation='retail',
                    reference_commit=REFERENCE_COMMIT, runtime_execution='not_asserted',
                    source_record=dict(disc_identity='sha256:'+digest, iso_file='PROT.DAT',
                        prot_entry=carrier.entry_index, record_kind='man_partition_1_scene_controller',
                        record_index=0, byte_coordinate_space='decoded_man_payload',
                        byte_offset=offset, byte_length=len(record), containing_decoded_size=len(carrier.payload),
                        sha256=sha256(record).hexdigest()),
                    record=dict(script_offset=entry, local_count=record[0], raw_hex=record.hex()),
                    man_source=carrier.provenance(),
                    limitations=['Retail controller only; no authored controller or runtime PC is substituted.',
                        'Controller header values have no inferred actor placement semantics.',
                        'Encoded instructions do not prove scheduling, branch activation or gameplay behavior.'],
                    **inspect_record(record, entry, semantic_id=identity, base_offset=offset))
