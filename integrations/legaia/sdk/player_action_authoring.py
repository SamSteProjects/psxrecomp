"""Fresh numeric PLAYER action Review/Apply with canonical Retail-ledger replay."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from importer.player_battle import _sources,actions,decode_part
from importer.player_animation_authoring import patch_player_action
from importer.core import ImportError as RetailImportError
from .player_battle import preview
from .battle_character_resources import _fresh
from .player_action_store import compose,effective,publish
from .project import ProjectError,digest


def _snapshot(project,action_slot,**context):
    if project.mode!='edit':raise ProjectError('PLAYER action authoring requires Edit mode')
    if type(action_slot) is not int or not 0<=action_slot<12:raise ProjectError('Choose an existing PLAYER action')
    receipt=preview(project,**context);record=receipt['record'];_,sources=_sources(project.disc_path);raw=sources[record['player_index']][3]
    if sha256(raw).hexdigest()!=record['source_record']['sha256']:raise ProjectError('PLAYER action Retail file changed')
    current,_=effective(project,record,raw);clips,bank=actions(current,record['player_index'],record['source_record']['disc']['sha256']);originals,original_bank=actions(raw,record['player_index'],record['source_record']['disc']['sha256'])
    if not clips[action_slot]['preview_supported']:raise ProjectError('Empty PLAYER action has no authorable channels')
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return record,raw,current,clips[action_slot],bank,originals[action_slot],original_bank


def inspect(project,action_slot,**context):
    record,raw,current,clip,bank,original,original_bank=_snapshot(project,action_slot,**context);source=clip['source_record'];start,length=source['byte_offset'],source['byte_length']
    return dict(schema_version='legaia.player-action-inspection.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],record=record,
        original_clip=original,current_clip=clip,current_file_sha256=sha256(current).hexdigest(),current_bank_sha256=sha256(bank).hexdigest(),
        original_action_base64=b64encode(original_bank[start:start+length]).decode(),current_action_base64=b64encode(bank[start:start+length]).decode(),
        binding=deepcopy(project.player_action_overrides.get(record['semantic_id'])),layer='current',read_only=True,project_changed=False,gameplay_verified=False)


def prepare_review(project,action_slot,expected_current_sha256,expected_action_sha256,edits,**context):
    record,retail,current,clip,bank,original,original_bank=_snapshot(project,action_slot,**context)
    if sha256(current).hexdigest()!=expected_current_sha256 or clip['source_record']['sha256']!=expected_action_sha256:raise ProjectError('PLAYER action Current changed; inspect again')
    if not isinstance(edits,list) or len(edits)>4096:raise ProjectError('PLAYER action Review accepts at most 4096 part-frame edits')
    try:direct,projection=patch_player_action(current,expected_current_sha256,record['player_index'],action_slot,expected_action_sha256,edits)
    except RetailImportError as e:raise ProjectError(str(e)) from e
    old=project.player_action_overrides.get(record['semantic_id']);value=deepcopy(old) if old else dict(schema_version='legaia.player-action-override.v1',asset_id=record['semantic_id'],source_record=deepcopy(record['source_record']),actions={},current_sha256='')
    key=f'{action_slot:04d}';held=value['actions'].get(key,{}).get('edits',[]);merged={(e['frame_index'],e['part_index']):deepcopy(e) for e in held}
    for edit in edits:
        pair=(edit['frame_index'],edit['part_index']);target=merged.setdefault(pair,dict(frame_index=pair[0],part_index=pair[1]))
        at=original['source_record']['byte_offset']+2+(pair[0]*clip['part_count']+pair[1])*9;source=decode_part(original_bank[at:at+9])
        for field in ('translation','rotation_psx'):
            for axis,v in edit.get(field,{}).items():
                axes=target.setdefault(field,{})
                if v==source[field]['xyz'.index(axis)]:axes.pop(axis,None)
                else:axes[axis]=v
                if not axes:target.pop(field,None)
        if set(target)=={'frame_index','part_index'}:merged.pop(pair)
    if len(merged)>4096:raise ProjectError('PLAYER action stored ledger exceeds 4096 part-frame edits')
    if merged:value['actions'][key]=dict(source_action_sha256=original['source_record']['sha256'],edits=[merged[k] for k in sorted(merged)],**({'glb_import':deepcopy(value['actions'][key]['glb_import'])} if 'glb_import' in value['actions'].get(key,{}) else {}))
    else:value['actions'].pop(key,None)
    if value['actions']:
        candidate,reports=compose(retail,record['semantic_id'],value);value['current_sha256']=sha256(candidate).hexdigest()
    else:candidate=retail;value=None;reports=[]
    _,direct_bank=actions(direct,record['player_index'],'0'*64);_,candidate_bank=actions(candidate,record['player_index'],'0'*64)
    if direct_bank!=candidate_bank:raise ProjectError('PLAYER canonical ledger differs from requested Current channels')
    projection['proposed_file_sha256']=sha256(candidate).hexdigest()
    source=original['source_record'];start,length=source['byte_offset'],source['byte_length']
    result=dict(schema_version='legaia.player-action-review.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],record=record,original_clip=original,
        projection=projection,binding=value,serialization='canonical_retail_ledger_replay',replay_reports=reports,
        current_action_base64=b64encode(bank[start:start+length]).decode(),proposed_action_base64=b64encode(candidate_bank[start:start+length]).decode(),layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    result['review_key']=digest(result);_fresh(project,context['expected_project_path'],context['expected_source_key'])
    return record,retail,result


def review(project,**args):return prepare_review(project,**args)[2]


def apply(project,review_key,**args):
    record,retail,result=prepare_review(project,**args)
    if result['review_key']!=review_key:raise ProjectError('PLAYER action Apply requires its exact fresh Review')
    if not result['projection']['channels']:raise ProjectError('PLAYER action Apply has no native changes')
    publish(project,record,retail,result['binding'])
    return dict(schema_version='legaia.player-action-apply.v1',binding=result['binding'],history_steps=1,project_changed=True,gameplay_verified=False)


def prepare_restore(project,action_slot,expected_current_sha256,expected_action_sha256,**context):
    record,_,current,clip,_,original,original_bank=_snapshot(project,action_slot,**context)
    if sha256(current).hexdigest()!=expected_current_sha256 or clip['source_record']['sha256']!=expected_action_sha256:
        raise ProjectError('PLAYER action Current changed; inspect again before restoring')
    binding=project.player_action_overrides.get(record['semantic_id'])
    held=binding.get('actions',{}).get(f'{action_slot:04d}') if binding else None
    if not held:raise ProjectError('Selected PLAYER action has no authored channels to restore')
    edits=[]
    for edit in held['edits']:
        frame,part=edit['frame_index'],edit['part_index'];at=original['source_record']['byte_offset']+2+(frame*clip['part_count']+part)*9
        source=decode_part(original_bank[at:at+9]);edits.append(dict(frame_index=frame,part_index=part,
            **{field:{axis:source[field]['xyz'.index(axis)] for axis in edit[field]} for field in ('translation','rotation_psx') if field in edit}))
    record,retail,result=prepare_review(project,action_slot=action_slot,expected_current_sha256=expected_current_sha256,
        expected_action_sha256=expected_action_sha256,edits=edits,**context)
    if result['proposed_action_base64']!=b64encode(original_bank[original['source_record']['byte_offset']:original['source_record']['byte_offset']+original['source_record']['byte_length']]).decode():
        raise ProjectError('PLAYER action restore differs from its complete Retail stream')
    result['operation']='restore_retail_action';result['review_key']=digest({k:v for k,v in result.items() if k!='review_key'})
    return record,retail,result


def review_restore(project,**args):return prepare_restore(project,**args)[2]


def apply_restore(project,review_key,**args):
    record,retail,result=prepare_restore(project,**args)
    if result['review_key']!=review_key:raise ProjectError('PLAYER restore Apply requires its exact fresh restore Review')
    publish(project,record,retail,result['binding'])
    return dict(schema_version='legaia.player-action-apply.v1',binding=result['binding'],history_steps=1,project_changed=True,gameplay_verified=False)


def prepare_range(project,action_slot,expected_current_sha256,expected_action_sha256,range_spec,**context):
    _,_,current,clip,bank,_,_=_snapshot(project,action_slot,**context)
    if sha256(current).hexdigest()!=expected_current_sha256 or clip['source_record']['sha256']!=expected_action_sha256:
        raise ProjectError('PLAYER range Current changed; inspect again')
    if not isinstance(range_spec,dict) or set(range_spec)!={'frame_start','frame_end','part_index','field','axis','mode','value'}:
        raise ProjectError('PLAYER range requires exact frame/part/channel/mode/value fields')
    start,end,part,value=(range_spec[k] for k in ('frame_start','frame_end','part_index','value'))
    field,axis,mode=(range_spec[k] for k in ('field','axis','mode'))
    if any(type(v) is not int for v in (start,end,part,value)) or not 0<=start<=end<clip['frame_count'] or not 0<=part<clip['part_count'] or field not in ('translation','rotation_psx') or axis not in ('x','y','z') or mode not in ('set','offset'):
        raise ProjectError('PLAYER range must name stored whole frames/part and an exact integer channel operation')
    low,high=(-2048,2047) if field=='translation' else (0,4095);edits=[]
    for frame in range(start,end+1):
        at=clip['source_record']['byte_offset']+2+(frame*clip['part_count']+part)*9;before=decode_part(bank[at:at+9])[field]['xyz'.index(axis)];after=value if mode=='set' else before+value
        if not low<=after<=high:raise ProjectError('PLAYER range result exceeds native bounds; no wrapping or clamping is applied')
        edits.append(dict(frame_index=frame,part_index=part,**{field:{axis:after}}))
    record,retail,result=prepare_review(project,action_slot=action_slot,expected_current_sha256=expected_current_sha256,expected_action_sha256=expected_action_sha256,edits=edits,**context)
    result.update(operation='native_channel_range',range_spec=deepcopy(range_spec));result['review_key']=digest({k:v for k,v in result.items() if k!='review_key'})
    return record,retail,result


def review_range(project,**args):return prepare_range(project,**args)[2]


def apply_range(project,review_key,**args):
    record,retail,result=prepare_range(project,**args)
    if result['review_key']!=review_key or not result['projection']['channels']:raise ProjectError('PLAYER range Apply requires a fresh changed Review')
    publish(project,record,retail,result['binding'])
    return dict(schema_version='legaia.player-action-apply.v1',binding=result['binding'],history_steps=1,project_changed=True,gameplay_verified=False)
