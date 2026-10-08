"""Retained retail-replayed full SEQ replacements and atomic native authoring."""
from copy import copy,deepcopy
from hashlib import sha256
import re
from .project import ProjectError,digest
from .audio_authoring import _source,_current,source_key
from .audio_sequence_midi import decode_upload
from importer.audio_sequence_midi import MAX_MIDI_BYTES
from importer.audio_sequence_replacement import replace_midi,insert_sequence,sequence_span
from importer.audio_sequence import inspect_sequence

FORMAT='seq-midi-replacement-v1'
COMMANDS={'set_audio_sequence_replacement','clear_audio_sequence_replacement'}
FIELDS={'format','source_scene_id','source_record','midi_sha256','byte_length','candidate_sequence_sha256'}
def _hash(raw):return sha256(raw).hexdigest()
def _path(p,b):
    path=p.root/'Authored/Audio/SequenceReplacements'/(b['midi_sha256']+'.mid')
    if not path.resolve().is_relative_to(p.root.resolve()):raise ProjectError('Replacement input path escapes project')
    return path

def _recipe(p,identifier,entry_hash,scene,raw):
    original,_,record=_source(p,identifier,entry_hash,scene)
    output,_,audit=replace_midi(original,raw,expected_current_sha256=_hash(original));start,size=sequence_span(output)
    sequence=output[start:start+size]
    binding=dict(format=FORMAT,source_scene_id=scene,source_record=record,midi_sha256=_hash(raw),byte_length=len(raw),candidate_sequence_sha256=_hash(sequence))
    return original,sequence,binding

def read(p,identifier,b):
    if not isinstance(b,dict) or set(b)!=FIELDS or b['format']!=FORMAT or not isinstance(identifier,str) or re.fullmatch('audio://legaia/prot/[0-9]{4}',identifier) is None:
        raise ProjectError('Invalid full sequence replacement binding')
    if any(not isinstance(b[k],str) or re.fullmatch('[a-f0-9]{64}',b[k]) is None for k in ('midi_sha256','candidate_sequence_sha256')) or type(b['byte_length']) is not int or not 26<=b['byte_length']<=MAX_MIDI_BYTES or not isinstance(b['source_record'],dict):raise ProjectError('Invalid replacement source/hash/byte extent')
    path=_path(p,b)
    if not path.is_file() or path.stat().st_size!=b['byte_length']:raise ProjectError('Retained replacement MIDI is missing or changed size')
    with path.open('rb') as f:raw=f.read(MAX_MIDI_BYTES+1)
    if len(raw)!=b['byte_length'] or _hash(raw)!=b['midi_sha256']:raise ProjectError('Retained replacement MIDI changed hash')
    body,sequence,actual=_recipe(p,identifier,b['source_record'].get('entry_sha256'),b['source_scene_id'],raw)
    if actual!=b:raise ProjectError('Replacement binding differs from independent retail replay')
    return body,sequence,raw

def validate_collection(p):
    rows=p.audio_sequence_replacements
    if not isinstance(rows,dict) or len(rows)>128:raise ProjectError('Sequence replacement collection exceeds its budget')
    sizes={}
    for identifier,b in rows.items():
        if identifier in p.audio_overrides:raise ProjectError('Full sequence replacement and operand override cannot share ownership')
        read(p,identifier,b);sizes[b['midi_sha256']]=b['byte_length']
    if sum(sizes.values())>16*1024*1024:raise ProjectError('Replacement MIDI inputs exceed 16 MiB')

def review(p,asset_id,expected_entry_sha256,expected_authoring_key,midi_base64):
    if p.mode!='edit' or source_key(p)!=expected_authoring_key:raise ProjectError('Replacement authoring requires fresh Edit mode')
    raw=decode_upload(midi_base64);original,current,_,record,_=_current(p,asset_id,expected_entry_sha256)
    _,sequence,binding=_recipe(p,asset_id,expected_entry_sha256,p.active_scene,raw)
    if record!=binding['source_record']:raise ProjectError('Replacement retail ownership changed')
    view=copy(p);view.audio_overrides=deepcopy(p.audio_overrides);view.audio_overrides.pop(asset_id,None)
    view.audio_sequence_replacements=deepcopy(p.audio_sequence_replacements);view.audio_sequence_replacements.pop(asset_id,None)
    from .audio_composition import read_entry
    baseline=read_entry(view,asset_id,original);candidate=insert_sequence(baseline,sequence)
    at,size=sequence_span(candidate);before_at,before_size=sequence_span(current)
    _,fresh,_,fresh_record,_=_current(p,asset_id,expected_entry_sha256)
    if fresh!=current or fresh_record!=record or source_key(p)!=expected_authoring_key:raise ProjectError('Replacement native sources changed before publication')
    result=dict(schema_version='legaia.sequence-replacement-authoring.v1',asset_id=asset_id,authoring_key=expected_authoring_key,
        source_record=record,midi_sha256=_hash(raw),byte_length=len(raw),proposed_binding=binding,
        before_entry_sha256=_hash(current),after_entry_sha256=_hash(candidate),before_entry_size=len(current),after_entry_size=len(candidate),
        current_sequence_offset=before_at,current_sequence_size=before_size,candidate_sequence_offset=at,candidate_sequence_size=size,
        candidate_sequence_sha256=_hash(sequence),sequence=inspect_sequence(sequence),supersedes_sequence_operands=asset_id in p.audio_overrides,
        project_changed=False,runtime_state='not_observed')
    result['review_key']=digest(result);return deepcopy(result)

def command(p,v):
    fields={'type','asset_id','expected_entry_sha256','expected_authoring_key'};kind=v['type']
    if kind=='set_audio_sequence_replacement':fields|={'midi_base64','review_key'}
    elif kind!='clear_audio_sequence_replacement':raise ProjectError('Unsupported sequence replacement command')
    if set(v)!=fields:raise ProjectError('Replacement command requires exact source and reviewed input fields')
    identifier=v['asset_id']
    if not isinstance(identifier,str) or re.fullmatch('audio://legaia/prot/[0-9]{4}',identifier) is None:raise ProjectError('Choose a native sequence asset identity')
    before=dict(replacement=deepcopy(p.audio_sequence_replacements.get(identifier)),operands=deepcopy(p.audio_overrides.get(identifier)))
    if kind=='set_audio_sequence_replacement':
        report=review(p,identifier,v['expected_entry_sha256'],v['expected_authoring_key'],v['midi_base64'])
        if report['review_key']!=v['review_key']:raise ProjectError('Replacement differs from fresh reviewed candidate')
        binding=report['proposed_binding'];raw=decode_upload(v['midi_base64']);path=_path(p,binding)
        if path.exists():
            if not path.is_file() or path.stat().st_size!=len(raw):raise ProjectError('Retained replacement input conflicts with its extent')
            with path.open('rb') as f:existing=f.read(MAX_MIDI_BYTES+1)
            if existing!=raw:raise ProjectError('Retained replacement input conflicts with its identity')
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as f:f.write(raw)
        after=dict(replacement=binding,operands=None)
    else:
        if p.mode!='edit' or source_key(p)!=v['expected_authoring_key']:raise ProjectError('Replacement clear requires fresh Edit mode')
        _current(p,identifier,v['expected_entry_sha256']);after=dict(replacement=None,operands=before['operands'])
    if before==after:return
    view=copy(p);view.audio_sequence_replacements=deepcopy(p.audio_sequence_replacements);view.audio_overrides=deepcopy(p.audio_overrides)
    for field,key in [('audio_sequence_replacements','replacement'),('audio_overrides','operands')]:
        if after[key] is None:getattr(view,field).pop(identifier,None)
        else:getattr(view,field)[identifier]=deepcopy(after[key])
    validate_collection(view)
    p.audio_sequence_replacements=view.audio_sequence_replacements;p.audio_overrides=view.audio_overrides
    p.undo_stack.append(dict(target='audio_sequence_replacement',asset_id=identifier,before=before,after=deepcopy(after)));p.redo_stack.clear()


def preserve_build_inputs(p,destination,input_key,boundary):
    if not p.audio_sequence_replacements:return None
    from .build import authored_state_key,_write_exact
    from .project import canonical
    if input_key!=authored_state_key(p):raise ProjectError('Replacement Build identity changed')
    validate_collection(p);root=destination/'sequence-replacement-inputs'/input_key;files={}
    for identifier,b in sorted(p.audio_sequence_replacements.items()):
        _,_,raw=read(p,identifier,b);h=b['midi_sha256'];_write_exact(root/(h+'.mid'),raw,boundary);files[h]=dict(file=h+'.mid',sha256=h,byte_length=len(raw))
    manifest=dict(schema_version='legaia.sequence-replacement-build-inputs.v1',authored_state_key=input_key,sources=deepcopy(p.audio_sequence_replacements),files=[files[h] for h in sorted(files)],runtime_state='not_observed')
    manifest['manifest_key']=digest(manifest);_write_exact(root/'manifest.json',canonical(manifest)+b'\n',boundary)
    return manifest


def options(p,asset_id,expected_entry_sha256,expected_authoring_key):
    if p.mode!='edit' or source_key(p)!=expected_authoring_key:raise ProjectError('Replacement options require fresh Edit mode')
    original,current,_,record,_=_current(p,asset_id,expected_entry_sha256);at,size=sequence_span(current)
    result=dict(schema_version='legaia.sequence-replacement-options.v1',asset_id=asset_id,authoring_key=expected_authoring_key,source_record=record,
        current_entry_sha256=_hash(current),current_entry_size=len(current),current_sequence_offset=at,current_sequence_size=size,current_sequence_sha256=_hash(current[at:at+size]),
        current=inspect_sequence(current[at:at+size]),binding=deepcopy(p.audio_sequence_replacements.get(asset_id)),operands_present=asset_id in p.audio_overrides,
        project_changed=False,runtime_state='not_observed')
    if source_key(p)!=expected_authoring_key:raise ProjectError('Replacement options changed during inspection')
    return result
