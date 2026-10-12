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
    if merged:value['actions'][key]=dict(source_action_sha256=original['source_record']['sha256'],edits=[merged[k] for k in sorted(merged)])
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
