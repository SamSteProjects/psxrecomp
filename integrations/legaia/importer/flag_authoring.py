"""Source-preserving flag-bit operands; runtime variable identities remain unresolved.

Pinned evidence: engine-vm/src/field/step.rs 0x2B..0x33 and ctx.rs flag widths.
Only low-five-bit indices change. Context SET8/CLEAR10 side effects remain gated.
"""
from copy import deepcopy
import hashlib,re
from .core import ImportError
from .script_inspection import inspect_record
from .dialogue_authoring import load_dialogue_authoring_context

MAX_FLAG_EDITS=1024
LIMITATIONS=[
 'Only reached LFLAG/GFLAG/CFLAG SET/CLEAR/TEST bit operands with no unknown/conflicting path stops are candidates.',
 'Local flag bits16..31, context SET8/CLEAR10, system selectors and flag branches remain unsupported.',
 'Opcode, extended dispatch target, upper operand bits, record lengths and branch bytes remain unchanged.',
 'Source-qualified flag indices are not universal runtime variables; story meaning, current values and execution remain unresolved.',
 'Project history and persistence are supported; editor Apply and playable composition remain pending.'
]

def validate_flag_values(values):
    if not isinstance(values,dict) or set(values)!={'bit'} or type(values['bit']) is not int or not 0<=values['bit']<=31:
        raise ImportError('Flag operand requires only an integer bit index0..31')
    return values['bit']

def _target(record,entry,pc,bit=None,*,report=None):
    if type(pc) is not int or pc<0:raise ImportError('Flag PC must be a nonnegative source-record offset')
    report=inspect_record(record,entry) if report is None else report
    if report['stops']:raise ImportError('Flag authoring requires no unknown or conflicting source-path stops')
    node=next((n for n in report['instructions'] if n['pc']==pc),None)
    if node is None or node['mnemonic'] not in tuple(f'{bank}_{op}' for bank in ('LFLAG','GFLAG','CFLAG') for op in ('SET','CLEAR','TEST')):
        raise ImportError('Flag PC must identify a supported decoded bit instruction')
    original=node['operands']['bit'];value=original if bit is None else bit
    if (node['mnemonic'].startswith('LFLAG_') and (original>=16 or value>=16) or
        node['mnemonic']=='CFLAG_SET' and (original==8 or value==8) or
        node['mnemonic']=='CFLAG_CLEAR' and (original==10 or value==10)):
        raise ImportError('Flag width or context side effect is unsupported for authoring')
    return node,pc+(2 if node['target_context'] is not None else 1),report

def patch_flag_bit(record,entry,pc,values,*,base_offset=0):
    bit=validate_flag_values(values)
    if type(base_offset) is not int or base_offset<0:raise ImportError('Flag base offset must be nonnegative')
    node,offset,report=_target(record,entry,pc,bit)
    after=(record[offset]&0xe0)|bit
    if after==record[offset]:return record,[]
    changed=bytearray(record);changed[offset]=after;changed=bytes(changed)
    check=inspect_record(changed,entry)
    shape=lambda result:[(n['pc'],n['mnemonic'],n['length'],n['target_context'],n['successors']) for n in result['instructions']]
    if check['stops']!=report['stops'] or shape(check)!=shape(report):
        raise ImportError('Flag edit changed decoded instruction layout or continuations')
    return changed,[dict(field='bit',pc=pc,mnemonic=node['mnemonic'],target_context=node['target_context'],
      record_relative_byte_offset=offset,decoded_byte_offset=base_offset+offset,
      before_byte=record[offset],after_byte=after,before_bit=node['operands']['bit'],after_bit=bit,
      source_record_sha256=hashlib.sha256(record).hexdigest())]

class FlagAuthoringContext:
    def __init__(self,source):self._source,self._man=source,source._man
    def provenance(self):return dict(self._source.provenance(),limitations=list(LIMITATIONS))
    def options(self,owner):
        offset,record,entry=self._source.verified_record(owner);report=inspect_record(record,entry);targets=[];unavailable=[]
        if not report['stops']:
            for node in report['instructions']:
                if not node['mnemonic'].startswith(('LFLAG_','GFLAG_','CFLAG_')):continue
                try:_target(record,entry,node['pc'],report=report)
                except ImportError as exc:unavailable.append(dict(pc=node['pc'],mnemonic=node['mnemonic'],reason=str(exc)));continue
                targets.append(dict(semantic_id='script://'+owner.removeprefix('scene://')+f"/flag-bit/{node['pc']:04x}",
                  pc=node['pc'],mnemonic=node['mnemonic'],target_context=node['target_context'],values={'bit':node['operands']['bit']},
                  maximum=15 if node['mnemonic'].startswith('LFLAG_') else 31,source_record_sha256=hashlib.sha256(record).hexdigest()))
        return dict(supported=bool(targets),targets=targets,unavailable=unavailable,
          reason='Flag authoring requires no unknown/conflicting path stops' if report['stops'] else None,
          source=self.provenance(),limitations=list(LIMITATIONS))
    def patch_appended(self,candidate,edits):
        from .man_layout import read_man_layout
        _,changes=self.patch(edits)
        layout=read_man_layout(candidate);records={(row['partition'],row['record_index']):row for row in layout['records']}
        output=bytearray(candidate);audit=[]
        for change in changes:
            owner=change['owner_id'];_,original,entry=self._source.verified_record(owner)
            partition=2 if '/scripts/man-p2/' in owner else 1
            target=records.get((partition,int(owner.rsplit('/',1)[1])))
            if target is None or target['byte_length']!=len(original):raise ImportError('Appended flag owner differs from verified source extent')
            start=target['byte_offset']
            if sum(row['byte_offset']==start for row in layout['records'])!=1:raise ImportError('Appended flag owner is aliased')
            node,relative,_=_target(candidate[start:start+len(original)],entry,change['pc'],change['after_bit'])
            if node['mnemonic']!=change['mnemonic'] or relative!=change['record_relative_byte_offset'] or candidate[start+relative]!=change['before_byte']:
                raise ImportError('Appended flag instruction or preimage differs from verified source')
            offset=start+relative;output[offset]=change['after_byte']
            audit.append(dict(change,source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=offset,
              appended_man_sha256=hashlib.sha256(candidate).hexdigest(),appended_target_context=node['target_context']))
        result=bytes(output)
        if read_man_layout(result)!=layout:raise ImportError('Flag authoring changed appended MAN layout')
        return result,audit
    def patch(self,edits,*,original=None):
        if original is not None and original!=self._man:raise ImportError('Flag MAN differs from verified source')
        if not isinstance(edits,dict) or len(edits)>MAX_FLAG_EDITS:raise ImportError('Flag edit set exceeds bounds')
        audit=[];occupied=set()
        for key,values in edits.items():
            match=re.fullmatch(r'script://([A-Za-z0-9_-]+/(?:actors/man-p1|scripts/man-p2)/[0-9]{4})/flag-bit/([0-9a-f]{4})',key) if isinstance(key,str) else None
            if match is None:raise ImportError('Flag identity requires source owner and hexadecimal PC')
            owner='scene://'+match[1];offset,record,entry=self._source.verified_record(owner)
            _,changes=patch_flag_bit(record,entry,int(match[2],16),values,base_offset=offset)
            for change in changes:
                if change['decoded_byte_offset'] in occupied:raise ImportError('Flag edits overlap another authored span')
                occupied.add(change['decoded_byte_offset']);audit.append(dict(change,flag_id=key,owner_id=owner,source_decoded_man_sha256=hashlib.sha256(self._man).hexdigest()))
        audit.sort(key=lambda row:row['decoded_byte_offset']);result=bytearray(self._man)
        for change in audit:result[change['decoded_byte_offset']]=change['after_byte']
        return bytes(result),deepcopy(audit)

def load_flag_authoring_context(disc,scene):return FlagAuthoringContext(load_dialogue_authoring_context(disc,scene))
