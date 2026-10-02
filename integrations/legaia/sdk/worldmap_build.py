"""Guarded SCUS data overlays for the existing landmark table, never code edits."""
from hashlib import sha256
import struct

from importer.worldmap_menu import decode_worldmap_menu
from .project import ProjectError
from .worldmap_authoring import OWNER, COMPONENT, FIELDS, _field, _context

SPANS = {'name_index': (0, 1), 'discovery_flag_index': (1, 1),
         'destination_scene_id': (2, 2), 'menu_position.x': (4, 1), 'menu_position.y': (5, 1)}


def prepare_worldmap_overlay(project, image, disc_sha256):
    """Independently bind the serializer output to actual source EXE row spans."""
    binding = project.overrides.get(OWNER, {}).get(COMPONENT)
    if binding is None:
        return [], []
    project._validate_worldmap_menu(OWNER, binding)
    context, options, _ = _context(project)
    node = image.find('SCUS_942.54')
    original = image.read_file(node)
    if (sha256(original).hexdigest() != options['source_executable_sha256']
            or disc_sha256 != binding['source_disc_sha256']):
        raise ProjectError('World-map Build source differs from the bound executable/disc')
    candidate, audit = context.patch(binding['entries'], original=original)
    rows = {row['semantic_id']: row for row in options['placements']}
    expected = bytearray(original)
    expected_rows = {}
    for identifier, value in binding['entries'].items():
        row = rows[identifier]
        offset = row['source_offset']
        encoded = struct.pack('<BBHBB', value['name_index'], value['discovery_flag_index'] - 32,
                              value['destination_scene_id'], value['menu_position']['x'], value['menu_position']['y'])
        expected[offset:offset + 6] = encoded
        if original[offset:offset + 6] != encoded:
            expected_rows[identifier] = dict(row=row, value=value, changed_bytes=[
                dict(file_offset=offset + i, before_byte=a, after_byte=b)
                for i, (a, b) in enumerate(zip(original[offset:offset + 6], encoded)) if a != b])
    if candidate != bytes(expected) or len(candidate) != len(original):
        raise ProjectError('World-map serializer changed bytes outside the requested source rows')
    indexed = {row['entity_id']: row for row in audit}
    if len(indexed) != len(audit) or set(indexed) != set(expected_rows):
        raise ProjectError('World-map serializer audit omits or invents a changed row')
    changes = []
    for identifier, expected_row in expected_rows.items():
        row, values = expected_row['row'], expected_row['value']
        emitted = indexed[identifier]
        retail = row['values']
        if (emitted['before_value'] != retail or emitted['after_value'] != values
                or emitted['changed_bytes'] != expected_row['changed_bytes']
                or emitted['file_offset'] != row['source_offset'] or emitted['byte_length'] != 6
                or emitted['scope'] != 'worldmap-menu-record-only'
                or emitted['source_executable_sha256'] != sha256(original).hexdigest()
                or emitted['candidate_executable_sha256'] != sha256(candidate).hexdigest()):
            raise ProjectError('World-map row audit differs from independently encoded values')
        for field in FIELDS:
            before, after = _field(retail, field), _field(values, field)
            if before == after:
                continue
            relative, width = SPANS[field]
            at = row['source_offset'] + relative
            changes.append(dict(scene='worldmap-menu', semantic_id=OWNER, worldmap_placement_id=identifier,
                field='worldmap.' + field, before_value=before, after_value=after, record_index=row['record_index'],
                executable_file_offset=at, byte_length=width, scope='worldmap-menu-record-only',
                source_executable_sha256=sha256(original).hexdigest(), candidate_executable_sha256=sha256(candidate).hexdigest(),
                changed_bytes=[change for change in emitted['changed_bytes'] if at <= change['file_offset'] < at + width]))
    if not changes:
        return [], []
    start = options['source_record']['table_file_offset']
    end = start + (options['source_record']['terminator_record_index'] + 1) * 6
    before, payload = original[start:end], candidate[start:end]
    # Reopen a complete executable from only the emitted overlay and use the
    # independent reader again; executable code, names and headers stay exact.
    reopened = original[:start] + payload + original[end:]
    if reopened != candidate or decode_worldmap_menu(reopened) != decode_worldmap_menu(candidate):
        raise ProjectError('World-map overlay failed independent executable readback')
    offset = node.extent_lba * 2048 + start
    disc_user_size = image.size // 2352 * 2048
    if image.read_user(0, offset, len(before), disc_user_size) != before:
        raise ProjectError('World-map file-to-disc extent binding failed')
    overlay = dict(scene='worldmap-menu', source_kind='SCUS_worldmap_menu', iso_file='SCUS_942.54',
        executable_file_offset=start, offset=offset, size=len(payload), file='assets/worldmap-menu.bin',
        payload=payload, sha256=sha256(payload).hexdigest(), expected_sha256=sha256(before).hexdigest(),
        source_executable_sha256=sha256(original).hexdigest(), candidate_executable_sha256=sha256(candidate).hexdigest())
    return [overlay], changes
