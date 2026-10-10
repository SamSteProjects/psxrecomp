"""Portable source-bound world-map working groups, never game transforms."""
from copy import copy, deepcopy
import re
import uuid
from .project import ProjectError, AssetDatabase, digest
from .metadata_text import metadata_name
from .worldmap_authoring import state_key
from .worldmap_placements import context, SCENES

COMMANDS={'create_worldmap_selection_set','rename_worldmap_selection_set','update_worldmap_selection_set','delete_worldmap_selection_set'}


def _ids(values):
    if not isinstance(values,list) or not 1<=len(values)<=128 or any(not isinstance(v,str) or not re.fullmatch('[0-9]{4}',v) or int(v)>=512 for v in values) or len(set(values))!=len(values):
        raise ProjectError('World selection requires 1..128 unique native record IDs')
    return sorted(values)


def validate(project,identifier,value):
    try:
        token=identifier.removeprefix('worldmap-selection://')
        if not identifier.startswith('worldmap-selection://') or str(uuid.UUID(token))!=token:raise ValueError()
    except (ValueError,AttributeError):raise ProjectError('Invalid saved world selection identity') from None
    if not isinstance(value,dict) or set(value)!={'id','name','scene','source_record','record_ids','bindings'} or value['id']!=identifier or value['scene'] not in SCENES or metadata_name(value['name'],'World selection name')!=value['name'] or _ids(value['record_ids'])!=value['record_ids']:
        raise ProjectError('Saved world selection requires canonical source-bound metadata')
    source=value['source_record'];bindings=value['bindings']
    if not isinstance(source,dict) or set(source)!={'scene','source_disc_sha256','source_map_sha256','source_floor_lut_sha256'} or source['scene']!=value['scene'] or any(not isinstance(source[k],str) or not re.fullmatch('[0-9a-f]{64}',source[k]) for k in source if k!='scene') or not isinstance(bindings,dict) or set(bindings)!=set(value['record_ids']):
        raise ProjectError('Saved world selection provenance or owner bindings are invalid')
    seen=set();prefix=f'scene://{value["scene"]}/worldmap/placements/'
    for binding in bindings.values():
        if not isinstance(binding,dict) or set(binding)!={'source_record_sha256','entity_ids'} or not isinstance(binding['source_record_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',binding['source_record_sha256']):raise ProjectError('Saved world selection requires native source hashes')
        ids=binding['entity_ids']
        if not isinstance(ids,list) or not 1<=len(ids)<=512 or any(not isinstance(id,str) or not id.startswith(prefix) or not re.fullmatch('[0-9a-f]{4}',id[len(prefix):]) or int(id[len(prefix):],16)>=16384 for id in ids) or ids!=sorted(set(ids)) or seen.intersection(ids):raise ProjectError('Saved world selection has invalid or conflicting source seeds')
        seen.update(ids)
    if len(seen)>512:raise ProjectError('Saved world selection exceeds 512 source seeds')


def review_key(project,value):return digest(dict(project_root=str(project.root),worldmap_selection=value))


def binding(project,scene,record_ids,expected_key):
    ids=_ids(record_ids)
    if project.mode!='edit' or scene not in SCENES or expected_key!=state_key(project):raise ProjectError('World selection requires the same Edit project and fresh source inputs')
    view=copy(project)
    for name,value in vars(project).items():
        if name!='assets':setattr(view,name,deepcopy(value))
    view.assets=AssetDatabase()
    if state_key(view)!=expected_key:raise ProjectError('World selection source changed while capturing inputs')
    _,provenance,records,_,_,_,_,_=context(view,scene)
    bindings={};seen=set()
    for id in ids:
        row=records.get(id)
        if not row or row.get('record_id')!=id or row.get('object_record_index')!=int(id) or not row['writable'] or row['source_cell_count']!=len(row['placements']) or any(p.get('object_record_index')!=int(id) or p.get('source_record_sha256')!=row['source_record_sha256'] for p in row['placements']):raise ProjectError('Saved world groups require complete qualified native ownership')
        entities=sorted(p['entity_id'] for p in row['placements'])
        if seen.intersection(entities):raise ProjectError('World selection source has conflicting native owners')
        seen.update(entities);bindings[id]=dict(source_record_sha256=row['source_record_sha256'],entity_ids=entities)
    if len(seen)>512 or state_key(project)!=expected_key or state_key(view)!=expected_key:raise ProjectError('World selection source changed or exceeds 512 seeds')
    return dict(source_record=deepcopy(provenance),record_ids=ids,bindings=bindings)


def _saved(project,identifier,key):
    if not isinstance(identifier,str) or identifier not in project.worldmap_selection_sets:raise ProjectError('Saved world selection is unavailable')
    value=deepcopy(project.worldmap_selection_sets[identifier]);validate(project,identifier,value)
    if key!=review_key(project,value):raise ProjectError('Saved world selection changed; reopen it')
    return value


def review(project,identifier,key,source_key):
    value=_saved(project,identifier,key);fresh=binding(project,value['scene'],value['record_ids'],source_key)
    if any(fresh[k]!=value[k] for k in fresh):raise ProjectError('Saved world selection source ownership changed; recall refused')
    return dict(schema_version='legaia.worldmap-selection-review.v1',read_only=True,source_key=source_key,selection=deepcopy(value),review_key=review_key(project,value))


def command(project,body):
    if project.mode!='edit' or not isinstance(body,dict) or body.get('type') not in COMMANDS:raise ProjectError('World selection commands require Edit mode')
    kind=body['type']
    if kind=='create_worldmap_selection_set':
        if set(body)!={'type','scene','source_key','record_ids','name'}:raise ProjectError('Save world selection requires exact kingdom/source, records and name')
        if len(project.worldmap_selection_sets)>=128:raise ProjectError('Project is limited to 128 saved world selections')
        identifier='worldmap-selection://'+str(uuid.uuid4());before=None
        after=dict(id=identifier,name=metadata_name(body['name'],'World selection name'),scene=body['scene'],**binding(project,body['scene'],body['record_ids'],body['source_key']))
    else:
        fields={'type','selection_set_id','review_key'}|({'name'} if kind=='rename_worldmap_selection_set' else {'source_key','record_ids'} if kind=='update_worldmap_selection_set' else set())
        if set(body)!=fields:raise ProjectError('World selection command has unsupported fields')
        identifier=body['selection_set_id'];before=_saved(project,identifier,body['review_key']);after=deepcopy(before)
        if kind=='rename_worldmap_selection_set':after['name']=metadata_name(body['name'],'World selection name')
        elif kind=='update_worldmap_selection_set':
            fresh=binding(project,before['scene'],before['record_ids'],body['source_key'])
            if any(fresh[k]!=before[k] for k in fresh):raise ProjectError('Saved world selection source changed; replacement refused')
            after.update(binding(project,before['scene'],body['record_ids'],body['source_key']))
        else:after=None
    if after is not None:
        validate(project,identifier,after)
        if any(id!=identifier and row['scene']==after['scene'] and row['name'].casefold()==after['name'].casefold() for id,row in project.worldmap_selection_sets.items()):raise ProjectError('A world selection with this name already exists in the kingdom')
    if before==after:return
    if after is None:project.worldmap_selection_sets.pop(identifier)
    else:project.worldmap_selection_sets[identifier]=deepcopy(after)
    project.undo_stack.append(dict(target='worldmap_selection_sets',selection_set_id=identifier,before=before,after=deepcopy(after)))
    project.redo_stack.clear()
