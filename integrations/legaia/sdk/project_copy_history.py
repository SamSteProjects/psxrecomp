"""Discover local editable copies; creation receipts are not current-input proofs."""
from hashlib import sha256
import os
import re
import json
from .build import _guard_output
from .build_history import _metadata
from .project import ProjectError, ProjectService
from .project_copy import source_key
from .project_settings import normalize_name

MAX_ENTRIES=4096
MAX_COPIES=64
MAX_RESPONSE=2*1024*1024


def _hash(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


def _entry(project,identifier):
    path=project.root/'ProjectCopies'/identifier
    _guard_output(path,project.root)
    receipt_path=path/'copy-report.json';metadata_path=path/'project.legaia.json'
    _guard_output(receipt_path,project.root);_guard_output(metadata_path,project.root)
    receipt,_=_metadata(receipt_path);metadata,data=_metadata(metadata_path)
    if (receipt.get('schema_version')!='legaia.project-copy.v1' or
            receipt.get('source_project')!=str(project.root) or receipt.get('copied_project')!=str(path) or
            any(not _hash(receipt.get(field)) for field in ['source_review_key','source_authored_state_key','project_source_key']) or
            type(receipt.get('source_dirty')) is not bool or
            receipt.get('readback_verified') is not True or receipt.get('reopened_metadata_verified') is not True or
            any(receipt.get(field) is not False for field in ['retail_disc_included','undo_history_included','generated_outputs_included','live_state_included'])):
        raise ProjectError('Invalid project copy creation receipt')
    creation_name=normalize_name(receipt.get('name'));name=normalize_name(metadata.get('name'))
    if metadata.get('format')!=ProjectService.FORMAT:raise ProjectError('Invalid saved project format')
    files=receipt.get('files')
    if not isinstance(files,list) or not 1<=len(files)<=512:raise ProjectError('Invalid copy input inventory')
    seen=set();total=0;project_record=None
    for row in files:
        if (not isinstance(row,dict) or not isinstance(row.get('path'),str) or
                not re.fullmatch(r'project\.legaia\.json|Imported/[0-9a-f]{64}\.json|Authored/Textures/[0-9a-f]{64}\.tim|Authored/Models/[0-9a-f]{64}\.tmd|Authored/TextureSources/[0-9a-f]{64}\.glb',row['path']) or
                row['path'] in seen or not _hash(row.get('sha256')) or type(row.get('byte_length')) is not int or not 0<=row['byte_length']<=64*1024*1024):
            raise ProjectError('Invalid copy input identity')
        seen.add(row['path']);total+=row['byte_length']
        if row['path']=='project.legaia.json':project_record=row
    if project_record is None or total>256*1024*1024:raise ProjectError('Invalid copy inventory size')
    return dict(id=identifier,path=str(path),name=name,creation_name=creation_name,status='recorded_copy',
                saved_metadata_state='matches_creation' if len(data)==project_record['byte_length'] and sha256(data).hexdigest()==project_record['sha256'] else 'changed_since_creation',
                current_inputs_validation='not_checked',creation_file_count=len(files))


def list_copies(project):
    if project.mode!='edit':raise ProjectError('Project copies require Edit mode')
    key=source_key(project);root=project.root/'ProjectCopies';_guard_output(root,project.root)
    identifiers=[];scan_truncated=False
    if root.exists():
        with os.scandir(root) as entries:
            for count,entry in enumerate(entries):
                if count>=MAX_ENTRIES:scan_truncated=True;break
                if re.fullmatch('project-[0-9a-f]{32}',entry.name):identifiers.append(entry.name)
    identifiers.sort();truncated=scan_truncated or len(identifiers)>MAX_COPIES
    rows=[]
    for identifier in identifiers[:MAX_COPIES]:
        try:rows.append(_entry(project,identifier))
        except (ProjectError,OSError,ValueError,TypeError,KeyError):
            rows.append(dict(id=identifier,path=str(root/identifier),name=None,creation_name=None,status='incomplete_or_invalid',saved_metadata_state='unavailable',current_inputs_validation='not_checked',creation_file_count=None))
    if source_key(project)!=key:raise ProjectError('Source project changed while listing copies')
    result=dict(schema_version='legaia.project-copy-list.v1',project_source_key=key,source_project=str(project.root),copies=rows,truncated=truncated,ordering='lexicographic_identity',current_inputs_validation='not_checked')
    if len(json.dumps(result).encode('utf-8'))>MAX_RESPONSE:raise ProjectError('Project copy list exceeds 2 MiB')
    return result
