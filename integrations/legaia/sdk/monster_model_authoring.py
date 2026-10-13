"""Source-qualified monster GLB export, Review and retained native Apply."""
from base64 import b64encode,b64decode
from hashlib import sha256
from .project import ProjectError,digest
from .battle_character_resources import _fresh,_disc
from importer import monster_model_authoring as native
from importer.monster_archive import decode_catalog,block
from importer.pipeline import _disc_context
from importer.core import ImportError as NativeError
from importer.serialization import serialize_lzs_decoded

MAX_GLB=8*1024*1024


def snapshot(project,expected_project_path,expected_source_key,asset_id,catalog_source_key):
    if project.mode!='edit':raise ProjectError('Monster model authoring requires Edit mode')
    _fresh(project,expected_project_path,expected_source_key)
    with _disc_context(project.disc_path) as (_,disc,_,archive):
        raw=archive.read_entry(archive.entry(867));catalog=decode_catalog(raw,disc);_disc(project,catalog)
        if catalog['source_key']!=catalog_source_key:raise ProjectError('Monster model catalog changed')
        record=next((r for r in catalog['models'] if r['semantic_id']==asset_id),None)
        if record is None:raise ProjectError('Monster native model owner is unsupported')
        texture=next((r for r in catalog['textures'] if r['model_asset_id']==asset_id),None)
        original,used=block(raw,record['monster_id']);current=original
        if texture:
            from .monster_palettes import compose
            binding=project.monster_palette_overrides.get(texture['semantic_id'])
            if binding:current=compose(original,texture,binding,project)
        from .monster_models import compose as compose_model
        current=compose_model(project,original,catalog,record['monster_id'],current)
    _fresh(project,expected_project_path,expected_source_key)
    return record,texture,original,current,raw,used


def export(project,**context):
    record,texture,original,current,_,_=snapshot(project,**context)
    try:
        at=record['source_record']['byte_offset'];size=record['source_record']['byte_length'];current_sha=sha256(current[at:at+size]).hexdigest()
        content,binding=native.export(current,record,texture,current_sha)
        roundtrip,_=native.convert(current,record,texture,binding,content,current_sha)
        if roundtrip!=current:raise NativeError('Monster authoring GLB failed exact native roundtrip')
    except NativeError as e:raise ProjectError(str(e)) from e
    if len(content)>MAX_GLB:raise ProjectError('Monster authoring GLB exceeds 8 MiB')
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return dict(schema_version='legaia.monster-model-export.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],record=record,binding=binding,glb_base64=b64encode(content).decode(),glb_sha256=sha256(content).hexdigest(),glb_byte_length=len(content),filename=f'monster-{record["monster_id"]}-native-authoring.glb',layer='current_native_authoring',read_only=True,project_changed=False,gameplay_verified=False,**texture_context(project,texture,original,current),**model_context(project,record,original,current))


def model_context(project,record,original,current):
    from copy import deepcopy
    at=record['source_record']['byte_offset'];end=at+record['source_record']['byte_length']
    return dict(model_binding=deepcopy(project.monster_model_overrides.get(record['semantic_id'])),retail_tmd_base64=b64encode(original[at:end]).decode(),current_tmd_base64=b64encode(current[at:end]).decode())


def texture_context(project,texture,original,current):
    from copy import deepcopy
    if texture is None:return dict(texture_record=None,source_pool_base64=None,retail_pool_base64=None,palette_binding=None)
    at=texture['source_record']['byte_offset']
    return dict(texture_record=texture,source_pool_base64=b64encode(current[at:]).decode(),retail_pool_base64=b64encode(original[at:]).decode(),palette_binding=deepcopy(project.monster_palette_overrides.get(texture['semantic_id'])))


def review(project,binding,glb_base64,**context):
    record,texture,original,current,raw,used=snapshot(project,**context)
    if not isinstance(glb_base64,str) or not 1<=len(glb_base64)<=11200000:raise ProjectError('Monster model GLB must be at most 8 MiB')
    try:content=b64decode(glb_base64,validate=True)
    except (ValueError,TypeError) as e:raise ProjectError('Monster GLB needs exact base64 bytes') from e
    if not 28<=len(content)<=MAX_GLB:raise ProjectError('Monster model GLB must be at most 8 MiB')
    try:
        model_at=record['source_record']['byte_offset'];size=record['source_record']['byte_length']
        proposed,projection=native.convert(current,record,texture,binding,content,sha256(current[model_at:model_at+size]).hexdigest())
        at=record['source_record']['compressed_stream_offset'];_,capacity=serialize_lzs_decoded(raw[at:at+used],len(original),proposed,'monster-model')
    except NativeError as e:raise ProjectError(str(e)) from e
    geometry=projection.pop('geometry')
    for crop in geometry['textures']:
        for key in ('rgba','stp'):
            if key in crop:crop[key+'_base64']=b64encode(crop.pop(key)).decode()
    model_at=record['source_record']['byte_offset'];end=model_at+record['source_record']['byte_length']
    value=dict(schema_version='legaia.monster-model-review.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],record=record,binding=binding,input_sha256=sha256(content).hexdigest(),input_byte_length=len(content),projection=projection,capacity=capacity,geometry=geometry,current_tmd_base64=b64encode(current[model_at:end]).decode(),candidate_tmd_base64=b64encode(proposed[model_at:end]).decode(),texture_record=texture,current_pool_base64=b64encode(current[texture['source_record']['byte_offset']:]).decode() if texture else None,layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    value.update(texture_context(project,texture,original,current))
    value.update(model_context(project,record,original,current))
    value['review_key']=digest(value);_fresh(project,context['expected_project_path'],context['expected_source_key']);return value


def apply(project,review_key,**args):
    from copy import deepcopy
    from .monster_models import retain,validate
    value=review(project,**args)
    if value['review_key']!=review_key or value['projection']['source_tmd_sha256']==value['projection']['candidate_tmd_sha256']:raise ProjectError('Monster model Apply requires exact fresh changed Review')
    record,_,original,current,_,_=snapshot(project,**{k:args[k] for k in ('expected_project_path','expected_source_key','asset_id','catalog_source_key')})
    candidate=b64decode(value['candidate_tmd_base64']);content=b64decode(args['glb_base64']);before=deepcopy(project.monster_model_overrides);after=deepcopy(before);old=before.get(record['semantic_id']);inputs=deepcopy(old['inputs']) if old else []
    at=record['source_record']['byte_offset'];retail=original[at:at+len(candidate)]
    if len(inputs)>=16 and candidate!=retail:raise ProjectError('Monster model input chain exceeds sixteen imports')
    inputs.append(dict(glb_sha256=retain(project,content,'glb'),glb_byte_length=len(content),baseline_sha256=retain(project,current,'block'),baseline_byte_length=len(current),binding=deepcopy(value['binding']),candidate_tmd_sha256=sha256(candidate).hexdigest(),review_key=review_key))
    if candidate==retail:after.pop(record['semantic_id'],None)
    else:after[record['semantic_id']]=dict(schema_version='legaia.monster-model-override.v1',asset_id=record['semantic_id'],source_record=deepcopy(record['source_record']),current_tmd_sha256=retain(project,candidate,'tmd'),byte_length=len(candidate),inputs=inputs,edits=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(retail,candidate)) if a!=b])
    validate(project,after);project.monster_model_overrides=after;project.undo_stack.append(dict(target='monster_model_overrides',before=before,after=deepcopy(after),label='Monster native model'));project.redo_stack.clear()
    return dict(history_steps=1,project_changed=True,gameplay_verified=False)
