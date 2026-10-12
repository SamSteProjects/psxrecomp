"""Read-only field equipment variants for imported party model identities."""
from importer.field_equipment import load_field_equipment_preview
from importer.animation import load_animation_preview
from .battle_character_resources import _fresh
from .project import ProjectError


def preview(project,expected_project_path,expected_source_key,asset_id,equipment_byte,clip_id,frame_index):
    _fresh(project,expected_project_path,expected_source_key)
    asset=project.assets.records.get(asset_id)
    if asset is None:raise ProjectError('Field equipment model must be registered in the imported project')
    if clip_id is None:
        if frame_index is not None:raise ProjectError('Unposed field equipment accepts no native frame')
        geometry=load_field_equipment_preview(project.disc_path,asset,equipment_byte);animation=None
    else:
        if clip_id not in ('idle','walk') or type(frame_index) is not int:raise ProjectError('Choose a qualified field idle/walk clip and whole frame')
        animation=load_animation_preview(project.disc_path,asset,clip_id,equipment_byte=equipment_byte)
        if not 0<=frame_index<len(animation['frames']):raise ProjectError('Field equipment frame exceeds the stored clip')
        geometry=animation.pop('geometry');posed=animation.pop('frames')[frame_index];geometry.update(posed);geometry.pop('triangle_normals',None);geometry.pop('normal_preview',None)
    _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.field-equipment-preview.v1',project_path=str(project.root),project_source_key=expected_source_key,asset_id=asset_id,equipment_byte=equipment_byte,clip_id=clip_id,frame_index=frame_index,
        geometry=geometry,animation=animation,layer='retail_selected_variant',read_only=True,project_changed=False,gameplay_verified=False)
