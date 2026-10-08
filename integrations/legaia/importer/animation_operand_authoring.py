"""Fixed native animation arguments; no clip binding or runtime pose inference.

Pinned field/step/menu_ctrl/nibble_8.rs sub1 reads u24/u16/u16 and advances;
field/step/effect.rs high-nibble3 reads one byte and advances. Dispatch selectors
and extended actor contexts remain immutable. Variable ANIMATE packets stay out
of this writer until their individual ownership is implemented.
"""
from copy import deepcopy
from hashlib import sha256
import re
from .core import ImportError
from .dialogue_authoring import load_dialogue_authoring_context
from .script_inspection import inspect_record

SPECS = {
    'SET_MODEL_ANIMATION': (('model_id',3),('animation_frame',2),('tween_frames',2)),
    'EFFECT_ANIMATION_TRIGGER': (('animation_operand',1),),
}
LIMITATIONS = [
    'Only reached fixed SET_MODEL_ANIMATION and EFFECT_ANIMATION_TRIGGER arguments in records without decoder stops are editable.',
    'Model IDs and effect animation operands are encoded arguments, not resolved SDK model or clip asset identities.',
    'Frame/tween operands are unsigned16 native fields; pose, time units, valid clip ranges and host behavior remain unverified.',
    'Opcode, selector, extended dispatch context, instruction/record lengths, branch edges and all unrelated bytes remain fixed.',
    'Variable ANIMATE packets, execution, scheduling, runtime actor identity and animation playback are not inferred.'
]


def validate_animation_operand_values(mnemonic, values):
    spec=SPECS.get(mnemonic)
    if spec is None or not isinstance(values,dict) or set(values)!={key for key,_ in spec}:
        raise ImportError('Animation operands require the exact typed fields of their fixed instruction')
    output=bytearray()
    for key,width in spec:
        value=values[key]
        if type(value) is not int or not 0<=value<(1<<(width*8)):
            raise ImportError(f'Animation operand {key} must be an integer 0..{(1<<(width*8))-1}')
        output.extend(value.to_bytes(width,'little'))
    return bytes(output)


def _target(record,entry,pc,report=None):
    if type(pc) is not int or not 0<=pc<=min(65535,len(record)-1):
        raise ImportError('Animation operand PC must be a source-record offset')
    report=inspect_record(record,entry) if report is None else report
    if report['stops']:
        raise ImportError('Animation operand authoring requires no unknown/conflicting source-path stops')
    node=next((row for row in report['instructions'] if row['pc']==pc),None)
    if node is None or node['mnemonic'] not in SPECS:
        raise ImportError('Animation operand PC must identify a reached supported fixed instruction')
    header=2 if node['target_context'] is not None else 1
    selector=record[pc+header]
    opcode=record[pc]&127
    if ((node['mnemonic']=='SET_MODEL_ANIMATION' and (opcode!=0x4c or selector!=0x81)) or
            (node['mnemonic']=='EFFECT_ANIMATION_TRIGGER' and (opcode!=0x34 or selector>>4!=3)) or
            node['length']!=header+1+sum(width for _,width in SPECS[node['mnemonic']])):
        raise ImportError('Animation operand differs from its fixed native dispatch or layout')
    return node,pc+header+1,report


def _values(node):
    return {key:node['operands'][key] for key,_ in SPECS[node['mnemonic']]}


def patch_animation_operands_target(record,entry,pc,values,*,base_offset=0):
    if type(base_offset) is not int or base_offset<0:
        raise ImportError('Animation operand base offset must be nonnegative')
    node,offset,report=_target(record,entry,pc)
    encoded=validate_animation_operand_values(node['mnemonic'],values)
    before=record[offset:offset+len(encoded)]
    if before==encoded:
        return record,[]
    result=record[:offset]+encoded+record[offset+len(encoded):]
    check=inspect_record(result,entry)
    shape=lambda r:[(n['pc'],n['mnemonic'],n['length'],n['target_context'],n['successors']) for n in r['instructions']]
    if check['stops']!=report['stops'] or shape(check)!=shape(report):
        raise ImportError('Animation edit changed instruction layout, dispatch or continuations')
    audit=[];relative=0
    for field,width in SPECS[node['mnemonic']]:
        old=before[relative:relative+width];new=encoded[relative:relative+width]
        if old!=new:
            audit.append(dict(field=field,pc=pc,mnemonic=node['mnemonic'],target_context=node['target_context'],
                              record_relative_byte_offset=offset+relative,decoded_byte_offset=base_offset+offset+relative,
                              byte_length=width,before_hex=old.hex(),after_hex=new.hex(),
                              before_value=node['operands'][field],after_value=values[field],source_record_sha256=sha256(record).hexdigest()))
        relative+=width
    return result,audit


class AnimationOperandAuthoringContext:
    def __init__(self,source):self._source,self._man=source,source._man
    def provenance(self):return dict(self._source.provenance(),limitations=list(LIMITATIONS))

    def options(self,owner):
        offset,record,entry=self._source.verified_record(owner);report=inspect_record(record,entry);targets=[]
        if not report['stops']:
            for node in report['instructions']:
                if node['mnemonic'] not in SPECS:continue
                _,relative,_=_target(record,entry,node['pc'],report)
                targets.append(dict(semantic_id='script://'+owner.removeprefix('scene://')+f"/animation-operands/{node['pc']:04x}",
                                    owner_id=owner,pc=node['pc'],mnemonic=node['mnemonic'],target_context=node['target_context'],
                                    decoded_byte_offset=offset+relative,instruction_length=node['length'],
                                    raw_instruction_hex=node['raw_hex'],values=_values(node),source_record_sha256=sha256(record).hexdigest()))
        return dict(supported=bool(targets),targets=targets,source=self.provenance(),limitations=list(LIMITATIONS),
                    reason='Animation operand authoring requires no decoder stops' if report['stops'] else None)

    def _requests(self,edits):
        if not isinstance(edits,dict) or len(edits)>1024:
            raise ImportError('Animation operand edit set exceeds bounds')
        requests=[]
        for key,values in sorted(edits.items(),key=lambda pair:str(pair[0])):
            match=re.fullmatch(r'script://([A-Za-z0-9_-]+/(?:actors/man-p1|scripts/man-p2)/[0-9]{4})/animation-operands/([0-9a-f]{4})',key) if isinstance(key,str) else None
            if match is None:raise ImportError('Animation operand identity requires source owner and hexadecimal PC')
            owner='scene://'+match[1];offset,record,entry=self._source.verified_record(owner);pc=int(match[2],16)
            node,relative,_=_target(record,entry,pc);validate_animation_operand_values(node['mnemonic'],values)
            requests.append((key,owner,offset,record,entry,pc,node,relative,deepcopy(values)))
        return requests

    def patch(self,edits,*,original=None):
        if original is not None and original!=self._man:raise ImportError('Animation operand MAN differs from verified source')
        result=bytearray(self._man);audit=[];occupied=set()
        for key,owner,offset,record,entry,pc,node,relative,values in self._requests(edits):
            _,changes=patch_animation_operands_target(record,entry,pc,values,base_offset=offset)
            span=set(range(offset+pc,offset+pc+node['length']))
            if occupied&span:raise ImportError('Animation operand source instruction ownership overlaps')
            occupied.update(span)
            for change in changes:
                at=change['decoded_byte_offset'];result[at:at+change['byte_length']]=bytes.fromhex(change['after_hex'])
                audit.append(dict(change,animation_operand_id=key,owner_id=owner,source_decoded_man_sha256=sha256(self._man).hexdigest()))
        return bytes(result),sorted(audit,key=lambda row:row['decoded_byte_offset'])

    def patch_appended(self,candidate,edits):
        from .man_layout import read_man_layout
        layout=read_man_layout(candidate);result=bytearray(candidate);audit=[];occupied=set()
        for key,owner,offset,record,entry,pc,node,relative,values in self._requests(edits):
            partition=2 if '/scripts/man-p2/' in owner else 1;index=int(owner.rsplit('/',1)[1])
            rows=[r for r in layout['records'] if r['partition']==partition and r['record_index']==index]
            if len(rows)!=1 or rows[0]['byte_length']!=len(record):raise ImportError('Appended animation owner differs from its source extent')
            start=rows[0]['byte_offset'];span=set(range(start+pc,start+pc+node['length']))
            if occupied&span or sum(r['byte_offset']==start for r in layout['records'])!=1:
                raise ImportError('Appended animation instruction ownership is aliased or overlapping')
            occupied.update(span)
            # Check the whole fixed instruction even for no-op requests.
            if candidate[start+pc:start+pc+node['length']]!=record[pc:pc+node['length']]:
                raise ImportError('Appended animation instruction, context, selector or preimage differs from source')
            _,changes=patch_animation_operands_target(candidate[start:start+len(record)],entry,pc,values,base_offset=start)
            for change in changes:
                at=change['decoded_byte_offset'];result[at:at+change['byte_length']]=bytes.fromhex(change['after_hex'])
                audit.append(dict(change,animation_operand_id=key,owner_id=owner,source_decoded_man_sha256=sha256(self._man).hexdigest(),
                                  source_decoded_byte_offset=offset+change['record_relative_byte_offset'],appended_man_sha256=sha256(candidate).hexdigest()))
        output=bytes(result)
        if read_man_layout(output)!=layout:raise ImportError('Animation operand edit changed appended MAN structure')
        return output,sorted(audit,key=lambda row:row['decoded_byte_offset'])


def load_animation_operand_authoring_context(disc,scene):
    return AnimationOperandAuthoringContext(load_dialogue_authoring_context(disc,scene))
