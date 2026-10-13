"""Historical monster model input metadata and exact original GLB recovery."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError
from .battle_character_resources import _fresh,_disc
from .monster_models import effective,read
from importer.pipeline import _disc_context
from importer.monster_archive import decode_catalog,block


def records(project,catalog):
    rows=[]
    if not project.monster_model_overrides:return rows
    with _disc_context(project.disc_path) as (_,_,_,archive):
        raw=archive.read_entry(archive.entry(867))
        for identifier,binding in sorted(project.monster_model_overrides.items()):
            model=next((r for r in catalog['models'] if r['semantic_id']==identifier),None)
            if model is None:raise ProjectError('Monster retained model owner is missing')
            texture=next((r for r in catalog['textures'] if r['model_asset_id']==identifier),None);original,_=block(raw,model['monster_id']);effective(project,original,model,texture,binding)
            for index,receipt in enumerate(binding['inputs']):
                rows.append(dict(semantic_id=f'retained-model://legaia/monster-archive/{model["monster_id"]:04d}/{index:02d}/{receipt["glb_sha256"]}',name=f'Monster {model["monster_id"]} Original GLB Input {index+1}',asset_kind='retained_monster_glb',layer='historical_authored_input',model_asset_id=identifier,import_index=index,import_count=len(binding['inputs']),sha256=receipt['glb_sha256'],byte_length=receipt['glb_byte_length'],source_record=deepcopy(receipt),retail_source=deepcopy(model['source_record']),current_tmd_sha256=binding['current_tmd_sha256'],references=[identifier],relationship='historical_import_input_not_final_current_model',read_only=True,gameplay_verified=False))
    return rows


def download(project,expected_project_path,expected_source_key,asset_id,expected_current_tmd_sha256,import_index,expected_input_sha256):
    _fresh(project,expected_project_path,expected_source_key)
    if type(import_index) is not int or not 0<=import_index<16:raise ProjectError('Choose an existing monster model import')
    with _disc_context(project.disc_path) as (_,disc,_,archive):
        raw=archive.read_entry(archive.entry(867));catalog=decode_catalog(raw,disc);_disc(project,catalog)
        model=next((r for r in catalog['models'] if r['semantic_id']==asset_id),None);binding=project.monster_model_overrides.get(asset_id)
        if model is None or binding is None:raise ProjectError('Monster model has no retained imports')
        if binding['current_tmd_sha256']!=expected_current_tmd_sha256 or import_index>=len(binding['inputs']):raise ProjectError('Monster Current model or input selection changed')
        texture=next((r for r in catalog['textures'] if r['model_asset_id']==asset_id),None);original,_=block(raw,model['monster_id']);effective(project,original,model,texture,binding)
        receipt=binding['inputs'][import_index]
        if receipt['glb_sha256']!=expected_input_sha256:raise ProjectError('Monster selected GLB input changed')
        content=read(project,receipt['glb_sha256'],receipt['glb_byte_length'],'glb')
    _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.monster-model-input-download.v1',project_path=str(project.root),project_source_key=expected_source_key,asset_id=asset_id,current_tmd_sha256=expected_current_tmd_sha256,import_index=import_index,input_count=len(binding['inputs']),retained_source=deepcopy(receipt),sha256=sha256(content).hexdigest(),byte_length=len(content),glb_base64=b64encode(content).decode(),filename=f'monster-{model["monster_id"]}-input-{import_index+1}.glb',layer='historical_authored_input',read_only=True,project_changed=False,gameplay_verified=False)
