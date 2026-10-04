"""Source-qualified topology review; exact current selections are ephemeral."""
from hashlib import sha256
from copy import deepcopy
import json
from importer.assets import decode_tmd
from importer.model_face_removal import remove_faces, restore_faces, FORMAT
from .project import ProjectError
from .scene_preview import source_key
from importer.model_primitives import inspect_model_primitives


def _budget(report, maximum):
    if len(json.dumps(report, allow_nan=False).encode('utf-8')) > maximum:
        raise ProjectError('Model face removal metadata exceeds its report budget')
    return report


def source(project, asset_id, expected_key):
    if project.mode != 'edit' or not expected_key or source_key(project) != expected_key:
        raise ProjectError('Face removal requires the current Edit source scene')
    original = project._model_source(asset_id, project.active_scene)
    binding = project.model_overrides.get(asset_id)
    effective = project.read_model_replacement(asset_id, binding) if binding else original
    objects = inspect_model_primitives(effective)['objects']
    report = dict(schema_version='legaia.model-face-removal-source.v2', asset_id=asset_id,
                  source_sha256=sha256(original).hexdigest(), effective_sha256=sha256(effective).hexdigest(),
                  project_source_key=expected_key, objects=[dict(object_index=obj['object_index'],
                  vertex_count=obj['vertex_count'], primitives=[dict(primitive_index=row['primitive_index'],
                  corner_count=row['corner_count']) for row in obj['primitives']]) for obj in objects],
                  removed_faces=binding['removed_faces'] if binding and binding['format'] == FORMAT else [])
    report['retail_objects'] = [dict(object_index=obj['object_index'], vertex_count=obj['vertex_count'], primitives=[dict(primitive_index=row['primitive_index'], corner_count=row['corner_count']) for row in obj['primitives']]) for obj in inspect_model_primitives(original)['objects']]
    if binding and binding['format'] == 'tmd-face-addition-v1':
        from .model_face_addition import _context
        *_,audit=_context(project,asset_id,expected_key)
        report.update(schema_version='legaia.model-face-removal-source.v3', face_topology=deepcopy(audit['faces']),
                      removed_face_ids=list(audit.get('removed_face_ids',[])), restoration_available=False)
        if report['removed_face_ids']:
            from importer.model_face_ledger import deleted_face_sources
            from .model_face_addition import base_content
            base=base_content(project,asset_id,original,binding)
            records=deleted_face_sources(base,binding['ledger'])
            from importer.model_face_reinsertion import _ledger_origins
            origins,ranks=_ledger_origins(base,binding['ledger'])
            rows=[]
            for identity in report['removed_face_ids']:
                record=records[identity]
                rows.append(dict(face=deepcopy(record['face']),origin_group_index=record['origin_group_index'],
                    stable_order=record['stable_order'],corner_count=4 if record['descriptor'][2]&2 else 3))
            report.update(schema_version='legaia.model-face-removal-source.v4',
                          restoration_available=True,restorable_faces=rows,
                          restoration_owners=[dict(face_id=face['face_id'],origin_group_index=origins[face['face_id']][1],
                              stable_order=ranks[face['face_id']]) for face in audit['faces']])
    if source_key(project) != expected_key:
        raise ProjectError('Project changed during face removal inspection')
    return _budget(report, 4 * 1024 * 1024)


def prepare(project, asset_id, selections, expected_sha256, expected_key, *, restore=False):
    if project.mode != 'edit' or not expected_key or source_key(project) != expected_key:
        raise ProjectError('Face removal requires the current Edit source scene')
    original = project._model_source(asset_id, project.active_scene)
    binding = project.model_overrides.get(asset_id)
    effective = project.read_model_replacement(asset_id, binding) if binding else original
    if sha256(effective).hexdigest() != expected_sha256:
        raise ProjectError('Model changed since face removal inspection')
    if binding and binding['format'] == 'tmd-face-addition-v1':
        from .model_face_addition import _context
        from importer.model_face_ledger import append_removal_ledger,append_restoration_ledger
        from importer.model_face_removal import _selection
        _,_,base,_,ledger,audit=_context(project,asset_id,expected_key)
        if restore:
            if (not isinstance(selections,list) or len(selections)>4096 or any(
                    not isinstance(row,dict) or set(row)!={'face_id'} or not isinstance(row['face_id'],str)
                    for row in selections)):
                raise ProjectError('Ledger restoration requires bounded exact stable identities')
            face_ids=[row['face_id'] for row in selections]
            if len(set(face_ids))!=len(face_ids) or any(identity not in audit.get('removed_face_ids',[]) for identity in face_ids):
                raise ProjectError('Only distinct deleted stable faces can be restored')
        else:
            _selection(inspect_model_primitives(effective),selections)
            identities={(row['object_index'],row['current_primitive_index']):row['face_id'] for row in audit['faces']}
            face_ids=[identities[row['object_index'],row['primitive_index']] for row in selections]
        if face_ids:
            candidate,ledger,proposed=(append_restoration_ledger if restore else append_removal_ledger)(base,ledger,face_ids)
        else:
            candidate,proposed=effective,audit
        updated=deepcopy(binding)
        updated.update(asset_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),ledger=ledger)
        report=dict(schema_version='legaia.model-face-restoration.v2' if restore else 'legaia.model-face-removal.v2',asset_id=asset_id,
                    source_sha256=sha256(original).hexdigest(),effective_sha256=expected_sha256,
                    proposed_sha256=updated['asset_sha256'],project_source_key=expected_key,
                    selections=deepcopy(selections),removed_face_ids=face_ids,
                    previous_removed_face_ids=list(audit.get('removed_face_ids',[])),topology=proposed,
                    current_preview=decode_tmd(effective),preview=decode_tmd(candidate),
                    project_changed=False,gameplay_verified=False,_effective=effective,_binding=updated)
        if restore:
            report['restored_face_ids']=report.pop('removed_face_ids')
        if source_key(project)!=expected_key:
            raise ProjectError('Project changed during face removal review')
        return candidate,[],report
    previous = binding['removed_faces'] if binding and binding['format'] == FORMAT else []
    candidate, removed = (restore_faces if restore else remove_faces)(original, effective, previous, selections)
    report = dict(schema_version='legaia.model-face-restoration.v1' if restore else 'legaia.model-face-removal.v1', asset_id=asset_id,
                  source_sha256=sha256(original).hexdigest(), effective_sha256=expected_sha256,
                  proposed_sha256=sha256(candidate).hexdigest(), project_source_key=expected_key,
                  selections=selections, removed_faces=removed, previous_removed_faces=previous,
                  current_preview=decode_tmd(effective), preview=decode_tmd(candidate),
                  project_changed=False, gameplay_verified=False, _effective=effective)
    if source_key(project) != expected_key:
        raise ProjectError('Project changed during face removal review')
    return candidate, removed, report


def review(*args, **kwargs):
    report = prepare(*args, **kwargs)[2]
    report.pop('_effective')
    report.pop('_binding',None)
    return _budget(report, 64 * 1024 * 1024)
