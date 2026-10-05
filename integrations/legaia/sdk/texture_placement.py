"""Read-only deterministic placement against known static native upload rectangles."""
from hashlib import sha256
from importer.texture_png import decode_png
from .project import ProjectError, digest
from .scene_preview import source_key
from .texture_slots import known_upload_rectangles, native_pack

MAX_PAIR_CHECKS = 1_000_000


def find_placement(width_words, height, palette_words, rectangles):
    """Top/left image preference and bottom/left aligned palette preference."""
    if (type(width_words) is not int or not 1 <= width_words <= 1024 or
            type(height) is not int or not 1 <= height <= 512 or
            type(palette_words) is not int or palette_words not in (0,16,256) or
            not isinstance(rectangles,list) or len(rectangles)>8192):
        raise ProjectError('Texture placement exceeds supported rectangle bounds')
    occupied=[0]*512
    for rectangle in rectangles:
        if (not isinstance(rectangle,(tuple,list)) or len(rectangle)!=4 or
                any(type(n) is not int for n in rectangle)):
            raise ProjectError('Known upload rectangle is malformed')
        x,y,w,h=rectangle
        if x<0 or y<0 or w<1 or h<1 or x+w>1024 or y+h>512:
            raise ProjectError('Known upload leaves VRAM bounds; automatic placement is unavailable')
        mask=((1<<w)-1)<<x
        for row in range(y,y+h):occupied[row]|=mask
    palette=[]
    if palette_words:
        mask=(1<<palette_words)-1
        palette=[(x,y) for y in range(511,-1,-1) for x in range(0,1025-palette_words,16) if not occupied[y]&(mask<<x)]
        if not palette:return dict(status='no_fit',placement=None,pair_checks=0,search_complete=True)
    mask=(1<<width_words)-1;checks=0
    for y in range(513-height):
        union=0
        for row in occupied[y:y+height]:union|=row
        for x in range(1025-width_words):
            if union&(mask<<x):continue
            if not palette_words:
                return dict(status='found',placement=dict(image_x=x,image_y=y,clut_x=0,clut_y=0),pair_checks=0,search_complete=True)
            for cx,cy in palette:
                checks+=1
                if checks>MAX_PAIR_CHECKS:
                    return dict(status='search_budget_exhausted',placement=None,pair_checks=MAX_PAIR_CHECKS,search_complete=False)
                if not(y<=cy<y+height and x<cx+palette_words and cx<x+width_words):
                    return dict(status='found',placement=dict(image_x=x,image_y=y,clut_x=cx,clut_y=cy),pair_checks=checks,search_complete=True)
    return dict(status='no_fit',placement=None,pair_checks=checks,search_complete=True)


def _upload_context(project, asset_id, expected_source_key):
    key=source_key(project)
    if (project.mode!='edit' or key!=expected_source_key or not key or
            not isinstance(asset_id,str)):
        raise ProjectError('Static upload inspection requires the current Edit source')
    excluded=None
    if asset_id.startswith('texture-new://'):
        from .texture_slot_edit import source
        source(project,asset_id,key)
        binding=project.texture_additions[asset_id];anchor=binding['anchor_asset_id'];excluded=asset_id
    elif asset_id.startswith('texture://'):
        anchor=asset_id
    else:
        raise ProjectError('Placement finder requires a source texture pack or current authored slot')
    context=project._texture_context(anchor)
    with context._archive() as archive:
        native_pack(context,archive,anchor)
    return key,context,excluded


def _upload_evidence(rows):
    return [dict(asset_id=owner,kind=kind,rectangle=dict(x=r[0],y=r[1],width_words=r[2],height=r[3])) for owner,kind,r in rows]


def upload_map(project, asset_id, expected_source_key):
    key,context,excluded=_upload_context(project,asset_id,expected_source_key)
    rows=known_upload_rectangles(project,context,exclude_asset_id=excluded)
    if len(rows)>8192:
        raise ProjectError('Static upload map exceeds its rectangle budget')
    evidence=_upload_evidence(rows)
    report=dict(schema_version='legaia.texture-upload-map.v1',read_only=True,project_changed=False,
                project_source_key=key,scene_id=project.active_scene,asset_id=asset_id,excluded_asset_id=excluded,
                coverage='known-static-scene-authored-and-boot-uploads',runtime_residency_verified=False,
                vram_width_words=1024,vram_height=512,known_rectangle_count=len(rows),
                occupancy_sha256=digest(evidence),rectangles=evidence)
    if source_key(project)!=key:
        raise ProjectError('Texture source changed during static upload inspection')
    return report


def suggest(project, asset_id, expected_source_key, png_content, bpp):
    if type(bpp) is not int or bpp not in (4,8,16,24):
        raise ProjectError('Placement finder requires a supported native mode')
    key,context,excluded=_upload_context(project,asset_id,expected_source_key)
    png=decode_png(png_content);width,height=png['width'],png['height']
    if width*bpp%16 or not 1<=width*bpp//16<=1024 or not 1<=height<=512:
        raise ProjectError('PNG dimensions must encode whole native words within VRAM')
    words=width*bpp//16;palette=1<<bpp if bpp<=8 else 0
    if 20+words*height*2+(12+palette*2 if palette else 0)>1024*1024:
        raise ProjectError('Planned TIM exceeds the authored content budget')
    rows=known_upload_rectangles(project,context,exclude_asset_id=excluded)
    result=find_placement(words,height,palette,[row[2] for row in rows])
    evidence=_upload_evidence(rows)
    report=dict(schema_version='legaia.texture-placement.v1',read_only=True,project_changed=False,
                project_source_key=key,scene_id=project.active_scene,asset_id=asset_id,excluded_asset_id=excluded,
                png_sha256=sha256(png_content).hexdigest(),png_byte_length=len(png_content),
                width=width,height=height,bpp=bpp,width_words=words,palette_words=palette,
                coverage='known-static-scene-authored-and-boot-uploads',runtime_residency_verified=False,
                known_rectangle_count=len(rows),occupancy_sha256=digest(evidence),**result,
                limitations=['Only known Current scene, authored slots and boot upload rectangles are excluded.',
                             'A static free region does not establish runtime residency, upload order or material compatibility.',
                             'PNG conversion, pixel/STP validity and native material binding remain separately reviewed.',
                             'No project change or file is published by this placement query.'])
    if source_key(project)!=key:
        raise ProjectError('Texture source changed during placement search')
    return report
