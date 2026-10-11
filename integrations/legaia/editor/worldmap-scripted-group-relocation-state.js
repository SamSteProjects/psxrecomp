import {placementDigest,decodeWorldPlacementSeeds,equalWorldPlacementBytes} from './worldmap-placement-replay.js';
import {allocateScriptedWorldPlacements,mergeScriptedWorldCurrent} from './worldmap-scripted-placement-replay.js';
import {nativeWorldPlacementMatches as same} from './worldmap-current-placements.js';
const fail=()=>{throw Error('Scripted group relocation Review differs from native replay or saved ownership.');};
const bytes=v=>Uint8Array.from(atob(v),c=>c.charCodeAt(0));
export async function qualifyScriptedGroupRelocationReview(value,qualified,ids,delta){
 const {source,man,map}=qualified;
 if(!Array.isArray(ids)||ids.length<2||ids.length>32||ids.some((id,i)=>typeof id!=='string'||i>0&&id<=ids[i-1])||!delta||!same(Object.keys(delta).sort(),['col','row'])||Object.values(delta).some(n=>!Number.isSafeInteger(n)||n < -127||n>127)||!source.binding||value?.schema_version!=='legaia.worldmap-scripted-group-relocation-review.v1'||typeof value.review_key!=='string'||!/^[0-9a-f]{64}$/.test(value.review_key))fail();
 const indexed=new Map(source.authored_scripted_placements.map(a=>[a.placement_id,a]));if(ids.some(id=>!indexed.has(id)))fail();
 const selected=ids.map(id=>indexed.get(id)),vacated=new Set(selected.flatMap(a=>[a.target_cell,a.anchor_cell])),destinations=new Map(),anchors=new Map();
 const currentView=new DataView(map.current.buffer,map.current.byteOffset,map.current.byteLength);
 for(const a of selected){const col=a.target_cell%128+delta.col,row=Math.floor(a.target_cell/128)+delta.row;if(col<0||col>127||row<0||row>127)fail();const target=row*128+col;if(!source.target_cells.includes(target)&&!vacated.has(target))fail();destinations.set(a.placement_id,target);const dc=currentView.getInt8(a.record_index*32+6),dr=currentView.getInt8(a.record_index*32+7);if(col+dc<0||col+dc>127||row+dr<0||row+dr>127)fail();anchors.set(a.placement_id,(row+dr)*128+col+dc);}
 const binding=structuredClone(source.binding),priorMoves=new Map(),found=[],dependents=[];
 for(const operation of binding.operations){
  for(const r of operation.requests)if(priorMoves.has(r.donor_cell)&&priorMoves.get(r.donor_cell)!==r.donor_cell){r.donor_cell=priorMoves.get(r.donor_cell);dependents.push(r.placement_id);}
  for(const r of operation.requests)if(destinations.has(r.placement_id)){r.target_cell=destinations.get(r.placement_id);found.push(r.placement_id);}
  for(const r of operation.requests)if(destinations.has(r.placement_id))priorMoves.set(indexed.get(r.placement_id).target_cell,destinations.get(r.placement_id));
 }
 if(found.length!==ids.length||!same([...found].sort(),ids))fail();
 const base=bytes(source.retained_base_map_base64),fallback=bytes(source.fallback_base64),baseView=new DataView(base.buffer),audits=[],oldAudits=[];let canonical=base,oldCanonical=base;
 for(const [index,operation] of binding.operations.entries()){
  const old=source.binding.operations[index],oldResult=await allocateScriptedWorldPlacements(oldCanonical,fallback,man.current,man.floor,source.scene,old.requests,old.relocation_offset,binding.schema_version==='legaia.worldmap-scripted-placement-ledger.v2');oldCanonical=oldResult.bytes;oldAudits.push(oldResult.audit);
  const result=await allocateScriptedWorldPlacements(canonical,fallback,man.current,man.floor,source.scene,operation.requests,operation.relocation_offset,binding.schema_version==='legaia.worldmap-scripted-placement-ledger.v2');canonical=result.bytes;operation.proposed_map_sha256=await placementDigest(canonical);audits.push(result.audit);
 }
 const candidate=await mergeScriptedWorldCurrent(base,canonical,map.normal,man.floor,source.scene,audits),allocations=audits.flatMap(a=>a.allocations),after=new Map(allocations.map(a=>[a.placement_id,a]));
 const expectedBytes=map.current.slice(),view=new DataView(expectedBytes.buffer),normal=new DataView(map.normal.buffer,map.normal.byteOffset,map.normal.byteLength);
 for(const cell of vacated)expectedBytes.set(map.normal.slice(32768+2*cell,32770+2*cell),32768+2*cell);
 for(const a of selected){const edited=after.get(a.placement_id),target=destinations.get(a.placement_id);if(!edited||edited.script_id!==a.script_id||edited.record_index!==a.record_index||edited.target_cell!==target||edited.anchor_cell!==anchors.get(a.placement_id))fail();view.setUint16(32768+2*target,(normal.getUint16(32768+2*target,true)&~511)|a.record_index,true);const environment=(baseView.getUint16(32768+2*target,true)&511)*32;expectedBytes.set(base.slice(environment+20,environment+24),a.record_index*32+20);}
 for(const a of selected){const at=32768+2*anchors.get(a.placement_id);view.setUint16(at,view.getUint16(at,true)|1024,true);}
 const byBind=new Map(selected.map(a=>[a.bind_id,a])),bindIndices=new Map();
 for(const [index,audit] of audits.entries()){const b=audit.bind_allocation,old=oldAudits[index].bind_allocation;if(b.proposed_table_offset!==old.proposed_table_offset||b.proposed_row_count!==old.proposed_row_count)fail();for(const a of old.allocations)if(byBind.has(a.bind_id))bindIndices.set(a.bind_id,a.record_index);for(const [id,index] of bindIndices){const cell=anchors.get(byBind.get(id).placement_id);expectedBytes.set([cell%128,Math.floor(cell/128)],65536+b.proposed_table_offset+4*index);}}
 if(bindIndices.size!==byBind.size||!equalWorldPlacementBytes(candidate,expectedBytes)||typeof value.proposed_map_base64!=='string'||value.proposed_map_base64.length!==98304||!equalWorldPlacementBytes(candidate,bytes(value.proposed_map_base64)))fail();
 const original=await decodeWorldPlacementSeeds(map.current,man.floor,source.scene),decoded=await decodeWorldPlacementSeeds(candidate,man.floor,source.scene),seeds=new Map(decoded.placements.map(s=>[s.source_cell,s])),oldCells=new Set(selected.map(a=>a.target_cell)),cells=new Set(original.placements.filter(s=>!oldCells.has(s.source_cell)).map(s=>s.source_cell));for(const cell of destinations.values())cells.add(cell);
 if(!same(decoded.coverage,original.coverage)||!same(decoded.unresolved,original.unresolved)||seeds.size!==cells.size||[...cells].some(c=>!seeds.has(c))||original.placements.some(s=>!oldCells.has(s.source_cell)&&!same(seeds.get(s.source_cell),s)))fail();
 const refreshed=allocations.map(a=>({...a,native_seed:structuredClone(seeds.get(a.target_cell))}));
 const expected={schema_version:'legaia.worldmap-scripted-group-relocation-review.v1',project_path:source.project_path,scene:source.scene,source_key:source.source_key,source_record:source.source_record,placement_ids:ids,delta,current_map_sha256:source.current_map_sha256,current_man_sha256:source.current_man_sha256,proposed_map_sha256:await placementDigest(candidate),proposed_map_base64:value.proposed_map_base64,before_binding:source.binding,binding,audit:{before:selected,after:ids.map(id=>refreshed.find(a=>a.placement_id===id)),dependent_donor_placements:dependents,authored_scripted_placements:refreshed,scope:'authored-scripted-group-relocation-only',changed_bytes:[...candidate].flatMap((n,i)=>n===map.current[i]?[]:[{byte_offset:i,before_byte:map.current[i],after_byte:n}]),gameplay_verified:false},read_only:true,project_changed:false,gameplay_verified:false,build_ready:false,review_key:value.review_key};
 if(!same(value,expected))fail();return structuredClone(value);
}
