"""Rewrite reached opcode44 operands; never claim opaque script coverage."""
from hashlib import sha256
from .core import ImportError
from .script_inspection import inspect_record
from .man_layout import read_man_layout
from .trigger_scripts import _p2_entry


def inspect_spawn_reindex(source: bytes, rebuilt: bytes) -> dict:
    """Inventory reached P1/P2 rewrites without mutating either MAN buffer."""
    mapping = spawn_index_map(source, rebuilt)
    reports = []
    for span in read_man_layout(source)['records']:
        if span['partition'] == 0:
            continue
        record = source[span['byte_offset']:span['byte_offset']+span['byte_length']]
        report = dict(partition=span['partition'], record_index=span['record_index'],
                      byte_offset=span['byte_offset'])
        try:
            entry = 1+record[0]*2+4 if span['partition'] == 1 else _p2_entry(record)[0]
            _, audit = reindex_spawn_operands(record, sha256(record).hexdigest(), entry, mapping)
            report.update(coverage=audit['coverage'], changes=audit['changes'],
                          stops=audit['stops'], opaque_byte_count=audit['opaque_byte_count'],
                          extended_context_references=audit['extended_context_references'])
        except ImportError as exc:
            report.update(coverage='rejected', reason=str(exc), changes=[])
        reports.append(report)
    return dict(source_sha256=sha256(source).hexdigest(),
                candidate_sha256=sha256(rebuilt).hexdigest(), records=reports,
                excluded_partitions=[0], complete_relocation_verified=False)


def spawn_index_map(original: bytes, rebuilt: bytes) -> dict[int, int]:
    """Map partition2 identities only when their complete bytes are preserved."""
    before, after = read_man_layout(original), read_man_layout(rebuilt)
    if before['partition_counts'][2] != after['partition_counts'][2]:
        raise ImportError('Spawn mapping requires unchanged partition2 record count')
    old_first = sum(before['partition_counts'][:2])
    new_first = sum(after['partition_counts'][:2])
    old_records = [r for r in before['records'] if r['partition'] == 2]
    new_records = [r for r in after['records'] if r['partition'] == 2]
    mapping = {}
    for old, new in zip(old_records, new_records):
        old_index, new_index = old_first+old['record_index'], new_first+new['record_index']
        if old_index > 255 or new_index > 255:
            raise ImportError('Spawn mapping exceeds encoded byte index capacity')
        if original[old['byte_offset']:old['byte_offset']+old['byte_length']] != rebuilt[new['byte_offset']:new['byte_offset']+new['byte_length']]:
            raise ImportError('Spawn mapping target record bytes changed')
        mapping[old_index] = new_index
    return mapping


def reindex_spawn_operands(record: bytes, expected_sha256: str, script_offset: int,
                           index_map: dict[int, int]):
    """Return a candidate record and exact metadata-only changes.

    Mapping keys and values are encoded global record indices. The caller owns
    validation against old/new MAN layouts. This does not rewrite other encoded
    reference families or establish native-spawn safety.
    """
    if not isinstance(record, bytes) or sha256(record).hexdigest() != expected_sha256:
        raise ImportError('Script reindex source hash mismatch')
    if (not isinstance(index_map, dict) or len(index_map) > 256 or
            any(type(k) is not int or type(v) is not int or
                not 0 <= k <= 255 or not 0 <= v <= 255
                for k, v in index_map.items())):
        raise ImportError('Script index mapping requires byte integer keys and values')
    graph = inspect_record(record, script_offset)
    result, changes = bytearray(record), []
    for row in graph['instructions']:
        if row['mnemonic'] != 'SPAWN_RECORD':
            continue
        old = row['operands']['global_record_index']
        if old not in index_map:
            raise ImportError('Decoded spawn target has no validated index mapping')
        new = index_map[old]
        if old == new:
            continue
        offset = row['pc'] + (2 if row['target_context'] is not None else 1)
        result[offset] = new
        changes.append(dict(pc=row['pc'], byte_offset=offset, before=old, after=new))
    rebuilt = bytes(result)
    check = inspect_record(rebuilt, script_offset)
    # Operand values may change, but the instruction boundaries/control flow may not.
    shape = lambda g: [(r['pc'], r['length'], r['mnemonic'], r['successors'])
                       for r in g['instructions']]
    if shape(graph) != shape(check) or graph['opaque_regions'] != check['opaque_regions']:
        raise ImportError('Spawn reindex changed script boundaries or opaque bytes')
    return rebuilt, dict(source_sha256=expected_sha256,
                         result_sha256=sha256(rebuilt).hexdigest(), changes=changes,
                         stops=[dict(pc=stop['pc'], reason=stop['reason']) for stop in graph['stops']],
                         opaque_byte_count=sum(region['length'] for region in graph['opaque_regions']),
                         extended_context_references=[dict(pc=row['pc'], target=row['target_context'])
                                                      for row in graph['instructions']
                                                      if row['target_context'] is not None],
                         coverage=graph['status'], complete_relocation_verified=False)
