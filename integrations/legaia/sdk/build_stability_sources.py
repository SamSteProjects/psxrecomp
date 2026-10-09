"""Deterministic Build-host source evidence, distinct from target binary acceptance."""
from copy import deepcopy
from pathlib import PurePosixPath
import re
from .stability_sources import audit_stability_sources
from .project import ProjectError

FIELDS={'schema_version','read_only','scope','basis_revision','execution_evidence_date','release_reference_revision','comparison_receipt_sha256','files','all_matched','execution_repeated','runtime_binary_verified','gameplay_verified'}
STATUSES={'matched','changed','missing','unreadable','unsafe','oversized','unstable'}

def validate(value):
    hash_ok=lambda v:isinstance(v,str) and re.fullmatch(r'[a-f0-9]{64}',v) is not None
    if (not isinstance(value,dict) or set(value)!=FIELDS or value['schema_version']!='legaia.build-stability-source.v1'
        or value['scope']!='build_host_recorded_source_inclusion_only' or value['read_only'] is not True
        or any(value[k] is not False for k in ('execution_repeated','runtime_binary_verified','gameplay_verified'))
        or any(not isinstance(value[k],str) or not re.fullmatch(r'[a-f0-9]{40}',value[k]) for k in ('basis_revision','release_reference_revision'))
        or not hash_ok(value['comparison_receipt_sha256']) or not isinstance(value['execution_evidence_date'],str)
        or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value['execution_evidence_date'])
        or not isinstance(value['files'],list) or not 1<=len(value['files'])<=32 or type(value['all_matched']) is not bool):
        raise ProjectError('Invalid Build-host stability source evidence')
    seen=set()
    for row in value['files']:
        if not isinstance(row,dict) or set(row)!={'path','category','expected_sha256','actual_sha256','status'}:
            raise ProjectError('Invalid Build-host stability source row')
        name=row['path']
        if (not isinstance(name,str) or not name or len(name)>1024 or name in seen or ':' in name or '\\' in name
            or PurePosixPath(name).is_absolute() or any(part in ('','.', '..') for part in name.split('/'))
            or row['category'] not in ('source_sha256','fixture_sha256') or not hash_ok(row['expected_sha256'])
            or not isinstance(row['status'],str) or row['status'] not in STATUSES):
            raise ProjectError('Invalid Build-host stability source identity')
        seen.add(name)
        if row['status'] in ('matched','changed'):
            if not hash_ok(row['actual_sha256']) or (row['status']=='matched')!=(row['actual_sha256']==row['expected_sha256']):
                raise ProjectError('Invalid Build-host stability hash comparison')
        elif row['actual_sha256'] is not None:raise ProjectError('Unavailable Build-host source cannot claim a hash')
    if value['all_matched']!=all(row['status']=='matched' for row in value['files']):
        raise ProjectError('Build-host stability summary differs from source rows')
    return deepcopy(value)

def capture(root=None,manifest=None):
    value=audit_stability_sources(root,manifest)
    value.pop('checked_at')
    value.update(schema_version='legaia.build-stability-source.v1',scope='build_host_recorded_source_inclusion_only')
    return validate(value)
