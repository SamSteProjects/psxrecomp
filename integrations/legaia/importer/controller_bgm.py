"""Controller BGM u16 argument serialization; operation and playback are not authored."""
from copy import deepcopy
from hashlib import sha256
import re
from .core import ImportError
from .controller_system_flags import ControllerRecordSource,load_controller_record_source
from .scene_controller import controller_record
from .script_inspection import inspect_record
from .man_layout import read_man_layout

LIMITATIONS=[
 'Only reached BGM instructions on controller paths without decoder stops are candidates.',
 'The u16 argument is an encoded host request ID, not a verified music asset association.',
 'The dispatch byte, extended context, continuations, record lengths and other bytes remain unchanged.',
 'Project/editor Review/Apply and native Build support the encoded argument; audible playback remains unverified.',
 'Host dispatch, scheduling, audible playback and gameplay remain unverified.']

def validate_bgm_values(values):
 if not isinstance(values,dict) or set(values)!={'encoded_id'} or type(values['encoded_id']) is not int or not 0<=values['encoded_id']<=65535:
  raise ImportError('BGM argument requires exactly one integer encoded_id0..65535')
 return values['encoded_id'].to_bytes(2,'little')

def _shape(report):
 return [(n['pc'],n['mnemonic'],n['length'],n['target_context'],n['successors']) for n in report['instructions']]

def _target(record,entry,pc,report=None):
 if type(pc) is not int or pc<0:raise ImportError('BGM PC must be a nonnegative source instruction offset')
 report=inspect_record(record,entry) if report is None else report
 if report['stops']:raise ImportError('BGM editing requires no unknown or conflicting controller path stops')
 node=next((n for n in report['instructions'] if n['pc']==pc),None)
 if node is None or node['mnemonic']!='BGM':raise ImportError('BGM PC must identify a reached source BGM instruction')
 header=1 if node['target_context'] is None else 2;relative=pc+header
 if (record[pc]!=(0x35 if header==1 else 0xb5) or header==2 and record[pc+1]!=node['target_context']
     or node['length']!=header+3 or node['successors']!=[{'pc':pc+header+3,'condition':'encoded_continuation'}]
     or int.from_bytes(record[relative:relative+2],'little')!=node['operands']['encoded_id']
     or record[relative+2]!=node['operands']['sub_op']):
  raise ImportError('BGM dispatch, argument preimage or continuation differs from source bytes')
 return node,relative,report

class ControllerBgmAuthoringContext:
 def __init__(self,source):
  if not isinstance(source,ControllerRecordSource):raise ImportError('BGM authoring requires a dedicated verified controller source')
  self._source,self._man=source,source._man
 def provenance(self):return dict(self._source.provenance(),limitations=list(LIMITATIONS))
 def options(self,owner):
  offset,record,entry=self._source.verified_record(owner);report=inspect_record(record,entry);targets=[]
  if not report['stops']:
   for node in report['instructions']:
    if node['mnemonic']!='BGM':continue
    node,relative,_=_target(record,entry,node['pc'],report)
    targets.append(dict(semantic_id=owner.replace('scene://','script://',1)+f"/bgm/{node['pc']:04x}",owner_id=owner,
      pc=node['pc'],mnemonic='BGM',sub_op=node['operands']['sub_op'],target_context=node['target_context'],
      decoded_byte_offset=offset+relative,values=dict(encoded_id=node['operands']['encoded_id']),source_record_sha256=sha256(record).hexdigest()))
  return dict(supported=bool(targets),targets=targets,source=self.provenance(),inspection=deepcopy(report),limitations=list(LIMITATIONS),
    reason='BGM editing requires no decoder stops' if report['stops'] else None)
 def patch(self,edits,*,original=None):
  if original is not None and original!=self._man:raise ImportError('BGM MAN differs from its verified Retail source')
  if not isinstance(edits,dict) or len(edits)>1024:raise ImportError('BGM edit set exceeds bounds')
  result=bytearray(self._man);audit=[];occupied=set();reports={}
  for identity,values in edits.items():
   match=re.fullmatch(r'script://([A-Za-z0-9_-]+/controllers/man-p1/0000)/bgm/([a-f0-9]{4})',identity) if isinstance(identity,str) else None
   if match is None:raise ImportError('BGM identity requires its exact controller owner and source PC')
   owner='scene://'+match[1];offset,record,entry=self._source.verified_record(owner);node,relative,report=_target(record,entry,int(match[2],16))
   after=validate_bgm_values(values);before=record[relative:relative+2];at=offset+relative
   span={at,at+1}
   if occupied&span:raise ImportError('BGM edit windows overlap')
   occupied.update(span);reports[owner]=(offset,record,entry,report)
   if before==after:continue
   result[at:at+2]=after
   audit.append(dict(bgm_id=identity,owner_id=owner,pc=node['pc'],mnemonic='BGM',sub_op=node['operands']['sub_op'],
    target_context=node['target_context'],record_relative_byte_offset=relative,decoded_byte_offset=at,byte_length=2,
    before_hex=before.hex(),after_hex=after.hex(),before_values=dict(encoded_id=int.from_bytes(before,'little')),after_values=deepcopy(values),
    source_record_sha256=sha256(record).hexdigest(),source_decoded_man_sha256=sha256(self._man).hexdigest()))
  result=bytes(result)
  for offset,record,entry,report in reports.values():
   check=inspect_record(result[offset:offset+len(record)],entry)
   if check['stops'] or _shape(check)!=_shape(report) or check['dialogues']!=report['dialogues']:
    raise ImportError('BGM edit changed source layout or continuations')
  if read_man_layout(result)!=read_man_layout(self._man):raise ImportError('BGM edit changed MAN layout')
  return result,deepcopy(sorted(audit,key=lambda row:row['decoded_byte_offset']))
 def patch_appended(self,candidate,edits):
  if not isinstance(candidate,bytes):raise ImportError('Relocated BGM MAN must be bytes')
  _,audit=self.patch(edits);_,source_record,entry=self._source.verified_record(self._source.owner_id)
  at,record,candidate_entry=controller_record(candidate,self._source.scene)
  if record!=source_record or candidate_entry!=entry:raise ImportError('Relocated BGM controller differs from its source preimage')
  layout=read_man_layout(candidate);result=bytearray(candidate);moved=[]
  for row in audit:
   offset=at+row['record_relative_byte_offset'];source_offset=row['decoded_byte_offset']
   if candidate[offset:offset+2].hex()!=row['before_hex']:raise ImportError('Relocated BGM argument preimage changed')
   result[offset:offset+2]=bytes.fromhex(row['after_hex']);moved.append(dict(row,decoded_byte_offset=offset,source_decoded_byte_offset=source_offset))
  result=bytes(result);check=inspect_record(result[at:at+len(record)],entry)
  if read_man_layout(result)!=layout or check['stops'] or _shape(check)!=_shape(inspect_record(record,entry)):
   raise ImportError('Relocated BGM edit changed layout or continuations')
  return result,moved

def load_controller_bgm_context(disc,scene):return ControllerBgmAuthoringContext(load_controller_record_source(disc,scene))
