"""Read-only tagged PLAYER GLB export and native section proposal Review."""
from base64 import b64encode,b64decode
from hashlib import sha256
from copy import deepcopy
import json
from .project import ProjectError,digest
from .player_battle import preview,_pixels
from .battle_character_resources import _fresh
from importer import player_model_authoring as native
from importer.player_battle import _sources,assemble_tmd
from importer.player_battle_textures import reconstruct_source
from importer.core import ImportError as RetailImportError

MAX_GLB=4*1024*1024


def _snapshot(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,equipped):
    if project.mode!='edit':raise ProjectError('PLAYER model authoring requires Edit mode')
    receipt=preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,equipped)
    source=receipt['record']['source_record'];_,sources=_sources(project.disc_path);retail=sources[receipt['record']['player_index']][3]
    from .player_model_store import effective
    raw=effective(project,receipt['record'],retail)
    from .player_action_store import effective as effective_actions
    from importer.player_battle import actions
    action_file,_=effective_actions(project,receipt['record'],retail)
    receipt['_action_file']=action_file
    receipt['action_clips'],_=actions(action_file,receipt['record']['player_index'],source['disc']['sha256'])
    receipt['action_file_sha256']=sha256(action_file).hexdigest()
    receipt['action_binding']=deepcopy(project.player_action_overrides.get(asset_id))
    if raw!=retail:
        g,a,_=assemble_tmd(raw,equipped);g['textures'],a['texture_assembly']=reconstruct_source(raw,receipt['record']['player_index'],source['disc']['sha256'],a,g,receipt['assembly']['texture_assembly']['placement']);a['texture_routing']='static_authoring_projection';_pixels(g);g.update(semantic_id=asset_id,source_record=deepcopy(source));receipt.update(geometry=g,assembly=a,layer='current')
    try:glb,binding=native.export_player_model(raw,sha256(raw).hexdigest(),equipped,receipt['geometry'])
    except RetailImportError as e:raise ProjectError(str(e)) from e
    if len(glb)>MAX_GLB:raise ProjectError('PLAYER authoring GLB exceeds its 4 MiB budget')
    wrapped=dict(schema_version='legaia.player-model-source-binding.v1',project_path=str(project.root),project_source_key=expected_source_key,asset_id=asset_id,catalog_source_key=catalog_source_key,native_binding=binding)
    if len(json.dumps(wrapped).encode())>256*1024:raise ProjectError('PLAYER source binding exceeds its metadata budget')
    _fresh(project,expected_project_path,expected_source_key)
    return raw,receipt,glb,wrapped


def export(project,**context):
    raw,receipt,glb,binding=_snapshot(project,**context);_,_,tmd=assemble_tmd(raw,context['equipped'])
    candidate,report=native.import_player_model(raw,binding['native_binding'],glb)
    if candidate!=raw or report['changes']:raise ProjectError('PLAYER tagged GLB failed its exact native roundtrip')
    return dict(schema_version='legaia.player-model-export.v1',binding=binding,record=receipt['record'],assembly=receipt['assembly'],glb_base64=b64encode(glb).decode('ascii'),glb_sha256=sha256(glb).hexdigest(),glb_byte_length=len(glb),source_tmd_base64=b64encode(tmd).decode('ascii'),filename=f'player-{receipt["record"]["player_index"]}-native-authoring.glb',read_only=True,project_changed=False,gameplay_verified=False)


def prepare_review(project,binding,glb_base64,**context):
    raw,receipt,_,fresh=_snapshot(project,**context)
    if not isinstance(binding,dict) or digest(binding)!=digest(fresh):raise ProjectError('PLAYER authoring binding changed; export the current selection again')
    if not isinstance(glb_base64,str) or len(glb_base64)>4*((MAX_GLB+2)//3):raise ProjectError('PLAYER GLB exceeds its 4 MiB input budget')
    try:content=b64decode(glb_base64,validate=True)
    except (ValueError,TypeError) as e:raise ProjectError('PLAYER GLB requires canonical base64 bytes') from e
    if not 28<=len(content)<=MAX_GLB or b64encode(content).decode('ascii')!=glb_base64:raise ProjectError('PLAYER GLB byte coverage is invalid')
    try:proposed,projection=native.import_player_model(raw,binding['native_binding'],content)
    except RetailImportError as e:raise ProjectError(str(e)) from e
    if len(projection['changes'])>60000:raise ProjectError('PLAYER Review exceeds its typed change budget')
    geometry,assembly,tmd=assemble_tmd(proposed,context['equipped']);proof=receipt['assembly']['texture_assembly']['placement']
    geometry['textures'],assembly['texture_assembly']=reconstruct_source(proposed,receipt['record']['player_index'],receipt['record']['source_record']['disc']['sha256'],assembly,geometry,proof);assembly['texture_routing']='static_authoring_projection';_pixels(geometry)
    geometry.update(semantic_id=context['asset_id'],source_record=dict(original=deepcopy(receipt['record']['source_record']),proposed_sha256=projection['proposed_sha256']))
    result=dict(schema_version='legaia.player-model-review.v1',binding=deepcopy(binding),record=receipt['record'],input_sha256=sha256(content).hexdigest(),input_byte_length=len(content),projection=projection,candidate_tmd_base64=b64encode(tmd).decode('ascii'),geometry=geometry,assembly=assembly,layer='proposed',read_only=True,project_changed=False,gameplay_verified=False,persistence='not_applied')
    result['review_key']=digest(result)
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return raw,proposed,content,result


def review(project,binding,glb_base64,**context):
    return prepare_review(project,binding,glb_base64,**context)[3]


def apply(project,binding,glb_base64,review_key,**context):
    from .player_model_store import publish
    raw,proposed,content,result=prepare_review(project,binding,glb_base64,**context)
    if result['review_key']!=review_key:raise ProjectError('PLAYER Apply requires its exact fresh Review')
    if not result['projection']['changes']:raise ProjectError('PLAYER Apply has no quantized changes')
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    published=publish(project,result['record'],raw,proposed,content,binding,review_key)
    return dict(schema_version='legaia.player-model-apply.v1',binding=published,project_changed=True,history_steps=1,gameplay_verified=False)


def current(project,**context):
    raw,receipt,_,binding=_snapshot(project,**context)
    _,_,tmd=assemble_tmd(raw,context['equipped'])
    _,sources=_sources(project.disc_path);_,_,retail_tmd=assemble_tmd(sources[receipt['record']['player_index']][3],context['equipped'])
    from importer.player_battle import table
    descriptor=table(raw)[0]['descriptor_offset'];action=receipt['_action_file']
    composed=raw[:16]+action[16:descriptor]+raw[descriptor:]
    return dict(schema_version='legaia.player-model-current.v2',project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],record=receipt['record'],assembly=receipt['assembly'],geometry=receipt['geometry'],binding=deepcopy(project.player_model_overrides.get(context['asset_id'])),effective_file_sha256=sha256(raw).hexdigest(),current_composed_sha256=sha256(composed).hexdigest(),action_clips=receipt['action_clips'],action_file_sha256=receipt['action_file_sha256'],action_binding=receipt['action_binding'],tmd_base64=b64encode(tmd).decode('ascii'),retail_tmd_base64=b64encode(retail_tmd).decode('ascii'),layer='current',read_only=True,project_changed=False,gameplay_verified=False)


def _current_tracks(project, expected_current_sha256, action_slot, **context):
    from importer.player_battle import action_frames_source
    raw, receipt, _, _ = _snapshot(project, **context)
    if sha256(raw).hexdigest() != expected_current_sha256:
        raise ProjectError('PLAYER Current changed; inspect Current again')
    if type(action_slot) is not int or not 0 <= action_slot < 12:
        raise ProjectError('Choose an existing PLAYER action slot')
    clip = receipt['record']['actions'][action_slot]
    if not clip['preview_supported']:
        raise ProjectError('Empty PLAYER action has no Current pose or clip')
    # Model pools and action record0 are independently source-qualified. Sample
    # the effective action ledger through the selected Current model mapping.
    action_file=receipt['_action_file']
    frames = action_frames_source(action_file,receipt['record']['player_index'],receipt['record']['source_record']['disc']['sha256'], receipt['assembly'], receipt['action_clips'][action_slot])
    return receipt, clip, frames


def current_pose(project, expected_current_sha256, action_slot, frame_index, **context):
    from importer.animation import pose_vertices
    receipt, clip, frames = _current_tracks(project, expected_current_sha256, action_slot, **context)
    if type(frame_index) is not int or not 0 <= frame_index < len(frames):
        raise ProjectError('Choose an existing whole PLAYER action frame')
    geometry = receipt['geometry']
    transforms = frames[frame_index]['object_transforms']
    geometry['vertices'] = pose_vertices(geometry['vertices'], geometry['objects'], transforms)
    geometry['bounds'] = dict(min=[min(v[i] for v in geometry['vertices']) for i in range(3)],
        max=[max(v[i] for v in geometry['vertices']) for i in range(3)])
    geometry.update(posed=True, coordinate_system='retail_psx_actor_local_y_down')
    geometry.pop('triangle_normals', None); geometry.pop('normal_preview', None)
    _fresh(project, context['expected_project_path'], context['expected_source_key'])
    return dict(schema_version='legaia.player-battle-pose.v1',
        project_path=str(project.root), project_source_key=context['expected_source_key'],
        catalog_source_key=context['catalog_source_key'], record=receipt['record'],
        assembly=receipt['assembly'], geometry=geometry, clip=clip, object_transforms=transforms,
        action_slot=action_slot, frame_index=frame_index, effective_file_sha256=expected_current_sha256,current_action_clip=receipt['action_clips'][action_slot],
        layer='current', read_only=True, project_changed=False, gameplay_verified=False)


def current_export(project, expected_current_sha256, mode, action_slot, frame_index, fps, **context):
    import math
    from importer.export import encode_model_glb
    if mode not in ('object-local', 'pose', 'clip'):
        raise ProjectError('Choose a supported PLAYER GLB export mode')
    if mode == 'object-local':
        if any(v is not None for v in (action_slot, frame_index, fps)):
            raise ProjectError('Object-local export accepts no action, frame or rate')
        raw, receipt, _, _ = _snapshot(project, **context)
        if sha256(raw).hexdigest() != expected_current_sha256:
            raise ProjectError('PLAYER Current changed; inspect Current again')
        clip, frames = None, None
    else:
        if mode == 'pose' and fps is not None:
            raise ProjectError('Baked pose export accepts no playback rate')
        if mode == 'clip' and (frame_index is not None or type(fps) not in (int, float)
                or not math.isfinite(fps) or not 1 <= fps <= 120):
            raise ProjectError('Full clip requires interchange rate 1–120 fps and no frame')
        receipt, clip, frames = _current_tracks(project, expected_current_sha256, action_slot, **context)
        if mode == 'pose' and (type(frame_index) is not int or not 0 <= frame_index < len(frames)):
            raise ProjectError('Choose an existing whole PLAYER action frame')
    geometry = receipt['geometry']
    geometry['source_record'] = dict(original=deepcopy(receipt['record']['source_record']),
        current_sha256=expected_current_sha256, player_assembly=receipt['assembly'])
    geometry['representation'] = 'current-selected-player-equipment-assembly'
    if mode != 'object-local':
        geometry['animation'] = dict(semantic_id=clip['semantic_id'], source_record=receipt['action_clips'][action_slot]['source_record'],
            timing=clip['timing'], runtime_state='not_observed',
            **({'source_frame_index':frame_index} if mode == 'pose' else {}))
        if mode == 'pose':
            from importer.animation import pose_vertices
            transforms = frames[frame_index]['object_transforms']
            posed = deepcopy(geometry)
            posed['vertices'] = pose_vertices(geometry['vertices'], geometry['objects'], transforms)
            posed.update(posed=True, coordinate_system='retail_psx_actor_local_y_down', object_transforms=transforms)
            posed.pop('triangle_normals', None); posed.pop('normal_preview', None)
            geometry['frames'] = [posed]
        else:
            geometry['frames'] = frames
    content, audit = encode_model_glb(geometry, 0 if mode == 'pose' else None,
        clip_fps=fps if mode == 'clip' else None)
    _fresh(project, context['expected_project_path'], context['expected_source_key'])
    suffix = 'object-local' if mode == 'object-local' else f'action-{action_slot}-frame-{frame_index}' if mode == 'pose' else f'action-{action_slot}-clip'
    return dict(schema_version='legaia.player-battle-export.v1', project_path=str(project.root),
        project_source_key=context['expected_source_key'], catalog_source_key=context['catalog_source_key'],
        record=receipt['record'], assembly=receipt['assembly'], mode=mode, action_slot=action_slot,
        frame_index=frame_index, fps=fps, clip=clip,
        filename=f'player-{receipt["record"]["player_index"]}-'+ '-'.join(str(i) for i in context['equipped'])+'-current-'+suffix+'.glb',
        glb_base64=b64encode(content).decode('ascii'), audit=audit,
        effective_file_sha256=expected_current_sha256, current_action_clip=receipt['action_clips'][action_slot] if clip else None,layer='current',
        read_only=True, project_changed=False, gameplay_verified=False)
