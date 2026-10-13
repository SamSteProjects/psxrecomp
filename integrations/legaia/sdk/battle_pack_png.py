"""Fresh real TIM PNG export, reviewed import, paired Apply and input recovery."""
from base64 import b64encode,b64decode
from copy import deepcopy
from hashlib import sha256
import struct
from .project import ProjectError,canonical
from .battle_character_resources import _fresh
from .battle_pack_palettes import snapshot,inspect,_preview,validate as validate_palettes
from .battle_pack_png_inputs import describe,budget,retain_import,validate as validate_images,read
from importer import battle_pack_png as native
from importer.core import ImportError as NativeError


def _bytes(value):
    if not isinstance(value,str) or len(value)>4*((8*1024*1024+2)//3):raise ProjectError('Pack PNG input exceeds8MiB')
    try:content=b64decode(value,validate=True)
    except (ValueError,TypeError) as error:raise ProjectError('Pack PNG requires exact base64') from error
    if not 1<=len(content)<=8*1024*1024 or b64encode(content).decode()!=value:raise ProjectError('Pack PNG byte coverage changed')
    return content


def _snapshot(project,expected_current_tim_sha256,expected_current_entry_sha256,**context):
    value=snapshot(project,**context)
    if sha256(value[4]).hexdigest()!=expected_current_tim_sha256 or sha256(value[5]).hexdigest()!=expected_current_entry_sha256:raise ProjectError('Pack Current TIM or composed entry changed; inspect again')
    return value


def download(project,palette_index,**args):
    context={k:args[k] for k in ('expected_project_path','expected_source_key','asset_id','catalog_source_key')}
    original,catalog,record,_,body,_=_snapshot(project,**args)
    try:png,stp,profile=native.export(original,catalog,record,palette_index,body)
    except NativeError as error:raise ProjectError(str(error)) from error
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return dict(schema_version='legaia.battle-pack-png-download.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],record=record,
        palette_index=palette_index,current_tim_sha256=args['expected_current_tim_sha256'],current_entry_sha256=args['expected_current_entry_sha256'],profile=profile,
        png_base64=b64encode(png).decode(),stp_base64=b64encode(stp).decode(),png_sha256=sha256(png).hexdigest(),stp_sha256=sha256(stp).hexdigest(),
        filename=f'battle-pack-{record["source_record"]["record_index"]}-palette-{palette_index}.png',layer='current',read_only=True,project_changed=False,gameplay_verified=False)


def _prepare(project,palette_index,palette_mode,png_base64,stp_base64,expected_current_tim_sha256,expected_current_entry_sha256,**context):
    if project.mode!='edit':raise ProjectError('Pack PNG authoring requires Edit mode')
    original,catalog,record,retail,body,entry=_snapshot(project,expected_current_tim_sha256,expected_current_entry_sha256,**context)
    png=_bytes(png_base64);stp=_bytes(stp_base64) if stp_base64 is not None else None
    try:candidate,projection=native.convert(original,catalog,record,palette_index,png,palette_mode,stp,current=body)
    except (NativeError,TypeError,ValueError) as error:raise ProjectError('Pack PNG cannot produce a bounded native projection') from error
    image=describe(record,palette_index,png,palette_mode,stp,body,candidate);images=deepcopy(project.battle_pack_image_overrides);images[context['asset_id']]=image;budget(images)
    edits=[dict(palette_index=i//16,entry_index=i%16,word=struct.unpack_from('<H',candidate,20+i*2)[0]) for i in range(256) if candidate[20+i*2:22+i*2]!=retail[20+i*2:22+i*2]]
    palette_only=candidate[:544]+retail[544:]
    owner=dict(schema_version='legaia.battle-pack-palette-override.v1',asset_id=context['asset_id'],source_record=deepcopy(record['source_record']),edits=edits,current_tim_sha256=sha256(palette_only).hexdigest()) if edits else None
    palettes=deepcopy(project.battle_pack_palette_overrides)
    if owner:palettes[context['asset_id']]=owner
    else:palettes.pop(context['asset_id'],None)
    validate_palettes(project,palettes);at=record['source_record']['byte_offset'];end=at+33312;proposed=entry[:at]+candidate+entry[end:]
    value=dict(schema_version='legaia.battle-pack-png-review.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],record=record,
        palette_index=palette_index,palette_mode=palette_mode,current_inspection=inspect(project,palette_index=palette_index,**context),projection=projection,image_binding=image,palette_binding=owner,
        current_tim_base64=b64encode(body).decode(),candidate_tim_base64=b64encode(candidate).decode(),current_entry_base64=b64encode(entry).decode(),candidate_entry_base64=b64encode(proposed).decode(),
        current_entry_sha256=expected_current_entry_sha256,candidate_entry_sha256=sha256(proposed).hexdigest(),proposed_preview=_preview(candidate,palette_index),
        layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    encoded=canonical(value);value['review_key']=sha256(encoded).hexdigest();value['review_receipt_base64']=b64encode(encoded).decode()
    _fresh(project,context['expected_project_path'],context['expected_source_key']);return value,palettes,images,png,stp,original,catalog,record,body,candidate


def review(project,**args):return _prepare(project,**args)[0]


def apply(project,review_key,**args):
    value,palettes,images,png,stp,original,catalog,record,body,candidate=_prepare(project,**args)
    if value['review_key']!=review_key or value['projection']['byte_change_count']==0:raise ProjectError('Pack PNG Apply requires exact fresh changed Review')
    _fresh(project,args['expected_project_path'],args['expected_source_key'])
    owner,retained,proof=retain_import(project,original,catalog,record,args['palette_index'],png,args['palette_mode'],stp,body)
    if owner!=value['image_binding'] or retained!=candidate:raise ProjectError('Pack retained PNG differs from Review')
    images[args['asset_id']]=owner;validate_images(project,images)
    _fresh(project,args['expected_project_path'],args['expected_source_key'])
    before=dict(palettes=deepcopy(project.battle_pack_palette_overrides),images=deepcopy(project.battle_pack_image_overrides));after=dict(palettes=palettes,images=images)
    project.battle_pack_palette_overrides=palettes;project.battle_pack_image_overrides=images;project.undo_stack.append(dict(target='battle_pack_texture_state',before=before,after=deepcopy(after),label='Battle Pack PNG Texture'));project.redo_stack.clear()
    return dict(schema_version='legaia.battle-pack-png-apply.v1',asset_id=args['asset_id'],retained_input=deepcopy(owner['input']),history_steps=1,project_changed=True,gameplay_verified=False)


def download_input(project,kind,**args):
    _,_,record,_,_,_=_snapshot(project,**args)
    if kind not in ('png','stp'):raise ProjectError('Choose original pack PNG or STP input')
    owner=project.battle_pack_image_overrides.get(args['asset_id'])
    if owner is None or owner['input'][kind+'_sha256'] is None:raise ProjectError('Selected pack image has no retained input of this kind')
    r=deepcopy(owner['input']);content=read(project,r[kind+'_sha256'],r[kind+'_byte_length'],'png')
    _fresh(project,args['expected_project_path'],args['expected_source_key'])
    return dict(schema_version='legaia.battle-pack-png-input-download.v1',project_path=str(project.root),project_source_key=args['expected_source_key'],catalog_source_key=args['catalog_source_key'],record=record,
        current_tim_sha256=args['expected_current_tim_sha256'],current_entry_sha256=args['expected_current_entry_sha256'],kind=kind,retained_input=r,sha256=sha256(content).hexdigest(),byte_length=len(content),
        png_base64=b64encode(content).decode(),filename=f'battle-pack-{record["source_record"]["record_index"]}-original-{kind}.png',layer='historical_authored_input',read_only=True,project_changed=False,gameplay_verified=False)
