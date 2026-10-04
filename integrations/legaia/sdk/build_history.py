"""Bounded project-local Build receipts and read-only artifact verification."""
from hashlib import sha256
import json
import os
import re
import zipfile
import tomllib

from .build import _guard_output, authored_state_key, build_report
from .project import ProjectError
from .build_inventory import package_inventory, MAX_RELOCATION
from importer.core import ImportError as DiscImportError
from importer.disc_relocation_package import decode_relocation_package

MAX_METADATA = 8 * 1024 * 1024
MAX_ARCHIVE = 512 * 1024 * 1024


def _hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def _path(project, identifier, relative=''):
    if not isinstance(identifier, str) or not re.fullmatch('[0-9a-f]{16}', identifier):
        raise ProjectError('Invalid saved Build identity')
    path = project.root / 'Builds' / identifier / relative
    _guard_output(path, project.root)
    return path


def _metadata(path):
    if not path.is_file() or path.stat().st_size > MAX_METADATA:
        raise ProjectError('Saved Build metadata is missing or exceeds 8 MiB')
    data = path.read_bytes()
    if len(data) > MAX_METADATA:
        raise ProjectError('Saved Build metadata grew beyond 8 MiB')
    def reject_constant(value):
        raise ProjectError('Nonfinite saved metadata value')
    value = json.loads(data,parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ProjectError('Saved Build metadata must be an object')
    return value, data


def _load(project, identifier):
    receipt, _ = _metadata(_path(project, identifier, 'build-receipt.json'))
    if (receipt.get('schema_version') != 'legaia.build-receipt.v1'
            or any(not _hash(receipt.get(k)) for k in ('authored_state_key','audit_sha256','manifest_sha256','archive_sha256','source_disc_sha256'))
            or receipt.get('runtime_status') != 'package_built_not_launched'
            or receipt.get('feature_id') != 'placements'
            or receipt.get('build_kind') not in ('authored','retail')
            or type(receipt.get('archive_bytes')) is not int or not 0 < receipt['archive_bytes'] <= MAX_ARCHIVE
            or not isinstance(receipt.get('package_id'),str) or not re.fullmatch(r'legaia\.sdk\.[0-9a-f]{12}',receipt['package_id'])
            or receipt.get('version') != '0.1.0-'+identifier
            or receipt.get('archive_file') != receipt['package_id']+'-'+receipt['version']+'.psxmod'):
        raise ProjectError('Saved Build completion receipt is invalid')
    audit, data = _metadata(_path(project,identifier,'build-audit.json'))
    if (sha256(data).hexdigest() != receipt['audit_sha256']
            or identifier not in (sha256(data).hexdigest()[:16],sha256(data+receipt['authored_state_key'].encode('ascii')).hexdigest()[:16])
            or audit.get('schema_version') != 'legaia.build-audit.v1'
            or audit.get('disc_sha256') != receipt['source_disc_sha256']
            or audit.get('build_kind') != receipt['build_kind']
            or not isinstance(audit.get('edits'),list) or len(audit['edits'])>65536
            or not isinstance(audit.get('overlays'),list) or len(audit['overlays'])>4096):
        raise ProjectError('Saved audit does not match its completion receipt')
    # O(1) lookup of a retained current-input receipt; never scan nested folders.
    current = authored_state_key(project)
    candidate = _path(project,identifier,'input-receipts/'+current+'.json')
    if candidate.exists():
        recorded, _ = _metadata(candidate)
        if (recorded.get('authored_state_key')!=current or
                {k:v for k,v in recorded.items() if k!='authored_state_key'} !=
                {k:v for k,v in receipt.items() if k!='authored_state_key'}):
            raise ProjectError('Saved current-input receipt differs from completion artifacts')
        receipt=recorded
    return receipt, audit


def list_builds(project):
    root = project.root / 'Builds'
    _guard_output(root,project.root)
    if not root.exists():
        return {'builds':[], 'truncated':False, 'coverage':'project_Builds_only_identity_order'}
    candidates = []
    truncated = False
    # Bound all immediate entries, including unrelated exports. Never recurse.
    with os.scandir(root) as entries:
        for index, entry in enumerate(entries):
            if index >= 4096:
                truncated = True
                break
            if re.fullmatch('[0-9a-f]{16}',entry.name):
                candidates.append(entry.name)
    current = authored_state_key(project)
    items = []
    for identifier in sorted(candidates)[:256]:
        try:
            receipt_path = _path(project,identifier,'build-receipt.json')
            if not receipt_path.exists():
                items.append(dict(id=identifier,status='legacy_or_incomplete',matches_current_inputs=None,
                                  integrity='unavailable',gameplay_verified=False))
                continue
            receipt,audit = _load(project,identifier)
            items.append(dict(id=identifier,status='completed',matches_current_inputs=receipt['authored_state_key']==current,
                              integrity='not_checked',gameplay_verified=False,build_kind=receipt['build_kind'],
                              change_count=len(audit['edits']),source_disc_sha256=receipt['source_disc_sha256'],
                              archive_sha256=receipt['archive_sha256'],archive_path=str(_path(project,identifier,receipt['archive_file']))))
        except (OSError,ValueError,TypeError,KeyError,ProjectError) as error:
            items.append(dict(id=identifier,status='invalid',error=str(error)[:8192],gameplay_verified=False))
    return {'builds':items,'truncated':truncated or len(candidates)>256,'coverage':'project_Builds_only_identity_order'}


def _file_hash(path,expected,size=None,maximum=MAX_ARCHIVE):
    length=path.stat().st_size
    if not path.is_file() or not 0<=length<=maximum or size is not None and length!=size:
        raise ProjectError('Saved artifact length differs from receipt or exceeds limit')
    digest=sha256()
    with path.open('rb') as stream:
        remaining=length
        while remaining:
            chunk=stream.read(min(1024*1024,remaining))
            if not chunk: raise ProjectError('Saved artifact changed during verification')
            remaining-=len(chunk);digest.update(chunk)
        if stream.read(1):raise ProjectError('Saved artifact grew during verification')
    if digest.hexdigest()!=expected:
        raise ProjectError('Saved artifact SHA-256 differs from receipt')


def verify_build(project,identifier):
    try:
        return _verify_build(project,identifier)
    except (OSError,ValueError,TypeError,KeyError,zipfile.BadZipFile,RuntimeError,DiscImportError) as error:
        raise ProjectError('Saved Build verification failed: '+str(error)[:8192]) from error


def _verify_build(project,identifier):
    receipt,audit=_load(project,identifier)
    manifest_path=_path(project,identifier,'package/manifest.toml')
    _file_hash(manifest_path,receipt['manifest_sha256'],maximum=MAX_METADATA)
    manifest_bytes=manifest_path.read_bytes()
    if sha256(manifest_bytes).hexdigest()!=receipt['manifest_sha256']:
        raise ProjectError('Saved manifest changed during verification')
    manifest=tomllib.loads(manifest_bytes.decode('utf-8'))
    if manifest.get('id')!=receipt['package_id'] or manifest.get('version')!=receipt['version'] or manifest.get('target')!=[{'game_id':'SCUS-94254','disc_sha256':receipt['source_disc_sha256']}]:
        raise ProjectError('Manifest identity differs from receipt')
    expected={'manifest.toml':(receipt['manifest_sha256'],len(manifest_bytes))}
    payloads=package_inventory(manifest,audit['overlays'],audit.get('relocation_payload'))
    expected.update(payloads)
    if sum(size for _,size in expected.values())>MAX_ARCHIVE:
        raise ProjectError('Manifest payload inventory exceeds limit')
    for name,(digest,size) in payloads.items():
        path=_path(project,identifier,'package/'+name)
        _file_hash(path,digest,size,MAX_RELOCATION if audit.get('relocation_payload') else 64*1024*1024)
        if audit.get('relocation_payload'):
            decode_relocation_package(path.read_bytes(),digest)
    archive_path=_path(project,identifier,receipt['archive_file'])
    _file_hash(archive_path,receipt['archive_sha256'],receipt['archive_bytes'])
    with zipfile.ZipFile(archive_path) as archive:
        infos=archive.infolist()
        if len(infos)!=len(expected) or {i.filename for i in infos}!=set(expected):
            raise ProjectError('Package ZIP entries differ from audited inventory')
        for info in infos:
            digest,length=expected[info.filename]
            if info.file_size!=length:raise ProjectError('Package ZIP member length differs from audit')
            hasher=sha256()
            with archive.open(info) as member:
                remaining=length
                while remaining:
                    chunk=member.read(min(1024*1024,remaining))
                    if not chunk:raise ProjectError('Package ZIP member is truncated')
                    remaining-=len(chunk);hasher.update(chunk)
                if member.read(1):raise ProjectError('Package ZIP member exceeds audit')
            if hasher.hexdigest()!=digest:raise ProjectError('Package ZIP member hash differs from audit')
    # Recheck the completion metadata/archive after ZIP reads.
    if _load(project,identifier)[0]!=receipt:raise ProjectError('Receipt changed during verification')
    _file_hash(archive_path,receipt['archive_sha256'],receipt['archive_bytes'])
    return dict(id=identifier,integrity='verified',gameplay_verified=False,
                matches_current_inputs=receipt['authored_state_key']==authored_state_key(project),
                report=build_report(audit),receipt=receipt,
                scope='receipt_audit_manifest_package_source_files_and_ZIP_members',
                source_disc_integrity='not_checked',runtime_status='package_built_not_launched')
