"""Read-only field equipment variants for imported party model identities."""
from importer.field_equipment import load_field_equipment_preview
from importer.animation import load_animation_preview
from .battle_character_resources import _fresh
from .project import ProjectError
from base64 import b64encode
from importer.assets import load_model_source
from importer.field_equipment import project_field_equipment
from importer.textures import TextureCatalog,load_asset_texture_catalog,associate_material
from copy import deepcopy


def _textures(project,asset,geometry):
    catalog=load_asset_texture_catalog(project.disc_path,asset,TextureCatalog('field-equipment',asset['source_record']['disc']['sha256']))
    geometry['texture_catalog']=catalog.metadata();geometry['texture_scope']='field_party';geometry['textures']=[];budget=2*1024*1024
    for index,material in enumerate(geometry['materials']):
        if not material.get('textured'):
            geometry['textures'].append(dict(material_index=index,status='untextured',reason='Material uses vertex colors'));continue
        uvs=[uv for i,face in enumerate(geometry['triangle_uvs']) if geometry['triangle_materials'][i]==index for uv in (face or [])]
        if not uvs or index>=32:
            geometry['textures'].append(dict(material_index=index,status='unsupported',reason='No active UVs or material budget exceeded'));continue
        result=associate_material(catalog,material,(min(v[0] for v in uvs),min(v[1] for v in uvs),max(v[0] for v in uvs),max(v[1] for v in uvs)))
        rgba,stp=result.pop('rgba',None),result.pop('stp',None)
        if rgba is not None:
            if stp is None or len(stp)*4!=len(rgba) or any(b not in (0,1) for b in stp):raise ProjectError('Field equipment texture masks changed')
            if len(rgba)+len(stp)>budget:result=dict(status='unsupported',reason='Field equipment texture byte budget exceeded')
            else:
                budget-=len(rgba)+len(stp);result.update(rgba_base64=b64encode(rgba).decode(),stp_base64=b64encode(stp).decode())
        geometry['textures'].append(dict(result,material_index=index))


def preview(project,expected_project_path,expected_source_key,asset_id,equipment_byte,clip_id,frame_index):
    _fresh(project,expected_project_path,expected_source_key)
    asset=project.assets.records.get(asset_id)
    if asset is None:raise ProjectError('Field equipment model must be registered in the imported project')
    base=load_field_equipment_preview(project.disc_path,asset,equipment_byte)
    original=load_model_source(project.disc_path,asset)
    projected,_=project_field_equipment(original,base['equipment_variant']['party_slot'],equipment_byte)
    _textures(project,asset,base)
    if clip_id is None:
        if frame_index is not None:raise ProjectError('Unposed field equipment accepts no native frame')
        geometry=base;animation=None
    else:
        if clip_id not in ('idle','walk') or type(frame_index) is not int:raise ProjectError('Choose a qualified field idle/walk clip and whole frame')
        animation=load_animation_preview(project.disc_path,asset,clip_id,equipment_byte=equipment_byte)
        if not 0<=frame_index<len(animation['frames']):raise ProjectError('Field equipment frame exceeds the stored clip')
        geometry=animation.pop('geometry');posed=animation.pop('frames')[frame_index];geometry.update(posed);geometry.pop('triangle_normals',None);geometry.pop('normal_preview',None)
        for key in ('texture_scope','texture_catalog','textures'):geometry[key]=base[key]
    _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.field-equipment-preview.v1',project_path=str(project.root),project_source_key=expected_source_key,asset_id=asset_id,equipment_byte=equipment_byte,clip_id=clip_id,frame_index=frame_index,
        geometry=geometry,base_geometry=base,source_record=asset['source_record'],source_tmd_base64=b64encode(original).decode(),projected_tmd_base64=b64encode(projected).decode(),animation=animation,layer='retail_selected_variant',read_only=True,project_changed=False,gameplay_verified=False)


def export(project,**context):
    from importer.export import encode_model_glb
    receipt=preview(project,**context);geometry=deepcopy(receipt['base_geometry'])
    geometry['source_record']=dict(original=receipt['source_record'],equipment_variant=geometry['equipment_variant'])
    if context['clip_id'] is not None:
        geometry['animation']=dict(receipt['animation'],source_frame_index=context['frame_index'])
        geometry['frames']=[receipt['geometry']]
    content,audit=encode_model_glb(geometry,0 if context['clip_id'] is not None else None)
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    suffix='unposed' if context['clip_id'] is None else f'{context["clip_id"]}-frame-{context["frame_index"]}'
    return dict(schema_version='legaia.field-equipment-export.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],asset_id=context['asset_id'],equipment_byte=context['equipment_byte'],clip_id=context['clip_id'],frame_index=context['frame_index'],source_record=receipt['source_record'],equipment_variant=geometry['equipment_variant'],
        filename=f'field-party-{geometry["equipment_variant"]["party_slot"]}-equipment-{context["equipment_byte"]}-{suffix}.glb',glb_base64=b64encode(content).decode(),audit=audit,layer='retail_selected_variant',read_only=True,project_changed=False,gameplay_verified=False)


def export_clip(project,export_fps,**context):
    """Export all stored rigid frames at an explicit interchange rate."""
    from math import isfinite
    from importer.export import encode_model_glb
    if type(export_fps) not in (int,float) or not isfinite(export_fps) or not 1<=export_fps<=120:
        raise ProjectError('Field clip export requires an explicit rate from 1 to 120 fps')
    if context['clip_id'] not in ('idle','walk'):
        raise ProjectError('Field clip export requires a selected idle or walk clip')
    receipt=preview(project,**context)
    asset=project.assets.records[context['asset_id']]
    animation=load_animation_preview(project.disc_path,asset,context['clip_id'],equipment_byte=context['equipment_byte'])
    geometry=deepcopy(receipt['base_geometry'])
    geometry['source_record']=dict(original=receipt['source_record'],equipment_variant=geometry['equipment_variant'])
    geometry['frames']=animation.pop('frames');animation.pop('geometry');geometry['animation']=animation
    content,audit=encode_model_glb(geometry,clip_fps=export_fps)
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return dict(schema_version='legaia.field-equipment-export.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],asset_id=context['asset_id'],equipment_byte=context['equipment_byte'],clip_id=context['clip_id'],frame_index=context['frame_index'],source_record=receipt['source_record'],equipment_variant=geometry['equipment_variant'],full_clip=True,export_fps=export_fps,
        filename=f'field-party-{geometry["equipment_variant"]["party_slot"]}-equipment-{context["equipment_byte"]}-{context["clip_id"]}-clip.glb',glb_base64=b64encode(content).decode(),audit=audit,layer='retail_selected_variant',read_only=True,project_changed=False,gameplay_verified=False)
