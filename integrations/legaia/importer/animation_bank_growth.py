"""Qualify expanded native ANM banks and relocate their compressed scene owner."""
from hashlib import sha256
import struct

from .animation import animation_record_ranges, decode_animation_record
from .animation_authoring import replace_animation_record
from .core import ImportError, parse_scene_assets, decompress_lzs
from .serialization import compress_lzs
from .model_pack_archive import _archive
from .prot_layout import locate_physical_span
from .prot_rebuild import replace_physical_entry


def qualify_animation_bank(source, candidate):
    if not isinstance(source,bytes) or not isinstance(candidate,bytes) or not 0<len(candidate)<=4*1024*1024:
        raise ImportError('Expanded animation bank exceeds native byte bounds')
    old,new = animation_record_ranges(source),animation_record_ranges(candidate)
    if not 0 <= len(new)-len(old) <= 64 or len(new)>4096:
        raise ImportError('Expanded animation bank changed existing record count or exceeds allocation bounds')
    if source[4+4*len(old):old[0][0]] != candidate[4+4*len(new):new[0][0]]:
        raise ImportError('Expanded animation bank changed opaque table padding')
    changes=[];channels=0
    for index,(start,end) in enumerate(new):
        record=candidate[start:end]
        if index<len(old):
            a,b=old[index];original=source[a:b]
            if original!=record:
                # Equal-layout existing channel edits are permitted; opaque,
                # header/layout and unsupported neighbor changes are not.
                replace_animation_record(original,sha256(original).hexdigest(),record)
        else:
            decoded=decode_animation_record(record)
            channels+=decoded['frame_count']*decoded['bone_count']
            if channels>4096:
                raise ImportError('Expanded animation bank exceeds cumulative new-channel budget')
        changes.append(dict(record_index=index,record_sha256=sha256(record).hexdigest(),
            byte_offset=start,byte_length=end-start,allocated=index>=len(old)))
    return dict(source_record_count=len(old),proposed_record_count=len(new),
        allocated_record_count=len(new)-len(old),source_sha256=sha256(source).hexdigest(),
        proposed_sha256=sha256(candidate).hexdigest(),records=changes,opaque_table_padding_preserved=True)


def grow_scene_animation_bank(source,expected_sha256,table_offset,descriptor_index,
                              expected_bank_sha256,bank):
    if not isinstance(source,bytes) or sha256(source).hexdigest()!=expected_sha256 or len(source)>16*1024*1024:
        raise ImportError('Animation scene carrier source changed or exceeds bounds')
    if type(table_offset) is not int or type(descriptor_index) is not int:
        raise ImportError('Animation scene carrier requires exact integer locators')
    table=parse_scene_assets(source,0,table_offset)
    if table is None or not 0<=descriptor_index<len(table.descriptors):
        raise ImportError('Animation scene carrier descriptor is missing')
    descriptor=table.descriptors[descriptor_index]
    if descriptor.type_byte!=5 or not descriptor.size:
        raise ImportError('Animation scene carrier requires a nonempty type-5 resource')
    table_end=8+8*len(table.descriptors)
    if any(not table_end<=d.data_offset<=len(source)-table_offset or d.size and d.data_offset==len(source)-table_offset for d in table.descriptors):
        raise ImportError('Animation scene descriptor overlaps its table or exceeds physical owner')
    start=table_offset+descriptor.data_offset
    end=min([table_offset+d.data_offset for d in table.descriptors if d.data_offset>descriptor.data_offset]+[len(source)])
    if start>=end or sum(d.data_offset==descriptor.data_offset for d in table.descriptors)!=1:
        raise ImportError('Animation scene resource has an empty or aliased physical slot')
    original,consumed=decompress_lzs(source[start:end],descriptor.size)
    if sha256(original).hexdigest()!=expected_bank_sha256:
        raise ImportError('Animation scene bank preimage changed')
    bank_audit=qualify_animation_bank(original,bank)
    stream=source[start:start+consumed] if bank==original else compress_lzs(bank)
    decoded,used=decompress_lzs(stream,len(bank))
    if decoded!=bank or used!=len(stream):
        raise ImportError('Expanded animation compression failed independent readback')
    growth=(max(0,len(stream)-(end-start))+3)&~3
    if len(source)+growth>16*1024*1024:
        raise ImportError('Animation scene carrier growth exceeds native bounds')
    result=bytearray(source[:end]+bytes(growth)+source[end:])
    result[start:start+len(stream)]=stream
    struct.pack_into('<I',result,table_offset+8+8*descriptor_index,(5<<24)|len(bank))
    moved=[]
    for d in table.descriptors:
        if growth and table_offset+d.data_offset>=end:
            struct.pack_into('<I',result,table_offset+12+8*d.index,d.data_offset+growth)
            moved.append(dict(descriptor_index=d.index,source_byte_offset=table_offset+d.data_offset,
                proposed_byte_offset=table_offset+d.data_offset+growth))
    candidate=bytes(result);reopened=parse_scene_assets(candidate,0,table_offset)
    if reopened is None or candidate[end+growth:]!=source[end:] or candidate[:table_offset]!=source[:table_offset]:
        raise ImportError('Animation scene relocation changed preceding or following opaque payload')
    for before,after in zip(table.descriptors,reopened.descriptors):
        if (after.type_byte!=before.type_byte or after.size!=(len(bank) if before.index==descriptor_index else before.size)
                or after.data_offset!=before.data_offset+(growth if table_offset+before.data_offset>=end else 0)):
            raise ImportError('Animation scene descriptor relocation failed readback')
    if decompress_lzs(candidate[start:start+len(stream)],len(bank))[0]!=bank:
        raise ImportError('Animation scene emitted bank differs from the qualified candidate')
    return candidate,dict(source_sha256=expected_sha256,proposed_sha256=sha256(candidate).hexdigest(),
        table_offset=table_offset,descriptor_index=descriptor_index,compressed_size=len(stream),
        source_capacity=end-start,growth_bytes=growth,moved_descriptors=moved,bank_audit=bank_audit,
        following_payload_preserved=True,build_ready=False,gameplay_verified=False)


def rebuild_animation_bank_entry(source,expected_sha256,entry_index,table_offset,descriptor_index,
                                 expected_bank_sha256,bank,*,header_offset=0):
    if not isinstance(source,bytes) or sha256(source).hexdigest()!=expected_sha256:
        raise ImportError('Animation archive source preimage changed')
    if type(entry_index) is not int or type(header_offset) is not int or header_offset not in (0,2048) or len(source)%2048:
        raise ImportError('Animation archive requires typed locators and whole sectors')
    archive=_archive(source)
    if archive.header_offset!=header_offset:
        raise ImportError('Animation archive header locator changed')
    entry=archive.entry(entry_index);span=locate_physical_span(archive,entry.start_lba*2048)
    if span['entry_index']!=entry_index or span['offset_within_span']!=0:
        raise ImportError('Animation archive requires a unique consecutive physical owner')
    start,length=span['byte_offset'],span['byte_length']
    carrier=source[start:start+length]
    encoded,report=grow_scene_animation_bank(carrier,sha256(carrier).hexdigest(),table_offset,
        descriptor_index,expected_bank_sha256,bank)
    encoded+=bytes((-len(encoded))%2048)
    result,audit=replace_physical_entry(source,expected_sha256,entry_index,encoded,header_offset=header_offset)
    reopened=_archive(result);target=reopened.entry(entry_index)
    physical=locate_physical_span(reopened,target.start_lba*2048)
    if ([row.index for row in reopened.entries]!=[row.index for row in archive.entries]
            or physical['entry_index']!=entry_index or physical['byte_length']!=len(encoded)
            or result[physical['byte_offset']:physical['byte_offset']+len(encoded)]!=encoded):
        raise ImportError('Animation archive reopened carrier or entry identities changed')
    return result,dict(entry_index=entry_index,carrier=report,archive=audit,
        reopened_bank_verified=True,physical_neighbors_preserved=True,
        disc_relocation_required=audit['disc_relocation_required'],build_ready=False,gameplay_verified=False)


def verify_rebuilt_animation_banks(source,requests):
    """Read qualified banks after other resource/MAN relocations have finished."""
    if not isinstance(source,bytes) or not isinstance(requests,list) or not 1<=len(requests)<=32:
        raise ImportError('Final animation bank verification requires immutable archive and bounded requests')
    archive=_archive(source);reports=[];seen=set()
    for request in requests:
        fields={'kind','entry_index','table_offset','descriptor_index','expected_bank_sha256','bank'}
        if not isinstance(request,dict) or set(request)!=fields or request['kind']!='animation-bank':
            raise ImportError('Final animation bank request is malformed')
        entry_index,offset,index=(request[k] for k in ('entry_index','table_offset','descriptor_index'))
        if any(type(v) is not int or v<0 for v in (entry_index,offset,index)) or not isinstance(request['bank'],bytes) or not 0<len(request['bank'])<=4*1024*1024:
            raise ImportError('Final animation bank locator or payload is outside bounds')
        identity=(entry_index,offset,index)
        if identity in seen:raise ImportError('Final animation bank requests duplicate a resource')
        seen.add(identity);entry=archive.entry(entry_index);span=locate_physical_span(archive,entry.start_lba*2048)
        if span['entry_index']!=entry_index or span['offset_within_span']!=0:
            raise ImportError('Final animation bank requires its unique physical owner')
        raw=source[span['byte_offset']:span['byte_offset']+span['byte_length']]
        table=parse_scene_assets(raw,entry_index,offset)
        if table is None or not 0<=index<len(table.descriptors):raise ImportError('Final animation bank descriptor is missing')
        descriptor=table.descriptors[index];start=offset+descriptor.data_offset
        end=min([offset+d.data_offset for d in table.descriptors if d.data_offset>descriptor.data_offset]+[len(raw)])
        if descriptor.type_byte!=5 or descriptor.size!=len(request['bank']) or not offset+8+8*len(table.descriptors)<=start<end<=len(raw) or sum(d.data_offset==descriptor.data_offset for d in table.descriptors)!=1:
            raise ImportError('Final animation bank descriptor type, size or span changed')
        decoded,_=decompress_lzs(raw[start:end],descriptor.size)
        if decoded!=request['bank']:raise ImportError('Final animation bank differs after resource or MAN relocation')
        reports.append(dict(entry_index=entry_index,table_offset=offset,descriptor_index=index,
            bank_sha256=sha256(decoded).hexdigest(),record_count=len(animation_record_ranges(decoded)),final_bank_verified=True))
    return reports
