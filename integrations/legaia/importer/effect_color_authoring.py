"""Fixed-width source EFFECT sub0 operands; host rendering is not evaluated."""
from copy import deepcopy
from hashlib import sha256
import re,struct
from .core import ImportError
from .dialogue_authoring import load_dialogue_authoring_context
from .script_inspection import inspect_record

LIMITATIONS=[
    'Only reached EFFECT_COLOR_INTENSITY instructions in records without decoder stops are editable.',
    'Red/green/blue are encoded unsigned bytes and intensity is signed16; visual color space and host effect are unresolved.',
    'Opcode, actor context, selector, branch bytes, instruction/record lengths and all other bytes are preserved.',
    'Native serialization is supported; actual rendering and runtime scheduling require gameplay verification.'
]

def validate_effect_color_values(values):
    if not isinstance(values,dict) or set(values)!={'red','green','blue','intensity'}:
        raise ImportError('Effect color requires red, green, blue and intensity only')
    for key in ('red','green','blue','intensity'):
        low,high=(-32768,32767) if key=='intensity' else (0,255)
        if type(values[key]) is not int or not low<=values[key]<=high:
            raise ImportError(f'Effect color {key} must be an integer {low}..{high}')
    return struct.pack('<BBBh',values['red'],values['green'],values['blue'],values['intensity'])

def _values(node):
    return dict(zip(('red','green','blue'),node['operands']['rgb']),intensity=node['operands']['intensity'])

def _target(record,entry,pc,report=None):
    if type(pc) is not int or not 0<=pc<len(record):raise ImportError('Effect color PC must be a source-record offset')
    report=inspect_record(record,entry) if report is None else report
    if report['stops']:raise ImportError('Effect color authoring requires no unknown/conflicting source-path stops')
    node=next((row for row in report['instructions'] if row['pc']==pc),None)
    if node is None or node['mnemonic']!='EFFECT_COLOR_INTENSITY':raise ImportError('Effect color PC must identify a reached sub0 instruction')
    return node,pc+(2 if node['target_context'] is not None else 1)+1,report

def patch_effect_color_target(record,entry,pc,values,*,base_offset=0):
    after=validate_effect_color_values(values)
    if type(base_offset) is not int or base_offset<0:raise ImportError('Effect color base offset must be nonnegative')
    node,offset,report=_target(record,entry,pc);before=record[offset:offset+5]
    if before==after:return record,[]
    result=record[:offset]+after+record[offset+5:];check=inspect_record(result,entry)
    shape=lambda r:[(n['pc'],n['mnemonic'],n['length'],n['target_context'],n['successors']) for n in r['instructions']]
    if check['stops']!=report['stops'] or shape(check)!=shape(report):raise ImportError('Effect color edit changed instruction layout or continuations')
    return result,[dict(field='color_intensity',pc=pc,mnemonic=node['mnemonic'],target_context=node['target_context'],
        record_relative_byte_offset=offset,decoded_byte_offset=base_offset+offset,byte_length=5,before_hex=before.hex(),after_hex=after.hex(),
        before_values=_values(node),after_values=deepcopy(values),source_record_sha256=sha256(record).hexdigest())]

class EffectColorAuthoringContext:
    def __init__(self,source):self._source,self._man=source,source._man
    def provenance(self):return dict(self._source.provenance(),limitations=list(LIMITATIONS))
    def options(self,owner):
        offset,record,entry=self._source.verified_record(owner);report=inspect_record(record,entry);targets=[]
        if not report['stops']:
            for node in report['instructions']:
                if node['mnemonic']!='EFFECT_COLOR_INTENSITY':continue
                _,relative,_=_target(record,entry,node['pc'],report)
                targets.append(dict(semantic_id='script://'+owner.removeprefix('scene://')+f"/effect-color/{node['pc']:04x}",owner_id=owner,
                    pc=node['pc'],mnemonic=node['mnemonic'],target_context=node['target_context'],decoded_byte_offset=offset+relative,
                    values=_values(node),source_record_sha256=sha256(record).hexdigest()))
        return dict(supported=bool(targets),targets=targets,unavailable=[],reason='Effect color authoring requires no decoder stops' if report['stops'] else None,
                    source=self.provenance(),limitations=list(LIMITATIONS))
    def patch(self,edits,*,original=None):
        if original is not None and original!=self._man:raise ImportError('Effect color MAN differs from verified source')
        if not isinstance(edits,dict) or len(edits)>1024:raise ImportError('Effect color edit set exceeds bounds')
        audit=[];occupied=set()
        for key,values in edits.items():
            match=re.fullmatch(r'script://([A-Za-z0-9_-]+/(?:actors/man-p1|scripts/man-p2)/[0-9]{4})/effect-color/([0-9a-f]{4})',key) if isinstance(key,str) else None
            if match is None:raise ImportError('Effect color identity requires source owner and hexadecimal PC')
            owner='scene://'+match[1];offset,record,entry=self._source.verified_record(owner)
            _,changes=patch_effect_color_target(record,entry,int(match[2],16),values,base_offset=offset)
            for change in changes:
                span=set(range(change['decoded_byte_offset'],change['decoded_byte_offset']+5))
                if span&occupied:raise ImportError('Effect color edits overlap another authored span')
                occupied.update(span);audit.append(dict(change,effect_color_id=key,owner_id=owner,source_decoded_man_sha256=sha256(self._man).hexdigest()))
        result=bytearray(self._man);audit.sort(key=lambda c:c['decoded_byte_offset'])
        for change in audit:
            at=change['decoded_byte_offset'];result[at:at+5]=bytes.fromhex(change['after_hex'])
        return bytes(result),deepcopy(audit)
    def patch_appended(self,candidate,edits):
        from .man_layout import read_man_layout
        _,changes=self.patch(edits);layout=read_man_layout(candidate);records={(r['partition'],r['record_index']):r for r in layout['records']};result=bytearray(candidate);audit=[]
        for change in changes:
            owner=change['owner_id'];_,record,entry=self._source.verified_record(owner);partition=2 if '/scripts/man-p2/' in owner else 1
            target=records.get((partition,int(owner.rsplit('/',1)[1])))
            if target is None or target['byte_length']!=len(record):raise ImportError('Appended effect color owner differs from verified source extent')
            start=target['byte_offset']
            if sum(r['byte_offset']==start for r in layout['records'])!=1:raise ImportError('Appended effect color owner is aliased')
            node,relative,_=_target(candidate[start:start+len(record)],entry,change['pc']);at=start+relative
            if relative!=change['record_relative_byte_offset'] or candidate[at:at+5].hex()!=change['before_hex']:raise ImportError('Appended effect color instruction or preimage differs from source')
            result[at:at+5]=bytes.fromhex(change['after_hex']);audit.append(dict(change,source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at,
                appended_man_sha256=sha256(candidate).hexdigest(),appended_target_context=node['target_context']))
        result=bytes(result)
        if read_man_layout(result)!=layout:raise ImportError('Effect color authoring changed appended MAN layout')
        return result,audit

def load_effect_color_authoring_context(disc,scene):return EffectColorAuthoringContext(load_dialogue_authoring_context(disc,scene))
