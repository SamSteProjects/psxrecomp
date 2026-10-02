import {decodeActorAnimationOptions} from './actor-animation.js';

export const ANIMATION_PRESET_SCOPE='authored-actor-preset-v2';
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const exact=(value,keys)=>object(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const canonical=value=>Array.isArray(value)?value.map(canonical):object(value)?Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])])):value;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const component=binding=>binding?{donor_entity_id:binding.actor_semantic_id,animation_asset_id:binding.semantic_id,source_record_sha256:binding.source_record.record_sha256}:null;
const assignment=value=>value&&Object.keys(value).length?value:null;
export const presetScopeLabel=scope=>({'authored-position-v1':'Position','authored-appearance-v1':'Appearance','authored-actor-preset-v1':'Position and appearance',[ANIMATION_PRESET_SCOPE]:'Initial animation preset'}[scope]??scope);
export function validatePresetMetadata(template){
  const source=template?.source,components=template?.components,scene=source?.scene_id,actorPrefix=scene+'/actors/man-p1/',clipPrefix='animation://'+scene?.slice(8)+'/scene-anm/';
  const actorId=id=>typeof id==='string'&&id.startsWith(actorPrefix)&&/^[0-9]{4}$/.test(id.slice(actorPrefix.length));
  if(!exact(template,['id','name','scope','source','components'])||!/^template:\/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(template.id)||typeof template.name!=='string'||template.name!==template.name.trim()||!template.name.length||template.name.length>80||!exact(source,['disc_identity','scene_id','entity_id'])||!/^scene:\/\/[a-z0-9_]+$/.test(scene)||!actorId(source.entity_id)||!/^sha256:[0-9a-f]{64}$/.test(source.disc_identity)||!object(components))throw new Error('Invalid portable preset metadata.');
  const scopes={'authored-position-v1':['Transform'],'authored-appearance-v1':['ActorAppearance'],'authored-actor-preset-v1':['Transform','ActorAppearance']};
  if(template.scope===ANIMATION_PRESET_SCOPE){if(!Object.hasOwn(components,'ActorAnimation')||Object.keys(components).some(key=>!['Transform','ActorAppearance','ActorAnimation'].includes(key)))throw new Error('Animation preset scope requires its captured clip.');}
  else if(!scopes[template.scope]||!exact(components,scopes[template.scope]))throw new Error('Portable preset components differ from their scope.');
  if(Object.hasOwn(components,'Transform')&&(!exact(components.Transform,['position'])||!object(components.Transform.position)||!Object.keys(components.Transform.position).length||Object.entries(components.Transform.position).some(([axis,value])=>!['x','y','z'].includes(axis)||!Number.isFinite(value)||Math.abs(value)>32767)))throw new Error('Invalid preset position axes.');
  if(Object.hasOwn(components,'ActorAppearance')&&(!exact(components.ActorAppearance,['donor_entity_id'])||!actorId(components.ActorAppearance.donor_entity_id)))throw new Error('Invalid preset appearance donor.');
  const animation=components.ActorAnimation;
  if(Object.hasOwn(components,'ActorAnimation')&&(!exact(animation,['donor_entity_id','animation_asset_id','source_record_sha256'])||!actorId(animation.donor_entity_id)||typeof animation.animation_asset_id!=='string'||!animation.animation_asset_id.startsWith(clipPrefix)||!/^[0-9]{4}$/.test(animation.animation_asset_id.slice(clipPrefix.length))||Number(animation.animation_asset_id.slice(clipPrefix.length))>254||!hash(animation.source_record_sha256)))throw new Error('Invalid captured initial animation source.');
  return structuredClone(template);
}
export function presetReviewContext(state,ids,templateId=null){
  return JSON.stringify([state.project?.path,state.project?.mode,state.scene?.id,state.selection?.entity_id,state.scene_preview_source_key,state.asset_reference_source_key,state.scene?.entities,state.actor_templates,templateId,[...ids].sort()]);
}
function validateBinding(binding,entityId,sceneId){
  // Reuse the exact raw/compressed source, association and channel contract.
  // A synthetic unavailable options envelope validates one metadata record;
  // it does not claim that its witness is the target's inherited appearance.
  decodeActorAnimationOptions({schema_version:'legaia.actor-animation-options.v1',entity_id:entityId,scene_id:sceneId,source_key:'0'.repeat(64),supported:false,reason:'Preset metadata validation',imported:null,base:binding,effective:binding,authored:null,choices:[],limitations:[]},entityId,'0'.repeat(64),sceneId);
}
export function decodePresetAnimation(value,entityId,sceneId){
  if(value===null)return null;
  if(!exact(value,['imported','base','effective','proposed','authored','after','witness'])||!value.base||!value.proposed)throw new Error('Invalid preset animation layers.');
  for(const key of ['imported','base','effective','proposed'])validateBinding(value[key],entityId,sceneId);
  if(value.imported&&value.imported.actor_semantic_id!==entityId||value.authored!==null&&!same(value.authored,component(value.effective))||value.after!==null&&!same(value.after,component(value.proposed))||value.after===null&&!same(value.proposed,value.base)||value.proposed.asset_semantic_id!==value.base.asset_semantic_id||!same(value.proposed.association.active_object_indices,value.base.association.active_object_indices)||!same(value.proposed.association.excluded_object_indices,value.base.association.excluded_object_indices))throw new Error('Preset animation assignment differs from its observed layers.');
  const witness=value.witness,reference=witness?.model_reference;
  if(!exact(witness,['entity_id','source_record','model_reference'])||witness.entity_id!==value.proposed.actor_semantic_id||!same(witness.source_record,value.proposed.association.actor_source_record)||!object(reference)||Object.keys(reference).length>64||reference.asset_semantic_id!==value.proposed.asset_semantic_id||reference.model_index!==Number(value.proposed.asset_semantic_id.slice(-4)))throw new Error('Preset animation witness differs from the immutable imported model.');
  return structuredClone(value);
}
export function validatePresetComponentChange(row,template,actor,sceneId){
  const before=row.before??{},after=row.after??{},animation=row.animation===undefined?null:decodePresetAnimation(row.animation,row.entity_id,sceneId);
  if(template.scope===ANIMATION_PRESET_SCOPE&&!animation)throw new Error('Animation preset is missing its reviewed clip.');
  if(!object(before)||!object(after))throw new Error('Invalid preset component proposal.');
  if(animation){
    if(!same(animation.authored,before.ActorAnimation??null)||!same(animation.after,after.ActorAnimation??null)||actor&&!same(animation.authored,assignment(actor.components?.ActorAnimation?.authored)))throw new Error('Preset animation changed its current authored assignment.');
    const current=actor?.components?.ActorAnimation?.effective;
    if(current&&(animation.effective?.semantic_id!==current.animation_asset_id||animation.effective?.actor_semantic_id!==current.donor_entity_id))throw new Error('Preset effective animation differs from the current actor.');
  }
  const expected=structuredClone(before),captured=template.components;
  if(captured.Transform)expected.Transform={...(expected.Transform??{}),position:{...(expected.Transform?.position??{}),...captured.Transform.position}};
  if(captured.ActorAppearance)expected.ActorAppearance=structuredClone(captured.ActorAppearance);
  if(captured.ActorAnimation){
    if(!exact(captured.ActorAnimation,['donor_entity_id','animation_asset_id','source_record_sha256'])||!hash(captured.ActorAnimation.source_record_sha256))throw new Error('Invalid captured animation preset.');
    if(captured.ActorAnimation.animation_asset_id===animation.base.semantic_id){
      if(captured.ActorAnimation.source_record_sha256!==animation.base.source_record.record_sha256)throw new Error('Captured inherited clip source differs from the proposal.');
      delete expected.ActorAnimation;
    }else expected.ActorAnimation=structuredClone(captured.ActorAnimation);
  }
  if(!same(expected,after)||!same(animation?.after??null,after.ActorAnimation??null))throw new Error('Preset changed omitted components or clip witness.');
  return animation;
}
function sharedGeometry(preview){const result=structuredClone(preview);if(result?.pose){delete result.pose.actor_semantic_id;if(result.pose.association)delete result.pose.association.actor_source_record;}return result;}
export function decodePresetAnimationScene(scene,current,rows){
  const selected=new Map(rows.map(row=>[row.entity_id,row])),owners=new Map(scene.entities.map(row=>[row.entity_id,row])),assets=new Map(scene.assets.map(row=>[row.geometry_key,row])),oldAssets=new Map(current.assets.map(row=>[row.geometry_key,row]));
  if(selected.size!==rows.length||owners.size!==scene.entities.length||owners.size!==current.entities.length||assets.size!==scene.assets.length||[...selected.keys()].some(id=>!owners.has(id)))throw new Error('Ambiguous preset animation scene owners or geometry.');
  const bindings=new Set(['geometry_key','asset_id','source_actor_id','source_record','model_reference','appearance_authored','animation_assignment_authored','pose_kind','reason','renderable']);
  for(const original of current.entities){
    const target=owners.get(original.entity_id),row=selected.get(original.entity_id);
    if(!target)throw new Error('Preset animation scene owner is missing.');
    const strip=value=>Object.fromEntries(Object.entries(value).filter(([key])=>row?!bindings.has(key):key!=='geometry_key'));
    if(!same(strip(target),strip(original)))throw new Error('Preset changed placement, channels or unrelated owners.');
    const geometry=assets.get(target.geometry_key);
    if(target.renderable&&(!geometry||geometry.asset_id!==target.asset_id))throw new Error('Preset animation geometry is missing.');
    if(!row){if(target.renderable&&!same(sharedGeometry(geometry.preview),sharedGeometry(oldAssets.get(original.geometry_key)?.preview)))throw new Error('Preset changed unrelated posed geometry.');continue;}
    const animation=decodePresetAnimation(row.animation??null,row.entity_id,current.scene_id);
    if(target.appearance_authored!==Boolean(row.after?.ActorAppearance)||target.animation_assignment_authored!==Boolean(animation?.after))throw new Error('Preset scene authored binding flags differ from review.');
    if(!animation){
      if(row.appearance){if(target.source_actor_id!==row.proposed_donor||target.asset_id!==row.appearance.asset_id)throw new Error('Preset appearance differs from its donor.');}
      else if([...bindings].filter(key=>key!=='geometry_key').some(key=>!same(target[key],original[key])))throw new Error('Preset changed an uncaptured binding.');
      continue;
    }
    const proposed=animation.proposed,witness=animation.witness;
    if(target.source_actor_id!==witness.entity_id||!same(target.source_record,witness.source_record)||!same(target.model_reference,witness.model_reference)||target.asset_id!==proposed.asset_semantic_id)throw new Error('Preset scene clip is not bound to its qualified imported witness.');
    if(target.renderable){
      const pose=geometry.preview?.pose,source=structuredClone(proposed.source_record);delete source.record_sha256;
      if(!pose||pose.semantic_id!==proposed.semantic_id||pose.asset_semantic_id!==proposed.asset_semantic_id||pose.reference_commit!==proposed.reference_commit||pose.frame_index!==0||pose.frame_count!==proposed.frame_count||pose.bone_count!==proposed.bone_count||pose.header_a!==proposed.header_a||pose.header_flags!==proposed.header_flags||!same(pose.source_record,source)||pose.association?.kind!==proposed.association.kind||pose.association?.animation_id!==proposed.association.animation_id||!same(pose.association?.active_object_indices,proposed.association.active_object_indices)||!same(pose.association?.excluded_object_indices,proposed.association.excluded_object_indices)||animation.after&&target.pose_kind!=='authored_initial_animation_frame0')throw new Error('Preset scene pose differs from the reviewed initial clip.');
      // If a pose was already available, retained imported channel edits must
      // remain byte-identical apart from the deduplicated actor witness label.
      const retained=current.entities.find(item=>item.asset_id===target.asset_id&&item.renderable&&oldAssets.get(item.geometry_key)?.preview?.pose?.semantic_id===proposed.semantic_id);
      if(retained&&!same(sharedGeometry(geometry.preview),sharedGeometry(oldAssets.get(retained.geometry_key).preview)))throw new Error('Preset retargeted or changed existing shared clip channels.');
    }
  }
  return structuredClone(scene);
}
export function appendPresetAnimationLayers(host,animation){
  if(!animation)return;
  for(const [label,key] of [['Imported initial clip','imported'],['Inherited final appearance clip','base'],['Current effective clip','effective'],['Proposed initial clip · not applied','proposed']]){
    const binding=animation[key],p=document.createElement('p');p.textContent=binding?`${label}: ${binding.semantic_id} · witness ${binding.actor_semantic_id} · SHA-256 ${binding.source_record.record_sha256}`:`${label}: unavailable`;host.append(p);
  }
  const note=document.createElement('p');note.className='field-note';note.textContent='Initial MAN animation header only. Scripts may replace it; gameplay playback remains unverified. Animation channels retain their imported shared-clip ownership.';host.append(note);
}
