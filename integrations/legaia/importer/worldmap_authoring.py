"""Source-bound writes to existing world-map menu records in SCUS_942.54.

Evidence: d6e64c68ede25813d35db20980da82a1a025549b,
crates/asset/src/worldmap_menu.rs: PLACEMENT_TABLE_ADDR, PlacementRecord and
parse_scus. Each <BBHBB row is name index, encoded discovery flag, numeric
destination, menu X and menu Y. Discovery indices add 32 to the stored byte.
Only the original six-byte rows preceding the first FF terminator are
editable. Names, terminator, executable code and every other byte are retained.
X/Y use a reference menu-pixel interpretation; their executing consumers remain
unverified. These encoded fields do not establish world geometry, activation
or a traversable destination.
"""
from copy import deepcopy
from hashlib import sha256
import re
import struct

from .core import ImportError
from .pipeline import _disc_context
from .worldmap_menu import decode_worldmap_menu, resolve_menu_destinations, worldmap_field_evidence

MAX_ENTRIES = 64
VALUE_FIELDS = ('name_index', 'discovery_flag_index', 'destination_scene_id', 'menu_position')
LIMITATIONS = [
    'Only existing source menu records are editable; row count, ordering, terminator and landmark names are retained.',
    'X/Y are encoded bytes with a reference menu-pixel interpretation; executing draw consumers, field coordinates and 3D world positions are unverified.',
    'Discovery indices encode a byte plus32 passed to the qualified retail system bitmap reader; current flags and activation are not evaluated.',
    'Destination labels are exact CDNAME definitions, not evidence of a supported scene import, traversable edge or gameplay reachability.',
    'Duplicate names and coincident positions remain distinct source records; the retail walker compares the last emitted name after discovery passes.',
]


def _hash(data):
    return sha256(data).hexdigest()


def _values(row):
    return {key: deepcopy(row[key]) for key in VALUE_FIELDS}


def _validate_values(value, mapping):
    if not isinstance(value, dict) or set(value) != set(VALUE_FIELDS):
        raise ImportError('World-map values require name_index, discovery_flag_index, destination_scene_id and menu_position only')
    for field, lower, upper in [('name_index', 0, 15), ('discovery_flag_index', 32, 287),
                                ('destination_scene_id', 0, 65535)]:
        if type(value[field]) is not int or not lower <= value[field] <= upper:
            raise ImportError(f'World-map {field} must be an integer from {lower} through {upper}')
    if value['destination_scene_id'] not in mapping:
        raise ImportError('World-map destination requires an exact numeric definition in the verified CDNAME source')
    position = value['menu_position']
    if (not isinstance(position, dict) or set(position) != {'x', 'y'} or
            any(type(axis) is not int or not 0 <= axis <= 255 for axis in position.values())):
        raise ImportError('World-map menu_position requires only integer byte coordinates x and y')
    return deepcopy(value)


class WorldMapAuthoringContext:
    """Immutable executable and CDNAME snapshot with detached review products."""
    def __init__(self, executable: bytes, mapping: dict[int, str], source: dict | None = None):
        report = decode_worldmap_menu(executable)
        if not isinstance(mapping, dict) or not 1 <= len(mapping) <= 4096:
            raise ImportError('World-map destinations require a bounded nonempty CDNAME mapping')
        if any(type(index) is not int or not 0 <= index <= 65535 or
               not isinstance(label, str) or not 1 <= len(label) <= 128 or
               any(not 33 <= ord(character) <= 126 for character in label)
               for index, label in mapping.items()):
            raise ImportError('World-map CDNAME definitions require exact u16 IDs and bounded ASCII labels')
        if source is None:
            source = {}
        if (not isinstance(source, dict) or set(source) - {'disc_sha256', 'cdname_sha256'} or
                any(not isinstance(value, str) or re.fullmatch(r'[0-9a-f]{64}', value) is None
                    for value in source.values())):
            raise ImportError('World-map source metadata accepts only exact disc and CDNAME SHA256 digests')
        record = report['source_record']
        start, names = record['table_file_offset'], record['name_table_file_offset']
        count, end = record['terminator_record_index'], start + 6 * (record['terminator_record_index'] + 1)
        if not 0 <= count < MAX_ENTRIES or end > names:
            raise ImportError('World-map placement rows and complete terminator must precede the name table')
        seen_ids, seen_offsets = set(), set()
        for index, row in enumerate(report['placements']):
            if (row['record_index'] != index or row['semantic_id'] != f'worldmap://legaia/menu/placements/{index:04d}' or
                    row['source_offset'] != start + index * 6 or row['byte_length'] != 6 or
                    row['semantic_id'] in seen_ids or row['source_offset'] in seen_offsets or
                    row['source_offset'] + 6 > end - 6):
                raise ImportError('World-map placement identity or source row span is ambiguous')
            seen_ids.add(row['semantic_id']); seen_offsets.add(row['source_offset'])
        if len(report['placements']) != count or executable[end - 6] != 255:
            raise ImportError('World-map placement count does not match its source terminator')
        self._executable = executable
        self._mapping = deepcopy(mapping)
        self._source = deepcopy(source)
        self._sha256 = _hash(executable)
        self._report = resolve_menu_destinations(report, self._mapping, self._source.get('cdname_sha256'))
        if 'disc_sha256' in source:
            self._report['source_record']['disc_sha256'] = source['disc_sha256']
        self._rows = {row['semantic_id']: row for row in self._report['placements']}

    def options(self) -> dict:
        return deepcopy({
            'schema_version': 'legaia.worldmap-authoring-options.v1',
            'source_executable_sha256': self._sha256,
            'source_record': self._report['source_record'],
            'destination_label_source': self._report['destination_label_source'],
            'field_evidence': self._report['field_evidence'],
            'names': self._report['names'],
            'placements': [dict(row, values=_values(row)) for row in self._rows.values()],
            'allowed_destinations': [dict(destination_scene_id=index, destination_source_label=label)
                                     for index, label in sorted(self._mapping.items())],
            'limits': {'maximum_entries': MAX_ENTRIES, 'source_record_count': len(self._rows),
                       'name_index': {'min': 0, 'max': 15},
                       'discovery_flag_index': {'min': 32, 'max': 287},
                       'destination_scene_id': {'min': 0, 'max': 65535},
                       'menu_position': {'min': 0, 'max': 255}},
            'scope': 'worldmap-menu-record-only', 'gameplay_verified': False,
            'limitations': LIMITATIONS,
        })

    def patch(self, entries: dict, *, original: bytes | None = None) -> tuple[bytes, list[dict]]:
        if original is not None and (not isinstance(original, bytes) or original != self._executable):
            raise ImportError('World-map executable differs from its verified source preimage')
        if _hash(self._executable) != self._sha256:
            raise ImportError('World-map executable differs from its fixed source hash')
        if not isinstance(entries, dict) or len(entries) > MAX_ENTRIES:
            raise ImportError('World-map entries require a bounded source-identity mapping')
        staged = []
        for identifier, value in entries.items():
            if not isinstance(identifier, str) or identifier not in self._rows:
                raise ImportError('World-map identity must select an existing original menu row')
            staged.append((self._rows[identifier], _validate_values(value, self._mapping)))
        output, audit = bytearray(self._executable), []
        for row, value in sorted(staged, key=lambda pair: pair[0]['record_index']):
            at = row['source_offset']
            before = self._executable[at:at + 6]
            after = struct.pack('<BBHBB', value['name_index'], value['discovery_flag_index'] - 32,
                                value['destination_scene_id'], value['menu_position']['x'], value['menu_position']['y'])
            if before == after:
                continue
            output[at:at + 6] = after
            audit.append(dict(entity_id=row['semantic_id'], record_index=row['record_index'],
                              before_value=_values(row), after_value=deepcopy(value),
                              file_offset=at, byte_length=6,
                              changed_bytes=[dict(file_offset=at + i, before_byte=a, after_byte=b)
                                             for i, (a, b) in enumerate(zip(before, after)) if a != b],
                              scope='worldmap-menu-record-only', source_executable_sha256=self._sha256))
        candidate = bytes(output)
        decoded = decode_worldmap_menu(candidate)
        expected = decode_worldmap_menu(self._executable)
        qualified = {row['semantic_id']: value for row, value in staged}
        for row in expected['placements']:
            if row['semantic_id'] not in qualified:
                continue
            row.update(deepcopy(qualified[row['semantic_id']]))
            row.update(name=expected['names'][row['name_index']]['name'], resolved_name=True,
                       discovery_flag_encoded=row['discovery_flag_index'] - 32)
        candidate_hash = _hash(candidate)
        expected['source_record']['sha256'] = candidate_hash
        if decoded != expected:
            raise ImportError('World-map independent readback changed an unaffected row, name or source extent')
        differences = {at: (a, b) for at, (a, b) in enumerate(zip(self._executable, candidate)) if a != b}
        audited = {change['file_offset']: (change['before_byte'], change['after_byte'])
                   for row in audit for change in row['changed_bytes']}
        if (len(candidate) != len(self._executable) or differences != audited or
                len(audited) != sum(len(row['changed_bytes']) for row in audit)):
            raise ImportError('World-map patch changed an unaudited or overlapping executable byte')
        for row in audit:
            row['candidate_executable_sha256'] = candidate_hash
        return candidate, deepcopy(audit)


def load_worldmap_authoring_context(disc) -> WorldMapAuthoringContext:
    with _disc_context(disc) as (image, digest, mapping, _):
        node = image.find('SCUS_942.54')
        if node.size > 2 * 1024 * 1024:
            raise ImportError('Executable exceeds the world-map authoring budget')
        executable = image.read_file(node)
        if worldmap_field_evidence(executable)['name_index'] != 'retail_static_analysis':
            raise ImportError('World-map authoring requires the verified retail menu consumer code windows')
        cdname = image.read_file(image.find('CDNAME.TXT'))
        return WorldMapAuthoringContext(executable, mapping,
                                        {'disc_sha256': digest, 'cdname_sha256': _hash(cdname)})
