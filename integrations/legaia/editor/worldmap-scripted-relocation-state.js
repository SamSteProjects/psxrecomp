import {placementDigest,decodeWorldPlacementSeeds,equalWorldPlacementBytes} from './worldmap-placement-replay.js';
import {allocateScriptedWorldPlacements,mergeScriptedWorldCurrent} from './worldmap-scripted-placement-replay.js';
import {nativeWorldPlacementMatches} from './worldmap-current-placements.js';
const fail=()=>{throw Error('Scripted relocation Review differs from complete native replay or selected ownership.');};
const bytes=v=>Uint8Array.from(atob(v),c=>c.charCodeAt(0));
export async function qualifyScriptedRelocationReview(value,qualified,placementId,targetCell){
 const {source,man,map}=qualified;
 if(!Number.isSafeInteger(targetCell)||targetCell<0||targetCell>=16384||!source.binding||value?.schema_version!=='legaia.worldmap-scripted-relocation-review.v1'||typeof value.review_key!=='string'||!/^[0-9a-f]{64}$/.test(value.review_key))fail();
 const before=source.authored_scripted_placements.find(a=>a.placement_id===placementId);if(!before||targetCell!==before.target_cell&&!source.target_cells.includes(targetCell))fail();
 const binding=structuredClone(source.binding),base=bytes(source.retained_base_map_base64),fallback=bytes(source.fallback_base64),dependents=[];
 let found=0;
 for(const operation of binding.operations){
  for(const request of operation.requests)if(found&&request.donor_cell===before.target_cell){request.donor_cell=targetCell;dependents.push(request.placement_id);}
  for(const request of operation.requests)if(request.placement_id===placementId){request.target_cell=targetCell;found++;}
 }
 if(found!==1)fail();
 const audits=[],oldAudits=[];let canonical=base,oldCanonical=base,environment;
 for(const [index,operation] of binding.operations.entries()){
  const old=source.binding.operations[index];const oldResult=await allocateScriptedWorldPlacements(oldCanonical,fallback,man.current,man.floor,source.scene,old.requests,old.relocation_offset);oldCanonical=oldResult.bytes;oldAudits.push(oldResult.audit);
  if(operation.requests.some(r=>r.placement_id===placementId)){const v=new DataView(canonical.buffer,canonical.byteOffset,canonical.byteLength),record=v.getUint16(32768+2*targetCell,true)&511;environment=canonical.slice(record*32+20,record*32+24);}
  const result=await allocateScriptedWorldPlacements(canonical,fallback,man.current,man.floor,source.scene,operation.requests,operation.relocation_offset);canonical=result.bytes;operation.proposed_map_sha256=await placementDigest(canonical);audits.push(result.audit);
 }
 const candidate=await mergeScriptedWorldCurrent(base,canonical,map.normal,man.floor,source.scene,audits),allocations=audits.flatMap(a=>a.allocations),after=allocations.find(a=>a.placement_id===placementId);
 if(after.script_id!==before.script_id||after.record_index!==before.record_index)fail();
 const expectedBytes=map.current.slice(),view=new DataView(expectedBytes.buffer),normal=new DataView(map.normal.buffer,map.normal.byteOffset,map.normal.byteLength);
 for(const cell of new Set([before.target_cell,before.anchor_cell]))expectedBytes.set(map.normal.slice(32768+2*cell,32770+2*cell),32768+2*cell);
 view.setUint16(32768+2*targetCell,(normal.getUint16(32768+2*targetCell,true)&~511)|before.record_index,true);
 const at=32768+2*after.anchor_cell;view.setUint16(at,view.getUint16(at,true)|1024,true);expectedBytes.set(environment,before.record_index*32+20);
 let bindIndex=null;
 for(const [index,audit] of audits.entries()){
  const b=audit.bind_allocation,old=oldAudits[index].bind_allocation;
  if(b.proposed_table_offset!==old.proposed_table_offset||b.proposed_row_count!==old.proposed_row_count)fail();
  for(const a of old.allocations)if(a.bind_id===before.bind_id)bindIndex=a.record_index;
  if(bindIndex!==null)expectedBytes.set([after.anchor_cell%128,Math.floor(after.anchor_cell/128)],65536+b.proposed_table_offset+4*bindIndex);
 }
 if(bindIndex===null||!equalWorldPlacementBytes(candidate,expectedBytes)||typeof value.proposed_map_base64!=='string'||value.proposed_map_base64.length!==98304||!equalWorldPlacementBytes(candidate,bytes(value.proposed_map_base64)))fail();
 const original=await decodeWorldPlacementSeeds(map.current,man.floor,source.scene),decoded=await decodeWorldPlacementSeeds(candidate,man.floor,source.scene),seeds=new Map(decoded.placements.map(s=>[s.source_cell,s]));
 const cells=new Set(original.placements.map(s=>s.source_cell));cells.delete(before.target_cell);cells.add(targetCell);
 if(!nativeWorldPlacementMatches(decoded.coverage,original.coverage)||!nativeWorldPlacementMatches(decoded.unresolved,original.unresolved)||seeds.size!==cells.size||[...cells].some(c=>!seeds.has(c))||original.placements.some(s=>s.source_cell!==before.target_cell&&!nativeWorldPlacementMatches(seeds.get(s.source_cell),s)))fail();
 const refreshed=allocations.map(a=>({...a,native_seed:structuredClone(seeds.get(a.target_cell))})),edited=refreshed.find(a=>a.placement_id===placementId);
 const expected={schema_version:'legaia.worldmap-scripted-relocation-review.v1',project_path:source.project_path,scene:source.scene,source_key:source.source_key,source_record:source.source_record,placement_id:placementId,target_cell:targetCell,current_map_sha256:source.current_map_sha256,current_man_sha256:source.current_man_sha256,proposed_map_sha256:await placementDigest(candidate),proposed_map_base64:value.proposed_map_base64,before_binding:source.binding,binding,audit:{before,after:edited,dependent_donor_placements:dependents,authored_scripted_placements:refreshed,scope:'authored-scripted-relocation-only',changed_bytes:[...candidate].flatMap((n,i)=>n===map.current[i]?[]:[{byte_offset:i,before_byte:map.current[i],after_byte:n}]),gameplay_verified:false},read_only:true,project_changed:false,gameplay_verified:false,build_ready:false,review_key:value.review_key};
 if(!nativeWorldPlacementMatches(value,expected))fail();return structuredClone(value);
}
