"""Fresh read-only project APIs for separate battle sideband sources."""
from base64 import b64encode
from hashlib import sha256
from importer.core import ImportError
from importer.assets import decode_tmd
from sdk.project import ProjectError
from sdk.project_assets import source_key
from importer.battle_sideband import load_sources, texture_preview, SLOT_BYTES


def _fresh(project, path, key):
    if not project.disc_path or path != str(project.root) or key != source_key(project):
        raise ProjectError('Sideband inspection requires the current disc-backed project source')


def _source(project):
    catalog, entries = load_sources(project.disc_path)
    digest = catalog['source_disc_sha256']
    if any(row['source']['disc_identity'] != 'sha256:' + digest for row in project.imports.values()):
        raise ProjectError('Sideband source differs from imported project provenance')
    return catalog, entries


def resources(project, expected_project_path, expected_source_key):
    _fresh(project, expected_project_path, expected_source_key)
    try:
        catalog, _ = _source(project)
    except ImportError as error:
        raise ProjectError(str(error)) from error
    _fresh(project, expected_project_path, expected_source_key)
    return dict(schema_version='legaia.battle-sideband-resources.v1', project_path=str(project.root),
                project_source_key=expected_source_key, catalog=catalog, layer='retail',
                read_only=True, project_changed=False, gameplay_verified=False)


def preview(project, expected_project_path, expected_source_key, asset_id, catalog_source_key, palette_index):
    _fresh(project, expected_project_path, expected_source_key)
    try:
        catalog, entries = _source(project)
        if catalog_source_key != catalog['source_key']:
            raise ProjectError('Sideband catalog changed; refresh discovery')
        record = next((r for r in catalog['models'] + catalog['textures'] if r['semantic_id'] == asset_id), None)
        if record is None:
            raise ProjectError('Sideband source has no qualified preview for this resource')
        source = record['source_record']
        content = entries[source['prot_entry_index']]
        slot = content[source['slot_offset']:source['slot_offset'] + SLOT_BYTES]
        body = content[source['byte_offset']:source['byte_offset'] + source['byte_length']]
        if record['asset_kind'] == 'tmd_model':
            if type(palette_index) is not int or palette_index != 0:
                raise ProjectError('Object-local sideband models accept no palette override')
            value = decode_tmd(body)
            value.update(semantic_id=record['semantic_id'], source_record=source,
                         representation='retail_battle_sideband_object_local',
                         texture_association='unresolved_source_geometry_only')
        else:
            value = texture_preview(content, record, palette_index)
            for key in ('rgba', 'stp'):
                value[key + '_base64'] = b64encode(value.pop(key)).decode('ascii')
    except ImportError as error:
        raise ProjectError(str(error)) from error
    _fresh(project, expected_project_path, expected_source_key)
    return dict(schema_version='legaia.battle-sideband-preview.v1', project_path=str(project.root),
                project_source_key=expected_source_key, catalog_source_key=catalog_source_key,
                record=record, preview=value, source_slot_base64=b64encode(slot).decode('ascii'),
                palette_index=palette_index, layer='retail', read_only=True,
                project_changed=False, gameplay_verified=False)


def export(project, expected_project_path, expected_source_key, asset_id, catalog_source_key, palette_index, export_kind):
    if export_kind not in ('glb', 'png', 'stp'):
        raise ProjectError('Choose a source model GLB or source page PNG/STP export')
    receipt = preview(project, expected_project_path, expected_source_key, asset_id, catalog_source_key, palette_index)
    record, value = receipt['record'], receipt['preview']
    source = record['source_record']
    stem = f"sideband-{source['prot_entry_index']}-slot-{source['slot_index']}"
    if export_kind == 'glb':
        if record['asset_kind'] != 'tmd_model':
            raise ProjectError('Source GLB export requires an object-local model')
        from importer.export import encode_model_glb
        try:
            data, audit = encode_model_glb(value)
        except ImportError as error:
            raise ProjectError(str(error)) from error
        filename = stem + '-object-local.glb'
    else:
        if record['asset_kind'] != 'texture':
            raise ProjectError('Source PNG/STP export requires a native CLUT page')
        from base64 import b64decode
        from importer.texture_png import _encode_png
        rgba = b64decode(value['rgba_base64'])
        if export_kind == 'stp':
            rgba = bytes(channel for bit in b64decode(value['stp_base64']) for channel in (bit * 255, bit * 255, bit * 255, 255))
        data = _encode_png(value['width'], value['height'], rgba)
        audit = dict(width=value['width'], height=value['height'], pixel_format='RGBA8',
                     adapter='source_CLUT_page_pixels_not_native_TIM',
                     mask_convention='white_set_bit_black_clear_bit' if export_kind == 'stp' else None)
        filename = stem + f'-palette-{palette_index}' + ('-stp' if export_kind == 'stp' else '') + '.png'
    _fresh(project, expected_project_path, expected_source_key)
    return dict(schema_version='legaia.battle-sideband-export.v1', inspection=receipt, export_kind=export_kind,
                filename=filename, file_base64=b64encode(data).decode('ascii'), byte_length=len(data), sha256=sha256(data).hexdigest(),
                audit=audit, read_only=True, project_changed=False, gameplay_verified=False)
