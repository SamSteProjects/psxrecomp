"""Bounded PLAYER1..4 equipment assembly, before runtime registration.

Independent implementation from pinned battle-data-pack/character-mesh evidence.
No PROT 1203 rig, texture relocation, runtime identity or authored state.
"""
from hashlib import sha256
import struct
from .core import ImportError,decompress_lzs,validate_metadata_only
from .pipeline import _disc_context,REFERENCE_COMMIT
from .assets import decode_tmd

DATA_BASE=0x8000


def table(raw):
    if not isinstance(raw,bytes) or not DATA_BASE<len(raw)<=4*1024*1024:raise ImportError('PLAYER source footprint exceeds bounds')
    offset,ca,cb,budget=struct.unpack_from('<4I',raw)
    if not 16<=offset<DATA_BASE-12 or not 0<ca<cb<budget<=4*1024*1024:raise ImportError('PLAYER header is unsupported')
    rows=[];cursor=offset;end=0;section=0
    while len(rows)<256 and cursor+12<=DATA_BASE:
        item,start,size=struct.unpack_from('<3I',raw,cursor)
        if size==0:
            if item or start:raise ImportError('PLAYER descriptor terminator is noncanonical')
            break
        if item>255 or start!=end or size%0x800 or not 0<size<=4*1024*1024 or DATA_BASE+start+size>len(raw) or section>=5:raise ImportError('PLAYER descriptor chain or footprint is unsupported')
        rows.append(dict(record_index=len(rows),item_id=item,section_index=section,descriptor_offset=cursor,byte_offset=DATA_BASE+start,byte_length=size));end=start+size;cursor+=12
        if item==0:section+=1
    else:raise ImportError('PLAYER descriptor table has no bounded terminator')
    if section!=5 or DATA_BASE+end!=len(raw):raise ImportError('PLAYER sections do not exactly cover the adjacent-TOC-bounded file')
    return rows


def assemble(raw,equipped):
    rows=table(raw)
    if not isinstance(equipped,list) or len(equipped)!=5 or any(type(v) is not int or not 0<=v<=255 for v in equipped):raise ImportError('PLAYER selection requires five item-ID bytes')
    selected=[];entries=[];pool=bytearray();tags=[];bones=[];object_sources=[];extra_a=extra_b=0;attach=[]
    for section,want in enumerate(equipped):
        choices=[r for r in rows if r['section_index']==section];r=next((r for r in choices if r['item_id']==want),choices[-1]);at=r['byte_offset'];size=struct.unpack_from('<I',raw,at)[0]
        if not 20<=size<=4*1024*1024:raise ImportError('PLAYER decoded allocation exceeds bounds')
        d,used=decompress_lzs(raw[at+4:at+r['byte_length']],size)
        frame,swing_a,swing_b,body_end,attach_count,upload_flag=struct.unpack_from('<4IhH',d)
        if not 0<=attach_count<=24 or frame!=20+4*attach_count or frame+24>len(d) or not frame+24<=body_end<=len(d):raise ImportError('PLAYER loader frame is outside its decoded source')
        n=d[frame];data_size,magic,flags,count=struct.unpack_from('<4I',d,frame+8)
        if n>7 or magic!=0x80000002 or flags!=0 or not n<=count<=24 or count==0 or len(entries)+count>24:raise ImportError('PLAYER loader/TMD object layout is unsupported')
        bone_ids=list(d[frame+1:frame+1+n]);start=frame+24;stop=start+count*28;length=((data_size-count*28-9)//4)*4
        if length<0 or stop+length>body_end or any(b>=64 for b in bone_ids) or not bone_ids:raise ImportError('PLAYER attach list or data pool exceeds its decoded source')
        delta=24*28+len(pool)-count*28;last=bone_ids[-1]
        for i in range(count):
            words=list(struct.unpack_from('<7I',d,start+i*28))
            for k in (0,2,4):
                words[k]+=delta
                if not 0<=words[k]<=0xffffffff:raise ImportError('PLAYER relocated object offset overflow')
            entries.append(words);bone=bone_ids[i] if i<n else last;bones.append(bone)
            if i<n:tag=bone
            elif i==n:tag=200+extra_a;extra_a+=1;attach.append(last)
            else:tag=100+extra_b;extra_b+=1
            tags.append(tag);object_sources.append(dict(section_index=section,record_index=r['record_index'],source_object_index=i))
        pool.extend(d[stop:stop+length]);selected.append(dict(r,requested_item_id=want,fallback=r['item_id']!=want,decoded_byte_length=len(d),decoded_sha256=sha256(d).hexdigest(),compressed_bytes_consumed=used,compressed_sha256=sha256(raw[at:at+4+used]).hexdigest(),loader_frame_offset=frame,attach_record_count=attach_count,tmd_body_end=body_end,upload_flag=upload_flag,swing_record_offsets=[swing_a,swing_b]))
    # Selection sort retains the retail permutation even with equal tags.
    for i in range(len(tags)):
        j=min(range(i,len(tags)),key=lambda j:tags[j])
        for array in (entries,tags,bones,object_sources):array[i],array[j]=array[j],array[i]
    tmd=struct.pack('<3I',0x80000002,0,len(entries))+b''.join(struct.pack('<7I',*e) for e in entries)+bytes((24-len(entries))*28)+pool
    geometry=decode_tmd(tmd)
    return geometry,dict(equipped=equipped.copy(),sections=selected,bone_tags=tags,animation_part_indices=bones,attach_bones=attach,object_sources=object_sources,tmd_sha256=sha256(tmd).hexdigest(),tmd_byte_length=len(tmd),texture_routing='unresolved',animation_source='PLAYER record0, not PROT1203',runtime_registration='not_applied')


def _sources(disc):
    with _disc_context(disc) as (_,digest,_,archive):
        sources=[]
        for index in range(863,867):
            entry=archive.entry(index);following=archive.entry(index+1);length=(following.start_lba-entry.start_lba)*archive.SECTOR
            if not DATA_BASE<length<=4*1024*1024:raise ImportError('PLAYER physical PROT boundary is unsupported')
            raw=archive.image.read_user(archive.node.extent_lba,entry.start_lba*archive.SECTOR,length,archive.node.size)
            table(raw);sources.append((index,entry.start_lba,following.start_lba,raw))
        return digest,sources


def discover(disc):
    digest,sources=_sources(disc);models=[]
    for slot,(index,start,end,raw) in enumerate(sources):
        rows=table(raw);geometry,assembly=assemble(raw,[0]*5);source=dict(disc=dict(sha256=digest,serial='SCUS-94254'),iso_file='PROT.DAT',prot_entry_index=index,record_kind='adjacent_toc_bounded_player_file',start_lba=start,next_start_lba=end,byte_length=len(raw),sha256=sha256(raw).hexdigest(),boundary_evidence='adjacent_PROT_start_and_complete_descriptor_chain')
        models.append(dict(semantic_id=f'asset://legaia/models/player-battle/{slot:04d}',asset_kind='player_battle_model',name=f'PLAYER Battle Model {slot}',player_index=slot,source_record=source,descriptors=rows,default_assembly=assembly,preview_summary=dict(objects=len(geometry['objects']),vertices=len(geometry['vertices']),triangles=len(geometry['triangles'])),reference_commit=REFERENCE_COMMIT))
    key=sha256(('player-battle-v1:'+digest+':'+':'.join(m['source_record']['sha256'] for m in models)).encode()).hexdigest()
    result=dict(schema_version='legaia.player-battle-catalog.v1',source_disc_sha256=digest,source_key=key,models=models,reference_commit=REFERENCE_COMMIT,read_only=True,project_changed=False,gameplay_verified=False)
    validate_metadata_only(result);return result


def preview(disc,asset_id,expected_source_key,equipped):
    catalog=discover(disc)
    if expected_source_key!=catalog['source_key']:raise ImportError('PLAYER model source changed; refresh discovery')
    model=next((m for m in catalog['models'] if m['semantic_id']==asset_id),None)
    if model is None:raise ImportError('PLAYER model identity is unqualified')
    digest,sources=_sources(disc);raw=sources[model['player_index']][3]
    if digest!=catalog['source_disc_sha256'] or sha256(raw).hexdigest()!=model['source_record']['sha256']:raise ImportError('PLAYER file changed during preview')
    geometry,assembly=assemble(raw,equipped);geometry.update(semantic_id=asset_id,source_record=model['source_record'],reference_commit=REFERENCE_COMMIT)
    return catalog,model,geometry,assembly
