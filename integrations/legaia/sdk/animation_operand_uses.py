"""Matching encoded argument sets, never inferred model/clip identities."""
from copy import deepcopy
from importer.man_layout import read_man_layout
from .project import ProjectError
from .script_animation_operands import context,options,COMPONENT
from .script_branches import state_key

def inspect(project,owner,operand_id,expected_state_key,offset=0):
    if type(offset) is not int or not 0<=offset<8192 or offset%256:raise ProjectError('Animation usage page offset must be a multiple of 256 within the scan bound')
    key=state_key(project)
    if key!=expected_state_key:raise ProjectError('Animation argument usage inputs changed; reopen inspection')
    if project._dialogue_document(owner)['scene']['semantic_id']!=project.active_scene:raise ProjectError('Open the animation usage owner source scene first')
    selected=options(project,owner)
    target=next((row for row in selected['targets'] if row['semantic_id']==operand_id),None)
    if target is None:raise ProjectError('Select a qualified source animation argument target')
    adapter=context(project,owner);scene=project.active_scene;owners=[]
    for record in read_man_layout(adapter._man)['records']:
        partition,index=record['partition'],record['record_index']
        if partition not in (1,2) or partition==1 and index==0:continue
        owners.append(scene+('/actors/man-p1/' if partition==1 else '/scripts/man-p2/')+f'{index:04d}')
    found=[];scanned=0;cache={}
    def collect(entity,donor,kind,entries):
        nonlocal scanned
        if donor not in cache:cache[donor]=adapter.options(donor)['targets']
        native=cache[donor];known={row['semantic_id'] for row in native}
        if set(entries)-known:raise ProjectError('Animation argument usage contains unresolved authored targets')
        adapter.patch(entries)
        for original in native:
            scanned+=1
            if scanned>8192:raise ProjectError('Animation argument usage exceeds 8192 qualified instruction sites')
            row=deepcopy(original);row['authored_values']=deepcopy(entries.get(row['semantic_id']))
            row['effective_values']=deepcopy(entries.get(row['semantic_id'],row['values']))
            retail=row['mnemonic']==target['mnemonic'] and row['values']==target['effective_values']
            effective=row['mnemonic']==target['mnemonic'] and row['effective_values']==target['effective_values']
            if retail or effective:found.append(dict(entity_id=entity,donor_entity_id=donor,kind=kind,target=row,retail_match=retail,effective_match=effective))
    for identity in sorted(owners):collect(identity,identity,'source',project.overrides.get(identity,{}).get(COMPONENT,{}).get('entries',{}))
    for identity,draft in sorted(project.actor_drafts.items()):
        if draft['scene_id']!=scene:continue
        project._validate_actor_draft(identity,draft)
        collect(identity,draft['donor_entity_id'],'npc',draft.get('animation_operands',{}).get('entries',{}))
    if state_key(project)!=key:raise ProjectError('Project changed during animation argument usage inspection')
    if offset and offset>=len(found):raise ProjectError('Animation usage page is outside the matching result set')
    return dict(schema_version='legaia.animation-operand-uses.v2',scene_id=scene,owner_id=owner,animation_operand_id=operand_id,state_key=key,
        query_values=deepcopy(target['effective_values']),mnemonic=target['mnemonic'],source=deepcopy(selected['source']),
        rows=found[offset:offset+256],page_offset=offset,page_size=256,match_count=len(found),truncated=len(found)>256,scanned_owner_count=len(owners),scanned_target_count=scanned,
        read_only=True,gameplay_verified=False,runtime_binding='not_asserted',identity_resolution='numeric_arguments_only')
