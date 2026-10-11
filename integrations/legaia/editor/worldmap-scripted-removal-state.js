import {placementDigest,decodeWorldPlacementSeeds,equalWorldPlacementBytes} from './worldmap-placement-replay.js';
import {allocateScriptedWorldPlacements,mergeScriptedWorldCurrent,worldMapTriggerTables} from './worldmap-scripted-placement-replay.js';
import {nativeWorldPlacementMatches} from './worldmap-current-placements.js';
const fail=()=>{throw Error('Scripted removal Review differs from native replay, donor scope or selected ownership.');};
const bytes=v=>Uint8Array.from(atob(v),c=>c.charCodeAt(0));
export function scriptedRemovalIds(binding,placementId){
 const prior=new Map(),children=new Map(),ordered=[];
 if(!Array.isArray(binding?.operations)||!binding.operations.length||binding.operations.length>32)fail();
 for(const operation of binding.operations){
  for(const request of operation.requests){const id=request.placement_id;ordered.push(id);const donor=prior.get(request.donor_cell);if(donor!==undefined){if(!children.has(donor))children.set(donor,[]);children.get(donor).push(id);}}
  for(const request of operation.requests)prior.set(request.target_cell,request.placement_id);
 }
 if(!ordered.includes(placementId))fail();
 const removed=new Set([placementId]),queue=[placementId];while(queue.length)for(const id of children.get(queue.pop())??[])if(!removed.has(id)){removed.add(id);queue.push(id);}
 return ordered.filter(id=>removed.has(id));
}
export async function qualifyScriptedRemovalReview(value,qualified,placementId,cascade){
 const {source,man,map}=qualified;
 if(typeof cascade!=='boolean'||!source.binding||value?.schema_version!=='legaia.worldmap-scripted-removal-review.v1'||typeof value.review_key!=='string'||!/^[0-9a-f]{64}$/.test(value.review_key))fail();
 const removed=scriptedRemovalIds(source.binding,placementId),removedSet=new Set(removed);if(removed.length>1&&!cascade)fail();
 let binding=structuredClone(source.binding);binding.operations=binding.operations.map(o=>({...o,requests:o.requests.filter(r=>!removedSet.has(r.placement_id))})).filter(o=>o.requests.length);
 const base=bytes(source.retained_base_map_base64),fallback=bytes(source.fallback_base64),oldAudits=[],audits=[];
 let oldCanonical=base,canonical=base;
 for(const operation of source.binding.operations){const result=await allocateScriptedWorldPlacements(oldCanonical,fallback,man.current,man.floor,source.scene,operation.requests,operation.relocation_offset,source.binding.schema_version==='legaia.worldmap-scripted-placement-ledger.v2');oldCanonical=result.bytes;oldAudits.push(result.audit);}
 for(const operation of binding.operations){const result=await allocateScriptedWorldPlacements(canonical,fallback,man.current,man.floor,source.scene,operation.requests,operation.relocation_offset,binding.schema_version==='legaia.worldmap-scripted-placement-ledger.v2');canonical=result.bytes;operation.proposed_map_sha256=await placementDigest(canonical);audits.push(result.audit);}
 if(!binding.operations.length)binding=null;
 const candidate=audits.length?await mergeScriptedWorldCurrent(base,canonical,map.normal,man.floor,source.scene,audits):map.normal.slice();
 const expectedBytes=map.current.slice(),view=new DataView(expectedBytes.buffer),deleted=source.authored_scripted_placements.filter(a=>removedSet.has(a.placement_id));
 for(const allocation of deleted){const at=allocation.record_index*32;expectedBytes.set(map.normal.slice(at,at+32),at);for(const cell of new Set([allocation.target_cell,allocation.anchor_cell]))expectedBytes.set(map.normal.slice(32768+2*cell,32770+2*cell),32768+2*cell);}
 const payloads=new Map();
 for(const audit of oldAudits){const b=audit.bind_allocation,at=65536+b.proposed_table_offset,end=at+4*b.proposed_row_count;expectedBytes.set(map.normal.slice(at,end),at);for(const a of b.allocations)payloads.set(a.bind_id,Uint8Array.from(a.after_hex.match(/../g),n=>parseInt(n,16)));}
 expectedBytes.set(map.normal.slice(65542,65546),65542);
 const rows=worldMapTriggerTables(base.slice(65536)).tables[1].rows.map(r=>r.slice());
 for(const operation of binding?.operations??[]){for(const request of operation.requests)rows.push(payloads.get(request.placement_id.replace('placement://','bind://')));const at=65536+operation.relocation_offset;rows.forEach((r,i)=>expectedBytes.set(r,at+4*i));view.setInt16(65542,operation.relocation_offset,true);view.setInt16(65544,rows.length,true);}
 if(!equalWorldPlacementBytes(candidate,expectedBytes)||typeof value.proposed_map_base64!=='string'||value.proposed_map_base64.length!==98304||!equalWorldPlacementBytes(candidate,bytes(value.proposed_map_base64)))fail();
 const original=await decodeWorldPlacementSeeds(map.current,man.floor,source.scene),decoded=await decodeWorldPlacementSeeds(candidate,man.floor,source.scene),seeds=new Map(decoded.placements.map(s=>[s.source_cell,s])),removedCells=new Set(deleted.map(a=>a.target_cell)),remaining=original.placements.filter(s=>!removedCells.has(s.source_cell));
 if(seeds.size!==remaining.length||!nativeWorldPlacementMatches(decoded.unresolved,original.unresolved)||remaining.some(s=>!nativeWorldPlacementMatches(seeds.get(s.source_cell),s)))fail();
 const allocations=audits.flatMap(a=>a.allocations).map(a=>({...a,native_seed:structuredClone(seeds.get(a.target_cell))}));
 const expected={schema_version:'legaia.worldmap-scripted-removal-review.v1',project_path:source.project_path,scene:source.scene,source_key:source.source_key,source_record:source.source_record,placement_id:placementId,cascade,current_map_sha256:source.current_map_sha256,current_man_sha256:source.current_man_sha256,proposed_map_sha256:await placementDigest(candidate),proposed_map_base64:value.proposed_map_base64,before_binding:source.binding,binding,audit:{removed_placement_ids:removed,removed_placements:deleted,authored_scripted_placements:allocations,scope:'authored-scripted-removal-only',changed_bytes:[...candidate].flatMap((n,i)=>n===map.current[i]?[]:[{byte_offset:i,before_byte:map.current[i],after_byte:n}]),gameplay_verified:false},read_only:true,project_changed:false,gameplay_verified:false,build_ready:false,review_key:value.review_key};
 if(!nativeWorldPlacementMatches(value,expected))fail();return structuredClone(value);
}
