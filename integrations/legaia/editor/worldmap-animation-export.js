import {placementDigest} from './worldmap-placement-replay.js';
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const fail=()=>{throw Error('World animation export differs from the inspected clip, model or selected rate.');};
export async function qualifyWorldAnimationExport(value,receipt,layer,fps){
  if(!value||Object.keys(value).sort().join(',')!=='audit,filename,glb_base64,schema_version'||value.schema_version!=='legaia.world-animation-export-response.v1'||!['retail','current'].includes(layer)||!Number.isFinite(fps)||fps<1||fps>120)fail();
  const p=receipt.preview,source=layer==='current'?receipt.source.before:receipt,a=value.audit,m=a?.model_export;
  if(value.filename!==`${receipt.scene}-world-animation-${String(p.record_index).padStart(4,'0')}-${layer}.glb`||!a||a.schema_version!=='legaia.world-animation-export.v1'||a.project_path!==receipt.project_path||a.scene!==receipt.scene||a.source_key!==receipt.source_key||a.entity_id!==receipt.entity_id||a.animation_id!==`animation://${receipt.scene}/worldmap/anm/${String(p.record_index).padStart(4,'0')}`||a.model_asset_id!==source.model_asset_id||a.layer!==layer||a.frame_count!==p.frame_count||a.channel_count!==p.channel_count||a.bank_sha256!==p.bank_sha256||a.record_sha256!==p.record_sha256||a.fps!==fps||a.timing_evidence!=='caller_selected_rate_not_verified_retail_timing'||a.placement_included!==false||a.coordinate_transform!=='[x,-y,z]'||a.read_only!==true||a.project_changed!==false||a.gameplay_verified!==false||!m||m.full_clip!==true||m.frame_count!==p.frame_count||m.object_count!==p.channel_count||m.export_fps!==fps||m.sha256!==a.glb_sha256||m.byte_length!==a.byte_length||m.asset_semantic_id!==source.model_asset_id||JSON.stringify(canonical(m.source_record))!==JSON.stringify(canonical(source.model_source)))fail();
  if(typeof value.glb_base64!=='string'||value.glb_base64.length>90*1024*1024||!Number.isSafeInteger(a.byte_length)||a.byte_length<20||a.byte_length>64*1024*1024)fail();
  const bytes=Uint8Array.from(atob(value.glb_base64),c=>c.charCodeAt(0));if(bytes.length!==a.byte_length)fail();const view=new DataView(bytes.buffer);
  if(view.getUint32(0,true)!==0x46546c67||view.getUint32(4,true)!==2||view.getUint32(8,true)!==bytes.length||await placementDigest(bytes)!==a.glb_sha256)fail();
  return {bytes,filename:value.filename,audit:structuredClone(a)};
}
export function downloadWorldAnimationExport(result){
  for(const [content,name,type] of [[result.bytes,result.filename,'model/gltf-binary'],[JSON.stringify(result.audit,null,2)+'\n',result.filename.replace(/\.glb$/,'.audit.json'),'application/json']]){
    const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
  }
}
