"""Exact retained pack PNG/mask/baseline/index inputs and fresh native replay."""
import re
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError,atomic_write
from importer import battle_pack_png as native
from importer.core import ImportError as NativeError


def path(project,key,kind):
    if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key) or kind not in ('png','tim','idx'):
        raise ProjectError('Pack PNG retained identity changed')
    target=project.root/'Authored'/'BattlePackTextureInputs'/(key+'.'+kind)
    if not target.resolve().is_relative_to(project.root.resolve()):raise ProjectError('Pack PNG input escapes project root')
    return target


def read(project,key,size,kind):
    limit=8*1024*1024 if kind=='png' else 33312 if kind=='tim' else 32768
    target=path(project,key,kind)
    if type(size) is not int or not 1<=size<=limit or not target.is_file() or target.stat().st_size!=size:
        raise ProjectError('Pack PNG retained input is missing or changed size')
    content=target.read_bytes()
    if sha256(content).hexdigest()!=key:raise ProjectError('Pack PNG retained input hash changed')
    return content


def retain(project,content,kind):
    limit=8*1024*1024 if kind=='png' else 33312 if kind=='tim' else 32768
    if not isinstance(content,bytes) or not 1<=len(content)<=limit:raise ProjectError('Pack PNG retained bytes exceed their bounded native input')
    key=sha256(content).hexdigest();target=path(project,key,kind)
    if target.exists():read(project,key,len(content),kind)
    else:atomic_write(target,content)
    return key


def retain_import(project,original,catalog,record,palette_index,png,palette_mode,stp=None,baseline=None):
    from importer.battle_pack_palettes import source
    baseline=source(original,catalog,record) if baseline is None else baseline
    try:candidate,proof=native.convert(original,catalog,record,palette_index,png,palette_mode,stp,current=baseline)
    except NativeError as error:raise ProjectError(str(error)) from error
    receipt=dict(schema_version='legaia.battle-pack-png-input.v1',palette_index=palette_index,palette_mode=palette_mode,
        png_sha256=retain(project,png,'png'),png_byte_length=len(png),stp_sha256=retain(project,stp,'png') if stp is not None else None,
        stp_byte_length=len(stp) if stp is not None else None,baseline_sha256=retain(project,baseline,'tim'),baseline_byte_length=len(baseline),candidate_tim_sha256=proof['candidate_tim_sha256'])
    owner=dict(schema_version='legaia.battle-pack-image-override.v1',asset_id=record['semantic_id'],source_record=deepcopy(record['source_record']),
        input=receipt,index_sha256=retain(project,candidate[544:],'idx'),index_byte_length=32768)
    effective(project,original,catalog,record,owner)
    return owner,candidate,proof


def effective(project,original,catalog,record,owner):
    if (not isinstance(owner,dict) or set(owner)!={'schema_version','asset_id','source_record','input','index_sha256','index_byte_length'}
            or owner['schema_version']!='legaia.battle-pack-image-override.v1' or owner['asset_id']!=record['semantic_id']
            or owner['source_record']!=record['source_record'] or type(owner['index_byte_length']) is not int or owner['index_byte_length']!=32768):
        raise ProjectError('Pack image owner or native footprint changed')
    r=owner['input'];fields={'schema_version','palette_index','palette_mode','png_sha256','png_byte_length','stp_sha256','stp_byte_length','baseline_sha256','baseline_byte_length','candidate_tim_sha256'}
    if (not isinstance(r,dict) or set(r)!=fields or r['schema_version']!='legaia.battle-pack-png-input.v1'
            or type(r['palette_index']) is not int or not 0<=r['palette_index']<16 or r['palette_mode'] not in ('existing','rebuild')
            or type(r['baseline_byte_length']) is not int or r['baseline_byte_length']!=33312 or (r['stp_sha256'] is None)!=(r['stp_byte_length'] is None)):
        raise ProjectError('Pack original PNG receipt changed')
    png=read(project,r['png_sha256'],r['png_byte_length'],'png');stp=read(project,r['stp_sha256'],r['stp_byte_length'],'png') if r['stp_sha256'] is not None else None
    baseline=read(project,r['baseline_sha256'],33312,'tim')
    try:candidate,_=native.convert(original,catalog,record,r['palette_index'],png,r['palette_mode'],stp,current=baseline)
    except (NativeError,TypeError,ValueError) as error:raise ProjectError('Pack original PNG cannot replay its native projection') from error
    if sha256(candidate).hexdigest()!=r['candidate_tim_sha256']:raise ProjectError('Pack original PNG replay differs from its candidate hash')
    image=read(project,owner['index_sha256'],32768,'idx')
    if image!=candidate[544:]:raise ProjectError('Pack image differs from exact original PNG replay')
    return image


def compose(project,original,catalog,values,current=None):
    if not isinstance(values,dict) or len(values)>6:raise ProjectError('Pack image ownership exceeds six complete sources')
    result=bytearray(original if current is None else current)
    if len(result)!=len(original):raise ProjectError('Pack image composition changed the entry footprint')
    for identifier,owner in sorted(values.items()):
        record=next((r for r in catalog['textures'] if r['semantic_id']==identifier and r['preview_supported']),None)
        if record is None:raise ProjectError('Pack image owner has no complete immutable source')
        image=effective(project,original,catalog,record,owner);at=record['source_record']['byte_offset']+544;result[at:at+32768]=image
    return bytes(result)
