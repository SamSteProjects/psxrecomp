"""Fresh read-only project APIs for separate battle sideband sources."""
from base64 import b64encode
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
