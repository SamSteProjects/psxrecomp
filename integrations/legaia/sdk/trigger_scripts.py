"""Source-qualified trigger-to-script authoring, separate from trigger cell ownership."""
from copy import deepcopy
from hashlib import sha256
import re
from importer.core import ImportError
from importer.trigger_authoring import trigger_authoring_options
from importer.trigger_script_authoring import patch_trigger_scripts
from .project import ProjectError, digest
from .project_copy import source_key


def targets(project, scene):
    from importer.script_catalog import load_script_asset_catalog
    from importer.pipeline import REFERENCE_COMMIT
    if scene not in project.imports:
        raise ProjectError('Trigger script owner must be an imported scene')
    name = project.imports[scene]['scene']['name']
    catalog = load_script_asset_catalog(project.disc_path, name)
    if catalog.get('scene') != name or catalog.get('reference_commit') != REFERENCE_COMMIT:
        raise ProjectError('Trigger script catalog source identity changed')
    result = {}
    for record in catalog['assets']:
        if record.get('kind') != 'script' or record.get('partition') != 2:
            continue
        src = record.get('source_record', {})
        index = src.get('record_index')
        if (type(index) is not int or not 0 <= index <= 255 or type(src.get('record_alias_count')) is not int or src.get('record_alias_count') != 1 or
                record.get('status') == 'unavailable'):
            continue
        identifier = f'script://{name}/scripts/man-p2/{index:04d}'
        if (record.get('script_id') != identifier or record.get('semantic_id') != identifier or record.get('reference_commit') != REFERENCE_COMMIT or
                record.get('owner_semantic_id') != 'scene://' + identifier.removeprefix('script://') or
                src.get('partition') != 2 or src.get('disc', {}).get('serial') != 'SCUS-94254' or
                project.imports[scene]['source']['disc_identity'] != 'sha256:' + src.get('disc', {}).get('sha256', '') or
                src.get('iso_file') != 'PROT.DAT' or src.get('byte_coordinate_space') not in ('decoded_lzs_descriptor','raw_man_payload') or type(src.get('byte_offset')) is not int or not 0 <= src['byte_offset'] <= 4 * 1024 * 1024 or
                type(src.get('byte_length')) is not int or not 1 <= src['byte_length'] <= 4 * 1024 * 1024 or
                not isinstance(src.get('sha256'), str) or re.fullmatch(r'[0-9a-f]{64}', src['sha256']) is None or
                identifier in result):
            raise ProjectError('Trigger script target has conflicting source identity or provenance')
        result[identifier] = dict(script_id=identifier, source_sha256=src['sha256'], record_index=index,
                                  source_record=deepcopy(src), inspection_status=record['status'])
    return result


def validate(project, scene, value):
    if not isinstance(value, dict) or set(value) != {'source_sha256', 'edits'} or scene not in project.imports:
        raise ProjectError('Trigger scripts require source MAP hash and stable target edits')
    original = project._environment_source(scene)
    name = project.imports[scene]['scene']['name']
    try:
        patch_trigger_scripts(original, value['source_sha256'], name, value['edits'])
    except ImportError as error:
        raise ProjectError(str(error)) from error
    available = targets(project, scene)
    records = {r['trigger_id']: r for r in trigger_authoring_options(original, name)['records']}
    edits = []
    for edit in value['edits']:
        target = available.get(edit['script_id'])
        if target is None or target['source_sha256'] != edit['script_sha256']:
            raise ProjectError('Trigger script target is unavailable, aliased or changed')
        if records[edit['trigger_id']]['encoded']['record_index'] != target['record_index']:
            edits.append(deepcopy(edit))
    return dict(source_sha256=value['source_sha256'], edits=sorted(edits, key=lambda r:r['trigger_id'])) if edits else None


def review(project, trigger_id, script_id=None, action='set'):
    if project.mode != 'edit' or not isinstance(trigger_id, str) or re.fullmatch(r'trigger://[A-Za-z0-9_-]{1,128}/field-map/primary/kind-1/[0-9]{4}', trigger_id) is None:
        raise ProjectError('Trigger script review requires an editable primary gate-1 source row')
    scene = 'scene://' + trigger_id.split('/')[2]
    if scene != project.active_scene or scene not in project.imports or action not in ('set', 'clear') or action == 'clear' and script_id is not None:
        raise ProjectError('Trigger script review has an invalid scene or action')
    key = source_key(project)
    original = project._environment_source(scene)
    name = project.imports[scene]['scene']['name']
    records = {r['trigger_id']:r for r in trigger_authoring_options(original, name)['records']}
    row = records.get(trigger_id)
    if row is None or row['encoded']['gate'] != 1:
        raise ProjectError('Trigger row does not encode a partition-two script binding')
    available = targets(project, scene)
    stored = project.overrides.get(scene, {}).get('TriggerScripts')
    if 'TriggerScripts' in project.overrides.get(scene, {}):
        normalized = validate(project, scene, stored)
        if normalized != stored:
            raise ProjectError('Stored trigger script binding is not canonical')
    edits = {e['trigger_id']:deepcopy(e) for e in (stored or {}).get('edits', [])}
    imported_id = f"script://{name}/scripts/man-p2/{row['encoded']['record_index']:04d}"
    current_id = edits.get(trigger_id, {}).get('script_id', imported_id)
    authored_id = next((e['script_id'] for e in (stored or {}).get('edits', []) if e['trigger_id'] == trigger_id), None)
    if script_id is not None and (not isinstance(script_id, str) or script_id not in available):
        raise ProjectError('Choose a qualified same-scene partition-two source script')
    if action == 'clear' or script_id == imported_id:
        edits.pop(trigger_id, None)
    elif script_id is not None:
        edits[trigger_id] = dict(trigger_id=trigger_id, script_id=script_id, script_sha256=available[script_id]['source_sha256'])
    value = dict(source_sha256=sha256(original).hexdigest(), edits=[edits[k] for k in sorted(edits)])
    proposed_id = edits.get(trigger_id, {}).get('script_id', imported_id)
    patched, audit = patch_trigger_scripts(original, value['source_sha256'], name, value['edits'])
    report = dict(schema_version='legaia.trigger-scripts-review.v1', read_only=True, project_source_key=key,
                  scene_id=scene, trigger_id=trigger_id, source=deepcopy(row), map_sha256=value['source_sha256'],
                  targets=list(available.values()), layers=dict(imported=imported_id, authored=authored_id, current=current_id, proposed=proposed_id),
                  requested_script_id=script_id, action=action, value=value, audit=audit,
                  proposed_map_sha256=sha256(patched).hexdigest(),
                  project_change=False if script_id is None and action == 'set' else stored != (value if value['edits'] else None),
                  activation='not_evaluated', gameplay_verified=False)
    report['review_key'] = digest(report)
    if source_key(project) != key or sha256(project._environment_source(scene)).hexdigest() != value['source_sha256'] or source_key(project) != key:
        raise ProjectError('Trigger source or project changed during script review')
    return report


def apply(project, command):
    if not isinstance(command, dict) or set(command) != {'type','trigger_id','script_id','action','review_key'} or command['type'] != 'apply_trigger_scripts':
        raise ProjectError('Trigger script Apply requires exact reviewed fields')
    report = review(project, command['trigger_id'], command['script_id'], command['action'])
    if command['review_key'] != report['review_key']:
        raise ProjectError('Trigger script review changed before Apply')
    if report['project_change']:
        project.command(dict(type='set_trigger_scripts', entity_id=report['scene_id'], value=report['value']))
    return report
