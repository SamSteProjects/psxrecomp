"""Project-scoped source-only PLAYER equipment inspection."""
from importer import player_battle as native
from importer.core import ImportError as RetailImportError
from .project import ProjectError
from .battle_character_resources import _fresh,_disc
from base64 import b64encode


def _pixels(geometry):
    for t in geometry.get('textures',[]):
        for key in ('rgba','stp'):
            if key in t:t[key+'_base64']=b64encode(t.pop(key)).decode('ascii')


def resources(project,expected_project_path,expected_source_key):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog=native.discover(project.disc_path)
    except RetailImportError as e:raise ProjectError(str(e)) from e
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.player-battle-resources.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog=catalog,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


def preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,equipped):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog,model,geometry,assembly=native.preview(project.disc_path,asset_id,catalog_source_key,equipped)
    except RetailImportError as e:raise ProjectError(str(e)) from e
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key);_pixels(geometry)
    return dict(schema_version='legaia.player-battle-preview.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog_source_key=catalog_source_key,record=model,geometry=geometry,assembly=assembly,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


def pose(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,equipped,action_slot,frame_index):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog,model,geometry,assembly,clip,transforms=native.pose(project.disc_path,asset_id,catalog_source_key,equipped,action_slot,frame_index)
    except RetailImportError as e:raise ProjectError(str(e)) from e
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key);_pixels(geometry)
    return dict(schema_version='legaia.player-battle-pose.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog_source_key=catalog_source_key,record=model,geometry=geometry,assembly=assembly,clip=clip,object_transforms=transforms,action_slot=action_slot,frame_index=frame_index,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)
