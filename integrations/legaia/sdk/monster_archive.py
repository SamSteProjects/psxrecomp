"""Project-scoped Retail monster model discovery and object-local preview."""
from base64 import b64encode
from importer import monster_archive as native
from importer.core import ImportError as NativeError
from .battle_character_resources import _fresh,_disc
from .project import ProjectError


def resources(project,expected_project_path,expected_source_key):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog=native.discover(project.disc_path)
    except NativeError as e:raise ProjectError(str(e)) from e
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.monster-resources.v1',project_path=str(project.root),project_source_key=expected_source_key,
        catalog=catalog,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


def preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog,record,geometry,body=native.preview(project.disc_path,asset_id,catalog_source_key)
    except NativeError as e:raise ProjectError(str(e)) from e
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    geometry.update(semantic_id=asset_id,source_record=record['source_record'],textures=[])
    return dict(schema_version='legaia.monster-preview.v1',project_path=str(project.root),project_source_key=expected_source_key,
        catalog_source_key=catalog_source_key,record=record,geometry=geometry,source_tmd_base64=b64encode(body).decode(),
        layer='retail',read_only=True,project_changed=False,gameplay_verified=False)
