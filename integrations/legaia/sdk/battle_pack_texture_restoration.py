"""Reviewed image-only or whole selected TIM restoration; recovery files survive."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError,canonical
from .battle_pack_palettes import snapshot,inspect,_preview,validate as palettes
from .battle_pack_png_inputs import compose as images,validate as validate_images
from .battle_pack_models import compose as models
from .battle_character_resources import _fresh
from importer.battle_pack_palettes import compose as native_palettes


def _prepare(project,scope,palette_index,expected_current_tim_sha256,expected_current_entry_sha256,**context):
    if project.mode!='edit' or scope not in ('image','texture'):raise ProjectError('Choose image or whole texture restoration in Edit mode')
    original,catalog,record,retail,body,entry=snapshot(project,**context);identifier=context['asset_id']
    image_owner=deepcopy(project.battle_pack_image_overrides.get(identifier));palette_owner=deepcopy(project.battle_pack_palette_overrides.get(identifier))
    if image_owner is None and (scope=='image' or palette_owner is None):raise ProjectError('Selected restore scope has no active owner')
    if sha256(body).hexdigest()!=expected_current_tim_sha256 or sha256(entry).hexdigest()!=expected_current_entry_sha256:raise ProjectError('Current TIM or composed pack changed; inspect again')
    after=dict(palettes=deepcopy(project.battle_pack_palette_overrides),images=deepcopy(project.battle_pack_image_overrides));after['images'].pop(identifier,None)
    if scope=='texture':after['palettes'].pop(identifier,None)
    palettes(project,after['palettes']);validate_images(project,after['images']);candidate=images(project,original,catalog,after['images'],native_palettes(original,catalog,after['palettes'],models(project,original,catalog)))
    restored=body[:544]+retail[544:] if scope=='image' else retail;at=record['source_record']['byte_offset'];end=at+33312
    if candidate[at:end]!=restored or candidate[:at]!=entry[:at] or candidate[end:]!=entry[end:]:raise ProjectError('Texture restoration changed protected neighbors')
    value=dict(schema_version='legaia.battle-pack-texture-restoration-review.v1',scope=scope,project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],record=record,
        palette_index=palette_index,current_inspection=inspect(project,palette_index=palette_index,**context),removed_image_binding=image_owner,removed_palette_binding=palette_owner if scope=='texture' else None,
        palette_binding=after['palettes'].get(identifier),current_tim_base64=b64encode(body).decode(),candidate_tim_base64=b64encode(restored).decode(),
        current_entry_base64=b64encode(entry).decode(),candidate_entry_base64=b64encode(candidate).decode(),current_entry_sha256=sha256(entry).hexdigest(),candidate_entry_sha256=sha256(candidate).hexdigest(),
        candidate_tim_sha256=sha256(restored).hexdigest(),unchanged_neighbors_sha256=sha256(entry[:at]+entry[end:]).hexdigest(),byte_change_count=sum(a!=b for a,b in zip(body,restored)),
        native_content_changed=body!=restored,ownership_changed=True,proposed_preview=_preview(restored,palette_index),layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    encoded=canonical(value);value['review_key']=sha256(encoded).hexdigest();value['review_receipt_base64']=b64encode(encoded).decode();_fresh(project,context['expected_project_path'],context['expected_source_key']);return value,after


def review(project,**args):return _prepare(project,**args)[0]


def apply(project,review_key,**args):
    value,after=_prepare(project,**args)
    if value['review_key']!=review_key:raise ProjectError('Texture restoration requires its exact fresh Review')
    before=dict(palettes=deepcopy(project.battle_pack_palette_overrides),images=deepcopy(project.battle_pack_image_overrides));project.battle_pack_palette_overrides=after['palettes'];project.battle_pack_image_overrides=after['images']
    project.undo_stack.append(dict(target='battle_pack_texture_state',before=before,after=deepcopy(after),label='Restore Retail Pack '+args['scope'].title()));project.redo_stack.clear()
    return dict(schema_version='legaia.battle-pack-texture-restoration-apply.v1',asset_id=args['asset_id'],scope=args['scope'],history_steps=1,project_changed=True,gameplay_verified=False)
