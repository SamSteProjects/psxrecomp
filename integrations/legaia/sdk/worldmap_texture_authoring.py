"""Kingdom texture bindings reuse project TIM history without field ownership."""
import re
from hashlib import sha256
from .project import ProjectError

OWNERS = {f'worldmap://{scene}/textures': scene for scene in ('map01','map02','map03')}

def scene_for(identifier):
    match = re.fullmatch(r'texture://(map0[123])/kingdom/([0-9]{4,5})', identifier) if isinstance(identifier,str) else None
    if match and identifier == f'texture://{match[1]}/kingdom/{int(match[2]):04d}':
        return match[1]
    return None

def validate(project,binding,identifier=None):
    source = binding.get('source_scene_id') if isinstance(binding,dict) else None
    scene = OWNERS.get(source) if isinstance(source,str) else None
    if (scene is None or binding.get('format') != 'tim' or
            any(not isinstance(binding.get(k),str) or not re.fullmatch('[0-9a-f]{64}',binding[k])
                for k in ('source_disc_sha256','source_sha256')) or
            identifier is not None and scene_for(identifier) != scene):
        raise ProjectError('World TIM binding requires canonical kingdom and immutable Retail hashes')
    identities = {doc['source']['disc_identity'] for doc in project.imports.values()}
    if identities and identities != {'sha256:'+binding['source_disc_sha256']}:
        raise ProjectError('World TIM binding differs from the imported disc')
    return scene

def context(project,identifier):
    scene = scene_for(identifier)
    if not scene or not project.disc_path:
        raise ProjectError('World TIM authoring requires a canonical native texture and source disc')
    from importer.worldmap_texture_authoring import load_worldmap_texture_authoring_context
    result = load_worldmap_texture_authoring_context(project.disc_path,scene)
    original = result.original_tim(identifier)
    disc_hash = result._source(identifier)['disc']['sha256']
    identities = {doc['source']['disc_identity'] for doc in project.imports.values()}
    if identities and identities != {'sha256:'+disc_hash}:
        raise ProjectError('World TIM source differs from the imported disc')
    binding = project.texture_overrides.get(identifier)
    if binding:
        validate(project,binding,identifier)
        if binding['source_disc_sha256'] != disc_hash or binding['source_sha256'] != sha256(original).hexdigest():
            raise ProjectError('World TIM immutable source changed; refresh the project')
    return result


def review_palette(project,request):
    from .worldmap_authoring import state_key
    from .project import digest
    from importer.texture_authoring import patch_tim_palette_word
    fields={'texture_id','source_key','member_sha256','palette_index','entry_index','word','effective_sha256'}
    if not isinstance(request,dict) or set(request)!=fields or project.mode!='edit' or request['source_key']!=state_key(project) or not scene_for(request['texture_id']):
        raise ProjectError('World palette Review requires the exact current Edit source and native texture')
    for key in ('member_sha256','effective_sha256'):
        if not isinstance(request[key],str) or not re.fullmatch('[0-9a-f]{64}',request[key]):
            raise ProjectError('World palette Review requires inspected TIM hashes')
    if type(request['palette_index']) is not int or not 0<=request['palette_index']<=32767:
        raise ProjectError('World palette Review requires an explicit bounded palette index')
    if type(request['entry_index']) is not int or not 0<=request['entry_index']<256 or type(request['word']) is not int or not 0<=request['word']<=65535:
        raise ProjectError('World palette Review requires bounded integer entry and unsigned16 word')
    source=project.texture_palette_source(request['texture_id'],request['palette_index'])
    if source['source_sha256']!=request['member_sha256'] or source['effective_sha256']!=request['effective_sha256'] or request['entry_index']>=source['entry_count']:
        raise ProjectError('World palette source or effective TIM changed; preview Current again')
    ctx=project._texture_context(request['texture_id']);original=ctx.original_tim(request['texture_id'])
    binding=project.texture_overrides.get(request['texture_id'])
    effective=project.read_texture_replacement(binding) if binding else original
    candidate=patch_tim_palette_word(effective,request['effective_sha256'],request['palette_index'],request['entry_index'],request['word'])
    ctx.validate_replacement(request['texture_id'],candidate)
    index=request['entry_index']
    result=dict(schema_version='legaia.worldmap-palette-review.v1',project_path=str(project.root),
        request=dict(request),retail_word=source['retail_words'][index],current_word=source['words'][index],
        candidate_tim_sha256=sha256(candidate).hexdigest(),changed=candidate!=effective,
        scope='existing-TIM-palette-word-only',project_changed=False,gameplay_verified=False)
    result['review_key']=digest(result)
    if project.mode!='edit' or request['source_key']!=state_key(project):
        raise ProjectError('World palette source changed during Review')
    return result


def apply_palette(project,request,review_key):
    receipt=review_palette(project,request)
    if not isinstance(review_key,str) or receipt['review_key']!=review_key:
        raise ProjectError('World palette Apply requires the exact fresh Review receipt')
    project.set_texture_palette_word(request['texture_id'],request['palette_index'],request['entry_index'],request['word'],request['effective_sha256'])
    return receipt


def review_pixel(project,request):
    from .worldmap_authoring import state_key
    from .project import digest
    from importer.texture_authoring import patch_tim_pixel_index
    fields={'texture_id','source_key','member_sha256','palette_index','x','y','palette_entry','effective_sha256'}
    if not isinstance(request,dict) or set(request)!=fields or project.mode!='edit' or request['source_key']!=state_key(project) or not scene_for(request['texture_id']):
        raise ProjectError('World pixel Review requires the exact current Edit source and native texture')
    if any(not isinstance(request[k],str) or not re.fullmatch('[0-9a-f]{64}',request[k]) for k in ('member_sha256','effective_sha256')):
        raise ProjectError('World pixel Review requires inspected TIM hashes')
    if any(type(request[k]) is not int or not 0<=request[k]<=65535 for k in ('x','y')) or type(request['palette_index']) is not int or not 0<=request['palette_index']<=32767 or type(request['palette_entry']) is not int or not 0<=request['palette_entry']<256:
        raise ProjectError('World pixel Review requires bounded integer coordinates, palette and index')
    source=project.texture_pixel_source(request['texture_id'],request['palette_index'],request['x'],request['y'])
    if source['source_sha256']!=request['member_sha256'] or source['effective_sha256']!=request['effective_sha256']:
        raise ProjectError('World pixel source or effective TIM changed; preview Current again')
    ctx=project._texture_context(request['texture_id']);original=ctx.original_tim(request['texture_id']);binding=project.texture_overrides.get(request['texture_id'])
    effective=project.read_texture_replacement(binding) if binding else original
    candidate=patch_tim_pixel_index(effective,request['effective_sha256'],request['x'],request['y'],request['palette_entry']);ctx.validate_replacement(request['texture_id'],candidate)
    result=dict(schema_version='legaia.worldmap-pixel-review.v1',project_path=str(project.root),request=dict(request),retail_index=source['retail_entry'],current_index=source['pixel']['palette_entry'],bpp=source['pixel']['bpp'],candidate_tim_sha256=sha256(candidate).hexdigest(),changed=candidate!=effective,scope='existing-TIM-indexed-pixel-only',project_changed=False,gameplay_verified=False)
    result['review_key']=digest(result)
    if project.mode!='edit' or request['source_key']!=state_key(project):raise ProjectError('World pixel source changed during Review')
    return result


def apply_pixel(project,request,review_key):
    receipt=review_pixel(project,request)
    if not isinstance(review_key,str) or receipt['review_key']!=review_key:raise ProjectError('World pixel Apply requires the exact fresh Review receipt')
    project.set_texture_pixel_index(request['texture_id'],request['x'],request['y'],request['palette_entry'],request['effective_sha256'])
    return receipt


def _review_region(project, request, copy=False):
    """Qualify a region edit against inspected Current bytes without changing the project."""
    from .worldmap_authoring import state_key
    from .project import digest
    from importer.texture_authoring import patch_tim_index_rectangle, copy_tim_index_rectangle, texture_payload_changes
    fields = {'texture_id','source_key','member_sha256','palette_index','x','y','width','height','palette_entry','effective_sha256'}
    if copy:fields = (fields-{'palette_entry'}) | {'source_x','source_y'}
    if not isinstance(request,dict) or set(request)!=fields or project.mode!='edit' or request['source_key']!=state_key(project) or not scene_for(request['texture_id']):
        raise ProjectError('World rectangle Review requires the exact current Edit source and native texture')
    if any(not isinstance(request[k],str) or not re.fullmatch('[0-9a-f]{64}',request[k]) for k in ('member_sha256','effective_sha256')):
        raise ProjectError('World rectangle Review requires inspected TIM hashes')
    if any(type(request[k]) is not int or not 0<=request[k]<=65535 for k in (('x','y','source_x','source_y') if copy else ('x','y'))) or any(type(request[k]) is not int or not 1<=request[k]<=65535 for k in ('width','height')) or type(request['palette_index']) is not int or not 0<=request['palette_index']<=32767 or (not copy and (type(request['palette_entry']) is not int or not 0<=request['palette_entry']<256)):
        raise ProjectError('World rectangle Review requires bounded integer coordinates, dimensions and index')
    source = project.texture_pixel_source(request['texture_id'],request['palette_index'],request['x'],request['y'])
    if source['source_sha256']!=request['member_sha256'] or source['effective_sha256']!=request['effective_sha256']:
        raise ProjectError('World rectangle source or effective TIM changed; preview Current again')
    ctx = project._texture_context(request['texture_id'])
    original = ctx.original_tim(request['texture_id'])
    binding = project.texture_overrides.get(request['texture_id'])
    effective = project.read_texture_replacement(binding) if binding else original
    candidate = (copy_tim_index_rectangle(effective,request['effective_sha256'],request['source_x'],request['source_y'],request['x'],request['y'],request['width'],request['height']) if copy else patch_tim_index_rectangle(effective,request['effective_sha256'],request['x'],request['y'],request['width'],request['height'],request['palette_entry']))
    ctx.validate_replacement(request['texture_id'],candidate)
    changes = texture_payload_changes(effective,candidate)
    result = dict(schema_version='legaia.worldmap-copy-review.v1' if copy else 'legaia.worldmap-rectangle-review.v1',project_path=str(project.root),request=dict(request),bpp=source['pixel']['bpp'],changed_pixel_count=changes['pixel_indices_changed'],candidate_tim_sha256=sha256(candidate).hexdigest(),changed=candidate!=effective,scope='existing-TIM-indexed-copy-only' if copy else 'existing-TIM-indexed-rectangle-only',project_changed=False,gameplay_verified=False)
    result['review_key'] = digest(result)
    if project.mode!='edit' or request['source_key']!=state_key(project):
        raise ProjectError('World rectangle source changed during Review')
    return result


def review_rectangle(project,request):
    return _review_region(project,request)


def review_copy(project,request):
    return _review_region(project,request,copy=True)


def apply_copy(project,request,review_key):
    receipt = review_copy(project,request)
    if not isinstance(review_key,str) or receipt['review_key']!=review_key:
        raise ProjectError('World rectangle copy Apply requires the exact fresh Review receipt')
    project.copy_texture_index_rectangle(request['texture_id'],request['source_x'],request['source_y'],request['x'],request['y'],request['width'],request['height'],request['effective_sha256'])
    return receipt


def apply_rectangle(project,request,review_key):
    receipt = review_rectangle(project,request)
    if not isinstance(review_key,str) or receipt['review_key']!=review_key:
        raise ProjectError('World rectangle Apply requires the exact fresh Review receipt')
    project.set_texture_index_rectangle(request['texture_id'],request['x'],request['y'],request['width'],request['height'],request['palette_entry'],request['effective_sha256'])
    return receipt


def _replacement_inputs(project,request):
    import base64
    from .worldmap_authoring import state_key
    fields={'texture_id','source_key','member_sha256','effective_sha256','palette_index','content_base64'}
    if not isinstance(request,dict) or set(request)!=fields or project.mode!='edit' or request['source_key']!=state_key(project) or not scene_for(request['texture_id']):
        raise ProjectError('World TIM replacement requires the exact current Edit source')
    if any(not isinstance(request[k],str) or not re.fullmatch('[0-9a-f]{64}',request[k]) for k in ('member_sha256','effective_sha256')) or type(request['palette_index']) is not int or not 0<=request['palette_index']<=32767:
        raise ProjectError('World TIM replacement requires inspected hashes and an explicit palette')
    encoded=request['content_base64']
    if not isinstance(encoded,str) or not 1<=len(encoded)<=1398104:
        raise ProjectError('World TIM replacement exceeds its 1 MiB file budget')
    try:content=base64.b64decode(encoded,validate=True)
    except ValueError as exc:raise ProjectError('World TIM replacement requires valid base64') from exc
    if not 1<=len(content)<=1048576 or base64.b64encode(content).decode('ascii')!=encoded:
        raise ProjectError('World TIM replacement requires bounded canonical base64 bytes')
    ctx,original,effective=_inspected_current(project,request)
    ctx.validate_replacement(request['texture_id'],content)
    return content,effective


def review_replacement(project,request):
    import base64
    from .project import digest
    from .worldmap_authoring import state_key
    from importer.texture_authoring import texture_payload_changes
    from importer.textures import parse_tim,decode_tim
    content,effective=_replacement_inputs(project,request)
    tim=parse_tim(content);count=len(tim.clut.data)//((1<<tim.bpp)*2) if tim.bpp<=8 and tim.clut else 0 if tim.bpp<=8 else 1
    if request['palette_index']>=max(1,count):raise ProjectError('Replacement preview palette is unavailable')
    if not 0<tim.width*tim.image.height<=2097152:raise ProjectError('Replacement preview exceeds its pixel budget')
    rgba=stp=b''
    if count:
        pixels=decode_tim(tim,request['palette_index']);rgba=pixels['rgba'];stp=pixels['stp']
    changes=texture_payload_changes(effective,content)
    result=dict(schema_version='legaia.worldmap-replacement-review.v1',project_path=str(project.root),request={k:v for k,v in request.items() if k!='content_base64'},candidate_tim_sha256=sha256(content).hexdigest(),byte_length=len(content),bpp=tim.bpp,width=tim.width,height=tim.image.height,palette_count=count,changed=content!=effective,changed_pixel_count=changes['pixel_indices_changed'],changed_palette_words=changes['palette_words_changed'],changed_image_bytes=changes['image_bytes_changed'],rgba_base64=base64.b64encode(rgba).decode('ascii'),stp_base64=base64.b64encode(stp).decode('ascii'),rgba_sha256=sha256(rgba).hexdigest(),stp_sha256=sha256(stp).hexdigest(),scope='existing-TIM-exact-layout-replacement',project_changed=False,gameplay_verified=False)
    result['review_key']=digest(result)
    if project.mode!='edit' or request['source_key']!=state_key(project):raise ProjectError('World TIM source changed during replacement Review')
    return result


def apply_replacement(project,request,review_key):
    receipt=review_replacement(project,request)
    if not isinstance(review_key,str) or receipt['review_key']!=review_key:raise ProjectError('World TIM replacement Apply requires the exact fresh Review receipt')
    if receipt['changed']:
        import base64
        project.set_texture_replacement(request['texture_id'],base64.b64decode(request['content_base64'],validate=True))
    return receipt


def _inspected_current(project,request):
    ctx=project._texture_context(request['texture_id']);original=ctx.original_tim(request['texture_id'])
    binding=project.texture_overrides.get(request['texture_id']);effective=project.read_texture_replacement(binding) if binding else original
    if sha256(original).hexdigest()!=request['member_sha256'] or sha256(effective).hexdigest()!=request['effective_sha256']:
        raise ProjectError('World TIM replacement source changed; preview Current again')
    ctx.validate_replacement(request['texture_id'],effective)
    return ctx,original,effective


def tim_source(project,request):
    """Return freshly qualified Retail or Current bytes without changing the project."""
    import base64
    from .worldmap_authoring import state_key
    fields={'texture_id','source_key','member_sha256','effective_sha256','layer'}
    if not isinstance(request,dict) or set(request)!=fields or project.mode!='edit' or request['source_key']!=state_key(project) or not scene_for(request['texture_id']) or request['layer'] not in ('retail','current'):
        raise ProjectError('World TIM download requires the exact current Edit source and layer')
    if any(not isinstance(request[k],str) or not re.fullmatch('[0-9a-f]{64}',request[k]) for k in ('member_sha256','effective_sha256')):
        raise ProjectError('World TIM download requires inspected source and Current hashes')
    _,original,effective=_inspected_current(project,request)
    content=original if request['layer']=='retail' else effective
    if not 1<=len(content)<=2097152:raise ProjectError('World TIM download exceeds its 2 MiB native source budget')
    result=dict(schema_version='legaia.worldmap-tim-source.v1',project_path=str(project.root),request=dict(request),tim_sha256=sha256(content).hexdigest(),byte_length=len(content),tim_base64=base64.b64encode(content).decode('ascii'),read_only=True,project_changed=False,gameplay_verified=False)
    if project.mode!='edit' or request['source_key']!=state_key(project):raise ProjectError('World TIM source changed during download')
    return result
