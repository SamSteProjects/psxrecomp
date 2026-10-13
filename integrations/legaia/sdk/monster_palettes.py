"""Canonical Retail palette ledgers and fixed-span native monster delivery."""
import re,struct
from copy import deepcopy
from hashlib import sha256
from base64 import b64encode
from importer.pipeline import _disc_context
from importer.monster_archive import decode_catalog,block
from importer.monster_textures import pixels,layout
from importer.serialization import serialize_lzs_decoded
from importer.core import ImportError as NativeError
from .battle_character_resources import _fresh,_disc
from .project import ProjectError,digest


def compose(original,record,binding,project=None):
    if not isinstance(binding,dict) or set(binding)-{'schema_version','asset_id','source_record','edits','current_pool_sha256','current_block_sha256','image_override','png_import'} or not {'schema_version','asset_id','source_record','edits','current_pool_sha256','current_block_sha256'}<=set(binding) or binding['schema_version']!='legaia.monster-palette-override.v1' or binding['asset_id']!=record['semantic_id'] or binding['source_record']!=record['source_record']:
        raise ProjectError('Monster palette source ownership changed')
    edits=binding['edits']
    if not isinstance(edits,list) or not 0<=len(edits)<=240 or not edits and 'image_override' not in binding:raise ProjectError('Monster palette ledger must own existing palette cells')
    candidate=bytearray(original);seen=set();order=[];pool_at=record['source_record']['byte_offset']
    for row in edits:
        if not isinstance(row,dict) or set(row)!={'palette_index','entry_index','word'} or any(type(row[k]) is not int for k in row):raise ProjectError('Monster palette ledger requires typed palette, entry and word')
        palette,entry,word=row['palette_index'],row['entry_index'],row['word'];key=(palette,entry)
        if not 0<=palette<15 or not 0<=entry<16 or not 0<=word<=65535 or key in seen:raise ProjectError('Monster palette ledger cell is duplicated or outside the source')
        at=pool_at+palette*32+entry*2
        if struct.unpack_from('<H',original,at)[0]==word:raise ProjectError('Monster palette ledger contains an unmodified Retail cell')
        struct.pack_into('<H',candidate,at,word);seen.add(key);order.append(key)
    if 'image_override' in binding:
        from .monster_png import read
        image=binding['image_override']
        if project is None or not isinstance(image,dict) or set(image)!={'sha256','byte_length'} or image['byte_length']!=len(original)-pool_at-480:raise ProjectError('Monster image override footprint changed')
        content=read(project,image['sha256'],image['byte_length'],'idx')
        if content==original[pool_at+480:]:raise ProjectError('Monster image override has no native changes')
        candidate[pool_at+480:]=content
    if 'png_import' in binding:
        from .monster_png import validate_input
        if project is None:raise ProjectError('Monster original PNG replay requires its project')
        validate_input(project,record,binding['png_import'])
    if order!=sorted(order):raise ProjectError('Monster palette ledger is not canonical')
    candidate=bytes(candidate);pool=candidate[pool_at:]
    if sha256(candidate).hexdigest()!=binding['current_block_sha256'] or sha256(pool).hexdigest()!=binding['current_pool_sha256']:raise ProjectError('Monster palette Current replay hash changed')
    return candidate


def snapshot(project,asset_id):
    with _disc_context(project.disc_path) as (_,disc,_,archive):
        raw=archive.read_entry(archive.entry(867));catalog=decode_catalog(raw,disc);_disc(project,catalog)
        record=next((r for r in catalog['textures'] if r['semantic_id']==asset_id),None)
        if record is None:raise ProjectError('Monster palette owner is unqualified')
        original,used=block(raw,record['monster_id']);binding=project.monster_palette_overrides.get(asset_id)
        current=compose(original,record,binding,project) if binding else original
        from .monster_models import compose as compose_model
        current=compose_model(project,original,catalog,record['monster_id'],current)
        from .monster_motions import compose as compose_motion
        current=compose_motion(original,catalog,record['monster_id'],project.monster_motion_overrides,current)
        return catalog,record,original,current,raw,used


def validate(project,values):
    if not isinstance(values,dict) or len(values)>186:raise ProjectError('Monster palette overrides require a bounded owner mapping')
    if not values:return {}
    retained_bytes=0
    if not project.disc_path:raise ProjectError('Monster palette validation requires its original source disc')
    with _disc_context(project.disc_path) as (_,disc,_,archive):
        raw=archive.read_entry(archive.entry(867));catalog=decode_catalog(raw,disc);_disc(project,catalog)
        for identifier,binding in values.items():
            record=next((r for r in catalog['textures'] if r['semantic_id']==identifier),None)
            if record is None:raise ProjectError('Monster palette binding has no qualified native owner')
            original,used=block(raw,record['monster_id']);current=compose(original,record,binding,project);start=record['source_record']['compressed_stream_offset']
            if 'png_import' in binding:
                receipt=binding['png_import'];retained_bytes+=receipt['png_byte_length']+(receipt['stp_byte_length'] or 0)+receipt['baseline_byte_length']
                if retained_bytes>64*1024*1024:raise ProjectError('Active monster PNG inputs exceed the 64 MiB project budget')
            try:serialize_lzs_decoded(raw[start:start+used],len(original),current,'monster-palette')
            except NativeError as e:raise ProjectError(str(e)) from e
    return deepcopy(values)


def inspect(project,expected_project_path,expected_source_key,asset_id,palette_index):
    _fresh(project,expected_project_path,expected_source_key)
    if type(palette_index) is not int or not 0<=palette_index<15:raise ProjectError('Choose an existing monster palette')
    catalog,record,original,current,_,_=snapshot(project,asset_id);original_pool,width=layout(original,record['source_record']['byte_offset']);pool,_=layout(current,record['source_record']['byte_offset']);value=pixels(pool,width,palette_index);value['rgba_base64']=b64encode(value.pop('rgba')).decode();value['stp_base64']=b64encode(value.pop('stp')).decode();_fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.monster-palette-inspection.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog_source_key=catalog['source_key'],record=record,
        palette_index=palette_index,retail_words=pixels(original_pool,width,palette_index)['words'],current_pool_sha256=sha256(pool).hexdigest(),current_block_sha256=sha256(current).hexdigest(),
        current_pool_base64=b64encode(pool).decode(),retail_pool_base64=b64encode(original_pool).decode(),binding=deepcopy(project.monster_palette_overrides.get(asset_id)),preview=value,layer='current',read_only=True,project_changed=False,gameplay_verified=False)


def review(project,expected_project_path,expected_source_key,asset_id,palette_index,entry_index,word,expected_current_sha256):
    if project.mode!='edit':raise ProjectError('Monster palette authoring requires Edit mode')
    _fresh(project,expected_project_path,expected_source_key)
    if any(type(n) is not int for n in (palette_index,entry_index,word)) or not 0<=palette_index<15 or not 0<=entry_index<16 or not 0<=word<=65535:raise ProjectError('Choose an existing palette/entry and unsigned16 native word')
    catalog,record,original,current,raw,used=snapshot(project,asset_id);pool_at=record['source_record']['byte_offset'];pool=current[pool_at:]
    if sha256(pool).hexdigest()!=expected_current_sha256:raise ProjectError('Monster Current palette changed; inspect again')
    before=struct.unpack_from('<H',pool,palette_index*32+entry_index*2)[0];ledger={(r['palette_index'],r['entry_index']):r['word'] for r in project.monster_palette_overrides.get(asset_id,{}).get('edits',[])};pair=(palette_index,entry_index);at=pool_at+palette_index*32+entry_index*2
    if word==struct.unpack_from('<H',original,at)[0]:ledger.pop(pair,None)
    else:ledger[pair]=word
    candidate=bytearray(current);struct.pack_into('<H',candidate,at,word);candidate=bytes(candidate);proposed_pool=candidate[pool_at:]
    extras={k:deepcopy(project.monster_palette_overrides.get(asset_id,{}))[k] for k in ('image_override','png_import') if k in project.monster_palette_overrides.get(asset_id,{})}
    binding=dict(**extras,schema_version='legaia.monster-palette-override.v1',asset_id=asset_id,source_record=deepcopy(record['source_record']),edits=[dict(palette_index=p,entry_index=e,word=w) for (p,e),w in sorted(ledger.items())],current_pool_sha256=sha256(proposed_pool).hexdigest(),current_block_sha256=sha256(original[:pool_at]+proposed_pool).hexdigest()) if ledger or 'image_override' in extras else None
    if binding:compose(original,record,binding,project)
    start=record['source_record']['compressed_stream_offset']
    try:_,capacity=serialize_lzs_decoded(raw[start:start+used],len(original),candidate,'monster-palette')
    except NativeError as e:raise ProjectError(str(e)) from e
    value=dict(schema_version='legaia.monster-palette-review.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog_source_key=catalog['source_key'],record=record,
        palette_index=palette_index,entry_index=entry_index,word=word,before_word=before,current_pool_sha256=expected_current_sha256,proposed_pool_sha256=sha256(proposed_pool).hexdigest(),
        current_pool_base64=b64encode(pool).decode(),proposed_pool_base64=b64encode(proposed_pool).decode(),binding=binding,capacity=capacity,layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    value['review_key']=digest(value);_fresh(project,expected_project_path,expected_source_key);return value


def apply(project,review_key,**args):
    value=review(project,**args)
    if value['review_key']!=review_key or value['current_pool_sha256']==value['proposed_pool_sha256']:raise ProjectError('Monster Apply requires an exact fresh changed Review')
    before=deepcopy(project.monster_palette_overrides);after=deepcopy(before)
    if value['binding']:after[args['asset_id']]=value['binding']
    else:after.pop(args['asset_id'],None)
    validate(project,after);project.monster_palette_overrides=after;project.undo_stack.append(dict(target='monster_palette_overrides',before=before,after=deepcopy(after),label='Monster native palette'));project.redo_stack.clear()
    return dict(history_steps=1,project_changed=True,gameplay_verified=False)


def prepare(project,archive,disc_hash):
    from .monster_build import prepare as prepare_slots
    return prepare_slots(project,archive,disc_hash)
