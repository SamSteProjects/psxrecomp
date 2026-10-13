"""Source-bound pack palette ownership, fresh inspection and atomic native edits."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError,canonical
from .battle_character_resources import _fresh,_disc
from importer.pipeline import _disc_context
from importer.battle_character_catalog import decode_catalog
from importer import battle_pack_palettes as native
from importer.core import ImportError as NativeError


def validate(project,values):
    if not isinstance(values,dict) or len(values)>6:raise ProjectError('Pack palettes require at most six complete source owners')
    if not values:return {}
    try:
        with _disc_context(project.disc_path) as (_,disc,_,archive):
            original=archive.read_entry(archive.entry(1204));catalog=decode_catalog(original,disc);_disc(project,catalog)
            native.compose(original,catalog,values)
    except NativeError as error:raise ProjectError(str(error)) from error
    return deepcopy(values)


def texture_entry(project,original,catalog):
    try:
        from .battle_pack_png_inputs import compose as images
        return images(project,original,catalog,getattr(project,'battle_pack_image_overrides',{}),native.compose(original,catalog,getattr(project,'battle_pack_palette_overrides',{})))
    except NativeError as error:raise ProjectError(str(error)) from error


def compose(project,original,catalog,models,values=None):
    try:
        from .battle_pack_png_inputs import compose as images
        return images(project,original,catalog,getattr(project,'battle_pack_image_overrides',{}),native.compose(original,catalog,getattr(project,'battle_pack_palette_overrides',{}) if values is None else values,models))
    except NativeError as error:raise ProjectError(str(error)) from error


def context(project,original,catalog):
    owners=getattr(project,'battle_pack_palette_overrides',{})
    return dict(palette_context=dict(schema_version='legaia.battle-pack-palette-context.v1',owners=deepcopy(owners),**(dict(image_owners=deepcopy(project.battle_pack_image_overrides)) if getattr(project,'battle_pack_image_overrides',{}) else {}),
        retail_entry_base64=b64encode(original).decode(),palette_entry_base64=b64encode(texture_entry(project,original,catalog)).decode()))


def snapshot(project,expected_project_path,expected_source_key,asset_id,catalog_source_key):
    _fresh(project,expected_project_path,expected_source_key)
    from .battle_pack_models import compose as models
    try:
        with _disc_context(project.disc_path) as (_,disc,_,archive):
            original=archive.read_entry(archive.entry(1204));catalog=decode_catalog(original,disc);_disc(project,catalog)
            if catalog['source_key']!=catalog_source_key:raise ProjectError('Pack palette catalogue changed')
            record=next((r for r in catalog['textures'] if r['semantic_id']==asset_id),None)
            if record is None:raise ProjectError('Choose an existing complete pack TIM')
            retail=native.source(original,catalog,record);body=native.effective(original,catalog,record,getattr(project,'battle_pack_palette_overrides',{}).get(asset_id))
            entry=compose(project,original,catalog,models(project,original,catalog))
            at=record['source_record']['byte_offset'];body=entry[at:at+len(retail)]
    except NativeError as error:raise ProjectError(str(error)) from error
    _fresh(project,expected_project_path,expected_source_key);return original,catalog,record,retail,body,entry


def _preview(body,palette):
    try:value=native.preview(body,palette)
    except NativeError as error:raise ProjectError(str(error)) from error
    for field in ('rgba','stp'):value[field+'_base64']=b64encode(value.pop(field)).decode()
    return value


def inspect(project,palette_index,**args):
    original,_,record,retail,body,entry=snapshot(project,**args)
    return dict(schema_version='legaia.battle-pack-palette-inspection.v1',project_path=str(project.root),project_source_key=args['expected_source_key'],catalog_source_key=args['catalog_source_key'],
        record=record,palette_index=palette_index,**(dict(image_binding=deepcopy(project.battle_pack_image_overrides[args['asset_id']])) if args['asset_id'] in getattr(project,'battle_pack_image_overrides',{}) else {}),binding=deepcopy(project.battle_pack_palette_overrides.get(args['asset_id'])),retail_tim_base64=b64encode(retail).decode(),current_tim_base64=b64encode(body).decode(),
        current_tim_sha256=sha256(body).hexdigest(),current_entry_sha256=sha256(entry).hexdigest(),retail_preview=_preview(retail,palette_index),preview=_preview(body,palette_index),
        layer='current',read_only=True,project_changed=False,gameplay_verified=False)


def review(project,palette_index,entry_index,word,expected_current_tim_sha256,expected_current_entry_sha256,**args):
    if project.mode!='edit':raise ProjectError('Pack palette authoring requires Edit mode')
    original,catalog,record,retail,body,entry=snapshot(project,**args)
    if sha256(body).hexdigest()!=expected_current_tim_sha256 or sha256(entry).hexdigest()!=expected_current_entry_sha256:raise ProjectError('Pack Current palette or composed entry changed; inspect again')
    try:owner,candidate,proof=native.project(original,catalog,record,project.battle_pack_palette_overrides.get(args['asset_id']),palette_index,entry_index,word)
    except NativeError as error:raise ProjectError(str(error)) from error
    # Native word ownership stays palette-only; preserve the independent image.
    candidate=candidate[:544]+body[544:]
    proof['current_tim_sha256']=sha256(body).hexdigest();proof['candidate_tim_sha256']=sha256(candidate).hexdigest();proof['unchanged_image_sha256']=sha256(body[544:]).hexdigest()
    at=record['source_record']['byte_offset'];end=at+len(candidate);proposed=entry[:at]+candidate+entry[end:]
    value=dict(schema_version='legaia.battle-pack-palette-review.v1',project_path=str(project.root),project_source_key=args['expected_source_key'],catalog_source_key=args['catalog_source_key'],record=record,
        palette_index=palette_index,entry_index=entry_index,word=word,binding=owner,proof=proof,current_tim_base64=b64encode(body).decode(),candidate_tim_base64=b64encode(candidate).decode(),
        current_entry_sha256=sha256(entry).hexdigest(),candidate_entry_sha256=sha256(proposed).hexdigest(),current_entry_base64=b64encode(entry).decode(),candidate_entry_base64=b64encode(proposed).decode(),
        current_preview=_preview(body,palette_index),proposed_preview=_preview(candidate,palette_index),layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    encoded=canonical(value);value['review_key']=sha256(encoded).hexdigest();value['review_receipt_base64']=b64encode(encoded).decode()
    _fresh(project,args['expected_project_path'],args['expected_source_key']);return value


def apply(project,review_key,**args):
    value=review(project,**args)
    if value['review_key']!=review_key or value['proof']['byte_change_count']==0:raise ProjectError('Pack palette Apply requires its exact fresh changed Review')
    before=deepcopy(project.battle_pack_palette_overrides);after=deepcopy(before)
    if value['binding']:after[args['asset_id']]=value['binding']
    else:after.pop(args['asset_id'],None)
    validate(project,after);_fresh(project,args['expected_project_path'],args['expected_source_key']);project.battle_pack_palette_overrides=after
    project.undo_stack.append(dict(target='battle_pack_palette_overrides',before=before,after=deepcopy(after),label='Battle Pack Native Palette'));project.redo_stack.clear()
    return dict(schema_version='legaia.battle-pack-palette-apply.v1',asset_id=args['asset_id'],history_steps=1,project_changed=True,gameplay_verified=False)


def prepare(project,archive,disc_hash):
    values=getattr(project,'battle_pack_palette_overrides',{});validate(project,values)
    if not values:return [],[]
    entry=archive.entry(1204);original=archive.read_entry(entry);catalog=decode_catalog(original,disc_hash);overlays=[];changes=[]
    for record in catalog['textures']:
        owner=values.get(record['semantic_id'])
        if owner is None:continue
        body=native.effective(original,catalog,record,owner);s=record['source_record'];at=s['byte_offset']+20;payload=body[20:532]
        source=deepcopy(s);source.update(byte_offset=at,byte_length=512,sha256=sha256(original[at:at+512]).hexdigest(),parent_tim_sha256=s['sha256'])
        overlays.append(dict(scene='battle-character-pack',offset=(archive.node.extent_lba+entry.start_lba)*archive.SECTOR+at,size=512,file=f'assets/battle-pack-{s["record_index"]}-clut.bin',payload=payload,
            sha256=sha256(payload).hexdigest(),expected_sha256=source['sha256'],source_kind='fixed_span_battle_pack_palette',source_record=source))
        changes.append(dict(scene='battle-character-pack',semantic_id=record['semantic_id'],field='texture.native_clut',scope='battle-pack-existing-CLUT-words-only',byte_offset=at,byte_length=512,before_sha256=source['sha256'],after_sha256=sha256(payload).hexdigest(),word_change_count=len(owner['edits'])))
    return overlays,changes
