"""Only the twelve evidenced stored monster header words/bytes are writable."""
from hashlib import sha256
import struct
from .core import ImportError

FIELDS=tuple(dict(field='stored_stats.'+name,byte_offset=0x0c+index*2,byte_width=2,min_value=0,max_value=65535) for index,name in enumerate(('hp','agility','mp','attack','defense_high','defense_low','intelligence','speed')))+(
 dict(field='stored_rewards.gold',byte_offset=0x44,byte_width=2,min_value=0,max_value=65535),
 dict(field='stored_rewards.experience',byte_offset=0x46,byte_width=2,min_value=0,max_value=65535),
 dict(field='stored_rewards.drop_item',byte_offset=0x48,byte_width=1,min_value=0,max_value=255),
 dict(field='stored_rewards.drop_chance',byte_offset=0x49,byte_width=1,min_value=0,max_value=255))
_layout={row['field']:(row['byte_offset'],row['byte_width'],row['max_value']) for row in FIELDS}


def header_values(data):
    if not isinstance(data,bytes) or not 0x4c<=len(data)<=0xa0000:
        raise ImportError('Monster stored record requires an exact bounded native header')
    return {field:struct.unpack_from('<H',data,at)[0] if width==2 else data[at] for field,(at,width,_) in _layout.items()}


def requested_values(values):
    if not isinstance(values,dict) or not 1<=len(values)<=len(_layout):
        raise ImportError('Monster record edits require a nonempty field/value mapping')
    for field,value in values.items():
        if field not in _layout or type(value) is not int or not 0<=value<=_layout[field][2]:
            raise ImportError('Monster record field or exact unsigned native value is unsupported')
    return dict(values)


def patch(original,current,record,values):
    source=record.get('source_record') if isinstance(record,dict) else None
    if not isinstance(original,bytes) or not isinstance(current,bytes) or len(original)!=len(current) or not isinstance(record,dict) or record.get('asset_kind')!='monster_record' or not isinstance(source,dict) or source.get('byte_offset')!=0 or source.get('byte_length')!=0x4c or source.get('containing_size')!=len(original) or sha256(original[:0x4c]).hexdigest()!=source.get('sha256'):
        raise ImportError('Monster stored header provenance changed')
    retail=header_values(original);before=header_values(current)
    expected={group+'.'+field:value for group in ('stored_stats','stored_rewards') for field,value in record.get(group,{}).items()}
    if expected!=retail:raise ImportError('Monster catalog values differ from their literal Retail header')
    requested=requested_values(values);candidate=bytearray(current);audit=[]
    for field,value in sorted(requested.items()):
        at,width,_=_layout[field]
        if before[field]==value:continue
        if width==2:struct.pack_into('<H',candidate,at,value)
        else:candidate[at]=value
        audit.append(dict(field=field,byte_offset=at,byte_width=width,before_value=before[field],after_value=value,
            byte_change_count=sum(a!=b for a,b in zip(current[at:at+width],candidate[at:at+width]))))
    result=bytes(candidate);allowed={offset for row in audit for offset in range(row['byte_offset'],row['byte_offset']+row['byte_width'])}
    if any(a!=b and at not in allowed for at,(a,b) in enumerate(zip(current,result))):
        raise ImportError('Monster record patch changed an unowned native byte')
    return result,audit
