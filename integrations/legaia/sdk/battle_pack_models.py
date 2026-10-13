"""Retained pack GLB imports, canonical ownership and complete native replay."""
from copy import deepcopy
from hashlib import sha256
import re
from .project import ProjectError, atomic_write
from importer import battle_pack_model_authoring as native
from importer.core import ImportError as NativeError

MAX_INPUT=8*1024*1024


def path(project,key,suffix):
    if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key) or suffix not in ('glb','tmd'):
        raise ProjectError('Battle pack model retained identity changed')
    target=project.root/'Authored'/'BattlePackModels'/(key+'.'+suffix)
    if not target.resolve().is_relative_to(project.root.resolve()):
        raise ProjectError('Battle pack model input escapes project root')
    return target


def read(project,key,size,suffix):
    target=path(project,key,suffix)
    if type(size) is not int or not 1<=size<=MAX_INPUT or not target.is_file() or target.stat().st_size!=size:
        raise ProjectError('Battle pack model retained bytes are missing or changed size')
    content=target.read_bytes()
    if sha256(content).hexdigest()!=key:raise ProjectError('Battle pack model retained hash changed')
    return content


def retain(project,content,suffix):
    if not isinstance(content,bytes) or not 1<=len(content)<=MAX_INPUT:
        raise ProjectError('Battle pack model retained bytes exceed bounds')
    key=sha256(content).hexdigest();target=path(project,key,suffix)
    if target.exists():read(project,key,len(content),suffix)
    else:atomic_write(target,content)
    return key


def effective(project,original,catalog,record,binding=None):
    binding=getattr(project,'battle_pack_model_overrides',{}).get(record['semantic_id']) if binding is None else binding
    retail,_=native.source(original,record,catalog)
    if binding is None:return retail
    keys={'schema_version','asset_id','source_record','current_tmd_sha256','byte_length','inputs','edits'}
    if (not isinstance(binding,dict) or set(binding)!=keys
            or binding['schema_version']!='legaia.battle-pack-model-override.v1'
            or binding['asset_id']!=record['semantic_id'] or binding['source_record']!=record['source_record']
            or binding['byte_length']!=len(retail) or not isinstance(binding['inputs'],list)
            or not 1<=len(binding['inputs'])<=16):
        raise ProjectError('Battle pack model owner or input chain changed')
    cursor=retail
    for receipt in binding['inputs']:
        fields={'glb_sha256','glb_byte_length','base_tmd_sha256','candidate_tmd_sha256','binding','review_key'}
        if (not isinstance(receipt,dict) or set(receipt)!=fields or not isinstance(receipt['review_key'],str)
                or not re.fullmatch('[a-f0-9]{64}',receipt['review_key'])
                or receipt['base_tmd_sha256']!=sha256(cursor).hexdigest()):
            raise ProjectError('Battle pack retained import receipt changed')
        glb=read(project,receipt['glb_sha256'],receipt['glb_byte_length'],'glb')
        try:cursor,_=native.convert(original,record,catalog,receipt['binding'],glb,cursor)
        except (NativeError,KeyError,TypeError,ValueError) as error:
            raise ProjectError('Battle pack original GLB cannot replay Current') from error
        if sha256(cursor).hexdigest()!=receipt['candidate_tmd_sha256']:
            raise ProjectError('Battle pack retained import result changed')
    candidate=read(project,binding['current_tmd_sha256'],len(retail),'tmd')
    ledger=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(retail,candidate)) if a!=b]
    if candidate!=cursor or not ledger or binding['edits']!=ledger:
        raise ProjectError('Battle pack Current model differs from complete replay or its Retail ledger')
    return candidate


def compose(project,original,catalog,values=None):
    values=getattr(project,'battle_pack_model_overrides',{}) if values is None else values
    if not isinstance(values,dict) or len(values)>5:raise ProjectError('Battle pack model owners exceed five sources')
    result=bytearray(original)
    for identifier,binding in sorted(values.items()):
        record=next((r for r in catalog['models'] if r['semantic_id']==identifier),None)
        if record is None or not isinstance(binding,dict):raise ProjectError('Battle pack model owner has no source')
        body=effective(project,original,catalog,record,binding);at=record['source_record']['byte_offset']
        result[at:at+len(body)]=body
    return bytes(result)


def validate(project,values):
    from importer.pipeline import _disc_context
    from importer.battle_character_catalog import decode_catalog
    from .battle_character_resources import _disc
    if not isinstance(values,dict) or len(values)>5:raise ProjectError('Battle pack model owner count exceeds bounds')
    if not values:return {}
    sizes={}
    with _disc_context(project.disc_path) as (_,disc,_,archive):
        original=archive.read_entry(archive.entry(1204));catalog=decode_catalog(original,disc);_disc(project,catalog)
        compose(project,original,catalog,values)
        for binding in values.values():
            for receipt in binding['inputs']:
                key=('glb',receipt['glb_sha256']);length=receipt['glb_byte_length']
                if key in sizes and sizes[key]!=length:raise ProjectError('Battle pack input size conflicts')
                sizes[key]=length
            sizes[('tmd',binding['current_tmd_sha256'])]=binding['byte_length']
    if sum(sizes.values())>64*1024*1024:raise ProjectError('Battle pack active model inputs exceed64MiB')
    return deepcopy(values)
