"""Source-backed landmark menu; not world geometry or evaluated story state."""
import hashlib
import struct
from .core import ImportError, validate_metadata_only
from .pipeline import REFERENCE_COMMIT, _disc_context


def decode_worldmap_menu(executable: bytes) -> dict:
    if not isinstance(executable, bytes) or not 0x800 <= len(executable) <= 2*1024*1024 or executable[:8] != b'PS-X EXE':
        raise ImportError('World-map menu requires a bounded PS-X executable')
    load = struct.unpack_from('<I',executable,0x18)[0]
    def span(address,length):
        offset=0x800+address-load
        if address<load or offset<0x800 or offset+length>len(executable):
            raise ImportError('World-map menu table is outside the executable')
        return offset,executable[offset:offset+length]
    name_offset,raw_names=span(0x80073B18,16*32)
    table_offset,table=span(0x80073A98,64*6)
    names=[]
    for i in range(16):
        value=raw_names[i*32:(i+1)*32].split(b'\0',1)[0]
        if any(v<32 or v>=127 for v in value):raise ImportError('World-map landmark name contains unsupported characters')
        names.append({'index':i,'name':value.decode('ascii'),'source_offset':name_offset+i*32})
    records=[]
    for i in range(64):
        name,flag,scene,x,y=struct.unpack_from('<BBHBB',table,i*6)
        if name==255:break
        records.append({'semantic_id':f'worldmap://legaia/menu/placements/{i:04d}',
                        'record_index':i,'name_index':name,'name':names[name]['name'] if name<16 else None,
                        'resolved_name':name<16,'discovery_flag_encoded':flag,'discovery_flag_index':flag+32,
                        'destination_scene_id':scene,'menu_position':{'x':x,'y':y},
                        'source_offset':table_offset+i*6,'byte_length':6})
    else:raise ImportError('World-map placement table has no bounded terminator')
    result={'schema_version':'legaia.worldmap-menu.v1','reference_commit':REFERENCE_COMMIT,
            'reference_path':'crates/asset/src/worldmap_menu.rs','source_record':{'iso_file':'SCUS_942.54',
            'sha256':hashlib.sha256(executable).hexdigest(),'load_address':load,'table_file_offset':table_offset,
            'table_ram_address':0x80073A98,'name_table_file_offset':name_offset,'terminator_record_index':i},
            'names':names,'placements':records,'metadata_only':True,'runtime_state':'not_observed',
            'limitations':['Positions are world-map menu pixels, not field or 3D world coordinates.',
                           'Discovery flag indices use the reference fourth system-flag bank; current flags are not read.',
                           'Consecutive duplicate names are retained as source records; runtime menu deduplication is not evaluated.',
                           'Destination numeric IDs are not resolved to CDNAME labels or asserted reachable.']}
    validate_metadata_only(result)
    return result


def load_worldmap_menu(disc) -> dict:
    with _disc_context(disc) as (image,digest,_,__):
        node=image.find('SCUS_942.54')
        if node.size>2*1024*1024:raise ImportError('Executable exceeds world-map inspection budget')
        result=decode_worldmap_menu(image.read_file(node))
        result['source_record']['disc_sha256']=digest
    return result
