// Saved recipes are editable input, never authority to Apply.
const fail=message=>{throw new Error(message);};
const integer=(v,max)=>Number.isSafeInteger(v)&&v>=0&&v<=max;
const keys=(value,required,optional=[])=>value&&typeof value==='object'&&!Array.isArray(value)&&required.every(k=>Object.hasOwn(value,k))&&Object.keys(value).every(k=>required.includes(k)||optional.includes(k));
export function decodeMeshAnimationPose(value){
  if(!keys(value,['animation_index','time_seconds'])||!integer(value.animation_index,63)||typeof value.time_seconds!=='number'||!Number.isFinite(value.time_seconds)||value.time_seconds<0||value.time_seconds>3600)fail('Choose an explicit animation clip and finite pose time from 0 through 3600 seconds.');
  return {animation_index:value.animation_index,time_seconds:value.time_seconds};
}
export function meshAnimationPoseMatches(value,expected){
  try{return JSON.stringify(value?decodeMeshAnimationPose(value):null)===JSON.stringify(expected?decodeMeshAnimationPose(expected):null);}catch{return false;}
}
export function meshInventoryPose(value){const p=value?.static_scope?.sampled_animation;return p?decodeMeshAnimationPose({animation_index:p.animation_index,time_seconds:p.time_seconds}):null;}
export function decodeMeshSettings(value){
  const common=['kind','material_colors','scene_index','uv_set','source_scale','source_offset','source_rotation'];
  const single=['donor_face_id','new_group','replace_group','replace_object','preserve_primitives','primitive_index'];
  const batch=['mappings','replace_objects'];
  if(!keys(value,[...common,...(value?.kind==='single'?single:value?.kind==='batch'?batch:[])],value?.kind==='single'?['animation_pose']:[])||!['single','batch'].includes(value.kind))fail('Import settings have unknown or missing fields.');
  if(Object.hasOwn(value,'animation_pose'))decodeMeshAnimationPose(value.animation_pose);
  if(typeof value.material_colors!=='boolean'||!(value.scene_index===null||integer(value.scene_index,63))||!integer(value.uv_set,7)||typeof value.source_scale!=='number'||!Number.isFinite(value.source_scale)||value.source_scale<1e-6||value.source_scale>1e6)fail('Import settings contain invalid scene, UV or unit scale.');
  for(const [field,min,max] of [['source_offset',-32768,32767],['source_rotation',-360,360]])if(!Array.isArray(value[field])||value[field].length!==3||value[field].some(n=>typeof n!=='number'||!Number.isFinite(n)||n<min||n>max))fail('Import settings contain invalid native origin or rotation.');
  const donor=v=>typeof v==='string'&&v.length>0&&v.length<=512;
  if(value.kind==='single'){
    if(!donor(value.donor_face_id)||single.slice(1,5).some(k=>typeof value[k]!=='boolean')||!(value.primitive_index===null||integer(value.primitive_index,65535))||((value.replace_group||value.replace_object||value.preserve_primitives)&&!value.new_group)||(value.replace_group&&value.replace_object))fail('Import settings contain invalid single-section choices.');
  }else{
    if(typeof value.replace_objects!=='boolean'||!Array.isArray(value.mappings)||!value.mappings.length||value.mappings.length>16)fail('Import settings contain invalid section mappings.');
    for(const [i,row] of value.mappings.entries())if(!keys(row,['primitive_index','donor_face_id','replace_group'],['uv_set'])||!integer(row.primitive_index,65535)||(i&&row.primitive_index<=value.mappings[i-1].primitive_index)||!donor(row.donor_face_id)||typeof row.replace_group!=='boolean'||(value.replace_objects&&row.replace_group)||(Object.hasOwn(row,'uv_set')&&!integer(row.uv_set,7)))fail('Import settings contain invalid section mappings.');
  }
  return structuredClone(value);
}
export function qualifyMeshSettings(value,source,inventory){
  const recipe=decodeMeshSettings(value);
  if(!meshAnimationPoseMatches(meshInventoryPose(inventory),recipe.animation_pose??null))fail('Selected GLB pose differs from recovered settings.');
  if((recipe.scene_index!==null&&inventory.scene_source?.scene_index!==recipe.scene_index)||(inventory.source_scale??1)!==recipe.source_scale||JSON.stringify(inventory.source_offset??[0,0,0])!==JSON.stringify(recipe.source_offset)||JSON.stringify(inventory.source_rotation??[0,0,0])!==JSON.stringify(recipe.source_rotation))fail('Selected GLB inventory differs from recovered settings.');
  const available=new Set([0,...(inventory.uv_sets??[]).flat()]);
  if(!available.has(recipe.uv_set))fail('Recovered UV channel is unavailable in the selected GLB scene.');
  const eligible=new Set(source.topology.faces.filter(face=>source.objects[face.object_index]?.primitives[face.current_primitive_index]?.corner_count===3).map(face=>face.face_id));
  const mappings=recipe.kind==='batch'?recipe.mappings:[{primitive_index:recipe.primitive_index,donor_face_id:recipe.donor_face_id,uv_set:recipe.uv_set}];
  for(const row of mappings)if((row.primitive_index!==null&&!inventory.primitives.some(p=>p.primitive_index===row.primitive_index))||!available.has(row.uv_set??recipe.uv_set))fail('Recovered source section or UV channel is unavailable in the selected GLB.');
  return {recipe,missingDonors:[...new Set(mappings.filter(row=>!eligible.has(row.donor_face_id)).map(row=>row.donor_face_id))]};
}
