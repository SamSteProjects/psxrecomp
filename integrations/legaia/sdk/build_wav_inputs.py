"""Read frozen Build WAV snapshots independently of Current source files."""
import base64,os,re
from copy import deepcopy
from .project import ProjectError
from .build import authored_state_key
from .build_history import _load,_metadata,_path,_hash
from .audio_sample_sources import read_build_inputs

def _fresh(project,key):
    if not _hash(key) or authored_state_key(project)!=key:
        raise ProjectError('Project inputs changed; reopen Build WAV recovery')

def _completed(project,identifier,archive_hash,input_key=None):
    receipt,_=_load(project,identifier,use_current=False)
    if not _hash(archive_hash) or receipt['archive_sha256']!=archive_hash:
        raise ProjectError('Build WAV recovery archive receipt changed')
    if input_key is not None:
        if not _hash(input_key):raise ProjectError('Choose a recorded Build input identity')
        if input_key!=receipt['authored_state_key']:
            recorded,_=_metadata(_path(project,identifier,'input-receipts/'+input_key+'.json'))
            if (recorded.get('authored_state_key')!=input_key or
                {k:v for k,v in recorded.items() if k!='authored_state_key'}!=
                {k:v for k,v in receipt.items() if k!='authored_state_key'}):
                raise ProjectError('Historical input receipt differs from completed Build artifacts')
            receipt=recorded
    return receipt

def snapshots(project,id,expected_archive_sha256,expected_project_key):
    _fresh(project,expected_project_key);_completed(project,id,expected_archive_sha256)
    root=_path(project,id,'wav-inputs');keys=[];truncated=False
    if root.exists():
        with os.scandir(root) as entries:
            for index,entry in enumerate(entries):
                if index>=4096:truncated=True;break
                if re.fullmatch('[a-f0-9]{64}',entry.name) and entry.is_dir(follow_symlinks=False):keys.append(entry.name)
    rows=[dict(input_key=key,matches_current_inputs=key==expected_project_key,integrity='not_checked') for key in sorted(keys)[:128]]
    _fresh(project,expected_project_key);_completed(project,id,expected_archive_sha256)
    return dict(schema_version='legaia.build-wav-snapshots.v1',id=id,archive_sha256=expected_archive_sha256,
        project_key=expected_project_key,snapshots=rows,truncated=truncated or len(keys)>128,
        coverage='immediate_wav_input_directories_identity_order',historical_inputs=True,
        project_changed=False,package_integrity='not_checked',gameplay_verified=False)

def _verified(project,id,archive_hash,input_key,key):
    _fresh(project,key);receipt=_completed(project,id,archive_hash,input_key)
    manifest,files=read_build_inputs(project,id,input_key)
    if _completed(project,id,archive_hash,input_key)!=receipt:
        raise ProjectError('Historical input receipt changed during verification')
    current,_=_metadata(_path(project,id,'wav-inputs/'+input_key+'/manifest.json'))
    if current!=manifest:raise ProjectError('Build WAV manifest changed during verification')
    _fresh(project,key);return manifest,files

def inputs(project,id,expected_archive_sha256,input_key,expected_project_key):
    manifest,_=_verified(project,id,expected_archive_sha256,input_key,expected_project_key)
    return dict(schema_version='legaia.build-wav-inputs-inspection.v1',id=id,archive_sha256=expected_archive_sha256,
        project_key=expected_project_key,input_key=input_key,manifest_key=manifest['manifest_key'],
        sources=deepcopy(list(manifest['sources'].values())),files=deepcopy(manifest['files']),
        integrity='input_receipt_manifest_and_wavs_verified',historical_inputs=True,project_changed=False,
        package_integrity='not_checked',gameplay_verified=False)

def download(project,id,expected_archive_sha256,input_key,expected_project_key,expected_manifest_key,receipt_key):
    manifest,files=_verified(project,id,expected_archive_sha256,input_key,expected_project_key)
    if not _hash(expected_manifest_key) or expected_manifest_key!=manifest['manifest_key']:
        raise ProjectError('Build WAV recovery snapshot changed; inspect again')
    receipt=manifest['sources'].get(receipt_key) if isinstance(receipt_key,str) else None
    if receipt is None:raise ProjectError('Choose a WAV receipt in the inspected Build snapshot')
    return dict(schema_version='legaia.build-wav-download.v1',id=id,archive_sha256=expected_archive_sha256,
        project_key=expected_project_key,input_key=input_key,manifest_key=expected_manifest_key,selected=deepcopy(receipt),
        wav_base64=base64.b64encode(files[receipt['wav_sha256']]).decode('ascii'),
        integrity='input_receipt_manifest_and_wavs_verified',historical_inputs=True,project_changed=False,
        package_integrity='not_checked',gameplay_verified=False)
