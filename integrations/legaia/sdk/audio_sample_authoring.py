"""Persistent source-qualified WAV sample edits and shared native delivery."""
from copy import copy,deepcopy
from hashlib import sha256
import base64,struct
from .project import ProjectError,digest
from .audio_authoring import source_key
from .audio_bank_authoring import _source
from .audio_sample_sources import validate_record,read_source
from importer.audio_bank import inspect_bank,bank_from_entry
from importer.audio_waveform import inspect_waveform
from importer.audio_sample_authoring import replace_audio_sample_wav,read_pcm_wav

COMMANDS={'set_audio_sample_wav','clear_audio_sample_wav'}
MAX_SAMPLES=32
def _hash(body):return sha256(body).hexdigest()
def _sample(bank,pieces,index):
    rows=inspect_bank(bank)['samples']
    if type(index) is not int or not 0<=index<len(rows):raise ProjectError('Choose an explicit source sample index')
    row=rows[index];at,size=row['offset'],row['size_bytes'];owners=[p for p in pieces if p['bank_offset']<=at and at+size<=p['bank_offset']+p['size_bytes']]
    if len(owners)!=1:raise ProjectError('Sample has no unique native piece owner')
    position=owners[0]['entry_offset']+at-owners[0]['bank_offset']
    return row,position,bank[at:at+size]

def _receipt(project,identifier,index,key,record,bank):
    receipt=project.audio_sample_sources.get(key) if isinstance(key,str) else None
    if receipt is None:raise ProjectError('Choose a retained WAV receipt registered in Current')
    validate_record(receipt)
    row,_,raw=_sample(bank,record['pieces'],index)
    if (receipt['asset_id']!=identifier or receipt['sample_index']!=index or receipt['source_record']!=record
            or receipt['bank_sha256']!=_hash(bank) or receipt['source_sample_sha256']!=_hash(raw)):
        raise ProjectError('Retained WAV source differs from freshly qualified native sample')
    return receipt,read_source(project,receipt)

def _candidate(project,identifier,index,key,body,bank,record,current=None):
    receipt,wav=_receipt(project,identifier,index,key,record,bank);row,position,raw=_sample(bank,record['pieces'],index)
    current=body if current is None else current;end=position+row['size_bytes']
    isolated=body[:position]+current[position:end]+body[end:]
    changed,audit=replace_audio_sample_wav(body,isolated,wav,expected_source_sha256=_hash(body),expected_current_sha256=_hash(isolated),
        expected_bank_sha256=_hash(bank),sample_index=index,expected_sample_sha256=_hash(raw),expected_current_sample_sha256=_hash(current[position:end]))
    if _hash(changed[position:end])!=receipt['candidate_sample_sha256']:raise ProjectError('Retained WAV candidate changed during fresh native reconstruction')
    candidate=current[:position]+changed[position:end]+current[end:]
    audit.update(before_entry_sha256=_hash(current),after_entry_sha256=_hash(candidate))
    return candidate,audit,receipt

def read(project,identifier,binding):
    if (not isinstance(binding,dict) or set(binding)!={'format','source_scene_id','source_record','bank_sha256','samples'}
            or binding['format']!='sample-wav-fixed-v1' or not isinstance(binding['source_record'],dict)
            or not isinstance(binding['samples'],list) or not 1<=len(binding['samples'])<=MAX_SAMPLES):raise ProjectError('Invalid native sample WAV binding')
    body,bank,record=_source(project,identifier,binding['source_record'].get('entry_sha256'),binding['source_scene_id'])
    if record!=binding['source_record'] or _hash(bank)!=binding['bank_sha256']:raise ProjectError('Saved sample bank ownership differs from retail')
    output=bytearray(body);last=-1;audits=[]
    for sample in binding['samples']:
        if not isinstance(sample,dict) or set(sample)!={'sample_index','receipt_key'} or type(sample['sample_index']) is not int or sample['sample_index']<=last:raise ProjectError('Native samples require sorted unique source indices')
        last=sample['sample_index'];candidate,audit,_=_candidate(project,identifier,last,sample['receipt_key'],body,bank,record)
        row,position,_=_sample(bank,record['pieces'],last);end=position+row['size_bytes']
        if candidate[position:end]==body[position:end]:raise ProjectError('Native sample binding must differ from retail bytes')
        output[position:end]=candidate[position:end];audits.append(audit)
    output=bytes(output)
    return body,output,record,dict(source_entry_sha256=_hash(body),before_entry_sha256=_hash(body),after_entry_sha256=_hash(output),
        changed_entry_byte_offsets=[i for i,(a,b) in enumerate(zip(body,output)) if a!=b],samples=audits)

def validate_collection(project):
    rows=project.audio_sample_overrides
    if not isinstance(rows,dict) or len(rows)>MAX_SAMPLES:raise ProjectError('Native sample overrides must be a bounded resource mapping')
    count=0
    for identifier,binding in rows.items():
        read(project,identifier,binding);count+=len(binding['samples'])
    if count>MAX_SAMPLES:raise ProjectError('Project exceeds 32 authored native samples')

def _current(project,identifier,entry_hash,index):
    from .audio_composition import read_entry
    body,bank,record=_source(project,identifier,entry_hash,project.active_scene)
    row,position,raw=_sample(bank,record['pieces'],index);current=read_entry(project,identifier,body)
    return body,current,bank,record,row,position,raw,project.audio_sample_overrides.get(identifier)

def options(project,asset_id,expected_entry_sha256,sample_index,expected_authoring_key):
    if expected_authoring_key!=source_key(project):raise ProjectError('Native sample inputs changed; inspect again')
    body,current,bank,record,row,position,raw,binding=_current(project,asset_id,expected_entry_sha256,sample_index)
    effective=current[position:position+row['size_bytes']]
    from .audio_sample_sources import validate_files
    validate_files(project,project.audio_sample_sources)
    inputs=[deepcopy(r) for r in project.audio_sample_sources.values() if r['asset_id']==asset_id and r['sample_index']==sample_index and r['source_record']==record and r['bank_sha256']==_hash(bank) and r['source_sample_sha256']==_hash(raw)]
    if expected_authoring_key!=source_key(project):raise ProjectError('Sample inputs changed during inspection')
    selected=next((r for r in binding['samples'] if r['sample_index']==sample_index),None) if binding else None
    return dict(schema_version='legaia.audio-sample-authoring.v1',asset_id=asset_id,sample_index=sample_index,authoring_key=expected_authoring_key,
        source_record=record,source_sample=row,current_entry_sha256=_hash(current),current_sample_sha256=_hash(effective),
        authored_sample=deepcopy(selected),retained_inputs=inputs,retail=inspect_waveform(raw),current=inspect_waveform(effective),
        project_changed=False,runtime_state='not_observed')

def review(project,asset_id,expected_entry_sha256,sample_index,expected_authoring_key,operation,receipt_key=None):
    if project.mode!='edit' or expected_authoring_key!=source_key(project):raise ProjectError('Sample inputs changed or are not in Edit mode')
    if operation not in ('apply','clear') or operation=='clear' and receipt_key is not None:raise ProjectError('Choose an explicit native sample Apply or Clear operation')
    body,current,bank,record,row,position,raw,binding=_current(project,asset_id,expected_entry_sha256,sample_index)
    end=position+row['size_bytes'];merged={r['sample_index']:deepcopy(r) for r in (binding['samples'] if binding else [])}
    if operation=='apply':
        candidate,audit,_=_candidate(project,asset_id,sample_index,receipt_key,body,bank,record,current)
        if candidate[position:end]==raw:merged.pop(sample_index,None)
        elif candidate!=current:merged[sample_index]=dict(sample_index=sample_index,receipt_key=receipt_key)
    else:
        candidate=current[:position]+raw+current[end:];merged.pop(sample_index,None)
        audit=dict(source_entry_sha256=_hash(body),before_entry_sha256=_hash(current),after_entry_sha256=_hash(candidate),
            sample_index=sample_index,sample_entry_byte_offset=position,sample_size_bytes=row['size_bytes'],
            changed_entry_byte_offsets=[i for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],sample=None)
    after=(dict(format='sample-wav-fixed-v1',source_scene_id=binding['source_scene_id'] if binding else project.active_scene,
        source_record=record,bank_sha256=_hash(bank),samples=[merged[k] for k in sorted(merged)]) if merged else None)
    view=copy(project);view.audio_sample_overrides=deepcopy(project.audio_sample_overrides)
    if after:view.audio_sample_overrides[asset_id]=after
    else:view.audio_sample_overrides.pop(asset_id,None)
    validate_collection(view)
    from .audio_composition import read_entry
    if read_entry(view,asset_id,body)!=candidate:raise ProjectError('Sample proposal differs from full native audio reconstruction')
    if expected_authoring_key!=source_key(project):raise ProjectError('Sample inputs changed during review')
    result=dict(schema_version='legaia.audio-sample-review.v1',asset_id=asset_id,sample_index=sample_index,operation=operation,
        authoring_key=expected_authoring_key,source_record=record,source_sample=row,proposed_binding=after,native_audit=audit,
        proposed_sample_sha256=_hash(candidate[position:end]),no_change=candidate==current,project_changed=False,runtime_state='not_observed')
    result['review_key']=digest(result);return result

def command(project,value):
    kind=value.get('type');fields={'type','asset_id','expected_entry_sha256','sample_index','expected_authoring_key','review_key'}
    if kind=='set_audio_sample_wav':fields.add('receipt_key');operation='apply'
    elif kind=='clear_audio_sample_wav':operation='clear'
    else:raise ProjectError('Unsupported native sample command')
    if set(value)!=fields:raise ProjectError('Sample commands require exact source, sample and reviewed fields')
    args={k:value[k] for k in fields-{'type','review_key'}};report=review(project,operation=operation,**args)
    if value['review_key']!=report['review_key']:raise ProjectError('Sample differs from its reviewed native proposal')
    if report['no_change']:return
    identifier=value['asset_id'];before=deepcopy(project.audio_sample_overrides.get(identifier));after=report['proposed_binding']
    if after:project.audio_sample_overrides[identifier]=deepcopy(after)
    else:project.audio_sample_overrides.pop(identifier,None)
    project.undo_stack.append(dict(target='audio_sample_overrides',asset_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()

def preview(project,asset_id,expected_entry_sha256,sample_index,expected_authoring_key,
            layer,expected_sample_sha256,operation=None,receipt_key=None,review_key=None):
    """Read one freshly qualified layer; no playback rate or project mutation."""
    if layer not in ('retail','current','proposed'):
        raise ProjectError('Choose an explicit Retail, Current or reviewed Proposed sample layer')
    if expected_authoring_key!=source_key(project):
        raise ProjectError('Sample preview inputs changed; inspect again')
    body,current,bank,record,row,position,raw,_=_current(project,asset_id,expected_entry_sha256,sample_index)
    if layer=='proposed':
        report=review(project,asset_id,expected_entry_sha256,sample_index,expected_authoring_key,operation,receipt_key)
        if review_key!=report['review_key']:
            raise ProjectError('Sample preview differs from its reviewed proposal')
        if operation=='apply':
            candidate,_,_=_candidate(project,asset_id,sample_index,receipt_key,body,bank,record,current)
            selected=candidate[position:position+row['size_bytes']]
        else:selected=raw
    else:
        if any(value is not None for value in (operation,receipt_key,review_key)):
            raise ProjectError('Retail and Current preview do not accept proposed input bindings')
        selected=raw if layer=='retail' else current[position:position+row['size_bytes']]
    if expected_sample_sha256!=_hash(selected):
        raise ProjectError('Sample preview layer hash changed')
    from importer.audio_waveform import _decode_waveform
    waveform,pcm=_decode_waveform(selected)
    if not waveform['decoded_frames']:
        raise ProjectError('This sample layer has no decoded frames to preview')
    if expected_authoring_key!=source_key(project):
        raise ProjectError('Sample preview inputs changed during decoding')
    return dict(schema_version='legaia.audio-sample-preview.v1',asset_id=asset_id,sample_index=sample_index,
        authoring_key=expected_authoring_key,layer=layer,review_key=review_key,source_record=record,
        sample_sha256=_hash(selected),waveform=waveform,format='s16le-mono',
        pcm_sha256=_hash(pcm),pcm_base64=base64.b64encode(pcm).decode('ascii'),
        project_changed=False,runtime_state='not_observed')

def _independent_pcm(raw,blocks):
    coefficients=((0,0),(60,0),(115,-52),(98,-55),(122,-60));last=prior=0;values=[]
    for at in range(0,blocks*16,16):
        header,flags=raw[at:at+2];predictor,shift=header>>4,header&15
        if predictor>4 or shift>12 or flags&~7:raise ProjectError('Authored sample has unsupported native block operands')
        a,b=coefficients[predictor]
        for byte in raw[at+2:at+16]:
            for nibble in (byte&15,byte>>4):
                signed=nibble if nibble<8 else nibble-16;value=max(-32768,min(32767,(signed<<(12-shift))+((last*a+prior*b+32)>>6)))
                values.append(value);prior,last=last,value
        if flags&1 and at+16!=blocks*16:raise ProjectError('Authored sample has an early encoded end')
    return values

def prepare_overlays(project,image,archive):
    validate_collection(project);overlays=[];changes=[]
    for identifier,binding in sorted(project.audio_sample_overrides.items()):
        body,candidate,record,audit=read(project,identifier,binding);bank,pieces,_=bank_from_entry(body);expected=bytearray(body)
        for selected,proof in zip(binding['samples'],audit['samples']):
            index=selected['sample_index'];row,position,raw=_sample(bank,pieces,index);end=position+row['size_bytes'];encoded=candidate[position:end]
            receipt,wav=_receipt(project,identifier,index,selected['receipt_key'],record,bank);native=proof['sample'];blocks=native['encoded_blocks'];consumed=blocks*16
            pcm,rate=read_pcm_wav(wav,blocks*28);targets=struct.unpack('<'+str(blocks*28)+'h',pcm);values=_independent_pcm(encoded,blocks)
            decoded=struct.pack('<'+str(len(values))+'h',*values);errors=[a-b for a,b in zip(targets,values)]
            if (encoded[1:consumed:16]!=raw[1:consumed:16] or encoded[consumed:]!=raw[consumed:]
                    or _hash(decoded)!=native['decoded_pcm_sha256'] or _hash(pcm)!=native['input_pcm_sha256'] or rate!=native['input_wav_rate']
                    or sum(v*v for v in errors)!=native['sum_squared_error'] or max(abs(v) for v in errors)!=native['maximum_absolute_error']):raise ProjectError('Native sample failed independent PCM, error, flag or tail qualification')
            expected[position:end]=encoded
            changes.append(dict(scene='global-audio',semantic_id=identifier,scope='audio-SPU-fixed-sample-prefix-only',field='audio.sample.waveform',
                before_value=row['source_sha256'],after_value=_hash(encoded),sample_index=index,sample_entry_byte_offset=position,sample_size_bytes=row['size_bytes'],
                decoded_frames=blocks*28,input_wav_rate=rate,maximum_absolute_error=native['maximum_absolute_error'],sum_squared_error=native['sum_squared_error'],
                wav_sha256=receipt['wav_sha256'],receipt_key=selected['receipt_key'],source_entry_sha256=_hash(body),candidate_entry_sha256=_hash(candidate)))
        if candidate!=bytes(expected):raise ProjectError('Native sample family changed bytes outside independently qualified sample spans')
        offset=archive.node.extent_lba*2048+record['entry_byte_offset']
        if image.read_user(0,offset,len(body),image.size//2352*2048)!=body:raise ProjectError('Native sample physical disc extent changed')
        overlays.append(dict(scene='global-audio',source_kind='raw_PROT_SPU_samples',iso_file='PROT.DAT',prot_entry_index=record['prot_entry_index'],
            entry_byte_offset=record['entry_byte_offset'],offset=offset,size=len(candidate),file=f"assets/audio-samples-{record['prot_entry_index']:04d}.bin",
            payload=candidate,sha256=_hash(candidate),expected_sha256=_hash(body)))
    return overlays,changes
