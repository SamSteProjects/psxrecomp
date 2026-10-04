"""Model pack growth in a consecutive-start PROT owner; ISO export is separate."""
from hashlib import sha256
import struct

from .core import ImportError, IsoNode, ProtArchive, parse_scene_assets, decompress_lzs
from .model_pack_growth import grow_scene_model_pack, _qualified_pack
from .prot_layout import locate_physical_span
from .prot_rebuild import replace_physical_entry


def verify_rebuilt_model_packs(source,candidates):
    """Read qualified expected pack hashes after all archive composition."""
    if (not isinstance(source,bytes) or not 0<len(source)<=256*1024*1024 or len(source)%2048 or
            not isinstance(candidates,list) or not 1<=len(candidates)<=32):
        raise ImportError('Final model pack readback requires a bounded archive and candidate batch')
    archive=_archive(source);seen=set();reports=[]
    for row in candidates:
        if (not isinstance(row,dict) or set(row)!={'entry_index','descriptor_index','pack_sha256'} or
                type(row['entry_index']) is not int or row['entry_index']<0 or
                type(row['descriptor_index']) is not int or row['descriptor_index']<0 or
                not isinstance(row['pack_sha256'],str) or len(row['pack_sha256'])!=64 or
                any(c not in '0123456789abcdef' for c in row['pack_sha256'])):
            raise ImportError('Final model pack candidate identity or hash is malformed')
        identity=(row['entry_index'],row['descriptor_index'])
        if identity in seen:raise ImportError('Final model pack readback duplicates a resource')
        seen.add(identity);entry=archive.entry(row['entry_index'])
        span=locate_physical_span(archive,entry.start_lba*2048)
        if span['entry_index']!=entry.index or span['offset_within_span']!=0:
            raise ImportError('Final model pack readback lacks unique physical ownership')
        raw=source[span['byte_offset']:span['byte_offset']+span['byte_length']]
        table=parse_scene_assets(raw,entry.index)
        index=row['descriptor_index']
        if table is None or index>=len(table.descriptors) or table.descriptors[index].type_byte!=2:
            raise ImportError('Final model pack resource descriptor changed')
        table_end=8+8*len(table.descriptors)
        if any(not table_end<=d.data_offset<=len(raw) for d in table.descriptors):
            raise ImportError('Final model pack descriptor payload exceeds its carrier')
        descriptor=table.descriptors[index]
        if sum(d.data_offset==descriptor.data_offset for d in table.descriptors)!=1:
            raise ImportError('Final model pack resource is aliased')
        end=min([d.data_offset for d in table.descriptors if d.data_offset>descriptor.data_offset]+[len(raw)])
        pack,_=decompress_lzs(raw[descriptor.data_offset:end],descriptor.size)
        _qualified_pack(pack)
        if sha256(pack).hexdigest()!=row['pack_sha256']:
            raise ImportError('Final model pack bytes differ from the qualified candidate')
        reports.append(dict(row,final_model_pack_verified=True))
    return reports


class _MemoryImage:
    def __init__(self, data):
        self.data = data

    def read_user(self, _lba, offset, length, file_size):
        if offset < 0 or length < 0 or offset+length > min(file_size, len(self.data)):
            raise ImportError('Model PROT read exceeds archive bounds')
        return self.data[offset:offset+length]


def _archive(data):
    return ProtArchive(_MemoryImage(data), IsoNode(0, len(data), False, 'PROT.DAT'))


def rebuild_model_pack_entry(source, expected_sha256, entry_index, descriptor_index,
                             expected_pack_sha256, replacements, *, header_offset=0):
    if not isinstance(source, bytes) or sha256(source).hexdigest() != expected_sha256:
        raise ImportError('Model PROT source hash changed')
    if (type(entry_index) is not int or type(header_offset) is not int
            or header_offset not in (0, 2048) or len(source) % 2048):
        raise ImportError('Model PROT requires a typed entry/header and whole sectors')
    archive = _archive(source)
    if archive.header_offset != header_offset:
        raise ImportError('Model PROT header location disagrees with caller')
    entry = archive.entry(entry_index)
    span = locate_physical_span(archive, entry.start_lba*2048)
    if span['entry_index'] != entry_index or span['offset_within_span'] != 0:
        raise ImportError('Model PROT entry lacks unique physical ownership')
    start, length = span['byte_offset'], span['byte_length']
    container = source[start:start+length]
    encoded, carrier_audit = grow_scene_model_pack(container, sha256(container).hexdigest(),
        descriptor_index, expected_pack_sha256, replacements, allow_growth=True)
    encoded += bytes((-len(encoded)) % 2048)
    result, archive_audit = replace_physical_entry(source, expected_sha256, entry_index,
                                                 encoded, header_offset=header_offset)
    reopened = _archive(result)
    if [row.index for row in reopened.entries] != [row.index for row in archive.entries]:
        raise ImportError('Model PROT relocation changed readable entry identities')
    target = reopened.entry(entry_index)
    new_span = locate_physical_span(reopened, target.start_lba*2048)
    if new_span['entry_index'] != entry_index or new_span['byte_length'] != len(encoded):
        raise ImportError('Model PROT relocated physical span disagrees with encoded carrier')
    raw = result[new_span['byte_offset']:new_span['byte_offset']+new_span['byte_length']]
    if raw != encoded:
        raise ImportError('Model PROT reopened carrier bytes changed')
    table = parse_scene_assets(raw, entry_index)
    if table is None or not 0 <= descriptor_index < len(table.descriptors):
        raise ImportError('Model PROT reopened resource descriptor is missing')
    descriptor = table.descriptors[descriptor_index]
    end = min([d.data_offset for d in table.descriptors if d.data_offset > descriptor.data_offset]+[len(raw)])
    pack, _ = decompress_lzs(raw[descriptor.data_offset:end], descriptor.size)
    _qualified_pack(pack)
    if sha256(pack).hexdigest() != carrier_audit['pack_audit']['proposed_sha256']:
        raise ImportError('Model PROT reopened decoded pack differs from its qualified candidate')
    header_end = header_offset+struct.unpack_from('<i', source, header_offset+8)[0]*2048
    if result[header_end:start] != source[header_end:start] or result[start+len(encoded):] != source[start+length:]:
        raise ImportError('Model PROT changed another physical payload')
    return result, dict(source_sha256=expected_sha256, proposed_sha256=sha256(result).hexdigest(),
        entry_index=entry_index, source_physical_byte_offset=start,
        proposed_physical_byte_offset=new_span['byte_offset'], source_physical_byte_length=length,
        proposed_physical_byte_length=len(encoded), carrier=carrier_audit, archive=archive_audit,
        reopened_pack_verified=True, physical_neighbors_preserved=True,
        disc_relocation_required=archive_audit['disc_relocation_required'], build_ready=False)
