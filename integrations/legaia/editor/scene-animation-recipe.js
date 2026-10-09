// Source-bound editor sampling metadata only; no vertices, native timing or autoplay.
export const MAX_SCENE_ANIMATION_RECIPE_BYTES=1024*1024;
const exact=(v,keys)=>v!==null&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const integer=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const fail=message=>{throw Error(message);};
const modes=['loop','hold','ping_pong','freeze'];
function source(report){
 if(report?.schema_version!=='legaia.scene-animation.v1'||!hash(report.project_source_key)||!hash(report.scene_source_key)||!['retail','authored'].includes(report.representation)||report.project_changed!==false||report.gameplay_verified!==false||!Array.isArray(report.tracks)||!report.tracks.length||report.tracks.length>128||!Array.isArray(report.instances)||report.instances.length>512||!Array.isArray(report.unavailable_instances)||report.unavailable_instances.length>512)fail('Recipe requires a qualified active scene animation report.');
 return {scene_id:report.scene_id,project_source_key:report.project_source_key,scene_source_key:report.scene_source_key,representation:report.representation};
}
function binding(report,track){
 return {geometry_key:track.geometry_key,asset_id:track.asset_id,clip_id:track.clip_id,pose_kind:track.pose_kind,frame_count:track.frame_count,vertex_count:track.vertex_count,
  instances:report.instances.filter(row=>row.geometry_key===track.geometry_key).map(row=>({entity_id:row.entity_id,source_actor_id:row.source_actor_id})).sort((a,b)=>a.entity_id.localeCompare(b.entity_id))};
}
export function decodeSceneAnimationRecipe(raw,report){
 const expected=source(report);
 if(!exact(raw,['schema_version','source','tick','preview_fps','tracks','unavailable_entity_ids'])||raw.schema_version!=='legaia.scene-animation-preview-recipe.v1'||!exact(raw.source,Object.keys(expected))||!same(raw.source,expected)||!integer(raw.tick,0,Number.MAX_SAFE_INTEGER)||!integer(raw.preview_fps,1,30)||!Array.isArray(raw.tracks)||raw.tracks.length!==report.tracks.length||!Array.isArray(raw.unavailable_entity_ids)||!same(raw.unavailable_entity_ids,report.unavailable_instances.map(row=>row.entity_id).sort()))fail('Preview recipe source, coverage or sampling controls differ from this scene.');
 const tracks=new Map(report.tracks.map(row=>[row.geometry_key,row])),seen=new Set();
 for(const row of raw.tracks){
  if(!exact(row,['geometry_key','asset_id','clip_id','pose_kind','frame_count','vertex_count','instances','mode','offset'])||seen.has(row.geometry_key)||!tracks.has(row.geometry_key))fail('Preview recipe has a missing, duplicate or foreign track.');
  const track=tracks.get(row.geometry_key),bound=binding(report,track);
  if(Object.keys(bound).some(key=>!same(row[key],bound[key]))||!modes.includes(row.mode)||!integer(row.offset,0,track.frame_count-1))fail('Preview recipe track binding or source-frame setting changed.');seen.add(row.geometry_key);
 }
 if(new TextEncoder().encode(JSON.stringify(raw)).byteLength>MAX_SCENE_ANIMATION_RECIPE_BYTES)fail('Preview recipe exceeds one MiB.');
 return structuredClone(raw);
}
export function createSceneAnimationRecipe(report,tick,previewFps,settings=new Map()){
 if(!(settings instanceof Map)||settings.size>128||[...settings.keys()].some(key=>!report.tracks.some(row=>row.geometry_key===key)))fail('Recipe settings belong to another scene track.');
 const raw={schema_version:'legaia.scene-animation-preview-recipe.v1',source:source(report),tick,preview_fps:previewFps,
  tracks:report.tracks.map(track=>{const setting=settings.get(track.geometry_key)??{mode:'loop',offset:0};if(!exact(setting,['mode','offset']))fail('Recipe setting has unexpected fields.');return {...binding(report,track),...setting};}).sort((a,b)=>a.geometry_key.localeCompare(b.geometry_key)),
  unavailable_entity_ids:report.unavailable_instances.map(row=>row.entity_id).sort()};
 return decodeSceneAnimationRecipe(raw,report);
}
