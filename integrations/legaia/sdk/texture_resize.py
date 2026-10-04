"""Reviewed image allocation; static overlaps are evidence, not upload-order proof."""
from hashlib import sha256

from .project import ProjectError,digest
from .scene_preview import source_key


def image_layout(content):
    from importer.textures import parse_tim
    tim=parse_tim(content)
    return dict(bpp=tim.bpp,x=tim.image.x,y=tim.image.y,width=tim.width,
                height=tim.image.height,width_words=tim.image.width_words)


def validate_binding(binding):
    row=binding.get('image_layout');source=binding.get('source_sha256')
    if (not isinstance(source,str) or len(source)!=64 or any(c not in '0123456789abcdef' for c in source) or
            not isinstance(row,dict) or set(row)!={'bpp','x','y','width','height','width_words'} or
            any(type(v) is not int for v in row.values()) or row['bpp'] not in (4,8,16,24) or
            not 0<=row['x']<1024 or not 0<=row['y']<512 or not 1<=row['height']<=512 or
            not 1<=row['width_words']<=1024 or row['width']*row['bpp']!=row['width_words']*16 or
            row['x']+row['width_words']>1024 or row['y']+row['height']>512):
        raise ProjectError('Invalid authored texture image allocation binding')


def _area(a,b):
    return max(0,min(a[0]+a[2],b[0]+b[2])-max(a[0],b[0]))*max(0,min(a[1]+a[3],b[1]+b[3])-max(a[1],b[1]))


def footprint_report(project,context,asset_id,current,candidate):
    from importer.textures import parse_tim
    old,new=parse_tim(current),parse_tim(candidate)
    before=(old.image.x,old.image.y,old.image.width_words,old.image.height)
    proposed=(new.image.x,new.image.y,new.image.width_words,new.image.height)
    shared=(before[0],before[1],min(before[2],proposed[2]),min(before[3],proposed[3]))
    rows=[];count=0;examined=0
    def inspect(rect,owner,kind,boot_index=None):
        nonlocal count,examined
        examined+=1;added=_area(proposed,rect)-_area(shared,rect)
        if added:
            count+=1
            if len(rows)<64:rows.append(dict(asset_id=owner,kind=kind,boot_upload_index=boot_index,
                rectangle=dict(x=rect[0],y=rect[1],width_words=rect[2],height=rect[3]),
                added_overlap_words=added))
    for tim,source in context._catalog.textures:
        owner=source['semantic_id'];binding=project.texture_overrides.get(owner)
        if binding:
            content=project.read_texture_replacement(binding)
            project.validate_effective_texture(owner,content,context=context)
            effective=parse_tim(content)
        else:effective=tim
        if owner!=asset_id:inspect((effective.image.x,effective.image.y,effective.image.width_words,effective.image.height),owner,'image')
        if effective.clut:inspect((effective.clut.x,effective.clut.y,effective.clut.width_words*effective.clut.height,1),owner,'flattened-clut')
    from .texture_slots import read
    for owner,binding in getattr(project,'texture_additions',{}).items():
        if binding['source_scene_id']!=project.active_scene:continue
        effective=parse_tim(read(project,owner,binding))
        inspect((effective.image.x,effective.image.y,effective.image.width_words,effective.image.height),owner,'image')
        if effective.clut:inspect((effective.clut.x,effective.clut.y,effective.clut.width_words*effective.clut.height,1),owner,'flattened-clut')
    for index,(block,_) in enumerate(context._catalog.boot_uploads):
        inspect((block.x,block.y,block.width_words,block.height),None,'boot-upload',index)
    return dict(schema_version='legaia.texture-footprint.v1',examined_upload_count=examined,
                potential_overlap_count=count,rows=rows,rows_truncated=count>len(rows),
                coverage='known-static-scene-and-boot-uploads',runtime_residency_verified=False)


def _prepare(project,asset_id,expected_sha256,expected_source_key,width,height,fill_value,accept_potential_overlap,resize_mode="crop-fill"):
    from importer.texture_layout_allocation import resize_tim_image
    if project.mode!='edit' or type(accept_potential_overlap) is not bool:
        raise ProjectError('Texture resize requires Edit mode and an explicit overlap choice')
    key=source_key(project)
    if not key or key!=expected_source_key:
        raise ProjectError('Texture source context changed; review resizing again')
    context=project._texture_context(asset_id);original=context.original_tim(asset_id)
    binding=project.texture_overrides.get(asset_id)
    current=project.read_texture_replacement(binding) if binding else original
    project.validate_effective_texture(asset_id,current,context=context)
    candidate,allocation=resize_tim_image(current,expected_sha256,width,height,fill_value,resize_mode)
    footprint=footprint_report(project,context,asset_id,current,candidate)
    report=dict(schema_version='legaia.texture-resize-review.v1',asset_id=asset_id,project_source_key=key,
                retail_sha256=sha256(original).hexdigest(),effective_sha256=sha256(current).hexdigest(),
                proposed_sha256=sha256(candidate).hexdigest(),width=width,height=height,fill_value=fill_value,resize_mode=resize_mode,
                current_layout=image_layout(current),proposed_layout=image_layout(candidate),
                allocation=allocation,footprint=footprint,accept_potential_overlap=accept_potential_overlap,
                can_apply=allocation['changed'] and (not footprint['potential_overlap_count'] or accept_potential_overlap),
                project_changed=False,gameplay_verified=False)
    report['review_key']=digest(report)
    if source_key(project)!=key:raise ProjectError('Texture source changed during resize review')
    return candidate,report


def review(project,asset_id,expected_sha256,expected_source_key,width,height,fill_value=0,accept_potential_overlap=False,resize_mode="crop-fill"):
    return _prepare(project,asset_id,expected_sha256,expected_source_key,width,height,fill_value,accept_potential_overlap,resize_mode)[1]


def source(project,asset_id,expected_source_key):
    from importer.textures import parse_tim
    key=source_key(project)
    if project.mode!='edit' or not key or key!=expected_source_key:
        raise ProjectError('Texture resize source requires the current Edit context')
    context=project._texture_context(asset_id);original=context.original_tim(asset_id)
    binding=project.texture_overrides.get(asset_id)
    current=project.read_texture_replacement(binding) if binding else original
    project.validate_effective_texture(asset_id,current,context=context)
    tim=parse_tim(current)
    report=dict(schema_version='legaia.texture-resize-source.v1',asset_id=asset_id,project_source_key=key,
        retail_sha256=sha256(original).hexdigest(),effective_sha256=sha256(current).hexdigest(),
        current_layout=image_layout(current),byte_length=len(current),
        palette_count=len(tim.clut.data)//((1<<tim.bpp)*2) if tim.bpp in (4,8) and tim.clut else 0,
        read_only=True,project_changed=False)
    if source_key(project)!=key:raise ProjectError('Texture source changed during resize inspection')
    return report


def reviewed(project,asset_id,expected_sha256,expected_source_key,width,height,fill_value,accept_potential_overlap,review_key,resize_mode="crop-fill"):
    candidate,report=_prepare(project,asset_id,expected_sha256,expected_source_key,width,height,fill_value,accept_potential_overlap,resize_mode)
    if report['review_key']!=review_key:
        raise ProjectError('Texture resize proposal changed; review again before inspection')
    return candidate,report


def pixels(project,asset_id,expected_sha256,expected_source_key,width,height,fill_value,accept_potential_overlap,review_key,palette_index,resize_mode="crop-fill"):
    import base64
    from importer.texture_png import export_texture_png
    from .texture_png import _json_size,MAX_PNG_BYTES
    candidate,report=reviewed(project,asset_id,expected_sha256,expected_source_key,width,height,fill_value,accept_potential_overlap,review_key,resize_mode)
    if type(palette_index) is not int or not 0<=palette_index<=32767:
        raise ProjectError('Resize pixel inspection requires an existing integer palette')
    binding=project.texture_overrides.get(asset_id)
    current=project.read_texture_replacement(binding) if binding else project._texture_context(asset_id).original_tim(asset_id)
    if sha256(current).hexdigest()!=expected_sha256:raise ProjectError('Texture changed during resize pixel inspection')
    current_png,_,_=export_texture_png(current,palette_index)
    proposed_png,_,_=export_texture_png(candidate,palette_index)
    if max(len(current_png),len(proposed_png))>MAX_PNG_BYTES:
        raise ProjectError('Resize pixel PNG exceeds the inspection byte budget')
    result=dict(report=report,palette_index=palette_index,current_png_base64=base64.b64encode(current_png).decode('ascii'),
                proposed_png_base64=base64.b64encode(proposed_png).decode('ascii'))
    _json_size(result,24*1024*1024,'Texture resize pixel preview')
    if source_key(project)!=expected_source_key:raise ProjectError('Texture source changed during resize pixel inspection')
    return result


def apply(project,asset_id,expected_sha256,expected_source_key,width,height,fill_value,accept_potential_overlap,review_key,resize_mode="crop-fill"):
    candidate,report=_prepare(project,asset_id,expected_sha256,expected_source_key,width,height,fill_value,accept_potential_overlap,resize_mode)
    if report['review_key']!=review_key or not report['can_apply']:
        raise ProjectError('Texture resize requires an applicable current review and the reviewed overlap choice')
    if report['proposed_sha256']==report['retail_sha256']:
        project.command(dict(type='clear_texture_replacement',asset_id=asset_id))
    else:
        project.set_texture_replacement(asset_id,candidate,image_allocation=True)
    return dict(report,project_changed=True)
