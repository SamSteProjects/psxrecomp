"""Reviewed removal of NPC-owned script families, preserving the retail donor."""
from copy import deepcopy
from .project import ProjectError, digest
from .project_copy import source_key
from .npc_script_binding import FAMILIES


def source(project, identifier):
    draft=project.actor_drafts.get(identifier) if isinstance(identifier,str) else None
    if project.mode!='edit' or not isinstance(draft,dict) or draft['scene_id']!=project.active_scene:
        raise ProjectError('NPC script reset requires an active-scene draft in Edit mode')
    project._validate_actor_draft(identifier,draft);key=source_key(project)
    rows=[dict(id=family,owned_count=len(draft.get(family,{}).get('runs' if family=='dialogue' else 'entries',{}))) for family in FAMILIES]
    result=dict(schema_version='legaia.npc-script-reset-source.v1',entity_id=identifier,
        scene_id=draft['scene_id'],project_source_key=key,draft=deepcopy(draft),families=rows,
        scope='project_metadata',native_byte_preview=False,runtime_binding='not_asserted',gameplay_verified=False)
    if key!=source_key(project):raise ProjectError('Project changed during NPC script reset inspection')
    return result


def review(project,request):
    if not isinstance(request,dict) or set(request)!={'entity_id','families'}:
        raise ProjectError('NPC script reset review requires identity and selected families')
    selected=request['families']
    if (not isinstance(selected,list) or not 1<=len(selected)<=len(FAMILIES) or
            any(not isinstance(f,str) or f not in FAMILIES for f in selected) or
            len(set(selected))!=len(selected) or selected!=[f for f in FAMILIES if f in selected]):
        raise ProjectError('NPC script reset requires unique supported families in Inspector order')
    report=source(project,request['entity_id']);before=report['draft'];after=deepcopy(before)
    if any(f not in before for f in selected):raise ProjectError('Selected NPC script family has no owned edits to reset')
    for family in selected:after.pop(family)
    project._validate_actor_draft(request['entity_id'],after)
    if report['project_source_key']!=source_key(project):raise ProjectError('Project changed during NPC script reset review')
    return dict(schema_version='legaia.npc-script-reset-review.v1',entity_id=request['entity_id'],
        project_source_key=report['project_source_key'],request=deepcopy(request),current=before,proposed=after,
        removed=[row for row in report['families'] if row['id'] in selected],
        review_key=digest(dict(source=report['project_source_key'],request=request,algorithm='npc-script-reset.v1')),
        scope='project_metadata',native_byte_preview=False,runtime_binding='not_asserted',gameplay_verified=False)


def apply(project,command):
    if not isinstance(command,dict) or set(command)!={'type','entity_id','families','review_key'} or command['type']!='reset_actor_draft_script':
        raise ProjectError('NPC script reset Apply requires exact reviewed fields')
    report=review(project,{key:command[key] for key in ('entity_id','families')})
    if command['review_key']!=report['review_key']:raise ProjectError('NPC script reset changed; Review again')
    project.actor_drafts[command['entity_id']]=deepcopy(report['proposed'])
    project.undo_stack.append(dict(target='actor_drafts',entity_id=command['entity_id'],before=deepcopy(report['current']),after=deepcopy(report['proposed'])))
    project.redo_stack.clear()
