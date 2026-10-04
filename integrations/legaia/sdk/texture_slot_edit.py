"""Reviewed full TIM interchange for a stable authored slot, not a Retail edit."""
from copy import deepcopy
from hashlib import sha256
import base64

from importer.texture_slot_allocation import append_texture_pack,validate_added_tim
from importer.texture_png import export_texture_png
from .project import ProjectError,atomic_write,digest
from .scene_preview import source_key
from .texture_resize import image_layout
from .texture_slots import read,validate_collection,native_pack,group,_footprint


def source(project,asset_id,expected_source_key):
    key=source_key(project)
    if project.mode!='edit' or not key or key!=expected_source_key:
        raise ProjectError('Authored slot editing requires the current Edit context')
    binding=project.texture_additions.get(asset_id) if isinstance(asset_id,str) else None
    if binding is None or binding['source_scene_id']!=project.active_scene:
        raise ProjectError('Authored texture slot is outside the current scene')
    validate_collection(project)
    content=read(project,asset_id,binding)
    context=project._texture_context(binding['anchor_asset_id'])
    with context._archive() as archive:
        group(project,project.active_scene,context,archive)
    tim=validate_added_tim(content)
    result=dict(schema_version='legaia.texture-slot-edit-source.v1',asset_id=asset_id,
        project_source_key=key,source_scene_id=project.active_scene,anchor_asset_id=binding['anchor_asset_id'],
        current_sha256=sha256(content).hexdigest(),byte_length=len(content),label=binding['label'],
        slot_index=binding['slot_index'],image_layout=image_layout(content),
        palette_count=len(tim.clut.data)//((1<<tim.bpp)*2) if tim.bpp in (4,8) and tim.clut else 0,
        read_only=True,project_changed=False)
    if 'image_source' in binding:result['image_source']=deepcopy(binding['image_source'])
    if source_key(project)!=key:raise ProjectError('Authored slot changed during source inspection')
    return content,result


def review(project,asset_id,content,expected_sha256,expected_source_key,label,accept_potential_overlap=False, *, conversion_source=None):
    if type(accept_potential_overlap) is not bool:
        raise ProjectError('Authored slot editing requires an explicit overlap choice')
    current,original=source(project,asset_id,expected_source_key)
    if original['current_sha256']!=expected_sha256:
        raise ProjectError('Authored slot TIM changed; review again')
    if not isinstance(label,str) or not label.strip() or len(label)>128 or any(ord(c)<32 for c in label):
        raise ProjectError('Texture label must contain one to 128 printable characters')
    tim=validate_added_tim(content)
    binding=project.texture_additions[asset_id]
    if sum(b['byte_length'] for b in project.texture_additions.values())-len(current)+len(content)>16*1024*1024:
        raise ProjectError('Edited texture slots exceed their 16 MiB content budget')
    context=project._texture_context(binding['anchor_asset_id'])
    with context._archive() as archive:
        pack_key,pack=native_pack(context,archive,binding['anchor_asset_id'])
        existing=group(project,project.active_scene,context,archive)[pack_key]
        edits=[]
        for identifier,override in project.texture_overrides.items():
            if override['source_scene_id']!=project.active_scene:continue
            locator=context._item(identifier)[1]
            if (locator['prot_entry_index'],locator.get('descriptor_index',-1))!=pack_key:continue
            effective=project.read_texture_replacement(override)
            project.validate_effective_texture(identifier,effective,context=context)
            retail=context.original_tim(identifier)
            if effective!=retail:edits.append(dict(slot_index=locator['pack_slot'],source_tim_sha256=sha256(retail).hexdigest(),tim=effective))
    additions=[content if identifier==asset_id else payload for identifier,_,payload in existing]
    proposed,allocation=append_texture_pack(pack,sha256(pack).hexdigest(),additions,edits=edits,standalone=pack_key[1]==-1)
    if pack_key[1]!=-1 and len(proposed)>4*1024*1024:
        raise ProjectError('Edited texture pack exceeds the native descriptor decoder budget')
    footprint=_footprint(project,context,content,exclude_asset_id=asset_id)
    changed=current!=content or original['label']!=label
    result=dict(schema_version='legaia.texture-slot-edit-review.v1',asset_id=asset_id,
        project_source_key=expected_source_key,source_scene_id=project.active_scene,
        anchor_asset_id=binding['anchor_asset_id'],source_pack_sha256=binding['source_pack_sha256'],
        source_slot_count=binding['source_slot_count'],pack_entry_index=pack_key[0],pack_descriptor_index=pack_key[1],
        slot_index=binding['slot_index'],current_sha256=expected_sha256,current_byte_length=len(current),
        current_label=original['label'],current_layout=original['image_layout'],
        proposed_sha256=sha256(content).hexdigest(),byte_length=len(content),label=label,image_layout=image_layout(content),
        palette_count=len(tim.clut.data)//((1<<tim.bpp)*2) if tim.bpp in (4,8) and tim.clut else 0,
        allocation=allocation,footprint=footprint,accept_potential_overlap=accept_potential_overlap,
        content_changed=current!=content,layout_changed=image_layout(current)!=image_layout(content),
        changed=changed,can_apply=changed and (not footprint['potential_overlap_count'] or accept_potential_overlap),
        project_changed=False,gameplay_verified=False)
    if conversion_source is not None:
        from .texture_slot_sources import prepare_recipe
        result['image_source']=prepare_recipe(project,content,conversion_source,asset_id)
    result['review_key']=digest(result)
    if source_key(project)!=expected_source_key:raise ProjectError('Authored slot changed during review')
    return result


def pixels(project,asset_id,content,expected_sha256,expected_source_key,label,accept_potential_overlap,review_key,palette_index, *, conversion_source=None):
    report=review(project,asset_id,content,expected_sha256,expected_source_key,label,accept_potential_overlap,conversion_source=conversion_source)
    if report['review_key']!=review_key:raise ProjectError('Authored slot pixels require the current review')
    if type(palette_index) is not int or not 0<=palette_index<max(1,report['palette_count']):
        raise ProjectError('Authored slot inspection requires an existing Proposed palette')
    proposed,_,_=export_texture_png(content,palette_index)
    current=read(project,asset_id,project.texture_additions[asset_id])
    old=validate_added_tim(current)
    current_supported=old.bpp>=16 or old.clut is not None and len(old.clut.data)>=(1<<old.bpp)*2
    before=export_texture_png(current,0)[0] if current_supported else None
    if max(len(proposed),len(before or b''))>8*1024*1024:raise ProjectError('Slot pixel inspection exceeds its PNG budget')
    if source_key(project)!=expected_source_key:raise ProjectError('Authored slot changed during pixel inspection')
    return dict(report=report,palette_index=palette_index,current_palette_index=0,
                current_png_base64=base64.b64encode(before).decode('ascii') if before else None,
                proposed_png_base64=base64.b64encode(proposed).decode('ascii'))


def apply(project,asset_id,content,expected_sha256,expected_source_key,label,accept_potential_overlap,review_key, *, conversion_source=None):
    report=review(project,asset_id,content,expected_sha256,expected_source_key,label,accept_potential_overlap,conversion_source=conversion_source)
    if report['review_key']!=review_key or not report['can_apply']:
        raise ProjectError('Authored slot Apply requires the applicable current review')
    before=deepcopy(project.texture_additions[asset_id]);after=deepcopy(before)
    after.update(asset_sha256=report['proposed_sha256'],byte_length=len(content),label=label,
                 accept_potential_overlap=accept_potential_overlap)
    if before['asset_sha256']!=after['asset_sha256']:after.pop('image_source',None)
    if 'image_source' in report:
        after['image_source']=deepcopy(report['image_source'])
        from .texture_slot_sources import write_recipe
        write_recipe(project,after,conversion_source)
    path=project.root/'Authored'/'Textures'/(after['asset_sha256']+'.tim')
    if not path.resolve().is_relative_to(project.root):raise ProjectError('Edited TIM path escapes the project')
    if path.exists():read(project,asset_id,after)
    else:atomic_write(path,content)
    project.texture_additions[asset_id]=after
    project.undo_stack.append(dict(target='texture_additions',asset_id=asset_id,before=before,after=deepcopy(after)))
    project.redo_stack.clear()
    return dict(report,project_changed=True)
