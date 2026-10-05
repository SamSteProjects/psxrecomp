"""Reviewed atomic X/Z placement operations across imported actors and scenery."""
from copy import deepcopy
import math

from importer.core import ImportError
from importer.serialization import encode_placement_coordinate
from .environment_group import _prepare, _merge
from .project import ProjectError, digest
from .project_copy import source_key


def _review(project, scene, entity_ids, delta, operation=None):
    if project.mode != 'edit' or not isinstance(scene, str) or scene != project.active_scene or scene not in project.imports:
        raise ProjectError('Mixed placement requires the active imported scene in Edit mode')
    if (not isinstance(entity_ids, list) or not 2 <= len(entity_ids) <= 128 or
            any(not isinstance(item, str) for item in entity_ids) or len(set(entity_ids)) != len(entity_ids)):
        raise ProjectError('Mixed placement requires 2..128 unique imported actor and decoration identities')
    if (not isinstance(delta, dict) or set(delta) != {'x', 'z'} or
            any(type(v) is not int or abs(v) > 16320 or v % 64 for v in delta.values())):
        raise ProjectError('Mixed offsets require exact X/Z integer multiples of 64 within -16320..16320')
    document = project.imports[scene]
    actors = {actor['semantic_id']: actor for actor in document['actors']}
    actor_ids = sorted(identifier for identifier in entity_ids if identifier in actors)
    decoration_ids = sorted(identifier for identifier in entity_ids if identifier not in actors)
    if not actor_ids or not decoration_ids:
        raise ProjectError('Mixed placement requires at least one imported actor and one static decoration')
    context = _prepare(project, scene, decoration_ids, minimum=1)
    targets, changes, reset_axes = [], {}, {}
    for identifier in actor_ids:
        actor = actors[identifier]
        retail = {axis: actor['imported_transform']['position'].get(axis) for axis in ('x', 'z')}
        before = deepcopy(project.overrides.get(identifier))
        authored = (before or {}).get('Transform', {}).get('position', {})
        current = {axis: authored.get(axis, retail[axis]) for axis in ('x', 'z')}
        proposed = {}
        for axis in ('x', 'z'):
            value = current[axis]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ProjectError(f'{identifier} has no finite {axis.upper()} placement')
            proposed[axis] = value + delta[axis]
            if operation is None or operation['kind']!='reset':
                try:
                    encode_placement_coordinate(proposed[axis], f'{identifier} proposed {axis.upper()}')
                except ImportError as exc:
                    raise ProjectError(str(exc)) from exc
        targets.append(dict(entity_id=identifier, kind='actor', retail=retail, current=current, proposed=proposed))
    targets.extend(dict(t,kind='decoration',proposed=deepcopy(t['current'])) for t in context['targets'])
    if operation is not None:
        axis=operation.get('axis')
        if operation['kind']=='reset':
            for target in targets:target['proposed']=deepcopy(target['retail'])
        elif operation['kind']=='scale':
            anchor=next((t for t in targets if t['entity_id']==operation['anchor_entity_id']),None)
            if anchor is None:raise ProjectError('Mixed scale anchor must be selected')
            if any(type(t['current'][a]) is not int for t in targets for a in ('x','z')):
                raise ProjectError('Mixed scale requires integer Current X/Z coordinates')
            for target in targets:
                step=64 if target['kind']=='actor' else 1
                proposed={}
                for a in ('x','z'):
                    n=anchor['current'][a]*100+(target['current'][a]-anchor['current'][a])*operation['percent']
                    denominator=100*step
                    units=(abs(n)+denominator//2)//denominator
                    proposed[a]=(-units if n<0 else units)*step
                target['proposed']=proposed
        elif operation['kind']=='rotate':
            anchor=next((t for t in targets if t['entity_id']==operation['anchor_entity_id']),None)
            if anchor is None:raise ProjectError('Mixed rotation anchor must be selected')
            if any(type(anchor['current'][a]) is not int or anchor['current'][a] % 64 for a in ('x','z')):
                raise ProjectError('Mixed rotation anchor must lie on the 64-unit actor grid')
            px,pz=anchor['current']['x'],anchor['current']['z']
            turns=operation['quarter_turns']
            for target in targets:
                dx,dz=target['current']['x']-px,target['current']['z']-pz
                x,z=(-dz,dx) if turns==1 else (dz,-dx) if turns==-1 else (-dx,-dz)
                target['proposed']=dict(x=px+x,z=pz+z)
        elif operation['kind']=='align':
            anchor=next((t for t in targets if t['entity_id']==operation['anchor_entity_id']),None)
            if anchor is None:raise ProjectError('Mixed layout anchor must be selected')
            value=anchor['current'][axis]
            if type(value) is not int or value % 64:raise ProjectError('Mixed alignment anchor must lie on the 64-unit actor grid')
            for target in targets:target['proposed'][axis]=value
        else:
            if any(type(t['current'][axis]) is not int or t['current'][axis] % 64 for t in targets):raise ProjectError('Mixed distribution requires selected source coordinates on the 64-unit actor grid')
            ordered=sorted(targets,key=lambda t:(t['current'][axis],t['entity_id']))
            low,high=ordered[0]['current'][axis]//64,ordered[-1]['current'][axis]//64
            span,intervals=high-low,len(ordered)-1
            if span<intervals:raise ProjectError('Mixed distribution requires at least one 64-unit interval per gap')
            for i,target in enumerate(ordered):target['proposed'][axis]=(low+(2*span*i+intervals)//(2*intervals))*64
    for target in targets:
        identifier=target['entity_id']
        if target['kind']=='decoration':
            if operation is None:target['proposed']={a:target['current'][a]+delta[a] for a in ('x','z')}
            continue
        before=deepcopy(project.overrides.get(identifier));after=deepcopy(before or {})
        for axis in ('x','z'):
            try:encode_placement_coordinate(target['proposed'][axis],f'{identifier} proposed {axis.upper()}')
            except ImportError as exc:raise ProjectError(str(exc)) from exc
            if target['proposed'][axis]!=target['current'][axis]:after.setdefault('Transform',{}).setdefault('position',{})[axis]=target['proposed'][axis]
        if operation is not None and operation['kind']=='reset':
            transform=after.get('Transform',{});position=transform.get('position',{})
            reset_axes[identifier]=[a for a in ('x','z') if a in (before or {}).get('Transform',{}).get('position',{})]
            for a in ('x','z'):position.pop(a,None)
            if not position:transform.pop('position',None)
            if not transform:after.pop('Transform',None)
        after=after or None
        if before!=after:changes[identifier]=after
    merged=_merge(project,scene,context,{t['entity_id']:t['proposed'] for t in targets if t['kind']=='decoration'})
    targets=[t for t in targets if t['kind']=='actor']+[dict(t,kind='decoration') for t in merged['targets']]
    if merged['project_change']:
        after = deepcopy(project.overrides.get(scene, {}))
        value = merged['value']
        if value.get('edits') or value.get('instances'):
            after['Environment'] = deepcopy(value)
        else:
            after.pop('Environment', None)
        changes[scene] = after or None
    if source_key(project) != context['before']:
        raise ProjectError('Project changed while reviewing mixed placement')
    identities = sorted(entity_ids)
    key = digest(dict(project_source_key=context['before'], scene=scene,
                      source_sha256=context['source_hash'], entity_ids=identities, delta=delta, **({'operation':operation,'algorithm':'native-coordinate-scale.v1' if operation['kind']=='scale' else 'source-grid-layout.v1','targets':targets} if operation is not None else {})))
    return dict(schema_version='legaia.scene-placement-layout-review.v1' if operation is not None else 'legaia.scene-placement-group-review.v1',
                project_source_key=context['before'], scene_id=scene, source_sha256=context['source_hash'],
                review_key=key, entity_ids=identities, delta=deepcopy(delta),
                targets=sorted(targets, key=lambda t: t['entity_id']), changes=changes,
                affected_count=sum(t['current'] != t['proposed'] for t in targets),
                project_change=bool(changes), scope='imported-actor-and-static-decoration-xz-only',
                gameplay_verified=False, **({'operation':deepcopy(operation)} if operation is not None else {}),
                **({'reset_actor_axes':reset_axes} if operation is not None and operation['kind']=='reset' else {}))


def review(project,scene,entity_ids,delta):
    return _review(project,scene,entity_ids,delta)


def layout_review(project,scene,entity_ids,operation):
    if not isinstance(operation,dict) or operation.get('kind') not in ('align','distribute','reset','rotate','scale'):
        raise ProjectError('Mixed layout requires align/distribute, reset, position rotation or grid spacing scale')
    kind=operation['kind']
    fields=({'kind','anchor_entity_id','percent'} if kind=='scale' else {'kind'} if kind=='reset' else {'kind','anchor_entity_id','quarter_turns'} if kind=='rotate'
            else {'kind','axis','anchor_entity_id'} if kind=='align' else {'kind','axis'})
    if set(operation)!=fields:raise ProjectError('Mixed layout accepts exact operation fields only')
    if kind in ('align','distribute') and operation['axis'] not in ('x','z'):
        raise ProjectError('Mixed layout axis must be X/Z')
    if kind=='rotate' and (type(operation['quarter_turns']) is not int or operation['quarter_turns'] not in (-1,1,2)):
        raise ProjectError('Mixed rotation requires -1, 1 or 2 exact quarter turns')
    if kind=='scale' and (type(operation['percent']) is not int or not 1<=operation['percent']<=1000):
        raise ProjectError('Mixed scale requires an integer percentage from 1 through 1000')
    return _review(project,scene,entity_ids,{'x':0,'z':0},operation)


def apply(project, command):
    if (not isinstance(command, dict) or
            command.get('type') not in ('apply_scene_placement_group','apply_scene_placement_layout') or
            set(command) != {'type','entity_id','entity_ids','review_key', 'operation' if command['type']=='apply_scene_placement_layout' else 'delta'}):
        raise ProjectError('Mixed placement Apply requires owner, selection, offset or layout, and current review key only')
    result = (layout_review(project,command['entity_id'],command['entity_ids'],command['operation']) if command['type']=='apply_scene_placement_layout' else review(project,command['entity_id'],command['entity_ids'],command['delta']))
    if result['review_key'] != command['review_key']:
        raise ProjectError('Mixed placement inputs changed since review')
    after = deepcopy(result['changes'])
    if not after:
        return
    before = {identifier: deepcopy(project.overrides.get(identifier)) for identifier in after}
    for identifier, value in after.items():
        if value is None:
            project.overrides.pop(identifier, None)
        else:
            project.overrides[identifier] = value
    project.undo_stack.append(dict(target='entity_overrides', entity_ids=sorted(before), before=before, after=deepcopy(after)))
    project.redo_stack.clear()
