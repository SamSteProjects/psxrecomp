import {validValues} from './worldmap-placement-state.js';
import {placementDigest,decodeWorldPlacementSeeds,equalWorldPlacementBytes} from './worldmap-placement-replay.js';
import {allocateScriptedWorldPlacements,mergeScriptedWorldCurrent} from './worldmap-scripted-placement-replay.js';
import {nativeWorldPlacementMatches} from './worldmap-current-placements.js';
const fail=()=>{throw Error('Scripted group Review differs from native replay or saved UUID ownership.');};
const bytes=v=>Uint8Array.from(atob(v),c=>c.charCodeAt(0));
export async function qualifyScriptedGroupReview(value,qualified,requested){
 const {source,man,map}=qualified;
 if(!Array.isArray(requested)||requested.length<2||requested.length>32||!source.binding||value?.schema_version!=='legaia.worldmap-scripted-group-transform-review.v1'||typeof value.review_key!=='string'||!/^[0-9a-f]{64}$/.test(value.review_key))fail();
 const ids=new Set();
 for(const e of requested){if(!e||Object.keys(e).sort().join(',')!=='placement_id,values'||typeof e.placement_id!=='string'||ids.has(e.placement_id)||!validValues(e.values))fail();ids.add(e.placement_id);}
 const entries=structuredClone(requested).sort((a,b)=>a.placement_id<b.placement_id?-1:a.placement_id>b.placement_id?1:0),edits=new Map(entries.map(e=>[e.placement_id,e.values]));
 const selected=new Map(source.authored_scripted_placements.map(a=>[a.placement_id,a]));if([...ids].some(id=>!selected.has(id)))fail();
 const binding=structuredClone(source.binding),fallback=bytes(source.fallback_base64);let canonical=bytes(source.retained_base_map_base64);const found=[],audits=[];
 for(const operation of binding.operations){
  for(const request of operation.requests)if(edits.has(request.placement_id)){request.values=structuredClone(edits.get(request.placement_id));found.push(request.placement_id);}
  const result=await allocateScriptedWorldPlacements(canonical,fallback,man.current,man.floor,source.scene,operation.requests,operation.relocation_offset,binding.schema_version==='legaia.worldmap-scripted-placement-ledger.v2');
  canonical=result.bytes;operation.proposed_map_sha256=await placementDigest(canonical);audits.push(result.audit);
 }
 if(found.length!==ids.size||new Set(found).size!==ids.size)fail();
 const candidate=await mergeScriptedWorldCurrent(bytes(source.retained_base_map_base64),canonical,map.normal,man.floor,source.scene,audits);
 const expectedBytes=map.current.slice(),view=new DataView(expectedBytes.buffer),old=new DataView(map.current.buffer,map.current.byteOffset,map.current.byteLength),currentValues=[],nativeIds=new Set();
 for(const e of entries){
  const a=selected.get(e.placement_id),at=a.record_index*32,yaw=old.getUint16(at+10,true);if(nativeIds.has(a.native_seed.entity_id))fail();nativeIds.add(a.native_seed.entity_id);
  currentValues.push({placement_id:e.placement_id,values:{offset:{x:old.getInt16(at,true),y:old.getInt16(at+2,true),z:old.getInt16(at+4,true)},yaw_units:yaw&4095}});
  for(const [i,axis] of ['x','y','z'].entries())view.setInt16(at+2*i,e.values.offset[axis],true);view.setUint16(at+10,(yaw&0xf000)|e.values.yaw_units,true);
 }
 if(!equalWorldPlacementBytes(candidate,expectedBytes)||typeof value.proposed_map_base64!=='string'||value.proposed_map_base64.length!==98304||!equalWorldPlacementBytes(candidate,bytes(value.proposed_map_base64)))fail();
 const decoded=await decodeWorldPlacementSeeds(candidate,man.floor,source.scene),original=await decodeWorldPlacementSeeds(map.current,man.floor,source.scene),seeds=new Map(decoded.placements.map(s=>[s.entity_id,s]));
 if(!nativeWorldPlacementMatches(decoded.coverage,original.coverage)||!nativeWorldPlacementMatches(decoded.unresolved,original.unresolved)||seeds.size!==original.placements.length||original.placements.some(s=>!seeds.has(s.entity_id)||!nativeIds.has(s.entity_id)&&!nativeWorldPlacementMatches(s,seeds.get(s.entity_id))))fail();
 const allocations=audits.flatMap(a=>a.allocations).map(a=>({...a,native_seed:structuredClone(seeds.get(a.native_seed.entity_id))}));
 for(const a of allocations){const prior=selected.get(a.placement_id);if(!prior||a.script_id!==prior.script_id||a.target_cell!==prior.target_cell)fail();}
 const expected={schema_version:'legaia.worldmap-scripted-group-transform-review.v1',project_path:source.project_path,scene:source.scene,source_key:source.source_key,source_record:source.source_record,entries,current_values:currentValues,current_map_sha256:source.current_map_sha256,current_man_sha256:source.current_man_sha256,proposed_map_sha256:await placementDigest(candidate),proposed_map_base64:value.proposed_map_base64,before_binding:source.binding,binding,audit:{before:entries.map(e=>selected.get(e.placement_id)),after:entries.map(e=>allocations.find(a=>a.placement_id===e.placement_id)),authored_scripted_placements:allocations,scope:'authored-scripted-group-transform-only',changed_bytes:[...candidate].flatMap((n,i)=>n===map.current[i]?[]:[{byte_offset:i,before_byte:map.current[i],after_byte:n}]),gameplay_verified:false},read_only:true,project_changed:false,gameplay_verified:false,build_ready:false,review_key:value.review_key};
 if(!nativeWorldPlacementMatches(value,expected))fail();return structuredClone(value);
}
