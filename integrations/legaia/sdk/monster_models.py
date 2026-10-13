"""Retained monster GLB history and exact Current TMD replay."""
from copy import deepcopy
from hashlib import sha256
import re
from .project import ProjectError,atomic_write
from importer import monster_model_authoring as native
from importer.model_authoring import replace_model_content
from importer.core import ImportError as NativeError

MAX_INPUT=8*1024*1024


def path(project,key,suffix):
    if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key) or suffix not in ('glb','block','tmd'):raise ProjectError('Monster model retained identity changed')
    result=project.root/'Authored'/'MonsterModelInputs'/(key+'.'+suffix)
    if not result.resolve().is_relative_to(project.root.resolve()):raise ProjectError('Monster model input escapes project root')
    return result


def read(project,key,size,suffix):
    target=path(project,key,suffix)
    if type(size) is not int or not 1<=size<=MAX_INPUT or not target.is_file() or target.stat().st_size!=size:raise ProjectError('Monster model retained bytes missing or changed size')
    content=target.read_bytes()
    if sha256(content).hexdigest()!=key:raise ProjectError('Monster model retained bytes changed hash')
    return content


def retain(project,content,suffix):
    key=sha256(content).hexdigest();target=path(project,key,suffix)
    if target.exists():read(project,key,len(content),suffix)
    else:atomic_write(target,content)
    return key


def effective(project,original,record,texture,binding=None):
    binding=getattr(project,'monster_model_overrides',{}).get(record['semantic_id']) if binding is None else binding
    at=record['source_record']['byte_offset'];length=record['source_record']['byte_length'];retail=original[at:at+length]
    if binding is None:return retail
    keys={'schema_version','asset_id','source_record','current_tmd_sha256','byte_length','inputs','edits'}
    if not isinstance(binding,dict) or set(binding)!=keys or binding['schema_version']!='legaia.monster-model-override.v1' or binding['asset_id']!=record['semantic_id'] or binding['source_record']!=record['source_record'] or binding['byte_length']!=length or not isinstance(binding['inputs'],list) or not 1<=len(binding['inputs'])<=16:raise ProjectError('Monster model ownership or input chain changed')
    cursor=retail
    for receipt in binding['inputs']:
        fields={'glb_sha256','glb_byte_length','baseline_sha256','baseline_byte_length','binding','candidate_tmd_sha256','review_key'}
        if not isinstance(receipt,dict) or set(receipt)!=fields or not isinstance(receipt['review_key'],str) or not re.fullmatch('[a-f0-9]{64}',receipt['review_key']):raise ProjectError('Monster model import receipt changed')
        baseline=read(project,receipt['baseline_sha256'],receipt['baseline_byte_length'],'block');glb=read(project,receipt['glb_sha256'],receipt['glb_byte_length'],'glb')
        if len(baseline)!=len(original) or baseline[at:at+length]!=cursor:raise ProjectError('Monster model history baseline changed')
        pool_at=texture['source_record']['byte_offset'] if texture else len(original)
        if baseline[:at]!=original[:at] or baseline[at+length:pool_at]!=original[at+length:pool_at] or not texture and baseline[at+length:]!=original[at+length:]:raise ProjectError('Monster model historical baseline changed protected slot bytes')
        try:
            proposed,_=native.convert(baseline,record,texture,receipt['binding'],glb,sha256(cursor).hexdigest());cursor=proposed[at:at+length]
            replace_model_content(retail,record['source_record']['sha256'],cursor,allow_normal_references=True)
        except (NativeError,KeyError,TypeError,ValueError) as e:raise ProjectError('Monster original GLB cannot replay Current') from e
        if sha256(cursor).hexdigest()!=receipt['candidate_tmd_sha256']:raise ProjectError('Monster model replay result changed')
    candidate=read(project,binding['current_tmd_sha256'],length,'tmd')
    if candidate!=cursor:raise ProjectError('Monster Current model differs from complete input replay')
    expected=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(retail,candidate)) if a!=b]
    if not expected or binding['edits']!=expected:raise ProjectError('Monster model Retail-relative byte ledger changed')
    return candidate


def validate(project,values):
    from importer.pipeline import _disc_context
    from importer.monster_archive import decode_catalog,block
    from .battle_character_resources import _disc
    if not isinstance(values,dict) or len(values)>186:raise ProjectError('Monster model owners exceed source bounds')
    if not values:return {}
    sizes={}
    with _disc_context(project.disc_path) as (_,disc,_,archive):
        raw=archive.read_entry(archive.entry(867));catalog=decode_catalog(raw,disc);_disc(project,catalog)
        for identifier,binding in values.items():
            record=next((r for r in catalog['models'] if r['semantic_id']==identifier),None)
            if record is None:raise ProjectError('Monster model owner has no native source')
            texture=next((r for r in catalog['textures'] if r['model_asset_id']==identifier),None);original,_=block(raw,record['monster_id']);effective(project,original,record,texture,binding)
            for receipt in binding['inputs']:
                for kind in ('glb','baseline'):sizes[(kind,receipt[kind+'_sha256'])]=receipt[kind+'_byte_length']
    if sum(sizes.values())>64*1024*1024:raise ProjectError('Monster active model inputs exceed 64 MiB')
    return deepcopy(values)


def compose(project,original,catalog,monster_id,current=None):
    result=bytearray(original if current is None else current);record=next((r for r in catalog['models'] if r['monster_id']==monster_id),None)
    if record is None:return bytes(result)
    texture=next((r for r in catalog['textures'] if r['model_asset_id']==record['semantic_id']),None);tmd=effective(project,original,record,texture);at=record['source_record']['byte_offset'];result[at:at+len(tmd)]=tmd
    return bytes(result)
