import {validValues} from './worldmap-placement-state.js';
import {placementDigest,decodeWorldPlacementSeeds,equalWorldPlacementBytes} from './worldmap-placement-replay.js';
import {allocateScriptedWorldPlacements,mergeScriptedWorldCurrent} from './worldmap-scripted-placement-replay.js';
import {nativeWorldPlacementMatches} from './worldmap-current-placements.js';
const fail=()=>{throw Error('Scripted transform Review differs from complete native replay or selected ownership.');};
const bytes=v=>Uint8Array.from(atob(v),c=>c.charCodeAt(0));
export async function qualifyScriptedTransformReview(value,qualified,placementId,values){
 const {source,man,map}=qualified;
 if(!validValues(values)||!source.binding||value?.schema_version!=='legaia.worldmap-scripted-transform-review.v1'||typeof value.review_key!=='string'||!/^[0-9a-f]{64}$/.test(value.review_key))fail();
 const before=source.authored_scripted_placements.find(a=>a.placement_id===placementId);if(!before)fail();
 const binding=structuredClone(source.binding),fallback=bytes(source.fallback_base64);let canonical=bytes(source.retained_base_map_base64),found=0;const audits=[];
 for(const operation of binding.operations){
  for(const request of operation.requests)if(request.placement_id===placementId){request.values=structuredClone(values);found++;}
  const result=await allocateScriptedWorldPlacements(canonical,fallback,man.current,man.floor,source.scene,operation.requests,operation.relocation_offset,binding.schema_version==='legaia.worldmap-scripted-placement-ledger.v2');
  canonical=result.bytes;operation.proposed_map_sha256=await placementDigest(canonical);audits.push(result.audit);
 }
 if(found!==1)fail();
 const candidate=await mergeScriptedWorldCurrent(bytes(source.retained_base_map_base64),canonical,map.normal,man.floor,source.scene,audits);
 const expectedBytes=map.current.slice(),at=before.record_index*32,view=new DataView(expectedBytes.buffer),old=new DataView(map.current.buffer,map.current.byteOffset,map.current.byteLength),yaw=old.getUint16(at+10,true);
 for(const [i,axis] of ['x','y','z'].entries())view.setInt16(at+2*i,values.offset[axis],true);view.setUint16(at+10,(yaw&0xf000)|values.yaw_units,true);
 if(!equalWorldPlacementBytes(candidate,expectedBytes)||typeof value.proposed_map_base64!=='string'||value.proposed_map_base64.length!==98304||!equalWorldPlacementBytes(candidate,bytes(value.proposed_map_base64)))fail();
 const decoded=await decodeWorldPlacementSeeds(candidate,man.floor,source.scene),seeds=new Map(decoded.placements.map(s=>[s.entity_id,s]));
 const allocations=audits.flatMap(a=>a.allocations).map(a=>({...a,native_seed:structuredClone(seeds.get(a.native_seed.entity_id))})),after=allocations.find(a=>a.placement_id===placementId);
 if(after.script_id!==before.script_id||after.target_cell!==before.target_cell)fail();
 const expected={schema_version:'legaia.worldmap-scripted-transform-review.v1',project_path:source.project_path,scene:source.scene,source_key:source.source_key,source_record:source.source_record,placement_id:placementId,values,current_values:{offset:{x:old.getInt16(at,true),y:old.getInt16(at+2,true),z:old.getInt16(at+4,true)},yaw_units:yaw&4095},current_map_sha256:source.current_map_sha256,current_man_sha256:source.current_man_sha256,proposed_map_sha256:await placementDigest(candidate),proposed_map_base64:value.proposed_map_base64,before_binding:source.binding,binding,audit:{before,after,authored_scripted_placements:allocations,scope:'authored-scripted-transform-only',changed_bytes:[...candidate].flatMap((n,i)=>n===map.current[i]?[]:[{byte_offset:i,before_byte:map.current[i],after_byte:n}]),gameplay_verified:false},read_only:true,project_changed:false,gameplay_verified:false,build_ready:false,review_key:value.review_key};
 if(!nativeWorldPlacementMatches(value,expected))fail();return structuredClone(value);
}
