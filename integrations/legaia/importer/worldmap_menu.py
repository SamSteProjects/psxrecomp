"""Source-backed landmark menu; not world geometry or evaluated story state."""
import hashlib
import struct
from .core import ImportError, validate_metadata_only
from .pipeline import REFERENCE_COMMIT, _disc_context

# Hashes of executing SCUS consumer windows. Keeping these separate from the
# landmark payload qualifies edited source tables without accepting changed code.
CONSUMER_WINDOWS = (
    (139376, 112, '9e3bb811f9b8f120cc0a6d2b818c6bea51d04ce44b4444e0814ab665eede18fa'),
    (134752, 52, '851a4033604f98bd1512114acfd31991dd2ecb8ce17a6da121fad8a663bc80c8'),
    (133100, 20, '9bff2c21ead3be35a883e71dee68c580cf8a6f7e15032ba4064507dd58644ce1'),
    (133288, 52, '9546ef02decb59fbd363619f8ef83d327e8367818fa71cd32df5426d606ca5a6'),
    (185956, 56, 'b4f9cf72c7afddb13a75f5072eb90990d380d3153716a3f087adcc1ae6d900fe'),
    (95400, 8, 'e5608cd2380010fb2871ded7707729adc7976bfaa8a441d7463fbdfca2b7d91a'),
)


def worldmap_field_evidence(executable: bytes) -> dict:
    qualified = (len(executable) >= 0x800 and executable[:8] == b'PS-X EXE'
                 and struct.unpack_from('<I', executable, 0x18)[0] == 0x80010000
                 and all(hashlib.sha256(executable[offset:offset + length]).hexdigest() == expected
                         for offset, length, expected in CONSUMER_WINDOWS))
    return dict(name_index='retail_static_analysis' if qualified else 'reference_interpretation',
                discovery_flag_index='retail_static_analysis' if qualified else 'reference_interpretation',
                destination_scene_id='reference_interpretation', menu_position='reference_interpretation')


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
            'field_evidence':worldmap_field_evidence(executable),
            'limitations':['X/Y are encoded bytes with a reference menu-pixel interpretation; executing draw consumers and 3D world coordinates are unverified.',
                           'Discovery indices add32 to the encoded byte. Qualified retail consumers query a system bitmap; current flags are not read.',
                           'Source rows remain distinct. The qualified executing walker deduplicates against the last accepted name; current discovery/activation is not evaluated.',
                           'Destination numeric IDs are not resolved to CDNAME labels or asserted reachable.']}
    validate_metadata_only(result)
    return result


def resolve_menu_destinations(report: dict, mapping: dict, cdname_sha256: str) -> dict:
    from copy import deepcopy
    result=deepcopy(report)
    for row in result['placements']:
        row['destination_source_label']=mapping.get(row['destination_scene_id'])
    result['destination_label_source']={'iso_file':'CDNAME.TXT','sha256':cdname_sha256,
                                      'association':'exact_define_numeric_value'}
    result['limitations']=[note for note in result['limitations'] if not note.startswith('Destination numeric IDs')]
    result['limitations'].append('Destination labels are exact CDNAME definitions; labels alone do not establish supported scene import, a traversable edge or gameplay reachability.')
    return result


def load_worldmap_menu(disc) -> dict:
    with _disc_context(disc) as (image,digest,mapping,__):
        node=image.find('SCUS_942.54')
        if node.size>2*1024*1024:raise ImportError('Executable exceeds world-map inspection budget')
        result=decode_worldmap_menu(image.read_file(node))
        result['source_record']['disc_sha256']=digest
        cdname=image.read_file(image.find('CDNAME.TXT'))
        result=resolve_menu_destinations(result,mapping,hashlib.sha256(cdname).hexdigest())
    return result


def load_worldmap_asset_catalog(disc, scene: str) -> dict:
    """Expose global menu records through the derived asset database."""
    from copy import deepcopy
    report = load_worldmap_menu(disc)
    assets = []
    for placement in report['placements']:
        assets.append({**deepcopy(placement), 'asset_kind': 'worldmap', 'kind': 'worldmap',
                       'scope': 'global-worldmap-menu',
                       'name': f"{placement['name'] or 'Unresolved landmark'} · record {placement['record_index']:02d}",
                       'source_record': deepcopy(report['source_record']),
                       'destination_label_source': deepcopy(report['destination_label_source']),
                       'reference_commit': report['reference_commit'], 'reference_path': report['reference_path'],
                       'field_evidence': deepcopy(report['field_evidence']),
                       'runtime_state': 'not_observed'})
    result = {'schema_version': 'legaia.worldmap-asset-catalog.v1', 'assets': assets,
              'scope': 'global-worldmap-menu', 'metadata_only': True,
              'limitations': deepcopy(report['limitations'])}
    validate_metadata_only(result)
    return result
