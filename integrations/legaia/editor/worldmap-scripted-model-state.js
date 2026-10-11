import {placementDigest,decodeWorldPlacementSeeds,equalWorldPlacementBytes} from './worldmap-placement-replay.js';
import {allocateScriptedWorldPlacements,mergeScriptedWorldCurrent} from './worldmap-scripted-placement-replay.js';
import {nativeWorldPlacementMatches} from './worldmap-current-placements.js';
const fail=()=>{throw Error('Scripted model Review differs from native replay or saved UUID ownership.');};
const bytes=v=>Uint8Array.from(atob(v),c=>c.charCodeAt(0));
export async function qualifyScriptedModelReview(value,qualified,placementIds,modelPoolIndex,currentGeometry){
 const {source,man,map}=qualified;
 if(!Array.isArray(placementIds)||placementIds.length<1||placementIds.length>32||placementIds.some(i=>typeof i!=='string')||new Set(placementIds).size!==placementIds.length||placementIds.some((id,i)=>i&&placementIds[i-1]>=id)||!Number.isSafeInteger(modelPoolIndex)||modelPoolIndex<1||modelPoolIndex>511||!source.binding||value?.schema_version!=='legaia.worldmap-scripted-model-review.v1'||typeof value.review_key!=='string'||!/^[0-9a-f]{64}$/.test(value.review_key))fail();
 const selected=new Map(source.authored_scripted_placements.map(a=>[a.placement_id,a]));if(placementIds.some(id=>!selected.has(id)))fail();
 const assetId=`asset://${source.scene}/worldmap/models/${String(modelPoolIndex).padStart(4,'0')}`,asset=currentGeometry?.scene_graph?.assets.find(a=>a.asset_id===assetId);
 if(currentGeometry?.project_source_key!==source.source_key||!asset?.preview?.vertices?.length||!asset.preview.triangles?.length)fail();
 const old=new DataView(map.current.buffer,map.current.byteOffset,map.current.byteLength),models=new Map([...selected].map(([id,a])=>[id,old.getUint16(a.record_index*32+16,true)])),changed=new Set(placementIds.filter(i=>models.get(i)!==modelPoolIndex)),cells=new Set([...changed].map(i=>selected.get(i).target_cell));
 const binding=structuredClone(source.binding),fallback=bytes(source.fallback_base64),pinned=[],found=[];let canonical=bytes(source.retained_base_map_base64);const audits=[];
 if(changed.size){binding.schema_version='legaia.worldmap-scripted-placement-ledger.v2';
  for(const operation of binding.operations)for(const request of operation.requests){const id=request.placement_id;
   if(changed.has(id)){request.model_pool_index=modelPoolIndex;found.push(id);}
   else if(!placementIds.includes(id)&&cells.has(request.donor_cell)){request.model_pool_index=models.get(id);pinned.push({placement_id:id,model_pool_index:models.get(id)});}
  }
  if(found.length!==changed.size||new Set(found).size!==changed.size)fail();
 }
 for(const operation of binding.operations){const result=await allocateScriptedWorldPlacements(canonical,fallback,man.current,man.floor,source.scene,operation.requests,operation.relocation_offset,binding.schema_version==='legaia.worldmap-scripted-placement-ledger.v2');canonical=result.bytes;operation.proposed_map_sha256=await placementDigest(canonical);audits.push(result.audit);}
 const candidate=await mergeScriptedWorldCurrent(bytes(source.retained_base_map_base64),canonical,map.normal,man.floor,source.scene,audits);
 const expectedBytes=map.current.slice(),view=new DataView(expectedBytes.buffer),nativeIds=new Set();
 for(const id of placementIds){const a=selected.get(id);if(nativeIds.has(a.native_seed.entity_id))fail();nativeIds.add(a.native_seed.entity_id);view.setUint16(a.record_index*32+16,modelPoolIndex,true);}
 if(!equalWorldPlacementBytes(candidate,expectedBytes)||typeof value.proposed_map_base64!=='string'||value.proposed_map_base64.length!==98304||!equalWorldPlacementBytes(candidate,bytes(value.proposed_map_base64)))fail();
 const decoded=await decodeWorldPlacementSeeds(candidate,man.floor,source.scene),original=await decodeWorldPlacementSeeds(map.current,man.floor,source.scene),seeds=new Map(decoded.placements.map(s=>[s.entity_id,s]));
 if(!nativeWorldPlacementMatches(decoded.coverage,original.coverage)||!nativeWorldPlacementMatches(decoded.unresolved,original.unresolved)||seeds.size!==original.placements.length||original.placements.some(s=>!seeds.has(s.entity_id)||!nativeIds.has(s.entity_id)&&!nativeWorldPlacementMatches(s,seeds.get(s.entity_id))))fail();
 const allocations=audits.flatMap(a=>a.allocations).map(a=>({...a,native_seed:structuredClone(seeds.get(a.native_seed.entity_id))}));
 for(const a of allocations){const prior=selected.get(a.placement_id);if(!prior||a.script_id!==prior.script_id||a.target_cell!==prior.target_cell)fail();}
 const expected={schema_version:'legaia.worldmap-scripted-model-review.v1',project_path:source.project_path,scene:source.scene,source_key:source.source_key,source_record:source.source_record,placement_ids:placementIds,model_pool_index:modelPoolIndex,asset_id:assetId,model_source_record:asset.source_record,current_map_sha256:source.current_map_sha256,current_man_sha256:source.current_man_sha256,proposed_map_sha256:await placementDigest(candidate),proposed_map_base64:value.proposed_map_base64,before_binding:source.binding,binding,audit:{before:placementIds.map(id=>selected.get(id)),after:placementIds.map(id=>allocations.find(a=>a.placement_id===id)),authored_scripted_placements:allocations,retained_child_models:pinned,scope:'authored-scripted-model-only',changed_bytes:[...candidate].flatMap((n,i)=>n===map.current[i]?[]:[{byte_offset:i,before_byte:map.current[i],after_byte:n}]),gameplay_verified:false},read_only:true,project_changed:false,gameplay_verified:false,build_ready:false,review_key:value.review_key};
 if(!nativeWorldPlacementMatches(value,expected))fail();return structuredClone(value);
}
