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



def _change_summary(archive):
    """Summarize completed audit categories without exposing private script text."""
    scenes = archive.get('scenes')
    records = list(scenes.values()) if isinstance(scenes, dict) else [archive]
    categories = set()
    fields = {'existing_actor_placement_changes': 'Actor positions',
              'existing_actor_appearance_changes': 'Actor appearances',
              'existing_actor_dialogue_changes': 'Dialogue', 'transition_changes': 'Transitions', 'movement_changes': 'Script movement'}
    nested = {'animation_changes': 'Animation channels', 'model_changes': 'Model shapes',
              'texture_changes': 'Textures'}
    drafts = archive.get('drafts')
    draft_count = len(drafts) if isinstance(drafts, dict) else None
    for record in records:
        if not isinstance(record, dict):
            continue
        for field, label in fields.items():
            if record.get(field): categories.add(label)
        for field, label in nested.items():
            value = record.get(field)
            if isinstance(value, dict) and value.get('changes'): categories.add(label)
        value = record.get('map_changes')
        if isinstance(value, dict):
            if value.get('environment_changes'): categories.add('Scenery')
            if value.get('collision_changes'): categories.add('Collision')
    if draft_count:
        categories.add('NPC additions')
    return dict(npc_draft_count=draft_count, categories=sorted(categories))

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
            items.append(dict(id=path.name, status='completed', change_summary=_change_summary(archive), report_path=str(directory/'report.json'),
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


def copy_export_inputs(project, identifier):
    """Create an editable project without modifying retained export evidence."""
    from uuid import uuid4
    from .project import atomic_write, ProjectService
    directory, report = _report(project, identifier)
    snapshot = report.get('input_snapshot')
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get('files'), list) or not 1<=len(snapshot['files'])<=4096:
        raise ProjectError('This export has no valid input snapshot')
    payloads = {}
    for item in snapshot['files']:
        if not isinstance(item, dict) or not isinstance(item.get('path'), str) or not item['path'].startswith('Inputs/'):
            raise ProjectError('Invalid saved input path')
        relative=item['path'][len('Inputs/'):]
        from pathlib import PurePosixPath
        if not relative or '\\' in relative or ':' in relative or '..' in PurePosixPath(relative).parts or relative in payloads:
            raise ProjectError('Invalid or duplicate saved input path')
        _verify_file(directory,item['path'],item.get('sha256'),item.get('byte_length'),64*1024*1024)
        payload=(directory/item['path']).read_bytes()
        if sha256(payload).hexdigest()!=item['sha256']:
            raise ProjectError('Saved input changed during copy')
        payloads[relative]=payload
    if 'project.legaia.json' not in payloads:
        raise ProjectError('Saved input project is missing')
    destination=(project.root/'ReviewCopies'/('export-'+uuid4().hex)).resolve()
    if not destination.is_relative_to(project.root.resolve()):
        raise ProjectError('Editable copy escapes current project')
    destination.mkdir(parents=True,exist_ok=False)
    for relative,payload in payloads.items():
        target=(destination/relative).resolve()
        if not target.is_relative_to(destination):
            raise ProjectError('Copied input escapes destination')
        atomic_write(target,payload)
    ProjectService.open(destination)
    return destination
