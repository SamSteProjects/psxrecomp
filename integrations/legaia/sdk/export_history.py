"""Project-local completed exports and on-demand artifact integrity checks."""
from hashlib import sha256
from datetime import datetime, timezone
import re

from .build import authored_state_key
from .project import ProjectError, read_metadata_json


def _directory(project, identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r'experimental-drafts-[0-9a-f]{32}', identifier):
        raise ProjectError('Invalid export identity')
    root = (project.root / 'Builds').resolve()
    directory = (root / identifier).resolve()
    if not root.is_relative_to(project.root.resolve()) or directory.parent != root:
        raise ProjectError('Export path escapes project Builds directory')
    return directory


def _report(project, identifier):
    directory = _directory(project, identifier)
    path = directory / 'report.json'
    if not path.resolve().is_relative_to(directory):
        raise ProjectError('Export report escapes its directory')
    report = read_metadata_json(path)
    disc = report.get('disc', {})
    if (report.get('schema_version') != 'legaia.experimental-draft-export.v1'
            or not isinstance(disc, dict) or disc.get('reopened_prot_verified') is not True
            or not isinstance(disc.get('output_sha256'), str)
            or not re.fullmatch('[0-9a-f]{64}', disc['output_sha256'])
            or type(disc.get('output_bytes')) is not int or not 0 < disc['output_bytes'] <= 2**31
            or not isinstance(report.get('archive'), dict)):
        raise ProjectError('Export completion report is invalid')
    return directory, report


def list_exports(project):
    root = (project.root / 'Builds').resolve()
    if not root.is_relative_to(project.root.resolve()):
        raise ProjectError('Builds directory escapes project')
    if not root.exists():
        return {'exports': [], 'truncated': False}
    candidates = sorted((p for p in root.iterdir() if re.fullmatch(r'experimental-drafts-[0-9a-f]{32}', p.name)),
                        key=lambda p: p.stat().st_mtime_ns, reverse=True)
    current = authored_state_key(project)
    items = []
    for path in candidates[:256]:
        try:
            directory, report = _report(project, path.name)
            archive = report['archive']
            items.append(dict(id=path.name, status='completed', report_path=str(directory/'report.json'),
                saved_at=datetime.fromtimestamp((directory/'report.json').stat().st_mtime,timezone.utc).isoformat(),
                disc_path=str(directory/'draft.bin'), output_sha256=report['disc']['output_sha256'],
                output_bytes=report['disc']['output_bytes'],
                matches_current_inputs=archive.get('authored_state_key') == current,
                input_project_path=str(directory/'Inputs'/'project.legaia.json') if report.get('input_snapshot') else None,
                scene_ids=sorted(archive.get('scenes', {})) or [archive.get('scene_id')],
                gameplay_verified=False, integrity='not_checked'))
        except (OSError, ValueError, TypeError, KeyError) as error:
            items.append(dict(id=path.name, status='incomplete_or_invalid', error=str(error), gameplay_verified=False))
    return {'exports': items, 'truncated': len(candidates)>256}


def _verify_file(directory, relative, expected, size, maximum):
    from pathlib import Path
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ProjectError('Invalid export artifact path')
    path = (directory / relative).resolve()
    if not path.is_relative_to(directory) or not path.is_file():
        raise ProjectError('Export artifact is missing or escapes its directory')
    if type(size) is not int or not 0 <= size <= maximum or path.stat().st_size != size:
        raise ProjectError('Export artifact size differs from report')
    digest = sha256()
    with path.open('rb') as stream:
        remaining = size
        while remaining:
            chunk = stream.read(min(1024*1024, remaining))
            if not chunk:
                raise ProjectError('Export artifact changed during verification')
            digest.update(chunk)
            remaining -= len(chunk)
        if stream.read(1):
            raise ProjectError('Export artifact grew during verification')
    if digest.hexdigest() != expected:
        raise ProjectError('Export artifact hash differs from report: ' + relative)


def verify_export(project, identifier):
    directory, report = _report(project, identifier)
    disc = report['disc']
    _verify_file(directory, 'draft.bin', disc['output_sha256'], disc['output_bytes'], 2**31)
    snapshot = report.get('input_snapshot')
    count = 0
    if snapshot is not None:
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get('files'), list) or len(snapshot['files'])>4096:
            raise ProjectError('Export input inventory is invalid')
        seen = set()
        for item in snapshot['files']:
            if not isinstance(item, dict) or not isinstance(item.get('path'), str) or not item['path'].startswith('Inputs/') or item['path'] in seen:
                raise ProjectError('Export input inventory has invalid paths')
            seen.add(item['path'])
            _verify_file(directory, item['path'], item.get('sha256'), item.get('byte_length'), 64*1024*1024)
            count += 1
        if 'Inputs/project.legaia.json' not in seen:
            raise ProjectError('Export input project is absent from inventory')
    return dict(id=identifier, disc_hash_verified=True, snapshot_files_verified=count,
                snapshot_available=snapshot is not None, gameplay_verified=False)
