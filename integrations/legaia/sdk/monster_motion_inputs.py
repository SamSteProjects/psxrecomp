"""Active historical monster motion GLB metadata and exact source recovery."""
from copy import deepcopy
from base64 import b64encode
from .project import ProjectError
from .battle_character_resources import _fresh,_disc
from .monster_motions import validate
from .monster_motion_glb import validate_input
from importer.pipeline import _disc_context
from importer.monster_archive import decode_catalog,block


def records(project,catalog):
    rows=[];values=project.monster_motion_overrides
    if not any('glb_import' in b for b in values.values()):return rows
    validate(project,values)
    for identifier,binding in sorted(values.items()):
        receipt=binding.get('glb_import')
        if receipt is None:continue
        clip=next((c for c in catalog['animations'] if c['semantic_id']==identifier),None)
        if clip is None:raise ProjectError('Monster retained motion input owner is absent')
        rows.append(dict(semantic_id=f'retained-animation://legaia/monster-archive/{clip["monster_id"]:04d}/entry/{clip["entry_index"]:04d}/glb/{receipt["glb_sha256"]}',name=f'Monster {clip["monster_id"]} Action {clip["entry_index"]} Original Motion GLB',asset_kind='retained_monster_motion_glb',layer='historical_authored_input',model_asset_id=clip['model_asset_id'],animation_asset_id=identifier,sha256=receipt['glb_sha256'],byte_length=receipt['glb_byte_length'],source_record=deepcopy(receipt),retail_source=deepcopy(clip['source_record']),current_motion_sha256=binding['current_motion_sha256'],references=[clip['model_asset_id'],identifier],relationship='historical_import_input_not_final_current_motion',read_only=True,gameplay_verified=False))
    return rows


def download(project,expected_project_path,expected_source_key,animation_id,expected_current_motion_sha256,expected_input_sha256):
    _fresh(project,expected_project_path,expected_source_key)
    with _disc_context(project.disc_path) as (_,disc,_,archive):
        raw=archive.read_entry(archive.entry(867));catalog=decode_catalog(raw,disc);_disc(project,catalog);clip=next((c for c in catalog['animations'] if c['semantic_id']==animation_id),None);binding=project.monster_motion_overrides.get(animation_id)
        if clip is None or binding is None or 'glb_import' not in binding:raise ProjectError('Monster action has no retained motion GLB input')
        receipt=binding['glb_import']
        if binding['current_motion_sha256']!=expected_current_motion_sha256 or receipt['glb_sha256']!=expected_input_sha256:raise ProjectError('Monster Current motion or selected original input changed')
        validate(project,{animation_id:binding});original,_=block(raw,clip['monster_id']);content,_=validate_input(project,original,clip,receipt)
    _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.monster-motion-input-download.v1',project_path=str(project.root),project_source_key=expected_source_key,animation_id=animation_id,current_motion_sha256=expected_current_motion_sha256,retained_source=deepcopy(receipt),sha256=receipt['glb_sha256'],byte_length=len(content),glb_base64=b64encode(content).decode(),filename=f'monster-{clip["monster_id"]}-entry-{clip["entry_index"]}-original-motion.glb',layer='historical_authored_input',read_only=True,project_changed=False,gameplay_verified=False)
