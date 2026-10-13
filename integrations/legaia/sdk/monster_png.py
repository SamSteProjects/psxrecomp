"""Fresh PNG conversion, immutable original inputs and native pool publication."""
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
from base64 import b64decode,b64encode
import struct,re
from importer.monster_png import export as export_png,convert
from importer.serialization import serialize_lzs_decoded
from importer.core import ImportError as NativeError
from .project import ProjectError,atomic_write,digest
from .battle_character_resources import _fresh


def path(project,key,suffix):
    if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key) or suffix not in ('png','pool','idx'):raise ProjectError('Monster image input identity changed')
    target=project.root/'Authored'/'MonsterTextureInputs'/(key+'.'+suffix)
    if not target.resolve().is_relative_to(project.root.resolve()):raise ProjectError('Monster image input escapes project root')
    return target


def retain(project,content,suffix):
    key=sha256(content).hexdigest();target=path(project,key,suffix)
    if target.exists():
        if target.read_bytes()!=content:raise ProjectError('Monster retained input changed')
    else:atomic_write(target,content)
    return key


def read(project,key,size,suffix):
    target=path(project,key,suffix);limit=8*1024*1024 if suffix=='png' else 33248
    if type(size) is not int or not 1<=size<=limit or not target.is_file() or target.stat().st_size!=size:raise ProjectError('Monster retained input missing or changed size')
    content=target.read_bytes()
    if sha256(content).hexdigest()!=key:raise ProjectError('Monster retained input hash changed')
    return content


def validate_input(project,record,receipt):
    keys={'schema_version','asset_id','png_sha256','png_byte_length','stp_sha256','stp_byte_length','baseline_sha256','baseline_byte_length','palette_index','palette_mode','candidate_pool_sha256'}
    if not isinstance(receipt,dict) or set(receipt)!=keys or receipt['schema_version']!='legaia.monster-png-input.v1' or receipt['asset_id']!=record['semantic_id'] or type(receipt['palette_index']) is not int or not 0<=receipt['palette_index']<15 or receipt['palette_mode'] not in ('existing','rebuild') or (receipt['stp_sha256'] is None)!=(receipt['stp_byte_length'] is None):raise ProjectError('Monster PNG provenance changed')
    png=read(project,receipt['png_sha256'],receipt['png_byte_length'],'png');baseline=read(project,receipt['baseline_sha256'],receipt['baseline_byte_length'],'pool');stp=read(project,receipt['stp_sha256'],receipt['stp_byte_length'],'png') if receipt['stp_sha256'] is not None else None
    try:candidate,_=convert(baseline,record['width'],receipt['palette_index'],png,receipt['palette_mode'],stp)
    except NativeError as e:raise ProjectError('Monster original PNG conversion cannot replay') from e
    if sha256(candidate).hexdigest()!=receipt['candidate_pool_sha256']:raise ProjectError('Monster PNG import replay hash changed')
    return png,stp,baseline


def download(project,expected_project_path,expected_source_key,asset_id,palette_index,expected_current_sha256):
    from .monster_palettes import snapshot
    _fresh(project,expected_project_path,expected_source_key);catalog,record,_,current,_,_=snapshot(project,asset_id);pool=current[record['source_record']['byte_offset']:]
    if sha256(pool).hexdigest()!=expected_current_sha256:raise ProjectError('Monster pool changed; inspect again')
    try:png,stp,profile=export_png(pool,record['width'],palette_index)
    except NativeError as e:raise ProjectError(str(e)) from e
    _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.monster-png-download.v1',project_path=str(project.root),project_source_key=expected_source_key,asset_id=asset_id,palette_index=palette_index,current_pool_sha256=expected_current_sha256,png_base64=b64encode(png).decode(),stp_base64=b64encode(stp).decode(),png_sha256=sha256(png).hexdigest(),stp_sha256=sha256(stp).hexdigest(),filename=f'monster-{record["monster_id"]}-palette-{palette_index}.png',adapter='derived_TIM_converter_coordinates_not_native_VRAM',layer='current',read_only=True,project_changed=False,gameplay_verified=False)


def input_bytes(value):
    if not isinstance(value,str) or not 1<=len(value)<=11200000:raise ProjectError('Monster PNG input must be at most 8 MiB')
    try:content=b64decode(value,validate=True)
    except (ValueError,TypeError) as e:raise ProjectError('Monster PNG input needs exact base64 bytes') from e
    if not 1<=len(content)<=8*1024*1024:raise ProjectError('Monster PNG input must be at most 8 MiB')
    return content


def records(project,catalog):
    """Active original inputs are metadata assets, distinct from Current pixels."""
    from importer.pipeline import _disc_context
    from importer.monster_archive import block
    from .monster_palettes import compose
    rows=[]
    owners={k:v for k,v in project.monster_palette_overrides.items() if 'png_import' in v}
    if not owners:return rows
    with _disc_context(project.disc_path) as (_,_,_,archive):
        raw=archive.read_entry(archive.entry(867))
        for identifier,binding in sorted(owners.items()):
            record=next((r for r in catalog['textures'] if r['semantic_id']==identifier),None)
            if record is None:raise ProjectError('Monster retained input owner is missing')
            original,_=block(raw,record['monster_id']);compose(original,record,binding,project)
            receipt=binding['png_import']
            for kind in ('png','stp'):
                key=receipt[kind+'_sha256']
                if key is None:continue
                rows.append(dict(semantic_id=f'retained-texture://legaia/monster-archive/{record["monster_id"]:04d}/{kind}/{key}',name=f'Monster {record["monster_id"]} Original '+('PNG Input' if kind=='png' else 'STP Mask Input'),asset_kind='retained_monster_png',kind=kind,layer='historical_authored_input',texture_asset_id=identifier,sha256=key,byte_length=receipt[kind+'_byte_length'],source_record=deepcopy(receipt),retail_source=deepcopy(record['source_record']),references=[identifier],current_pool_sha256=binding['current_pool_sha256'],relationship='historical_import_input_not_final_current_texture',read_only=True,gameplay_verified=False))
    return rows


def download_input(project,expected_project_path,expected_source_key,asset_id,expected_current_sha256,kind):
    from .monster_palettes import snapshot
    if kind not in ('png','stp'):raise ProjectError('Choose original monster PNG or STP mask')
    _fresh(project,expected_project_path,expected_source_key)
    _,record,_,current,_,_=snapshot(project,asset_id)
    pool=current[record['source_record']['byte_offset']:]
    if sha256(pool).hexdigest()!=expected_current_sha256:raise ProjectError('Monster Current pool changed; refresh its input')
    receipt=project.monster_palette_overrides.get(asset_id,{}).get('png_import')
    if receipt is None:raise ProjectError('Monster pool has no retained PNG input')
    png,stp,_=validate_input(project,record,receipt);content=png if kind=='png' else stp
    if content is None:raise ProjectError('Monster PNG import used no explicit STP mask')
    _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.monster-input-download.v1',project_path=str(project.root),project_source_key=expected_source_key,asset_id=asset_id,current_pool_sha256=expected_current_sha256,kind=kind,sha256=sha256(content).hexdigest(),byte_length=len(content),png_base64=b64encode(content).decode(),filename=f'monster-{record["monster_id"]}-original-{kind}.png',retained_source=deepcopy(receipt),layer='historical_authored_input',read_only=True,project_changed=False,gameplay_verified=False)


def review(project,expected_project_path,expected_source_key,asset_id,palette_index,expected_current_sha256,png_base64,palette_mode,stp_base64=None):
    from .monster_palettes import snapshot
    if project.mode!='edit':raise ProjectError('Monster image authoring requires Edit mode')
    _fresh(project,expected_project_path,expected_source_key);png=input_bytes(png_base64);stp=input_bytes(stp_base64) if stp_base64 is not None else None
    catalog,record,original,current,raw,used=snapshot(project,asset_id);at=record['source_record']['byte_offset'];pool=current[at:]
    if sha256(pool).hexdigest()!=expected_current_sha256:raise ProjectError('Monster Current pool changed; inspect again')
    try:candidate,analysis=convert(pool,record['width'],palette_index,png,palette_mode,stp)
    except NativeError as e:raise ProjectError(str(e)) from e
    changed=current[:at]+candidate;start=record['source_record']['compressed_stream_offset']
    try:_,capacity=serialize_lzs_decoded(raw[start:start+used],len(original),changed,'monster-image')
    except NativeError as e:raise ProjectError(str(e)) from e
    value=dict(schema_version='legaia.monster-png-review.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog_source_key=catalog['source_key'],record=record,palette_index=palette_index,palette_mode=palette_mode,png_sha256=sha256(png).hexdigest(),png_byte_length=len(png),stp_sha256=sha256(stp).hexdigest() if stp is not None else None,stp_byte_length=len(stp) if stp is not None else None,current_pool_sha256=expected_current_sha256,current_pool_base64=b64encode(pool).decode(),candidate_pool_base64=b64encode(candidate).decode(),candidate_pool_sha256=sha256(candidate).hexdigest(),quantization=analysis['quantization'],capacity=capacity,layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    value['review_key']=digest(value);_fresh(project,expected_project_path,expected_source_key);return value


def apply(project,review_key,**args):
    from .monster_palettes import snapshot,validate
    value=review(project,**args)
    if value['review_key']!=review_key or value['current_pool_sha256']==value['candidate_pool_sha256']:raise ProjectError('Monster PNG Apply requires exact fresh changed Review')
    _,record,original,current,_,_=snapshot(project,args['asset_id']);at=record['source_record']['byte_offset'];candidate=b64decode(value['candidate_pool_base64']);png=input_bytes(args['png_base64']);stp=input_bytes(args['stp_base64']) if args.get('stp_base64') is not None else None
    receipt=dict(schema_version='legaia.monster-png-input.v1',asset_id=args['asset_id'],png_sha256=retain(project,png,'png'),png_byte_length=len(png),stp_sha256=retain(project,stp,'png') if stp is not None else None,stp_byte_length=len(stp) if stp is not None else None,baseline_sha256=retain(project,current[at:],'pool'),baseline_byte_length=len(current)-at,palette_index=args['palette_index'],palette_mode=args['palette_mode'],candidate_pool_sha256=value['candidate_pool_sha256'])
    edits=[]
    for p in range(15):
        for e in range(16):
            offset=p*32+e*2;word=struct.unpack_from('<H',candidate,offset)[0]
            if word!=struct.unpack_from('<H',original,at+offset)[0]:edits.append(dict(palette_index=p,entry_index=e,word=word))
    image=candidate[480:];image_binding=dict(sha256=retain(project,image,'idx'),byte_length=len(image)) if image!=original[at+480:] else None
    binding=dict(schema_version='legaia.monster-palette-override.v1',asset_id=args['asset_id'],source_record=deepcopy(record['source_record']),edits=edits,current_pool_sha256=sha256(candidate).hexdigest(),current_block_sha256=sha256(original[:at]+candidate).hexdigest(),png_import=receipt,**({'image_override':image_binding} if image_binding else {}))
    before=deepcopy(project.monster_palette_overrides);after=deepcopy(before)
    if edits or image_binding:after[args['asset_id']]=binding
    else:after.pop(args['asset_id'],None)
    validate(project,after);project.monster_palette_overrides=after;project.undo_stack.append(dict(target='monster_palette_overrides',before=before,after=deepcopy(after),label='Monster native PNG texture'));project.redo_stack.clear()
    return dict(history_steps=1,retained_source=receipt,project_changed=True,gameplay_verified=False)
