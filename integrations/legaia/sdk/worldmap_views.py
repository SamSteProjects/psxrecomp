"""Source-bound global world display views in the shared saved-view collection."""
from copy import deepcopy
import math,re,uuid
from importer.worldmap_geometry import load_worldmap_geometry
from .project import ProjectError,digest
from .project_assets import _metadata,_budget
from .metadata_text import metadata_name
from .scene_views import review_key
from .worldmap_authoring import state_key
from .worldmap_placements import SCENES
COMMANDS={'create_worldmap_view','rename_worldmap_view','update_worldmap_view','delete_worldmap_view'}

def display(value):
 if not isinstance(value,dict) or set(value)!={'camera','layer','models','scope','selected_id','wireframe'}:raise ProjectError('World view requires exact camera, layer, visibility, scope and selection')
 c=value['camera'];number=lambda n,a,b:type(n) in (int,float) and a<=n<=b and math.isfinite(n)
 if not isinstance(c,dict) or set(c)!={'projection','yaw','pitch','distance','target'} or c['projection'] not in ('perspective','orthographic') or not number(c['yaw'],-1e12,1e12) or not number(c['pitch'],0 if c['projection']=='orthographic' else .05,math.pi/2) or not number(c['distance'],10,1e6) or not isinstance(c['target'],dict) or set(c['target'])!={'x','y','z'} or any(not number(n,-1e8,1e8) for n in c['target'].values()):raise ProjectError('World view camera exceeds supported finite display limits')
 if value['layer'] not in ('retail','current') or type(value['models']) is not bool or type(value['wireframe']) is not bool or value['scope'] not in ('all','selected','selected-asset') or not isinstance(value['selected_id'],str) or not re.fullmatch(r'scene://map0[123]/worldmap/(ground|placements/[0-3][0-9a-f]{3}|authored-placements/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})',value['selected_id']):raise ProjectError('World view has unsupported display membership')
 if '/authored-placements/' in value['selected_id'] and value['layer']!='current':raise ProjectError('Authored World view targets require the Current layer')
 return deepcopy(value)

def authored_owner(entity):
 a=entity['authored_placement']
 owner=dict(placement_id=a['placement_id'],native_entity_id=entity['native_entity_id'],record_index=a['record_index'],target_cell=a['target_cell'],model_pool_index=entity['model_pool_index'] if entity.get('placement_scope')=='authored_scripted_seed' else a['model_pool_index'])
 if entity.get('placement_scope')=='authored_scripted_seed':
  owner.update(placement_kind='scripted',script_id=a['script_id'],shared_script=a['shared_script'])
 return owner

def validate(project,identifier,value):
 try:
  if not isinstance(identifier,str) or not identifier.startswith('view://') or str(uuid.UUID(identifier[7:]))!=identifier[7:]:raise ValueError()
 except ValueError:raise ProjectError('Invalid world view identity') from None
 if not isinstance(value,dict) or set(value)!={'id','kind','name','scene_id','source_record','binding','display'} or value['id']!=identifier or value['kind']!='worldmap' or value['scene_id'] not in [f'scene://{s}/worldmap' for s in SCENES] or metadata_name(value['name'],'World view name')!=value['name']:raise ProjectError('World view has invalid saved identity or metadata')
 scene=value['scene_id'].split('/')[2];s=value['source_record'];b=value['binding'];d=display(value['display']);hash=lambda h:isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h)
 if not isinstance(s,dict) or s.get('scene')!=scene or any(not hash(s.get(k)) for k in ('disc_sha256','map_sha256','bundle_sha256','floor_lut_sha256')) or not isinstance(b,dict) or set(b)!=({'entity_id','asset_id','entity_sha256','asset_source_sha256','source_instance_ids'}|({'authored_owner'} if '/authored-placements/' in d['selected_id'] else set())) or b['entity_id']!=d['selected_id'] or not b['entity_id'].startswith(f'scene://{scene}/worldmap/') or not isinstance(b['asset_id'],str) or not re.fullmatch(f'asset://{scene}/worldmap/(walk-ground|models/[0-9a-f]{{4}})',b['asset_id']) or not hash(b['entity_sha256']) or not hash(b['asset_source_sha256']):raise ProjectError('World view source binding is invalid')
 authored='/authored-placements/' in d['selected_id']
 if authored:
  a=b['authored_owner'];target_uuid=d['selected_id'].rsplit('/',1)[1]
  if (not isinstance(a,dict) or set(a)!=({'placement_id','native_entity_id','record_index','target_cell','model_pool_index'}|({'placement_kind','script_id','shared_script'} if a.get('placement_kind')=='scripted' else set())) or a['placement_id']!='placement://authored/'+target_uuid or type(a['record_index']) is not int or not 4<=a['record_index']<512 or type(a['target_cell']) is not int or not 0<=a['target_cell']<16384 or type(a['model_pool_index']) is not int or not (0<=a['model_pool_index']<128 if a.get('placement_kind')=='scripted' else 0<a['model_pool_index']<512) or a['native_entity_id']!=f'scene://{scene}/worldmap/placements/{a["target_cell"]:04x}' or b['asset_id']!=f'asset://{scene}/worldmap/models/{a["model_pool_index"]:04d}' or b['entity_sha256']!=digest(a) or b['source_instance_ids']!=[d['selected_id']]):raise ProjectError('Authored World view has invalid stable native ownership')
  if a.get('placement_kind')=='scripted' and (a['shared_script'] is not True or not isinstance(a['script_id'],str) or not re.fullmatch(f'script://{scene}/worldmap/man-p0/[0-9]{{4}}',a['script_id'])):raise ProjectError('Scripted World view has invalid shared script ownership')
 ids=b['source_instance_ids']
 if not isinstance(ids,list) or not 1<=len(ids)<=512 or (not authored and any(not isinstance(id,str) or not re.fullmatch(f'scene://{scene}/worldmap/(ground|placements/[0-3][0-9a-f]{{3}}'+(r'|authored-placements/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}' if d['layer']=='current' else '')+')',id) for id in ids)) or ids!=sorted(set(ids)) or b['entity_id'] not in ids:raise ProjectError('World view asset instances are incomplete or conflicting')
 _metadata(value)
 if len(_budget(value))>128*1024 or len(_budget(s))>16*1024:raise ProjectError('World view source metadata exceeds its bounded saved format')

def binding(project,scene,shown,key):
 d=display(shown)
 if project.mode!='edit' or not project.disc_path or scene not in SCENES or key!=state_key(project):raise ProjectError('World view requires the current Edit project and source disc')
 from .worldmap_scripted_placement_binding import COMPONENT as SCRIPTED_COMPONENT,owner as scripted_owner
 scripted=d['layer']=='current' and SCRIPTED_COMPONENT in project.overrides.get(scripted_owner(scene),{})
 authored='/authored-placements/' in d['selected_id']
 if scripted:
  from .worldmap_scripted_placement_scene import inspect
  geometry=inspect(project,scene,key)
 else:
  if d['layer']=='current':
   from .worldmap_placements import context
   context(project,scene)
  geometry=load_worldmap_geometry(project.disc_path,scene)
  if authored:
   from .worldmap_current_placements import compose
   compose(project,geometry)
 graph=geometry['scene_graph'];e=next((r for r in graph['entities'] if r['entity_id']==d['selected_id']),None)
 if e is None:raise ProjectError('Saved World view target was removed or is not a qualified source instance')
 a=next((r for r in graph['assets'] if r['asset_id']==e['asset_id']),None)
 if a is None:raise ProjectError('Saved world view asset is unavailable')
 result=dict(source_record=deepcopy(geometry['source_record']),binding=dict(entity_id=e['entity_id'],asset_id=a['asset_id'],entity_sha256=digest(e),asset_source_sha256=digest(a['source_record']),source_instance_ids=sorted(r['entity_id'] for r in graph['entities'] if r['asset_id']==a['asset_id'])))
 if authored:
  stable=authored_owner(e)
  result['binding'].update(authored_owner=stable,entity_sha256=digest(stable),source_instance_ids=[e['entity_id']])
 if project.mode!='edit' or key!=state_key(project):raise ProjectError('World view sources changed during qualification')
 return result

def saved(project,id,key):
 if not isinstance(id,str) or id not in project.scene_views:raise ProjectError('Saved world view is unavailable')
 value=deepcopy(project.scene_views[id]);validate(project,id,value)
 if key!=review_key(project,value):raise ProjectError('Saved world view changed; reopen it')
 return value

def review(project,id,key,source_key):
 value=saved(project,id,key);scene=value['source_record']['scene'];fresh=binding(project,scene,value['display'],source_key)
 if any(value[k]!=fresh[k] for k in fresh):raise ProjectError('Saved world view source or instance ownership changed; recall refused')
 return dict(schema_version='legaia.worldmap-view-review.v1',read_only=True,source_key=source_key,view=value,review_key=review_key(project,value))

def command(project,body):
 if project.mode!='edit' or body.get('type') not in COMMANDS:raise ProjectError('World view commands require Edit mode')
 kind=body['type']
 if kind=='create_worldmap_view':
  if set(body)!={'type','scene','source_key','name','display'}:raise ProjectError('Save world view requires exact scene/source, name and display')
  if len(project.scene_views)>=128:raise ProjectError('Project is limited to 128 saved scene and world views')
  id='view://'+str(uuid.uuid4());before=None;after=dict(id=id,kind='worldmap',name=metadata_name(body['name'],'World view name'),scene_id=f'scene://{body["scene"]}/worldmap',display=display(body['display']),**binding(project,body['scene'],body['display'],body['source_key']))
 else:
  fields={'type','view_id','review_key'}|({'name'} if kind=='rename_worldmap_view' else {'source_key','display'} if kind=='update_worldmap_view' else set())
  if set(body)!=fields:raise ProjectError('World view command has unsupported fields')
  id=body['view_id'];before=saved(project,id,body['review_key']);after=deepcopy(before)
  if kind=='rename_worldmap_view':after['name']=metadata_name(body['name'],'World view name')
  elif kind=='update_worldmap_view':
   fresh=binding(project,before['source_record']['scene'],before['display'],body['source_key'])
   if any(before[k]!=fresh[k] for k in fresh):raise ProjectError('World view source changed; replacement refused')
   after.update(display=display(body['display']),**binding(project,before['source_record']['scene'],body['display'],body['source_key']))
  else:after=None
 if after is not None:
  validate(project,id,after)
  if any(k!=id and v['scene_id']==after['scene_id'] and v['name'].casefold()==after['name'].casefold() for k,v in project.scene_views.items()):raise ProjectError('A saved view with this name exists in the kingdom')
 if before==after:return
 if after is None:project.scene_views.pop(id)
 else:project.scene_views[id]=deepcopy(after)
 project.undo_stack.append(dict(target='scene_views',view_id=id,scene_id=(after or before)['scene_id'],before=before,after=deepcopy(after)));project.redo_stack.clear()
