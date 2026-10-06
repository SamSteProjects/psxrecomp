"""Retained, reviewed WAV inputs; historical receipts are not native edits."""
from copy import deepcopy
from hashlib import sha256
import base64,re
from .project import ProjectError,digest,atomic_write
from .audio_authoring import source_key
from .audio_bank_authoring import _source
from importer.audio_bank import inspect_bank
from importer.audio_sample_authoring import replace_audio_sample_wav,read_pcm_wav,MAX_WAV_BYTES

MAX_RECEIPTS=32
MAX_BYTES=16*1024*1024
FIELDS={'schema_version','asset_id','source_scene_id','source_record','bank_sha256','sample_index',
        'source_sample_sha256','wav_sha256','byte_length','input_wav_rate','decoded_frames',
        'candidate_sample_sha256','review_key','receipt_key'}
COMMANDS={'retain_audio_sample_source','remove_audio_sample_source'}

def _hash(value):return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None
def decode_upload(value):
    if not isinstance(value,str) or len(value)>((MAX_WAV_BYTES+2)//3)*4:raise ProjectError('WAV upload exceeds its byte budget')
    try:raw=base64.b64decode(value,validate=True)
    except (ValueError,TypeError) as error:raise ProjectError('WAV upload must use strict base64') from error
    if not 44<=len(raw)<=MAX_WAV_BYTES:raise ProjectError('WAV upload exceeds its byte budget')
    return raw

def validate_record(record):
    if not isinstance(record,dict) or set(record)!=FIELDS or record['schema_version']!='legaia.audio-sample-source.v1':raise ProjectError('Invalid WAV input receipt fields')
    if any(not _hash(record[k]) for k in ('bank_sha256','source_sample_sha256','wav_sha256','candidate_sample_sha256','review_key','receipt_key')):raise ProjectError('Invalid WAV receipt hash')
    if not isinstance(record['asset_id'],str) or re.fullmatch(r'audio://legaia/prot/[0-9]{4}',record['asset_id']) is None:raise ProjectError('WAV receipt requires a global audio identity')
    if not isinstance(record['source_scene_id'],str) or re.fullmatch(r'scene://[A-Za-z0-9_-]+',record['source_scene_id']) is None:raise ProjectError('WAV receipt requires its imported source scene')
    if (type(record['sample_index']) is not int or not 0<=record['sample_index']<=254
            or type(record['byte_length']) is not int or not 44<=record['byte_length']<=MAX_WAV_BYTES
            or type(record['decoded_frames']) is not int or not 28<=record['decoded_frames']<=114688 or record['decoded_frames']%28
            or type(record['input_wav_rate']) is not int or not 8000<=record['input_wav_rate']<=192000):raise ProjectError('Invalid WAV sample extent/rate')
    source=record['source_record']
    if (not isinstance(source,dict) or set(source)!={'disc_sha256','iso_file','prot_entry_index','entry_sha256','entry_byte_offset','entry_size_bytes','carrier','pieces'}
            or not _hash(source['disc_sha256']) or not _hash(source['entry_sha256']) or source['iso_file']!='PROT.DAT'
            or type(source['prot_entry_index']) is not int or source['prot_entry_index']!=int(record['asset_id'].rsplit('/',1)[-1])
            or type(source['entry_byte_offset']) is not int or not 0<=source['entry_byte_offset']<2**40
            or type(source['entry_size_bytes']) is not int or not 32<=source['entry_size_bytes']<=4194304
            or source['carrier'] not in ('standalone-vab','leading-contiguous-vab-chunk','split-vab-header-samples')):raise ProjectError('Invalid historical WAV source ownership')
    pieces=source['pieces'];end=0;physical=0
    if not isinstance(pieces,list) or len(pieces)!=(2 if source['carrier']=='split-vab-header-samples' else 1):raise ProjectError('Invalid WAV source piece extent')
    for p in pieces:
        if (not isinstance(p,dict) or set(p)!={'bank_offset','entry_offset','size_bytes'} or any(type(v) is not int for v in p.values())
                or p['bank_offset']!=end or p['entry_offset']!=(physical+4 if source['carrier']!='standalone-vab' else 0)
                or not 1<=p['size_bytes']<=source['entry_size_bytes']-p['entry_offset']):raise ProjectError('Invalid historical WAV source pieces')
        end+=p['size_bytes'];physical=p['entry_offset']+p['size_bytes']
    if digest({k:v for k,v in record.items() if k!='receipt_key'})!=record['receipt_key']:raise ProjectError('WAV input receipt changed')
    return deepcopy(record)

def validate_collection(records):
    if not isinstance(records,dict) or len(records)>MAX_RECEIPTS:raise ProjectError('WAV inputs require at most 32 receipts')
    sizes={}
    for key,record in records.items():
        validate_record(record)
        if key!=record['receipt_key']:raise ProjectError('WAV receipt collection identity changed')
        h=record['wav_sha256'];size=record['byte_length']
        if h in sizes and sizes[h]!=size:raise ProjectError('Conflicting WAV input lengths')
        sizes[h]=size
    if sum(sizes.values())>MAX_BYTES:raise ProjectError('WAV source inputs exceed 16 MiB')

def source_path(project,record):
    validate_record(record);path=project.root/'Authored'/'Audio'/'Sources'/(record['wav_sha256']+'.wav')
    if not path.resolve().is_relative_to(project.root.resolve()):raise ProjectError('WAV input path escapes project')
    return path

def read_source(project,record):
    path=source_path(project,record)
    if not path.is_file() or path.stat().st_size!=record['byte_length']:raise ProjectError('WAV input is missing or changed size')
    raw=path.read_bytes()
    if len(raw)!=record['byte_length'] or sha256(raw).hexdigest()!=record['wav_sha256']:raise ProjectError('WAV input content hash changed')
    _,rate=read_pcm_wav(raw,record['decoded_frames'])
    if rate!=record['input_wav_rate']:raise ProjectError('WAV input rate differs from its historical receipt')
    return raw

def validate_files(project,records):
    validate_collection(records)
    for record in records.values():read_source(project,record)

def review(project,asset_id,expected_entry_sha256,expected_bank_sha256,sample_index,expected_sample_sha256,expected_authoring_key,wav_base64):
    if project.mode!='edit' or expected_authoring_key!=source_key(project):raise ProjectError('WAV source inputs changed or are not in Edit mode')
    raw=decode_upload(wav_base64);body,bank,record=_source(project,asset_id,expected_entry_sha256,project.active_scene)
    samples=inspect_bank(bank)['samples']
    if type(sample_index) is not int or not 0<=sample_index<len(samples):raise ProjectError('Choose a typed source sample index')
    sample=samples[sample_index]
    candidate,audit=replace_audio_sample_wav(body,body,raw,expected_source_sha256=expected_entry_sha256,
        expected_current_sha256=expected_entry_sha256,expected_bank_sha256=expected_bank_sha256,sample_index=sample_index,
        expected_sample_sha256=expected_sample_sha256,expected_current_sample_sha256=expected_sample_sha256)
    at,size=audit['sample_entry_byte_offset'],sample['size_bytes']
    binding=dict(schema_version='legaia.audio-sample-source.v1',asset_id=asset_id,source_scene_id=project.active_scene,
        source_record=record,bank_sha256=expected_bank_sha256,sample_index=sample_index,source_sample_sha256=expected_sample_sha256,
        wav_sha256=sha256(raw).hexdigest(),byte_length=len(raw),input_wav_rate=audit['sample']['input_wav_rate'],
        decoded_frames=audit['sample']['decoded_frames'],candidate_sample_sha256=sha256(candidate[at:at+size]).hexdigest())
    report=dict(schema_version='legaia.audio-sample-source-review.v1',authoring_key=expected_authoring_key,
        binding=binding,native_audit=audit,historical_inputs=True,native_content_changed=False,project_changed=False,runtime_state='not_observed')
    report['review_key']=digest(report)
    if source_key(project)!=expected_authoring_key:raise ProjectError('WAV source context changed during review')
    return report

def command(project,value):
    kind=value.get('type')
    if kind=='retain_audio_sample_source':
        args=('asset_id','expected_entry_sha256','expected_bank_sha256','sample_index','expected_sample_sha256','expected_authoring_key','wav_base64')
        if set(value)!={'type','review_key',*args}:raise ProjectError('WAV retention requires exact source and reviewed fields')
        report=review(project,**{k:value[k] for k in args})
        if value['review_key']!=report['review_key']:raise ProjectError('WAV input differs from reviewed bytes/source')
        record=deepcopy(report['binding']);record['review_key']=report['review_key'];record['receipt_key']=digest(record)
        before=deepcopy(project.audio_sample_sources);after=deepcopy(before);after[record['receipt_key']]=record;validate_collection(after)
        raw=decode_upload(value['wav_base64']);path=source_path(project,record)
        if path.exists():
            if read_source(project,record)!=raw:raise ProjectError('Retained WAV hash path changed')
        else:atomic_write(path,raw)
        if read_source(project,record)!=raw or source_key(project)!=value['expected_authoring_key']:raise ProjectError('WAV input changed before retention')
    elif kind=='remove_audio_sample_source':
        if set(value)!={'type','receipt_key','expected_authoring_key','review_key'}:raise ProjectError('WAV removal requires exact reviewed fields')
        report=review_removal(project,value['receipt_key'],value['expected_authoring_key'])
        if report['review_key']!=value['review_key']:raise ProjectError('WAV inputs changed; review removal again')
        before=deepcopy(project.audio_sample_sources);after=deepcopy(before);del after[value['receipt_key']]
    else:raise ProjectError('Unsupported retained WAV command')
    if before==after:return
    project.audio_sample_sources=after;project.undo_stack.append(dict(target='audio_sample_sources',before=before,after=deepcopy(after)));project.redo_stack.clear()

def library(project,expected_authoring_key):
    if expected_authoring_key!=source_key(project):raise ProjectError('WAV input library changed')
    validate_files(project,project.audio_sample_sources)
    if expected_authoring_key!=source_key(project):raise ProjectError('WAV input library changed during inspection')
    return dict(schema_version='legaia.audio-sample-sources.v1',authoring_key=expected_authoring_key,
                imports=deepcopy(list(project.audio_sample_sources.values())),historical_inputs=True,project_changed=False,runtime_state='not_observed')

def download(project,receipt_key,expected_authoring_key):
    result=library(project,expected_authoring_key);record=next((r for r in result['imports'] if r['receipt_key']==receipt_key),None)
    if record is None:raise ProjectError('WAV receipt is absent from Current')
    raw=read_source(project,record)
    if expected_authoring_key!=source_key(project):raise ProjectError('WAV inputs changed during recovery')
    return dict(result,selected=record,wav_base64=base64.b64encode(raw).decode('ascii'))

def review_removal(project,receipt_key,expected_authoring_key):
    if project.mode!='edit':raise ProjectError('WAV receipt removal requires Edit mode')
    result=library(project,expected_authoring_key);record=next((r for r in result['imports'] if r['receipt_key']==receipt_key),None)
    if record is None:raise ProjectError('WAV receipt is absent from Current')
    if any(row['receipt_key']==receipt_key for binding in project.audio_sample_overrides.values() for row in binding['samples']):
        raise ProjectError('Clear the native sample binding before removing its retained WAV input')
    shared=sum(r['wav_sha256']==record['wav_sha256'] for r in project.audio_sample_sources.values())
    report=dict(schema_version='legaia.audio-sample-source-removal.v1',authoring_key=expected_authoring_key,receipt_key=receipt_key,
        wav_sha256=record['wav_sha256'],source_file_deleted=False,native_content_changed=False,
        registered_bytes_released=record['byte_length'] if shared==1 else 0)
    report['review_key']=digest(report);return report

def preserve_build_inputs(project,destination,input_key,boundary):
    """Historical WAV sidecar, independent of reused native artifact receipts."""
    if not project.audio_sample_sources:return None
    from .build import _write_exact,_guard_output,authored_state_key
    from .project import canonical
    if not _hash(input_key) or authored_state_key(project)!=input_key:raise ProjectError('Build WAV input identity changed')
    validate_files(project,project.audio_sample_sources);directory=destination/'wav-inputs'/input_key
    _guard_output(directory,boundary);files=[];seen=set()
    for record in project.audio_sample_sources.values():
        h=record['wav_sha256']
        if h in seen:continue
        seen.add(h);raw=read_source(project,record);relative=h+'.wav'
        _write_exact(directory/relative,raw,boundary)
        files.append(dict(file=relative,sha256=h,byte_length=len(raw)))
    manifest=dict(schema_version='legaia.build-wav-inputs.v1',authored_state_key=input_key,
        sources=deepcopy(project.audio_sample_sources),files=sorted(files,key=lambda r:r['file']),historical_inputs=True,native_content_changed=False)
    if authored_state_key(project)!=input_key:raise ProjectError('Build WAV inputs changed while preserving bytes')
    manifest['manifest_key']=digest(manifest);_write_exact(directory/'manifest.json',canonical(manifest),boundary)
    return manifest

def read_build_inputs(project,build_id,input_key):
    """Verify frozen historical inputs without trusting them as replay authority."""
    from .build_history import _path
    from .project import read_metadata_json
    if not _hash(input_key):raise ProjectError('Choose a recorded Build input key')
    directory=_path(project,build_id,'wav-inputs/'+input_key)
    manifest=read_metadata_json(_path(project,build_id,'wav-inputs/'+input_key+'/manifest.json'))
    if (not isinstance(manifest,dict) or set(manifest)!={'schema_version','authored_state_key','sources','files','historical_inputs','native_content_changed','manifest_key'}
            or manifest['schema_version']!='legaia.build-wav-inputs.v1' or manifest['authored_state_key']!=input_key
            or manifest['historical_inputs'] is not True or manifest['native_content_changed'] is not False
            or digest({k:v for k,v in manifest.items() if k!='manifest_key'})!=manifest['manifest_key']):raise ProjectError('Saved Build WAV input manifest changed')
    validate_collection(manifest['sources']);expected={r['wav_sha256']:r['byte_length'] for r in manifest['sources'].values()}
    files=manifest['files'];rows=[dict(file=h+'.wav',sha256=h,byte_length=size) for h,size in sorted(expected.items())]
    if files!=rows:raise ProjectError('Saved Build WAV file inventory changed')
    result={}
    for row in rows:
        path=_path(project,build_id,'wav-inputs/'+input_key+'/'+row['file'])
        if not path.is_file() or path.stat().st_size!=row['byte_length']:raise ProjectError('Saved Build WAV file is missing or changed size')
        raw=path.read_bytes()
        if len(raw)!=row['byte_length'] or sha256(raw).hexdigest()!=row['sha256']:raise ProjectError('Saved Build WAV file hash changed')
        result[row['sha256']]=raw
    for record in manifest['sources'].values():
        _,rate=read_pcm_wav(result[record['wav_sha256']],record['decoded_frames'])
        if rate!=record['input_wav_rate']:raise ProjectError('Saved WAV rate differs from its receipt')
    return manifest,result
