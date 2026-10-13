"""Reviewed restoration of one complete pack model owner; retained files survive."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError,canonical
from .battle_character_resources import _fresh
from .battle_pack_model_authoring import snapshot,current,_geometry
from .battle_pack_models import compose,validate
from importer.battle_pack_model_authoring import source


def _prepare(project,expected_current_tmd_sha256,expected_current_entry_sha256,**context):
    original,catalog,record,body,entry=snapshot(project,**context)
    identifier=record['semantic_id'];owner=deepcopy(project.battle_pack_model_overrides.get(identifier))
    if owner is None:raise ProjectError('Selected pack model has no active model owner to restore')
    if sha256(body).hexdigest()!=expected_current_tmd_sha256 or sha256(entry).hexdigest()!=expected_current_entry_sha256:
        raise ProjectError('Current pack model or composed entry changed; inspect again')
    after=deepcopy(project.battle_pack_model_overrides);after.pop(identifier);validate(project,after)
    from .battle_pack_palettes import compose as palettes,texture_entry
    candidate=palettes(project,original,catalog,compose(project,original,catalog,after));at=record['source_record']['byte_offset'];end=at+len(body);retail=original[at:end]
    if candidate[at:end]!=retail or candidate[:at]!=entry[:at] or candidate[end:]!=entry[end:] or body==retail:
        raise ProjectError('Pack restoration changed protected neighbors or has no native changes')
    _,geometry=source(original,record,catalog,texture_entry=texture_entry(project,original,catalog))
    value=dict(schema_version='legaia.battle-pack-model-restoration-review.v1',operation='restore_retail_pack_model',
        project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],
        record=record,model_binding=owner,current_preview=current(project,**context),retail_geometry=_geometry(geometry),
        retail_tmd_base64=b64encode(retail).decode(),current_tmd_sha256=sha256(body).hexdigest(),candidate_tmd_sha256=sha256(retail).hexdigest(),
        current_entry_base64=b64encode(entry).decode(),candidate_entry_base64=b64encode(candidate).decode(),
        current_entry_sha256=sha256(entry).hexdigest(),candidate_entry_sha256=sha256(candidate).hexdigest(),
        unchanged_neighbors_sha256=sha256(entry[:at]+entry[end:]).hexdigest(),byte_change_count=sum(a!=b for a,b in zip(body,retail)),
        removed_active_inputs=[dict(import_index=i,glb_sha256=r['glb_sha256'],glb_byte_length=r['glb_byte_length']) for i,r in enumerate(owner['inputs'])],
        scope='whole_selected_pack_model_owner',layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    encoded=canonical(value);value['review_key']=sha256(encoded).hexdigest();value['review_receipt_base64']=b64encode(encoded).decode()
    _fresh(project,context['expected_project_path'],context['expected_source_key']);return value,after


def review(project,**args):return _prepare(project,**args)[0]


def apply(project,review_key,**args):
    value,after=_prepare(project,**args)
    if value['review_key']!=review_key:raise ProjectError('Pack restoration requires its exact fresh Review')
    before=deepcopy(project.battle_pack_model_overrides);project.battle_pack_model_overrides=after
    project.undo_stack.append(dict(target='battle_pack_model_overrides',before=before,after=deepcopy(after),label='Restore Retail Pack Model'))
    project.redo_stack.clear()
    return dict(schema_version='legaia.battle-pack-model-restoration-apply.v1',asset_id=args['asset_id'],removed_active_inputs=value['removed_active_inputs'],history_steps=1,project_changed=True,gameplay_verified=False)
