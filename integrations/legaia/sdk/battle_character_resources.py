"""Read-only project-scoped battle resource discovery and private previews."""
from base64 import b64encode
from importer.battle_character_catalog import discover,preview as native_preview
from importer.core import ImportError as RetailImportError
from .project import ProjectError
from .project_assets import source_key


def _fresh(project,path,key):
    if not project.disc_path or path!=str(project.root) or key!=source_key(project):
        raise ProjectError('Battle resource inspection requires the current disc-backed project source')


def _disc(project,catalog):
    if any(d['source']['disc_identity']!='sha256:'+catalog['source_disc_sha256'] for d in project.imports.values()):
        raise ProjectError('Battle resource disc differs from imported project provenance')


def resources(project,expected_project_path,expected_source_key):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog=discover(project.disc_path)
    except RetailImportError as error:raise ProjectError(str(error)) from error
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.battle-character-resources.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog=catalog,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


def preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,palette_index):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog,record,value=native_preview(project.disc_path,asset_id,catalog_source_key,palette_index)
    except RetailImportError as error:raise ProjectError(str(error)) from error
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    if record['asset_kind']=='tmd_model':value.update(semantic_id=record['semantic_id'],source_record=record['source_record'])
    if record['asset_kind']=='texture':
        # Private native pixels, not persistent/import metadata.
        rgba,stp=value['rgba'],value['stp'];value={k:v for k,v in value.items() if k not in ('rgba','stp')}
        value.update(rgba_base64=b64encode(rgba).decode('ascii'),stp_base64=b64encode(stp).decode('ascii'))
        _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.battle-character-preview.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog_source_key=catalog_source_key,record=record,preview=value,layer='retail',palette_index=palette_index,read_only=True,project_changed=False,gameplay_verified=False)
