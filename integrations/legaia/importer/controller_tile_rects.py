"""Source-qualified controller tile request bytes; no runtime tile editing."""
from copy import deepcopy
from hashlib import sha256
import re
from .core import ImportError
from .controller_system_flags import ControllerRecordSource, load_controller_record_source
from .script_inspection import inspect_record
from .man_layout import read_man_layout

FIELDS = ('column_start', 'row_start', 'column_end', 'row_end', 'value')
LIMITATIONS = [
    'Only reached FIELD_TILE_RECT_REQUEST operands in fully decoded controller paths are candidates.',
    'The five encoded byte values do not establish tile capacity, runtime tile identity or gameplay effects.',
    'Opcode, dispatch context, instruction boundaries, successors, record lengths and MAN pointers remain unchanged.',
    'This is native serialization groundwork; project/editor/Build integration is not yet provided.',
]


def validate_tile_rect_values(values):
    if (not isinstance(values, dict) or set(values) != set(FIELDS) or
            any(type(values[key]) is not int or not 0 <= values[key] <= 255 for key in FIELDS)):
        raise ImportError('Tile request requires exactly five integer byte operands0..255')
    return bytes(values[key] for key in FIELDS)


def _target(record, entry, pc, report=None):
    if type(pc) is not int or pc < 0:
        raise ImportError('Tile request PC must be a nonnegative record offset')
    report = inspect_record(record, entry) if report is None else report
    if report['stops']:
        raise ImportError('Tile request authoring requires no unknown/conflicting source-path stops')
    node = next((row for row in report['instructions'] if row['pc'] == pc), None)
    if node is None or node['mnemonic'] != 'FIELD_TILE_RECT_REQUEST':
        raise ImportError('Tile request PC must identify a reached source instruction')
    relative = pc + (2 if node['target_context'] is not None else 1) + 1
    return node, relative, report


class ControllerTileRectAuthoringContext:
    def __init__(self, source):
        if not isinstance(source, ControllerRecordSource):
            raise ImportError('Tile request authoring requires a dedicated controller source')
        self._source, self._man = source, source._man

    def provenance(self):
        return dict(self._source.provenance(), limitations=list(LIMITATIONS))

    def options(self, owner):
        offset, record, entry = self._source.verified_record(owner)
        report = inspect_record(record, entry)
        targets = []
        if not report['stops']:
            for node in report['instructions']:
                if node['mnemonic'] != 'FIELD_TILE_RECT_REQUEST':
                    continue
                _, relative, _ = _target(record, entry, node['pc'], report)
                targets.append(dict(semantic_id=owner.replace('scene://', 'script://', 1)+f"/tile-rect/{node['pc']:04x}",
                    owner_id=owner, pc=node['pc'], mnemonic=node['mnemonic'], target_context=node['target_context'],
                    decoded_byte_offset=offset+relative, values={key:node['operands'][key] for key in FIELDS},
                    source_record_sha256=sha256(record).hexdigest()))
        return dict(supported=bool(targets), targets=targets, source=self.provenance(),
                    inspection=deepcopy(report), limitations=list(LIMITATIONS),
                    reason='Tile request authoring requires no decoder stops' if report['stops'] else None)

    def patch(self, edits, *, original=None):
        if original is not None and original != self._man:
            raise ImportError('Tile request MAN differs from verified Retail source')
        if not isinstance(edits, dict) or len(edits)>1024:
            raise ImportError('Tile request edit set exceeds bounds')
        result, audit, occupied = bytearray(self._man), [], set()
        records = {}
        for identity, values in edits.items():
            match = re.fullmatch(r'script://([A-Za-z0-9_-]+/controllers/man-p1/0000)/tile-rect/([a-f0-9]{4})', identity) if isinstance(identity, str) else None
            if match is None:
                raise ImportError('Tile request identity requires its controller owner and source PC')
            after = validate_tile_rect_values(values)
            owner = 'scene://'+match[1]
            offset, record, entry = self._source.verified_record(owner)
            node, relative, report = _target(record, entry, int(match[2],16))
            at = offset+relative; span = set(range(at,at+5))
            if occupied & span:
                raise ImportError('Tile request edits overlap another source span')
            occupied.update(span); records[owner] = (offset,record,entry,report)
            before = record[relative:relative+5]
            if before == after:
                continue
            result[at:at+5] = after
            audit.append(dict(tile_rect_id=identity,owner_id=owner,pc=node['pc'],mnemonic=node['mnemonic'],
                target_context=node['target_context'],record_relative_byte_offset=relative,decoded_byte_offset=at,
                byte_length=5,before_hex=before.hex(),after_hex=after.hex(),before_values=dict(zip(FIELDS,before)),
                after_values=deepcopy(values),source_record_sha256=sha256(record).hexdigest(),
                source_decoded_man_sha256=sha256(self._man).hexdigest()))
        result = bytes(result)
        shape = lambda r:[(n['pc'],n['mnemonic'],n['length'],n['target_context'],n['successors']) for n in r['instructions']]
        for offset,record,entry,report in records.values():
            check = inspect_record(result[offset:offset+len(record)],entry)
            if check['stops'] or shape(check)!=shape(report) or check['dialogues']!=report['dialogues']:
                raise ImportError('Tile request edit changed source layout or continuation')
        if read_man_layout(result)!=read_man_layout(self._man):
            raise ImportError('Tile request edit changed MAN layout')
        return result,deepcopy(sorted(audit,key=lambda row:row['decoded_byte_offset']))

    def patch_appended(self, candidate, edits):
        # This initial adapter accepts relocation with an exact controller
        # record. Spawn-reindexed controller records need a separate proof.
        _, changes = self.patch(edits)
        offset,record,entry = self._source.verified_record(self._source.owner_id)
        layout = read_man_layout(candidate)
        targets = [r for r in layout['records'] if r['partition']==1 and r['record_index']==0]
        if len(targets)!=1 or targets[0]['byte_length']!=len(record):
            raise ImportError('Relocated tile request controller extent changed')
        start = targets[0]['byte_offset']
        if sum(r['byte_offset']==start for r in layout['records'])!=1 or candidate[start:start+len(record)]!=record:
            raise ImportError('Relocated tile request controller preimage changed')
        result, audit = bytearray(candidate), []
        for change in changes:
            at = start+change['record_relative_byte_offset']
            result[at:at+5] = bytes.fromhex(change['after_hex'])
            audit.append(dict(change,source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at,
                              appended_man_sha256=sha256(candidate).hexdigest()))
        result = bytes(result)
        if read_man_layout(result)!=layout:
            raise ImportError('Tile request edit changed relocated MAN layout')
        return result,audit


def load_controller_tile_rect_context(disc, scene):
    return ControllerTileRectAuthoringContext(load_controller_record_source(disc,scene))
