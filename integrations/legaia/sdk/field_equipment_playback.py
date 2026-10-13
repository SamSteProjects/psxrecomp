"""Read-only, source-verified field equipment clips for local display sampling."""
from base64 import b64encode
from hashlib import sha256

from importer.animation import animation_record_ranges, decode_animation_record
from importer.core import decompress_lzs, parse_lzs_sections
from importer.pipeline import _disc_context
from .battle_character_resources import _fresh
from .field_equipment import preview as equipment_preview
from .project import ProjectError


def preview(project, expected_project_path, expected_source_key, asset_id,
            equipment_byte, clip_id, frame_index, model_layer='retail'):
    """Keep the Retail locomotion bank separate from Current model/TIM owners.

    The complete bank lets the browser independently verify the selected
    record's table range and packed channels before caching it. No caller FPS
    is accepted here: display cadence belongs to the local playback control.
    """
    _fresh(project, expected_project_path, expected_source_key)
    if clip_id not in ('idle', 'walk') or type(frame_index) is not int:
        raise ProjectError('Field equipment playback requires idle/walk and a whole source frame')
    held = equipment_preview(project, expected_project_path, expected_source_key,
                             asset_id, equipment_byte, clip_id, frame_index,
                             model_layer=model_layer)
    source = held['animation']['source_record']
    slot = held['geometry']['equipment_variant']['party_slot']
    index = slot * 7 + (1 if clip_id == 'idle' else 0)
    with _disc_context(project.disc_path) as (_, digest, _, archive):
        raw = archive.read_entry(archive.entry(874), extended=True)
        sections = parse_lzs_sections(raw)
        if len(sections) != 3:
            raise ProjectError('Field equipment locomotion container changed')
        section = sections[1]
        bank, consumed = decompress_lzs(
            raw[section.stream_offset:sections[2].stream_offset], section.decoded_size)
        ranges = animation_record_ranges(bank)
        if len(ranges) != 23:
            raise ProjectError('Field equipment locomotion bank requires 23 source records')
        start, end = ranges[index]
        record = bank[start:end]
        decoded = decode_animation_record(record)
        expected = dict(disc=dict(sha256=digest, serial='SCUS-94254'),
                        iso_file='PROT.DAT', prot_entry_index=874, container_section=1,
                        compressed_stream_offset=section.stream_offset,
                        compressed_bytes_consumed=consumed, record_index=index,
                        byte_offset=start, byte_length=end-start,
                        byte_coordinate_space='decoded_lzs_section', containing_size=len(bank))
        if (source != expected or digest != held['source_record']['disc']['sha256']
                or decoded['bone_count'] != 10
                or decoded['frame_count'] != held['animation']['frame_count']
                or decoded['frames'][frame_index]['object_transforms']
                   != held['geometry']['object_transforms']):
            raise ProjectError('Field equipment clip bytes differ from the qualified pose')
    _fresh(project, expected_project_path, expected_source_key)
    return dict(schema_version='legaia.field-equipment-playback.v1', preview=held,
                source_record=source, bank_base64=b64encode(bank).decode('ascii'),
                bank_sha256=sha256(bank).hexdigest(), bank_record_count=23,
                record_base64=b64encode(record).decode('ascii'),
                record_sha256=sha256(record).hexdigest(),
                frame_count=decoded['frame_count'], channel_count=10,
                active_object_indices=list(range(10)),
                timing='caller_selected_display_rate_not_native_cadence',
                looping='one_pass_display_only', read_only=True,
                project_changed=False, gameplay_verified=False)
