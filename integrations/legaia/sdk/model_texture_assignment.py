"""One reviewed native replacement for face fields and material page bindings."""
from hashlib import sha256
from importer.model_materials import patch_model_materials
from importer.model_authoring import replace_model_content
from importer.assets import decode_tmd
from .project import ProjectError,digest
from .scene_preview import source_key
from .model_materials import prepare as prepare_materials,_bounded,MAX_AUDIT


def _ordered(rows):
    return sorted(rows,key=lambda r:(r['byte_offset'],r['kind'],r.get('field',''),r.get('axis','')))


def prepare(project,asset_id,primitive_edits,material_edits,expected_sha256,expected_source_key):
    if not isinstance(primitive_edits,list) or not 1<=len(primitive_edits)<=256 or not isinstance(material_edits,list) or not 1<=len(material_edits)<=256:
        raise ProjectError('Combined face/material review requires 1 to 256 entries in each draft')
    _bounded(dict(primitive_edits=primitive_edits,material_edits=material_edits),'Combined model draft')
    # Both independently qualify the actual same Current source, without publishing
    # an intermediate override, history entry or metadata snapshot as Current.
    face_candidate,faces=project._prepare_model_primitives(asset_id,primitive_edits,expected_sha256,expected_source_key)
    material_candidate,materials=prepare_materials(project,asset_id,material_edits,expected_sha256,expected_source_key)
    candidate,material_pending=patch_model_materials(face_candidate,sha256(face_candidate).hexdigest(),material_edits)
    if _ordered(material_pending)!=_ordered(materials['changes_from_current']):
        raise ProjectError('Face and material drafts overlap their qualified native fields')
    original=project._model_source(asset_id,project.active_scene)
    effective=project.read_model_replacement(asset_id,project.model_overrides[asset_id]) if asset_id in project.model_overrides else original
    _,pending=replace_model_content(effective,expected_sha256,candidate,allow_normal_references=True)
    expected=faces['changes_from_current']+materials['changes_from_current']
    if _ordered(pending)!=_ordered(expected):raise ProjectError('Combined model candidate differs from the independent face/material audits')
    changes=project._model_candidate_changes(asset_id,original,candidate)
    if max(len(pending),len(changes))>MAX_AUDIT:raise ProjectError('Combined model candidate exceeds its native audit budget')
    if source_key(project)!=expected_source_key:raise ProjectError('Combined model source changed during review')
    result=dict(schema_version='legaia.model-texture-assignment-review.v1',asset_id=asset_id,scene_id=project.active_scene,
        source_sha256=sha256(original).hexdigest(),effective_sha256=sha256(effective).hexdigest(),project_source_key=expected_source_key,
        proposed_sha256=sha256(candidate).hexdigest(),face_candidate_sha256=sha256(face_candidate).hexdigest(),material_candidate_sha256=sha256(material_candidate).hexdigest(),
        primitive_edit_count=len(primitive_edits),material_edit_count=len(material_edits),face_changes_from_current=faces['changes_from_current'],
        material_changes_from_current=materials['changes_from_current'],changes_from_current=pending,coordinate_changes=changes,
        comparison=materials.get('comparison','retail_source'),project_changed=False,gameplay_verified=False,
        limitations=['Face fields and source material bindings share one native replacement; topology is unchanged.',
                    'Current is the actual project model; intermediate candidate hashes are readonly composition evidence.',
                    'Shared model consumers inherit both changes. Native page addresses do not prove live texture residency.',
                    'Existing topology ledgers and one model Undo entry are retained by the ordinary replacement publisher.'])
    result['review_key']=digest(dict(report=result,primitive_edits=primitive_edits,material_edits=material_edits))
    result.update(current_preview=decode_tmd(effective),preview=decode_tmd(candidate))
    for field in ('current_preview','preview'):result[field]['semantic_id']=asset_id
    _bounded(result,'Combined model review')
    if source_key(project)!=expected_source_key:raise ProjectError('Combined model source changed while constructing preview evidence')
    return candidate,result


def apply(project,asset_id,primitive_edits,material_edits,expected_sha256,expected_source_key,review_key):
    candidate,report=prepare(project,asset_id,primitive_edits,material_edits,expected_sha256,expected_source_key)
    if not isinstance(review_key,str) or review_key!=report['review_key']:raise ProjectError('Combined model draft changed after review')
    if not report['changes_from_current']:raise ProjectError('Combined model draft has no changes to apply')
    project.set_model_replacement(asset_id,candidate)
    report.pop('current_preview');report.pop('preview')
    return report
