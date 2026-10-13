"""Whole selected TIM CLUT owner restoration with model/other TIM preservation."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError,canonical
from .battle_pack_palettes import snapshot,inspect,compose,validate,_preview
from .battle_pack_models import compose as models
from .battle_character_resources import _fresh


def _prepare(project,palette_index,expected_current_tim_sha256,expected_current_entry_sha256,**context):
    if project.mode!='edit':raise ProjectError('Pack palette restoration requires Edit mode')
    original,catalog,record,retail,body,entry=snapshot(project,**context)
    owner=deepcopy(project.battle_pack_palette_overrides.get(context['asset_id']))
    if owner is None:raise ProjectError('Selected TIM has no active palette owner to restore')
    if sha256(body).hexdigest()!=expected_current_tim_sha256 or sha256(entry).hexdigest()!=expected_current_entry_sha256:
        raise ProjectError('Pack Current palette or composed entry changed; inspect again')
    after=deepcopy(project.battle_pack_palette_overrides);after.pop(context['asset_id']);validate(project,after)
    candidate=compose(project,original,catalog,models(project,original,catalog),after);at=record['source_record']['byte_offset'];end=at+len(body)
    if candidate[at:end]!=retail or candidate[:at]!=entry[:at] or candidate[end:]!=entry[end:] or body==retail:
        raise ProjectError('Whole palette restoration changed protected pack neighbors or has no native changes')
    inspection=inspect(project,palette_index=palette_index,**context)
    value=dict(schema_version='legaia.battle-pack-palette-restoration-review.v1',operation='restore_retail_pack_tim_palette_owner',project_path=str(project.root),
        project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],record=record,palette_index=palette_index,current_inspection=inspection,
        binding=None,removed_binding=owner,removed_word_count=len(owner['edits']),current_tim_base64=b64encode(body).decode(),candidate_tim_base64=b64encode(retail).decode(),
        current_entry_base64=b64encode(entry).decode(),candidate_entry_base64=b64encode(candidate).decode(),current_entry_sha256=sha256(entry).hexdigest(),candidate_entry_sha256=sha256(candidate).hexdigest(),
        current_preview=_preview(body,palette_index),proposed_preview=_preview(retail,palette_index),proof=dict(byte_change_count=sum(a!=b for a,b in zip(body,retail)),
            current_tim_sha256=sha256(body).hexdigest(),candidate_tim_sha256=sha256(retail).hexdigest(),unchanged_neighbors_sha256=sha256(entry[:at]+entry[end:]).hexdigest()),
        scope='whole_selected_TIM_palette_owner_all_sixteen_local_palettes',layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    encoded=canonical(value);value['review_key']=sha256(encoded).hexdigest();value['review_receipt_base64']=b64encode(encoded).decode()
    _fresh(project,context['expected_project_path'],context['expected_source_key']);return value,after


def review(project,**args):return _prepare(project,**args)[0]


def apply(project,review_key,**args):
    value,after=_prepare(project,**args)
    if value['review_key']!=review_key:raise ProjectError('Whole palette restoration requires its exact fresh Review')
    before=deepcopy(project.battle_pack_palette_overrides);project.battle_pack_palette_overrides=after
    project.undo_stack.append(dict(target='battle_pack_palette_overrides',before=before,after=deepcopy(after),label='Restore Retail Pack Palette Owner'));project.redo_stack.clear()
    return dict(schema_version='legaia.battle-pack-palette-restoration-apply.v1',asset_id=args['asset_id'],removed_word_count=value['removed_word_count'],history_steps=1,project_changed=True,gameplay_verified=False)
