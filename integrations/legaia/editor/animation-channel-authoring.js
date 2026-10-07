import {nativeChannelSeries} from './animation-channel-graph.js';
const integer=(v,a,b)=>Number.isSafeInteger(v)&&v>=a&&v<=b;
export function animationChannelAuthoringTarget(preview,entityId,frame,objectIndex){
  const a=preview?.animation;
  if(!/^scene:\/\/[A-Za-z0-9_-]+\/actors\/man-p1\/\d{4}$/.test(entityId)||a?.actor_semantic_id!==entityId||!integer(frame,0,(preview?.frames?.length??0)-1))throw new Error('Select the current imported actor and an existing inspected frame.');
  nativeChannelSeries(preview.frames,objectIndex,'translation');nativeChannelSeries(preview.frames,objectIndex,'rotation_psx');
  const initial={frame,object:objectIndex};
  if(['imported','authored'].includes(a.representation)&&['scene-header','authored-channels'].includes(a.clip_id)&&a.semantic_id?.startsWith(`animation://${entityId.split('/')[2]}/scene-anm/`)&&a.frame_count===preview.frames.length&&a.bone_count===preview.frames[0].object_transforms.length){
    return {kind:'imported',initial:{...initial,expected:{animation_id:a.semantic_id,asset_id:a.asset_semantic_id,frame_count:a.frame_count,object_count:a.bone_count}}};
  }
  const row=a.saved_record;
  if(a.representation==='allocated_record'&&/^[0-9a-f-]{36}$/.test(row?.record_id)&&/^[0-9a-f]{64}$/.test(row?.record_sha256)&&a.clip_id==='allocated-record'&&row?.entity_id===entityId&&row.animation_id===a.semantic_id&&row.record_id===a.source_record?.record_id&&row.record_sha256===a.source_record?.record_sha256&&row.donor_asset_id===a.asset_semantic_id&&row.frame_count===preview.frames.length&&row.object_count===preview.frames[0].object_transforms.length){return {kind:'retained',initial,row:structuredClone(row)};}
  throw new Error('This reference, assignment or proposed pose has no direct saved-channel authoring handoff.');
}
export function validateImportedChannelHandoff(initial,binding){
  if(!initial?.expected)return;
  const e=initial.expected;
  if(e.animation_id!==binding.semantic_id||e.asset_id!==binding.asset_semantic_id||e.frame_count!==binding.frame_count||e.object_count!==binding.bone_count||!integer(initial.frame,0,binding.frame_count-1)||!integer(initial.object,0,binding.bone_count-1))throw new Error('Inspected clip changed. Reopen the preview before authoring its channel.');
}
export function validateRetainedChannelHandoff(target,library,{sceneId,sourceKey}){
  if(target?.kind!=='retained'||library?.schema_version!=='legaia.animation-record-library.v1'||library.scene_id!==sceneId||library.project_source_key!==sourceKey||!Array.isArray(library.records)||library.records.length>4096)throw new Error('Saved clip library differs from the current inspected source.');
  const row=library.records.find(r=>r?.record_id===target.row.record_id);
  if(!row||Object.keys(row).sort().join('|')!==Object.keys(target.row).sort().join('|')||Object.keys(row).some(k=>row[k]!==target.row[k]))throw new Error('Saved clip changed. Reopen its preview.');
  return structuredClone(row);
}
