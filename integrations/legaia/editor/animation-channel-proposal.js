// Bind a read-only posed stream to exactly the reviewed imported contribution.
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b)),fail=()=>{throw Error('Proposed poses differ from the reviewed native channel samples.');};
export function decodeChannelPoseProposal(data,{entityId,binding,value,sourceKey}){
 const a=data?.animation,p=a?.proposal;
 if(data?.schema_version!=='legaia.model-preview.v1'||data.semantic_id!==binding.asset_semantic_id||a?.representation!=='channel_preview'||a.entity_id!==entityId||a.clip_id!=='channel-preview'||a.semantic_id!==binding.semantic_id||a.frame_count!==binding.frame_count||a.bone_count!==binding.bone_count||a.authored?.source_record_sha256!==binding.source_record.record_sha256||!p||Object.keys(p).sort().join(',')!=='gameplay_verified,project_changed,project_source_key,value'||p.project_changed!==false||p.gameplay_verified!==false||p.project_source_key!==sourceKey||!same(p.value,value)||!Array.isArray(data.frames)||data.frames.length!==binding.frame_count)fail();
 for(const row of value.edits){const frame=data.frames[row.frame_index],object=frame?.object_transforms?.[row.object_index];if(frame?.frame_index!==row.frame_index||frame.coordinate_system!=='retail_psx_actor_local_y_down'||object?.object_index!==row.object_index)fail();for(const kind of ['translation','rotation_psx'])for(const [axis,v] of Object.entries(row[kind]??{}))if(object[kind]?.['xyz'.indexOf(axis)]!==v)fail();}
 return data;
}
