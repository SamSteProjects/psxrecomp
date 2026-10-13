"""Fresh pack Current/export/Review/Apply with retained native model history."""
from base64 import b64encode,b64decode
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError,digest,canonical
from .battle_character_resources import _fresh,_disc
from .battle_pack_models import effective,compose,retain,validate,MAX_INPUT
from importer import battle_pack_model_authoring as native
from importer.pipeline import _disc_context
from importer.battle_character_catalog import decode_catalog
from importer.core import ImportError as NativeError


def snapshot(project,expected_project_path,expected_source_key,asset_id,catalog_source_key):
    if project.mode!='edit':raise ProjectError('Battle pack model authoring requires Edit mode')
    _fresh(project,expected_project_path,expected_source_key)
    with _disc_context(project.disc_path) as (_,disc,_,archive):
        original=archive.read_entry(archive.entry(1204));catalog=decode_catalog(original,disc);_disc(project,catalog)
        if catalog['source_key']!=catalog_source_key:raise ProjectError('Battle pack model catalogue changed')
        record=next((r for r in catalog['models'] if r['semantic_id']==asset_id),None)
        if record is None:raise ProjectError('Choose an existing bounded battle pack model')
        body=effective(project,original,catalog,record);current=compose(project,original,catalog)
        from .battle_pack_palettes import compose as palettes
        current=palettes(project,original,catalog,current)
    _fresh(project,expected_project_path,expected_source_key)
    return original,catalog,record,body,current


def _geometry(value):
    result=deepcopy(value)
    for texture in result['textures']:
        for field in ('rgba','stp'):
            if field in texture:texture[field+'_base64']=b64encode(texture.pop(field)).decode()
    return result


def current(project,**context):
    original,catalog,record,body,entry=snapshot(project,**context)
    from .battle_pack_palettes import texture_entry,context as palette_context
    _,geometry=native.source(original,record,catalog,body,texture_entry(project,original,catalog));at=record['source_record']['byte_offset']
    value=dict(schema_version='legaia.battle-pack-model-current.v1',project_path=str(project.root),
        project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],
        record=record,model_binding=deepcopy(project.battle_pack_model_overrides.get(record['semantic_id'])),
        current_tmd_sha256=sha256(body).hexdigest(),current_entry_sha256=sha256(entry).hexdigest(),
        current_tmd_base64=b64encode(body).decode(),retail_tmd_base64=b64encode(original[at:at+len(body)]).decode(),
        geometry=_geometry(geometry),**palette_context(project,original,catalog),layer='current',read_only=True,project_changed=False,gameplay_verified=False)
    _fresh(project,context['expected_project_path'],context['expected_source_key']);return value


def export(project,**context):
    original,catalog,record,body,entry=snapshot(project,**context)
    from .battle_pack_palettes import texture_entry
    try:content,binding=native.export(original,record,catalog,body,texture_entry(project,original,catalog))
    except NativeError as error:raise ProjectError(str(error)) from error
    if len(content)>MAX_INPUT:raise ProjectError('Battle pack authoring GLB exceeds8MiB')
    value=dict(schema_version='legaia.battle-pack-model-export.v1',project_path=str(project.root),
        project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],
        record=record,binding=binding,current_entry_sha256=sha256(entry).hexdigest(),
        current_tmd_base64=b64encode(body).decode(),glb_base64=b64encode(content).decode(),
        glb_sha256=sha256(content).hexdigest(),glb_byte_length=len(content),
        filename=f'battle-pack-{record["pool_index"]}-native-authoring.glb',layer='current_native_authoring',
        read_only=True,project_changed=False,gameplay_verified=False)
    _fresh(project,context['expected_project_path'],context['expected_source_key']);return value


def review(project,binding,glb_base64,expected_current_entry_sha256,**context):
    original,catalog,record,body,current_entry=snapshot(project,**context)
    if sha256(current_entry).hexdigest()!=expected_current_entry_sha256:
        raise ProjectError('Battle pack composed Current entry changed; inspect again')
    if not isinstance(glb_base64,str) or len(glb_base64)>4*((MAX_INPUT+2)//3):
        raise ProjectError('Battle pack GLB exceeds8MiB')
    try:content=b64decode(glb_base64,validate=True)
    except (TypeError,ValueError) as error:raise ProjectError('Battle pack GLB requires canonical base64') from error
    if not 28<=len(content)<=MAX_INPUT or b64encode(content).decode()!=glb_base64:
        raise ProjectError('Battle pack GLB byte coverage is invalid')
    try:candidate,projection=native.convert(original,record,catalog,binding,content,body)
    except NativeError as error:raise ProjectError(str(error)) from error
    from .battle_pack_palettes import texture_entry
    _,geometry=native.source(original,record,catalog,candidate,texture_entry(project,original,catalog))
    projection['geometry']=_geometry(geometry)
    at=record['source_record']['byte_offset'];end=at+len(candidate)
    if candidate!=body:
        retail=original[at:end];sizes={}
        for identifier,owner in project.battle_pack_model_overrides.items():
            if identifier==record['semantic_id'] and candidate==retail:continue
            for receipt in owner['inputs']:sizes[('glb',receipt['glb_sha256'])]=receipt['glb_byte_length']
            if identifier!=record['semantic_id']:sizes[('tmd',owner['current_tmd_sha256'])]=owner['byte_length']
        if candidate!=retail:
            inputs=project.battle_pack_model_overrides.get(record['semantic_id'],{}).get('inputs',[])
            if len(inputs)>=16:raise ProjectError('Battle pack model exceeds sixteen retained imports')
            sizes[('glb',sha256(content).hexdigest())]=len(content)
            sizes[('tmd',sha256(candidate).hexdigest())]=len(candidate)
        if sum(sizes.values())>64*1024*1024:raise ProjectError('Battle pack active inputs exceed64MiB')
    entry=current_entry[:at]+candidate+current_entry[end:]
    value=dict(schema_version='legaia.battle-pack-model-review.v1',project_path=str(project.root),
        project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],
        record=record,binding=deepcopy(binding),model_binding=deepcopy(project.battle_pack_model_overrides.get(record['semantic_id'])),
        input_sha256=sha256(content).hexdigest(),input_byte_length=len(content),projection=projection,
        current_tmd_base64=b64encode(body).decode(),candidate_tmd_base64=b64encode(candidate).decode(),
        current_entry_sha256=sha256(current_entry).hexdigest(),candidate_entry_sha256=sha256(entry).hexdigest(),
        current_entry_base64=b64encode(current_entry).decode(),candidate_entry_base64=b64encode(entry).decode(),
        unchanged_neighbors_sha256=sha256(current_entry[:at]+current_entry[end:]).hexdigest(),
        layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    encoded=canonical(value);value['review_key']=sha256(encoded).hexdigest()
    value['review_receipt_base64']=b64encode(encoded).decode()
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return value


def apply(project,review_key,**args):
    value=review(project,**args)
    if value['review_key']!=review_key or not value['projection']['changes']:
        raise ProjectError('Battle pack model Apply requires an exact fresh changed Review')
    context={k:args[k] for k in ('expected_project_path','expected_source_key','asset_id','catalog_source_key')}
    original,catalog,record,body,_=snapshot(project,**context)
    before=deepcopy(project.battle_pack_model_overrides);after=deepcopy(before)
    candidate=b64decode(value['candidate_tmd_base64']);at=record['source_record']['byte_offset'];retail=original[at:at+len(candidate)]
    inputs=deepcopy(before.get(record['semantic_id'],{}).get('inputs',[]))
    if candidate!=retail and len(inputs)>=16:raise ProjectError('Battle pack model exceeds sixteen retained imports')
    content=b64decode(args['glb_base64']);key=retain(project,content,'glb')
    if candidate==retail:after.pop(record['semantic_id'],None)
    else:
        inputs.append(dict(glb_sha256=key,glb_byte_length=len(content),base_tmd_sha256=sha256(body).hexdigest(),
            candidate_tmd_sha256=sha256(candidate).hexdigest(),binding=deepcopy(value['binding']),review_key=review_key))
        after[record['semantic_id']]=dict(schema_version='legaia.battle-pack-model-override.v1',
            asset_id=record['semantic_id'],source_record=deepcopy(record['source_record']),
            current_tmd_sha256=retain(project,candidate,'tmd'),byte_length=len(candidate),inputs=inputs,
            edits=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(retail,candidate)) if a!=b])
    validate(project,after);_fresh(project,context['expected_project_path'],context['expected_source_key'])
    project.battle_pack_model_overrides=after
    project.undo_stack.append(dict(target='battle_pack_model_overrides',before=before,after=deepcopy(after),label='Battle Pack Native Model'))
    project.redo_stack.clear()
    return dict(schema_version='legaia.battle-pack-model-apply.v1',asset_id=record['semantic_id'],
        history_steps=1,project_changed=True,gameplay_verified=False)
