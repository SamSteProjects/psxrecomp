"""Retained MIDI inputs with independently replayed retail-target receipts.

Retention never changes native sequence operands. History keeps blobs available
for Redo; a receipt is historical provenance, not authority to install a patch.
"""
import base64
from copy import deepcopy
from hashlib import sha256
import re
from importer.audio_sequence_midi import MAX_MIDI_BYTES, midi_operand_edits
from importer.audio_sequence_authoring import replace_sequence_operands
from .audio_sequence_midi import decode_upload
from .audio_authoring import _source, source_key
from .project import ProjectError, digest, atomic_write, canonical

COMMANDS={'retain_audio_midi_source','remove_audio_midi_source'}
FIELDS={'schema_version','asset_id','source_scene_id','source_record','midi_sha256',
        'byte_length','edits','candidate_sequence_sha256','review_key','receipt_key'}
HASH=lambda v:isinstance(v,str) and re.fullmatch('[a-f0-9]{64}',v) is not None


def validate_collection(records):
    if not isinstance(records,dict) or len(records)>32:
        raise ProjectError('MIDI sources require at most 32 receipts')
    sizes={}
    for key,r in records.items():
        if not isinstance(r,dict) or set(r)!=FIELDS or r['schema_version']!='legaia.audio-midi-source.v1':
            raise ProjectError('Invalid MIDI source receipt')
        if any(not HASH(r[k]) for k in ('midi_sha256','candidate_sequence_sha256','review_key','receipt_key')) or key!=r['receipt_key'] or digest({k:v for k,v in r.items() if k!='receipt_key'})!=key:
            raise ProjectError('MIDI source receipt identity changed')
        if not isinstance(r['asset_id'],str) or re.fullmatch('audio://legaia/prot/[0-9]{4}',r['asset_id']) is None or not isinstance(r['source_scene_id'],str) or re.fullmatch('scene://[A-Za-z0-9_-]+',r['source_scene_id']) is None:
            raise ProjectError('MIDI source requires native asset and scene ownership')
        if type(r['byte_length']) is not int or not 26<=r['byte_length']<=MAX_MIDI_BYTES:
            raise ProjectError('Invalid MIDI source byte extent')
        source=r['source_record']
        fields={'disc_sha256','iso_file','prot_entry_index','entry_sha256','entry_byte_offset','entry_size_bytes','sequence_offset','sequence_size_bytes','sequence_sha256'}
        if not isinstance(source,dict) or set(source)!=fields or any(not HASH(source[k]) for k in ('disc_sha256','entry_sha256','sequence_sha256')) or source['iso_file']!='PROT.DAT' or type(source['prot_entry_index']) is not int or source['prot_entry_index']!=int(r['asset_id'].rsplit('/',1)[-1]):
            raise ProjectError('Invalid MIDI retail source ownership')
        if any(type(source[k]) is not int for k in ('entry_byte_offset','entry_size_bytes','sequence_offset','sequence_size_bytes')) or not 0<=source['entry_byte_offset']<2**40 or not 15<=source['entry_size_bytes']<=4194304 or not 0<=source['sequence_offset']<=source['entry_size_bytes'] or not 15<=source['sequence_size_bytes']<=source['entry_size_bytes']-source['sequence_offset']:
            raise ProjectError('Invalid MIDI retail source extent')
        edits=r['edits'];last=-1
        if not isinstance(edits,list) or len(edits)>256:raise ProjectError('Invalid MIDI source edit extent')
        for e in edits:
            if not isinstance(e,dict) or set(e)!={'event_offset','values'} or type(e['event_offset']) is not int or not last<e['event_offset']<source['sequence_size_bytes'] or not isinstance(e['values'],list) or len(e['values']) not in (1,2) or any(type(v) is not int or not 0<=v<=16777215 for v in e['values']):raise ProjectError('Invalid MIDI source operand receipt')
            last=e['event_offset']
        h=r['midi_sha256'];size=r['byte_length']
        if h in sizes and sizes[h]!=size:raise ProjectError('Conflicting MIDI source sizes')
        sizes[h]=size
    if sum(sizes.values())>16*1024*1024:raise ProjectError('MIDI input storage exceeds 16 MiB')


def _path(project,r):
    path=project.root/'Authored'/'Audio'/'MidiSources'/(r['midi_sha256']+'.mid')
    if not path.resolve().is_relative_to(project.root.resolve()):raise ProjectError('MIDI source path escapes project')
    return path


def _binding(project,asset_id,entry_hash,scene,raw):
    _,sequence,source=_source(project,asset_id,entry_hash,scene)
    edits=midi_operand_edits(raw,sequence)
    candidate=sequence
    if edits:
        candidate,_=replace_sequence_operands(sequence,sequence,expected_source_sha256=sha256(sequence).hexdigest(),expected_current_sha256=sha256(sequence).hexdigest(),edits=edits)
    return dict(schema_version='legaia.audio-midi-source.v1',asset_id=asset_id,source_scene_id=scene,
        source_record=source,midi_sha256=sha256(raw).hexdigest(),byte_length=len(raw),
        edits=edits,candidate_sequence_sha256=sha256(candidate).hexdigest())


def read_source(project,r):
    validate_collection({r['receipt_key']:r})
    path=_path(project,r)
    if not path.is_file() or path.stat().st_size!=r['byte_length']:raise ProjectError('Retained MIDI source is missing or changed size')
    with path.open("rb") as stream:raw=stream.read(MAX_MIDI_BYTES+1)
    if len(raw)!=r['byte_length'] or sha256(raw).hexdigest()!=r['midi_sha256']:raise ProjectError('Retained MIDI source hash changed')
    binding=_binding(project,r['asset_id'],r['source_record']['entry_sha256'],r['source_scene_id'],raw)
    if binding!={k:v for k,v in r.items() if k not in ('review_key','receipt_key')}:raise ProjectError('Retained MIDI receipt differs from fresh native retail replay')
    return raw


def validate_files(project,records):
    validate_collection(records)
    for r in records.values():read_source(project,r)


def review(project,asset_id,expected_entry_sha256,expected_authoring_key,midi_base64):
    if project.mode!='edit' or source_key(project)!=expected_authoring_key:raise ProjectError('MIDI retention source context changed or is not in Edit mode')
    raw=decode_upload(midi_base64)
    binding=_binding(project,asset_id,expected_entry_sha256,project.active_scene,raw)
    result=dict(schema_version='legaia.audio-midi-source-review.v1',authoring_key=expected_authoring_key,
        binding=binding,historical_inputs=True,native_content_changed=False,project_changed=False,runtime_state='not_observed')
    result['review_key']=digest(result)
    if source_key(project)!=expected_authoring_key:raise ProjectError('MIDI sources changed during retention review')
    return result


def command(project,value):
    if value.get('type')=='remove_audio_midi_source':
        if set(value)!={'type','receipt_key','expected_authoring_key','review_key'}:raise ProjectError('MIDI removal requires exact reviewed fields')
        proposal=review_removal(project,value['receipt_key'],value['expected_authoring_key'])
        if value['review_key']!=proposal['review_key']:raise ProjectError('MIDI sources changed; review removal again')
        before=deepcopy(project.audio_midi_sources);after=deepcopy(before);del after[value['receipt_key']]
        project.audio_midi_sources=after
        project.undo_stack.append(dict(target='audio_midi_sources',before=before,after=deepcopy(after)));project.redo_stack.clear()
        return
    args=('asset_id','expected_entry_sha256','expected_authoring_key','midi_base64')
    if set(value)!={'type','review_key',*args} or value['type']!='retain_audio_midi_source':raise ProjectError('MIDI retention requires exact reviewed fields')
    proposal=review(project,**{k:value[k] for k in args})
    if proposal['review_key']!=value['review_key']:raise ProjectError('MIDI input differs from reviewed bytes/source')
    for existing in project.audio_midi_sources.values():
        if {k:v for k,v in existing.items() if k not in ('review_key','receipt_key')}==proposal['binding']:
            read_source(project,existing)
            if source_key(project)!=value['expected_authoring_key']:raise ProjectError('MIDI source changed before duplicate retention')
            return
    record=deepcopy(proposal['binding']);record['review_key']=proposal['review_key'];record['receipt_key']=digest(record)
    before=deepcopy(project.audio_midi_sources);after=deepcopy(before);after[record['receipt_key']]=record;validate_collection(after)
    raw=decode_upload(value['midi_base64']);path=_path(project,record)
    if path.exists():
        if read_source(project,record)!=raw:raise ProjectError('MIDI content path changed')
    else:atomic_write(path,raw)
    if read_source(project,record)!=raw or source_key(project)!=value['expected_authoring_key']:raise ProjectError('MIDI source changed before retention')
    if before==after:return
    project.audio_midi_sources=after
    project.undo_stack.append(dict(target='audio_midi_sources',before=before,after=deepcopy(after)));project.redo_stack.clear()


def library(project,expected_authoring_key):
    if source_key(project)!=expected_authoring_key:raise ProjectError('MIDI input library changed')
    rows=deepcopy(project.audio_midi_sources);validate_files(project,rows)
    if rows!=project.audio_midi_sources or source_key(project)!=expected_authoring_key:raise ProjectError('MIDI sources changed during inspection')
    return dict(schema_version='legaia.audio-midi-sources.v1',authoring_key=expected_authoring_key,
        receipts=rows,historical_inputs=True,project_changed=False,runtime_state='not_observed')


def download(project,receipt_key,expected_authoring_key):
    result=library(project,expected_authoring_key)
    r=result['receipts'].get(receipt_key)
    if r is None:raise ProjectError('MIDI source receipt is absent from Current')
    raw=read_source(project,r)
    if source_key(project)!=expected_authoring_key:raise ProjectError('MIDI sources changed during recovery')
    return dict(result,selected=r,midi_base64=base64.b64encode(raw).decode('ascii'))


def review_removal(project,receipt_key,expected_authoring_key):
    if project.mode!='edit':raise ProjectError('MIDI receipt removal requires Edit mode')
    if not HASH(receipt_key):raise ProjectError('Choose a typed MIDI receipt identity')
    result=library(project,expected_authoring_key);r=result['receipts'].get(receipt_key)
    if r is None:raise ProjectError('MIDI receipt is absent from Current')
    shared=sum(row['midi_sha256']==r['midi_sha256'] for row in result['receipts'].values())
    report=dict(schema_version='legaia.audio-midi-source-removal.v1',authoring_key=expected_authoring_key,
        receipt_key=receipt_key,midi_sha256=r['midi_sha256'],remaining_shared_receipts=shared-1,
        registered_bytes_released=r['byte_length'] if shared==1 else 0,
        source_file_deleted=False,native_content_changed=False,project_changed=False,runtime_state='not_observed')
    report['review_key']=digest(report)
    return report


def preserve_build_inputs(project,destination,input_key,boundary):
    if not getattr(project,"audio_midi_sources",{}):return None
    from .build import _write_exact,_guard_output,authored_state_key
    if authored_state_key(project)!=input_key:raise ProjectError('Build MIDI inputs changed')
    validate_files(project,project.audio_midi_sources)
    directory=destination/'midi-inputs'/input_key;_guard_output(directory,boundary)
    files={}
    for r in project.audio_midi_sources.values():
        raw=read_source(project,r);name=r['midi_sha256']+'.mid';_write_exact(directory/name,raw,boundary)
        files[name]=dict(file=name,sha256=r['midi_sha256'],byte_length=len(raw))
    manifest=dict(schema_version='legaia.build-midi-inputs.v1',authored_state_key=input_key,
        sources=deepcopy(project.audio_midi_sources),files=[files[k] for k in sorted(files)],historical_inputs=True,native_content_changed=False)
    if authored_state_key(project)!=input_key:raise ProjectError('Build MIDI sources changed while preserving inputs')
    manifest['manifest_key']=digest(manifest);_write_exact(directory/'manifest.json',canonical(manifest),boundary)
    return manifest
