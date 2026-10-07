"""Persistent native sample allocation, effective composition and reviewed commands."""
from copy import copy,deepcopy
from hashlib import sha256
import base64
from .project import ProjectError,digest
from .audio_authoring import source_key
from .audio_bank_authoring import _source
from .audio_sample_sources import validate_record,read_source,ALLOCATION_SCHEMA
from importer.audio_bank import bank_from_entry,inspect_bank
from importer.audio_sample_authoring import replace_sample_wav
from importer.audio_sample_allocation import allocate_sample_wav,repack_audio_samples

FORMAT='sample-wav-allocated-v1'
COMMANDS={'set_audio_sample_allocation','clear_audio_sample_allocation'}
def _hash(body):return sha256(body).hexdigest()

def selected(entry,index):
    from .audio_sample_authoring import _sample
    bank,pieces,_=bank_from_entry(entry)
    return _sample(bank,pieces,index)

def _receipt(project,identifier,index,key,record,bank):
    r=project.audio_sample_sources.get(key) if isinstance(key,str) else None
    if r is None:raise ProjectError('Choose a retained native sample input')
    validate_record(r)
    row=inspect_bank(bank)['samples'][index]
    if (r['asset_id']!=identifier or r['sample_index']!=index or r['source_record']!=record
            or r['bank_sha256']!=_hash(bank) or r['source_sample_sha256']!=row['source_sha256']):
        raise ProjectError('Retained sample input differs from fresh native source ownership')
    return r,read_source(project,r)

def _qualified(project,identifier,binding):
    if (not isinstance(binding,dict) or set(binding)!={'format','source_scene_id','source_record','bank_sha256','samples'}
            or binding['format']!=FORMAT or not isinstance(binding['source_record'],dict)
            or not isinstance(binding['samples'],list) or not 1<=len(binding['samples'])<=32):
        raise ProjectError('Invalid allocated native sample binding')
    body,bank,record=_source(project,identifier,binding['source_record'].get('entry_sha256'),binding['source_scene_id'])
    if record!=binding['source_record'] or _hash(bank)!=binding['bank_sha256']:raise ProjectError('Allocated sample source bank changed')
    last=-1;allocated=False;rows=[];sample_count=len(inspect_bank(bank)['samples'])
    for row in binding['samples']:
        if (not isinstance(row,dict) or set(row)!={'sample_index','receipt_key'} or type(row['sample_index']) is not int
                or not last<row['sample_index']<sample_count):
            raise ProjectError('Allocated samples require sorted unique source ordinals')
        last=row['sample_index'];r,wav=_receipt(project,identifier,last,row['receipt_key'],record,bank)
        allocated|=r['schema_version']==ALLOCATION_SCHEMA;rows.append((row,r,wav))
    if not allocated:raise ProjectError('Allocation binding needs at least one typed allocation input')
    return body,bank,record,rows

def compose(project,identifier,binding,current=None):
    """Apply fixed samples before allocation; current is qualified bank/SEQ composition."""
    body,bank,record,rows=_qualified(project,identifier,binding)
    current=body if current is None else current
    if len(current)!=len(body):raise ProjectError('Compose allocation only after fixed-span audio families')
    output=bytearray(current);replacements={};proofs=[]
    for row,r,wav in rows:
        index=row['sample_index'];source,position,raw=selected(body,index)
        writer=allocate_sample_wav if r['schema_version']==ALLOCATION_SCHEMA else replace_sample_wav
        encoded,proof=writer(raw,raw,wav,expected_source_sha256=_hash(raw),expected_current_sha256=_hash(raw))
        if _hash(encoded)!=r['candidate_sample_sha256'] or encoded==raw:
            raise ProjectError('Allocated binding candidate changed or is identical to Retail')
        if r['schema_version']==ALLOCATION_SCHEMA:replacements[index]=encoded
        else:output[position:position+source['size_bytes']]=encoded
        proofs.append(dict(sample_index=index,receipt_key=r['receipt_key'],allocation=r['schema_version']==ALLOCATION_SCHEMA,sample=proof))
    output,carrier=repack_audio_samples(bytes(output),replacements,expected_entry_sha256=_hash(bytes(output)))
    return body,output,record,dict(source_entry_sha256=_hash(body),before_entry_sha256=_hash(current),after_entry_sha256=_hash(output),
        source_size_bytes=len(body),before_size_bytes=len(current),after_size_bytes=len(output),samples=proofs,carrier=carrier)

def read(project,identifier,binding):return compose(project,identifier,binding)

def _binding(project,scene,record,bank,samples):
    if not samples:return None
    allocated=any(project.audio_sample_sources[r['receipt_key']]['schema_version']==ALLOCATION_SCHEMA for r in samples)
    return dict(format=FORMAT if allocated else 'sample-wav-fixed-v1',source_scene_id=scene,source_record=record,
                bank_sha256=_hash(bank),samples=sorted(samples,key=lambda r:r['sample_index']))

def options(project,asset_id,expected_entry_sha256,sample_index,expected_authoring_key):
    if expected_authoring_key!=source_key(project):raise ProjectError('Allocation authoring inputs changed')
    body,bank,record=_source(project,asset_id,expected_entry_sha256,project.active_scene)
    source,_,raw=selected(body,sample_index)
    from .audio_composition import read_entry
    current=read_entry(project,asset_id,body);row,position,effective=selected(current,sample_index)
    from importer.audio_waveform import inspect_waveform
    inputs=[deepcopy(r) for r in project.audio_sample_sources.values() if r['schema_version']==ALLOCATION_SCHEMA
            and r['asset_id']==asset_id and r['sample_index']==sample_index and r['source_record']==record and r['bank_sha256']==_hash(bank)]
    for r in inputs:_receipt(project,asset_id,sample_index,r['receipt_key'],record,bank)
    if expected_authoring_key!=source_key(project):raise ProjectError('Allocation inputs changed during inspection')
    binding=project.audio_sample_overrides.get(asset_id)
    authored=next((deepcopy(r) for r in binding['samples'] if r['sample_index']==sample_index),None) if binding else None
    return dict(schema_version='legaia.audio-allocation-authoring.v1',asset_id=asset_id,sample_index=sample_index,
        authoring_key=expected_authoring_key,source_record=record,source_sample=source,current_sample=row,
        current_sample_entry_byte_offset=position,current_entry_sha256=_hash(current),current_entry_size_bytes=len(current),
        current_sample_sha256=_hash(effective),retail=inspect_waveform(raw),current=inspect_waveform(effective),
        authored_sample=authored,current_input=deepcopy(project.audio_sample_sources[authored['receipt_key']]) if authored else None,
        retained_inputs=inputs,project_changed=False,runtime_state='not_observed')

def review(project,asset_id,expected_entry_sha256,sample_index,expected_authoring_key,operation,receipt_key=None):
    if project.mode!='edit' or expected_authoring_key!=source_key(project):raise ProjectError('Allocation inputs changed or are not in Edit mode')
    if operation not in ('apply','clear') or operation=='clear' and receipt_key is not None:raise ProjectError('Choose explicit allocation Apply or Retail restoration')
    body,bank,record=_source(project,asset_id,expected_entry_sha256,project.active_scene);source,_,raw=selected(body,sample_index)
    from .audio_composition import read_entry
    current=read_entry(project,asset_id,body);before_row,before_at,prior=selected(current,sample_index)
    binding=project.audio_sample_overrides.get(asset_id);merged={r['sample_index']:deepcopy(r) for r in binding['samples']} if binding else {}
    if operation=='apply':
        r,wav=_receipt(project,asset_id,sample_index,receipt_key,record,bank)
        if r['schema_version']!=ALLOCATION_SCHEMA:raise ProjectError('Allocation Apply needs a typed retained allocation input')
        encoded,_=allocate_sample_wav(raw,raw,wav,expected_source_sha256=_hash(raw),expected_current_sha256=_hash(raw))
        if _hash(encoded)!=r['candidate_sample_sha256']:raise ProjectError('Retained allocation candidate changed')
        if encoded==raw:merged.pop(sample_index,None)
        else:merged[sample_index]=dict(sample_index=sample_index,receipt_key=receipt_key)
    else:merged.pop(sample_index,None)
    after=_binding(project,binding['source_scene_id'] if binding else project.active_scene,record,bank,list(merged.values()))
    view=copy(project);view.audio_sample_overrides=deepcopy(project.audio_sample_overrides)
    if after:view.audio_sample_overrides[asset_id]=after
    else:view.audio_sample_overrides.pop(asset_id,None)
    from .audio_sample_authoring import validate_collection
    validate_collection(view);candidate=read_entry(view,asset_id,body);after_row,after_at,proposed=selected(candidate,sample_index)
    if source_key(project)!=expected_authoring_key:raise ProjectError('Allocation inputs changed during review')
    result=dict(schema_version='legaia.audio-allocation-review.v1',asset_id=asset_id,sample_index=sample_index,operation=operation,
        authoring_key=expected_authoring_key,source_record=record,source_sample=source,current_sample=before_row,proposed_sample=after_row,
        before_entry_sha256=_hash(current),after_entry_sha256=_hash(candidate),before_entry_size_bytes=len(current),after_entry_size_bytes=len(candidate),
        before_sample_entry_byte_offset=before_at,after_sample_entry_byte_offset=after_at,
        before_sample_sha256=_hash(prior),proposed_sample_sha256=_hash(proposed),proposed_binding=after,
        no_change=after==binding and candidate==current,native_content_changed=candidate!=current,
        project_changed=False,runtime_state='not_observed')
    result['review_key']=digest(result);return result

def preview(project,asset_id,expected_entry_sha256,sample_index,expected_authoring_key,layer,expected_sample_sha256,
            operation=None,receipt_key=None,review_key=None):
    if layer not in ('retail','current','proposed') or source_key(project)!=expected_authoring_key:
        raise ProjectError('Choose a fresh explicit allocation preview layer')
    body,_,record=_source(project,asset_id,expected_entry_sha256,project.active_scene)
    from .audio_composition import read_entry
    if layer=='proposed':
        proposal=review(project,asset_id,expected_entry_sha256,sample_index,expected_authoring_key,operation,receipt_key)
        if proposal['review_key']!=review_key:raise ProjectError('Allocation preview differs from its reviewed proposal')
        view=copy(project);view.audio_sample_overrides=deepcopy(project.audio_sample_overrides)
        if proposal['proposed_binding']:view.audio_sample_overrides[asset_id]=proposal['proposed_binding']
        else:view.audio_sample_overrides.pop(asset_id,None)
        entry=read_entry(view,asset_id,body)
    else:
        if any(v is not None for v in (operation,receipt_key,review_key)):raise ProjectError('Retail/Current previews do not accept proposed inputs')
        entry=body if layer=='retail' else read_entry(project,asset_id,body)
    row,position,raw=selected(entry,sample_index)
    if _hash(raw)!=expected_sample_sha256:raise ProjectError('Allocation preview sample hash changed')
    from importer.audio_waveform import _decode_waveform
    waveform,pcm=_decode_waveform(raw)
    if not waveform['decoded_frames'] or source_key(project)!=expected_authoring_key:raise ProjectError('Allocation preview is empty or became stale')
    return dict(schema_version='legaia.audio-allocation-preview.v1',asset_id=asset_id,sample_index=sample_index,layer=layer,
        authoring_key=expected_authoring_key,review_key=review_key,source_record=record,selected_sample=row,
        sample_entry_byte_offset=position,sample_sha256=_hash(raw),entry_sha256=_hash(entry),entry_size_bytes=len(entry),
        waveform=waveform,format='s16le-mono',pcm_sha256=_hash(pcm),pcm_base64=base64.b64encode(pcm).decode('ascii'),
        project_changed=False,runtime_state='not_observed')

def command(project,value):
    fields={'type','asset_id','expected_entry_sha256','sample_index','expected_authoring_key','review_key'}
    if value.get('type')=='set_audio_sample_allocation':fields.add('receipt_key');operation='apply'
    elif value.get('type')=='clear_audio_sample_allocation':operation='clear'
    else:raise ProjectError('Unsupported allocation command')
    if set(value)!=fields:raise ProjectError('Allocation command needs exact reviewed source and input fields')
    report=review(project,**{k:value[k] for k in fields-{'type','review_key'}},operation=operation)
    if report['review_key']!=value['review_key']:raise ProjectError('Allocation proposal changed; review again')
    if report['no_change']:return
    identifier=value['asset_id'];before=deepcopy(project.audio_sample_overrides.get(identifier));after=report['proposed_binding']
    if after:project.audio_sample_overrides[identifier]=deepcopy(after)
    else:project.audio_sample_overrides.pop(identifier,None)
    project.undo_stack.append(dict(target='audio_sample_overrides',asset_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()
