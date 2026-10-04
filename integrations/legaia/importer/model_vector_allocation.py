"""Append native SVECTOR rows without changing existing indices or opaque bytes.

New rows have explicit signed XYZ and zero padding. Packet references encode
16-bit byte offsets, so each addressable vector table is bounded to 8192 rows.
This codec does not publish bindings, edit face packets or relocate carriers.
"""
from hashlib import sha256
import struct
from .assets import MAX_MODEL_BYTES
from .core import ImportError
from .model_primitives import _qualified_model

MAX_NEW_VECTORS = 4096
MAX_ADDRESSABLE_VECTORS = 8192


def append_model_vectors(data,expected_sha256,requests):
    inspection,_=_qualified_model(data)
    if sha256(data).hexdigest()!=expected_sha256:
        raise ImportError('Vector allocation source hash changed')
    if not isinstance(requests,list) or not 0<len(requests)<=2048:
        raise ImportError('Vector allocation requires bounded nonempty table requests')
    tables={};total=0
    for request in requests:
        if (not isinstance(request,dict) or set(request)!={'object_index','kind','vectors'}
                or type(request['object_index']) is not int
                or not 0<=request['object_index']<len(inspection['objects'])
                or request['kind'] not in ('vertices','normals')
                or not isinstance(request['vectors'],list) or not request['vectors']):
            raise ImportError('Vector allocation requires exact object, table and XYZ rows')
        identity=(request['object_index'],request['kind'])
        if identity in tables:
            raise ImportError('Vector allocation repeats an existing table request')
        total+=len(request['vectors'])
        if total>MAX_NEW_VECTORS:
            raise ImportError('Vector allocation exceeds its new row budget')
        if any(not isinstance(row,list) or len(row)!=3 or any(type(value) is not int or not -32768<=value<=32767 for value in row) for row in request['vectors']):
            raise ImportError('New SVECTOR rows require signed 16-bit integer XYZ')
        owner,kind=identity;field=0 if kind=='vertices' else 8;header=12+owner*28
        offset,count=struct.unpack_from('<II',data,header+field)
        if count+len(request['vectors'])>MAX_ADDRESSABLE_VECTORS:
            raise ImportError('New vectors exceed native 16-bit byte-offset addressing')
        # An unused table has no owned pointer anchor; allocate it at EOF.
        at=12+offset+count*8 if count else len(data)
        payload=b''.join(struct.pack('<4h',*row,0) for row in request['vectors'])
        tables[identity]=dict(owner=owner,kind=kind,field=field,count=count,at=at,payload=payload)
    growth=total*8
    if len(data)+growth>MAX_MODEL_BYTES:
        raise ImportError('Vector allocation exceeds the model byte budget')
    events={}
    for identity,table in sorted(tables.items()):events.setdefault(table['at'],[]).append(table)
    candidate=bytearray();previous=0;allocations=[]
    for at,rows in sorted(events.items()):
        candidate.extend(data[previous:at])
        # Extend a table ending here before creating unused tables at EOF.
        # Otherwise the new table would interrupt the existing vector span.
        rows.sort(key=lambda row:(not bool(row['count']),row['owner'],row['kind']))
        for row in rows:
            row['new_rows_start']=len(candidate)
            candidate.extend(row['payload'])
            allocations.append(dict(object_index=row['owner'],kind=row['kind'],first_index=row['count'],
                added_count=len(row['payload'])//8,byte_offset=row['new_rows_start']))
        previous=at
    candidate.extend(data[previous:])
    def relocate(offset):
        return offset+sum(len(row['payload']) for at,rows in events.items() if at<=offset for row in rows)
    pointers=[]
    for obj in inspection['objects']:
        owner=obj['object_index'];header=12+owner*28
        for field in (0,8,16):
            old=struct.unpack_from('<I',data,header+field)[0]
            count=struct.unpack_from('<I',data,header+field+4)[0]
            kind='vertices' if field==0 else 'normals' if field==8 else None
            table=tables.get((owner,kind))
            new=(table['new_rows_start']-12 if table and not count else
                 relocate(old+12)-12 if field==16 or count else old)
            struct.pack_into('<I',candidate,header+field,new)
            if table:struct.pack_into('<I',candidate,header+field+4,count+len(table['payload'])//8)
            pointers.append(dict(object_index=owner,table_field_offset=field,source_offset=old,current_offset=new))
    candidate=bytes(candidate);_qualified_model(candidate)
    return candidate,dict(source_sha256=expected_sha256,proposed_sha256=sha256(candidate).hexdigest(),
        source_byte_length=len(data),proposed_byte_length=len(candidate),growth_bytes=growth,
        new_vectors=allocations,pointer_relocations=pointers)


def qualify_model_vector_allocation(data,expected_sha256,candidate,requests):
    expected,audit=append_model_vectors(data,expected_sha256,requests)
    if candidate!=expected:
        raise ImportError('Vector allocation candidate differs from its complete source-bound replay')
    return audit
