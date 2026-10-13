"""Existing complete pack TIM CLUT words; immutable layout and index pixels."""
from copy import deepcopy
from hashlib import sha256
import struct
from .core import ImportError
from .textures import parse_tim,decode_tim


def source(original,catalog,record):
    if (not isinstance(original,bytes) or not isinstance(catalog,dict) or record not in catalog.get('textures',[])
            or catalog.get('source_entry_index')!=1204 or len(original)!=catalog.get('source_entry_byte_length')
            or sha256(original).hexdigest()!=catalog.get('source_entry_sha256')
            or record.get('preview_supported') is not True or record.get('status')!='available'):
        raise ImportError('Pack palette requires its complete immutable Retail TIM source')
    s=record['source_record'];at=s['byte_offset'];length=s['byte_length'];body=original[at:at+length]
    if (s['prot_entry_index']!=1204 or s['record_kind']!='raw_prot_entry' or s['containing_sha256']!=catalog['source_entry_sha256']
            or s['containing_size']!=len(original) or length!=33312 or len(body)!=length or sha256(body).hexdigest()!=s['sha256']
            or record['bpp']!=4 or record['palette_count']!=16 or record['clut']['width_words']!=256 or record['clut']['height']!=1):
        raise ImportError('Pack palette source span or CLUT footprint changed')
    parse_tim(body)
    return body


def effective(original,catalog,record,binding=None):
    retail=source(original,catalog,record)
    if binding is None:return retail
    if (not isinstance(binding,dict) or set(binding)!={'schema_version','asset_id','source_record','edits','current_tim_sha256'}
            or binding['schema_version']!='legaia.battle-pack-palette-override.v1'
            or binding['asset_id']!=record['semantic_id'] or binding['source_record']!=record['source_record']
            or not isinstance(binding['edits'],list) or not 1<=len(binding['edits'])<=256):
        raise ImportError('Pack palette owner or native word ledger changed')
    result=bytearray(retail);seen=[]
    for row in binding['edits']:
        if (not isinstance(row,dict) or set(row)!={'palette_index','entry_index','word'}
                or any(type(row[k]) is not int for k in row)
                or not 0<=row['palette_index']<16 or not 0<=row['entry_index']<16 or not 0<=row['word']<=65535):
            raise ImportError('Pack palette requires existing typed CLUT cells and unsigned16 words')
        pair=(row['palette_index'],row['entry_index']);at=20+pair[0]*32+pair[1]*2
        if pair in seen or struct.unpack_from('<H',retail,at)[0]==row['word']:
            raise ImportError('Pack palette ledger repeats a cell or retains an unchanged Retail word')
        seen.append(pair);struct.pack_into('<H',result,at,row['word'])
    if seen!=sorted(seen) or sha256(result).hexdigest()!=binding['current_tim_sha256']:
        raise ImportError('Pack palette canonical replay hash changed')
    return bytes(result)


def compose(original,catalog,values,model_entry=None):
    if (not isinstance(original,bytes) or not isinstance(catalog,dict) or catalog.get('source_entry_index')!=1204
            or len(original)!=catalog.get('source_entry_byte_length') or sha256(original).hexdigest()!=catalog.get('source_entry_sha256')
            or model_entry is not None and not isinstance(model_entry,bytes)):
        raise ImportError('Pack palette composition requires the complete immutable entry and native model bytes')
    if not isinstance(values,dict) or len(values)>6:raise ImportError('Pack palette owners exceed the six complete TIMs')
    result=bytearray(original if model_entry is None else model_entry)
    if len(result)!=len(original):raise ImportError('Pack palette composition changed the entry footprint')
    if model_entry is not None:
        model_bytes={i for r in catalog['models'] for i in range(r['source_record']['byte_offset'],r['source_record']['byte_offset']+r['source_record']['byte_length'])}
        if any(a!=b and i not in model_bytes for i,(a,b) in enumerate(zip(original,result))):
            raise ImportError('Pack palette base contains changes outside existing model spans')
    for identifier,binding in sorted(values.items()):
        record=next((r for r in catalog['textures'] if r['semantic_id']==identifier),None)
        if record is None:raise ImportError('Pack palette owner has no immutable source')
        body=effective(original,catalog,record,binding);at=record['source_record']['byte_offset']
        if result[at:at+20]!=body[:20] or result[at+532:at+len(body)]!=body[532:]:
            raise ImportError('Pack palette composition changed protected TIM headers or image bytes')
        result[at+20:at+532]=body[20:532]
    return bytes(result)


def project(original,catalog,record,binding,palette_index,entry_index,word):
    if (any(type(n) is not int for n in (palette_index,entry_index,word))
            or not 0<=palette_index<16 or not 0<=entry_index<16 or not 0<=word<=65535):
        raise ImportError('Choose an existing pack palette cell and unsigned16 native word')
    retail=source(original,catalog,record);before=effective(original,catalog,record,binding)
    at=20+palette_index*32+entry_index*2;candidate=bytearray(before);struct.pack_into('<H',candidate,at,word);candidate=bytes(candidate)
    edits=[dict(palette_index=i//16,entry_index=i%16,word=struct.unpack_from('<H',candidate,20+i*2)[0])
           for i in range(256) if candidate[20+i*2:22+i*2]!=retail[20+i*2:22+i*2]]
    owner=dict(schema_version='legaia.battle-pack-palette-override.v1',asset_id=record['semantic_id'],
        source_record=deepcopy(record['source_record']),edits=edits,current_tim_sha256=sha256(candidate).hexdigest()) if edits else None
    if effective(original,catalog,record,owner)!=candidate:raise ImportError('Pack palette proposal differs from native replay')
    return owner,candidate,dict(palette_index=palette_index,entry_index=entry_index,word=word,before_word=struct.unpack_from('<H',before,at)[0],tim_word_byte_offset=at,
        current_tim_sha256=sha256(before).hexdigest(),candidate_tim_sha256=sha256(candidate).hexdigest(),byte_change_count=sum(a!=b for a,b in zip(before,candidate)),
        unchanged_header_sha256=sha256(before[:20]+before[532:544]).hexdigest(),unchanged_image_sha256=sha256(before[544:]).hexdigest())


def preview(body,palette_index):
    if type(palette_index) is not int or not 0<=palette_index<16:raise ImportError('Choose an existing whole pack palette')
    value=decode_tim(body,palette_index)
    value['words']=list(struct.unpack_from('<16H',body,20+palette_index*32))
    return value


def qualify_entry(original,catalog,current):
    """Texture-only view context; models and headers stay Retail; existing CLUT/index payloads may change."""
    if not isinstance(current,bytes) or len(current)!=len(original):raise ImportError('Pack texture context changed the entry footprint')
    allowed=set()
    for record in catalog['textures']:
        if not record['preview_supported']:continue
        source(original,catalog,record);at=record['source_record']['byte_offset']
        allowed.update(range(at+20,at+532));allowed.update(range(at+544,at+record['source_record']['byte_length']))
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(original,current))):
        raise ImportError('Pack texture context changed models, layout or partial atlas bytes')
    return current
