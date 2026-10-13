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


def describe(record,palette_index,png,palette_mode,stp,baseline,candidate):
    """Prospective ownership, used to preflight aggregate budget before writes."""
    return dict(schema_version='legaia.battle-pack-image-override.v1',asset_id=record['semantic_id'],source_record=deepcopy(record['source_record']),
        input=dict(schema_version='legaia.battle-pack-png-input.v1',palette_index=palette_index,palette_mode=palette_mode,
            png_sha256=sha256(png).hexdigest(),png_byte_length=len(png),stp_sha256=sha256(stp).hexdigest() if stp is not None else None,
            stp_byte_length=len(stp) if stp is not None else None,baseline_sha256=sha256(baseline).hexdigest(),baseline_byte_length=len(baseline),candidate_tim_sha256=sha256(candidate).hexdigest()),
        index_sha256=sha256(candidate[544:]).hexdigest(),index_byte_length=32768)


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


def budget(values):
    if not isinstance(values,dict) or len(values)>6:raise ProjectError('Pack image owners exceed six complete sources')
    sizes={}
    for owner in values.values():
        if not isinstance(owner,dict) or not isinstance(owner.get('input'),dict):raise ProjectError('Pack PNG input metadata changed')
        r=owner['input']
        for key,size,kind in [(r.get('png_sha256'),r.get('png_byte_length'),'png'),(r.get('stp_sha256'),r.get('stp_byte_length'),'png'),(r.get('baseline_sha256'),r.get('baseline_byte_length'),'tim'),(owner.get('index_sha256'),owner.get('index_byte_length'),'idx')]:
            if key is None and size is None and kind=='png':continue
            limit=8*1024*1024 if kind=='png' else 33312 if kind=='tim' else 32768
            if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key) or type(size) is not int or not 1<=size<=limit:raise ProjectError('Pack PNG retained budget metadata changed')
            pair=(key,kind)
            if pair in sizes and sizes[pair]!=size:raise ProjectError('Pack PNG input lengths conflict')
            sizes[pair]=size
    if sum(sizes.values())>64*1024*1024:raise ProjectError('Pack active PNG inputs exceed64MiB')
    return sum(sizes.values())


def validate(project,values):
    from importer.pipeline import _disc_context
    from importer.battle_character_catalog import decode_catalog
    from .battle_character_resources import _disc
    budget(values)
    if not values:return {}
    with _disc_context(project.disc_path) as (_,disc,_,archive):
        original=archive.read_entry(archive.entry(1204));catalog=decode_catalog(original,disc);_disc(project,catalog)
        compose(project,original,catalog,values)
    return deepcopy(values)


def prepare(project,archive,disc_hash):
    from importer.battle_character_catalog import decode_catalog
    values=getattr(project,'battle_pack_image_overrides',{});validate(project,values)
    if not values:return [],[]
    entry=archive.entry(1204);original=archive.read_entry(entry);catalog=decode_catalog(original,disc_hash);overlays=[];changes=[]
    for record in catalog['textures']:
        owner=values.get(record['semantic_id'])
        if owner is None:continue
        payload=effective(project,original,catalog,record,owner);s=record['source_record'];at=s['byte_offset']+544
        source=deepcopy(s);source.update(byte_offset=at,byte_length=32768,sha256=sha256(original[at:at+32768]).hexdigest(),parent_tim_sha256=s['sha256'])
        overlays.append(dict(scene='battle-character-pack',offset=(archive.node.extent_lba+entry.start_lba)*archive.SECTOR+at,size=32768,file=f'assets/battle-pack-{s["record_index"]}-indices.bin',payload=payload,
            sha256=sha256(payload).hexdigest(),expected_sha256=source['sha256'],source_kind='fixed_span_battle_pack_indices',source_record=source))
        changes.append(dict(scene='battle-character-pack',semantic_id=record['semantic_id'],field='texture.native_indices',scope='battle-pack-existing-index-image-only',byte_offset=at,byte_length=32768,before_sha256=source['sha256'],after_sha256=sha256(payload).hexdigest(),original_png_replayed=True))
    return overlays,changes
