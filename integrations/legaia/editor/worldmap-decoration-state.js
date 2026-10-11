import {worldPlacementInventory, allocateWorldPlacements, equalWorldPlacementBytes, placementDigest,
  replayWorldPlacementAllocations, composeWorldPlacementTransforms, decodeWorldPlacementSeeds} from './worldmap-placement-replay.js';
import {nativeWorldPlacementMatches} from './worldmap-current-placements.js';
import {validValues} from './worldmap-placement-state.js';
const fail = message => { throw Error(message); };
const exact = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) &&
  Object.keys(value).sort().join(',') === [...keys].sort().join(',');
const hash = value => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
const same = nativeWorldPlacementMatches;
const keys = ['schema_version','project_path','scene','source_key','source_record','current_map_sha256','current_map_base64',
  'floor_lut','authored_allocations','binding','donors','free_record_indices','target_cells','current_placements',
  'read_only','project_changed','gameplay_verified','limitations'];
const decode = text => {
  if (typeof text !== 'string' || text.length !== 98304 || !/^[A-Za-z0-9+/]+$/.test(text)) fail('Decoration source requires complete MAP bytes.');
  return Uint8Array.from(atob(text), c => c.charCodeAt(0));
};
export async function qualifyWorldDecorationSource(value, current, path) {
  const meta = current?.placement_authoring;
  if (!meta || current.representation !== 'current-source' || !exact(value, keys) ||
      value.schema_version !== 'legaia.worldmap-placement-allocation-source.v2' || value.project_path !== path ||
      value.scene !== current.scene || value.source_key !== current.project_source_key ||
      value.read_only !== true || value.project_changed !== false || value.gameplay_verified !== false ||
      !same(value.source_record, meta.source_record) || value.current_map_sha256 !== meta.current_map_sha256 ||
      value.current_map_base64 !== meta.current_map_base64 || !same(value.floor_lut, meta.floor_lut) ||
      !same(value.binding, meta.allocation_binding) || !same(value.authored_allocations, meta.authored_allocations) ||
      !Array.isArray(value.limitations) || value.limitations.some(v => typeof v !== 'string' || v.length > 4096))
    fail('Decoration source differs from the qualified Current scene.');
  const bytes = decode(value.current_map_base64), inventory = await worldPlacementInventory(bytes, value.floor_lut, value.scene);
  for (const key of ['donors','free_record_indices','target_cells','current_placements'])
    if (!same(value[key], inventory[key])) fail('Decoration donor, target or unused-record inventory differs from native MAP replay.');
  return {metadata: structuredClone(value), bytes, inventory, retailBytes: decode(meta.retail_map_base64),
    authoredRecords: structuredClone(meta.authored_records)};
}
export function worldDecorationDraft(source, donorCell, targetCell, values, newUuid = () => crypto.randomUUID(), placementId = null) {
  if (!source?.inventory.donors.some(p => p.source_cell === donorCell) || !source.inventory.target_cells.includes(targetCell) ||
      !source.inventory.free_record_indices.length) fail('Choose an available decoration donor and model-free target cell.');
  return {placement_id: placementId ?? `placement://authored/${newUuid()}`, donor_cell: donorCell, target_cell: targetCell,
    record_index: source.inventory.free_record_indices[0], values: structuredClone(values)};
}
export function worldDecorationDonorValues(source, donorCell) {
  const donor = source?.inventory.donors.find(p => p.source_cell === donorCell);
  if (!donor) fail('Choose a qualified native decoration donor.');
  const view = new DataView(source.bytes.buffer, source.bytes.byteOffset, source.bytes.byteLength), at = donor.object_record_index * 32;
  return {offset: {x: view.getInt16(at, true), y: view.getInt16(at + 2, true), z: view.getInt16(at + 4, true)},
    yaw_units: view.getUint16(at + 10, true) & 4095};
}
export async function qualifyWorldDecorationReview(value, source, requests) {
  const before = source?.metadata;
  if (!before || !exact(value, ['schema_version','project_path','scene','source_key','source_record','requests','current_map_sha256',
      'proposed_map_sha256','proposed_map_base64','audit','binding','before_binding','read_only','project_changed','gameplay_verified','build_ready','review_key']) ||
      value.schema_version !== 'legaia.worldmap-placement-allocation-review.v2' || value.project_path !== before.project_path ||
      value.scene !== before.scene || value.source_key !== before.source_key || !same(value.source_record, before.source_record) ||
      !same(value.requests, requests) || value.current_map_sha256 !== before.current_map_sha256 ||
      value.read_only !== true || value.project_changed !== false || value.gameplay_verified !== false || value.build_ready !== false ||
      !hash(value.review_key) || !same(value.before_binding, before.binding)) fail('Decoration Review lost its source, draft or read-only scope.');
  const allocated = await allocateWorldPlacements(source.bytes, before.floor_lut, before.scene, requests);
  if (value.proposed_map_sha256 !== allocated.audit.proposed_sha256 || !same(value.audit, allocated.audit) ||
      !equalWorldPlacementBytes(decode(value.proposed_map_base64), allocated.bytes)) fail('Decoration Review differs from complete independent allocation replay.');
  const binding = value.binding, prior = before.binding;
  const provenance = {...before.source_record, schema_version: prior?.schema_version??'legaia.worldmap-placement-allocation-ledger.v1'};
  if (!exact(binding, [...Object.keys(provenance), 'operations']) ||
      Object.entries(provenance).some(([k,v]) => binding[k] !== v) || !Array.isArray(binding.operations) ||
      binding.operations.length !== (prior?.operations.length ?? 0) + 1 || binding.operations.length > 32 ||
      !same(binding.operations.slice(0,-1), prior?.operations ?? []) ||
      !exact(binding.operations.at(-1), ['requests','proposed_map_sha256']) ||
      !same(binding.operations.at(-1).requests, requests) || !hash(binding.operations.at(-1).proposed_map_sha256))
    fail('Decoration Review changed existing retained allocation lineage.');
  const canonical = await replayWorldPlacementAllocations(source.retailBytes, before.floor_lut, before.scene, binding, before.source_record);
  const composed = await composeWorldPlacementTransforms(source.retailBytes, canonical.bytes, before.floor_lut, before.scene, source.authoredRecords);
  if (!equalWorldPlacementBytes(composed, allocated.bytes)) fail('Decoration Review canonical lineage conflicts with original transforms.');
  return structuredClone(value);
}

export async function transformWorldDecorationGroup(source, placementIds, delta) {
  if (!Array.isArray(placementIds) || placementIds.length < 1 || placementIds.length > 32 ||
      placementIds.some(i=>typeof i!=='string') || !same(placementIds,[...new Set(placementIds)].sort()) ||
      !exact(delta,['x','y','z','yaw_units']) || ['x','y','z'].some(a=>!Number.isInteger(delta[a])||Math.abs(delta[a])>65535) ||
      !Number.isInteger(delta.yaw_units) || Math.abs(delta.yaw_units)>4095 || !Object.values(delta).some(n=>n!==0))
    fail('Choose 1–32 unique retained identities and bounded nonzero integer deltas.');
  const binding=structuredClone(source.metadata.binding), changes=[];
  const all=binding?.operations.flatMap(op=>op.requests)??[], literal=source.bytes.slice(), view=new DataView(literal.buffer);
  for(const placementId of placementIds){
    const matches=all.filter(r=>r.placement_id===placementId), before=source.metadata.authored_allocations.find(a=>a.placement_id===placementId);
    if(matches.length!==1||!before)fail('Group contains an unavailable authored identity.');
    const current=matches[0].values, values={offset:Object.fromEntries(['x','y','z'].map(a=>[a,current.offset[a]+delta[a]])),yaw_units:((current.yaw_units+delta.yaw_units)%4096+4096)%4096};
    if(!validValues(values))fail('Group transform overflows a signed16 offset.');
    matches[0].values=values;
    const at=before.record_index*32,currentValues={offset:Object.fromEntries(['x','y','z'].map((a,i)=>[a,view.getInt16(at+i*2,true)])),yaw_units:view.getUint16(at+10,true)&4095};
    for(const [i,a] of ['x','y','z'].entries())view.setInt16(at+i*2,currentValues.offset[a]+delta[a],true);
    view.setUint16(at+10,(view.getUint16(at+10,true)&0xf000)|((currentValues.yaw_units+delta.yaw_units+4096)%4096),true);
    changes.push({placement_id:placementId,before:structuredClone(before),current_values:currentValues,values:structuredClone(values)});
  }
  let canonical=source.retailBytes;
  for(const op of binding.operations){const allocated=await allocateWorldPlacements(canonical,source.metadata.floor_lut,source.metadata.scene,op.requests);canonical=allocated.bytes;op.proposed_map_sha256=allocated.audit.proposed_sha256;}
  const replayed=await replayWorldPlacementAllocations(source.retailBytes,source.metadata.floor_lut,source.metadata.scene,binding,source.metadata.source_record);
  const bytes=await composeWorldPlacementTransforms(source.retailBytes,replayed.bytes,source.metadata.floor_lut,source.metadata.scene,source.authoredRecords);
  if(!equalWorldPlacementBytes(bytes,literal))fail('Group changed unrelated native bytes or unselected decorations.');
  for(const change of changes)change.after=replayed.allocations.find(a=>a.placement_id===change.placement_id);
  return {binding,bytes,audit:{placements:changes,changed_bytes:Array.from(bytes.entries()).filter(([i,n])=>n!==source.bytes[i]).map(([i,n])=>({byte_offset:i,before_byte:source.bytes[i],after_byte:n})),scope:'authored-decoration-group-transform-only',gameplay_verified:false}};
}

export async function qualifyWorldDecorationGroupReview(value,source,placementIds,delta){
  const before=source.metadata;
  if(!exact(value,['schema_version','project_path','scene','source_key','source_record','placement_ids','delta','current_map_sha256','proposed_map_sha256','proposed_map_base64','before_binding','binding','audit','read_only','project_changed','gameplay_verified','build_ready','review_key']) ||
      value.schema_version!=='legaia.worldmap-decoration-group-review.v1'||value.project_path!==before.project_path||value.scene!==before.scene||
      value.source_key!==before.source_key||!same(value.source_record,before.source_record)||!same(value.placement_ids,placementIds)||!same(value.delta,delta)||
      value.current_map_sha256!==before.current_map_sha256||!same(value.before_binding,before.binding)||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||value.build_ready!==false||!hash(value.review_key))
    fail('Group Review changed its Current identities, delta or read-only scope.');
  const revised=await transformWorldDecorationGroup(source,placementIds,delta);
  if(!same(value.binding,revised.binding)||!same(value.audit,revised.audit)||!equalWorldPlacementBytes(decode(value.proposed_map_base64),revised.bytes)||value.proposed_map_sha256!==await placementDigest(revised.bytes))
    fail('Group Review differs from independent recipe replay and complete literal patch.');
  return structuredClone(value);
}

export async function reviseWorldDecoration(source, placementId, values) {
  if (!validValues(values)) fail('Decoration transform requires signed16 XYZ and yaw 0–4095.');
  const before = source.metadata.authored_allocations.find(a => a.placement_id === placementId), binding = structuredClone(source.metadata.binding);
  const requests = binding?.operations.flatMap(op => op.requests).filter(r => r.placement_id === placementId) ?? [];
  if (!before || requests.length !== 1 || same(requests[0].values, values)) fail('Choose a changed retained authored decoration transform.');
  requests[0].values = structuredClone(values);
  let bytes = source.retailBytes;
  for (const op of binding.operations) {
    const allocated = await allocateWorldPlacements(bytes, source.metadata.floor_lut, source.metadata.scene, op.requests);
    bytes = allocated.bytes; op.proposed_map_sha256 = allocated.audit.proposed_sha256;
  }
  const replayed = await replayWorldPlacementAllocations(source.retailBytes, source.metadata.floor_lut, source.metadata.scene, binding, source.metadata.source_record);
  bytes = await composeWorldPlacementTransforms(source.retailBytes, replayed.bytes, source.metadata.floor_lut, source.metadata.scene, source.authoredRecords);
  const literal = source.bytes.slice(), view = new DataView(literal.buffer), at = before.record_index * 32;
  for (const [i,axis] of ['x','y','z'].entries()) view.setInt16(at + i*2, values.offset[axis], true);
  view.setUint16(at+10, (view.getUint16(at+10,true)&0xf000)|values.yaw_units, true);
  if (!equalWorldPlacementBytes(bytes,literal)) fail('Decoration edit changed unrelated bytes or another authored clone.');
  return {binding,bytes,audit:{before:structuredClone(before),after:replayed.allocations.find(a=>a.placement_id===placementId),
    changed_bytes:Array.from(bytes.entries()).filter(([i,n])=>n!==source.bytes[i]).map(([i,n])=>({byte_offset:i,before_byte:source.bytes[i],after_byte:n})),
    scope:'authored-decoration-transform-only',gameplay_verified:false}};
}

export async function qualifyWorldDecorationTransformReview(value, source, placementId, values) {
  const before = source.metadata, selected = before.authored_allocations.find(a=>a.placement_id===placementId);
  if (!exact(value,['schema_version','project_path','scene','source_key','source_record','placement_id','values','current_values',
      'current_map_sha256','proposed_map_sha256','proposed_map_base64','before_binding','binding','audit',
      'read_only','project_changed','gameplay_verified','build_ready','review_key']) ||
      value.schema_version !== 'legaia.worldmap-decoration-transform-review.v1' || value.project_path !== before.project_path ||
      value.scene !== before.scene || value.source_key !== before.source_key || !same(value.source_record,before.source_record) ||
      value.placement_id !== placementId || !selected || !same(value.values,values) ||
      !same(value.current_values,worldDecorationDonorValues(source,selected.target_cell)) ||
      value.current_map_sha256 !== before.current_map_sha256 || !same(value.before_binding,before.binding) ||
      value.read_only !== true || value.project_changed !== false || value.gameplay_verified !== false || value.build_ready !== false || !hash(value.review_key))
    fail('Decoration transform Review changed its Current owner, values or read-only scope.');
  const revised = await reviseWorldDecoration(source,placementId,values);
  if (!same(value.binding,revised.binding) || !same(value.audit,revised.audit) ||
      !equalWorldPlacementBytes(decode(value.proposed_map_base64),revised.bytes) || value.proposed_map_sha256 !== await placementDigest(revised.bytes))
    fail('Decoration transform Review differs from independent recipe replay and literal native patch.');
  return structuredClone(value);
}

export async function removeWorldDecoration(source,placementId){
  let binding=structuredClone(source.metadata.binding);
  const requests=binding?.operations.flatMap(op=>op.requests)??[],matches=requests.filter(r=>r.placement_id===placementId);
  const removed=source.metadata.authored_allocations.find(a=>a.placement_id===placementId);
  if(matches.length!==1||!removed)fail('Choose one retained authored decoration to remove.');
  const selected=matches[0],rebases=[];
  for(const op of binding.operations){
    for(const request of op.requests)if(request.placement_id!==placementId&&request.donor_cell===selected.target_cell){
      rebases.push({placement_id:request.placement_id,before_donor_cell:request.donor_cell,after_donor_cell:selected.donor_cell});request.donor_cell=selected.donor_cell;
      if(binding.schema_version==='legaia.worldmap-placement-allocation-ledger.v2')request.model_pool_index=source.metadata.authored_allocations.find(a=>a.placement_id===request.placement_id).model_pool_index;
    }
    op.requests=op.requests.filter(r=>r.placement_id!==placementId);
  }
  binding.operations=binding.operations.filter(op=>op.requests.length);
  if(!binding.operations.length)binding=null;
  let canonical=source.retailBytes;
  for(const op of binding?.operations??[]){const allocated=await allocateWorldPlacements(canonical,source.metadata.floor_lut,source.metadata.scene,op.requests);canonical=allocated.bytes;op.proposed_map_sha256=allocated.audit.proposed_sha256;}
  const replayed=binding?await replayWorldPlacementAllocations(source.retailBytes,source.metadata.floor_lut,source.metadata.scene,binding,source.metadata.source_record):{bytes:source.retailBytes,allocations:[]};
  const bytes=await composeWorldPlacementTransforms(source.retailBytes,replayed.bytes,source.metadata.floor_lut,source.metadata.scene,source.authoredRecords);
  const literal=source.bytes.slice(),at=removed.record_index*32,cellAt=0x8000+removed.target_cell*2;
  if(source.retailBytes.subarray(at,at+32).some(n=>n!==0))fail('Removal no longer owns an original unused zero record.');
  literal.set(source.retailBytes.subarray(at,at+32),at);literal.set(source.retailBytes.subarray(cellAt,cellAt+2),cellAt);
  if(!equalWorldPlacementBytes(bytes,literal))fail('Removal or donor rebasing changed surviving native bytes.');
  return {binding,bytes,audit:{removed:structuredClone(removed),rebased_donors:rebases,remaining_allocations:replayed.allocations,
    changed_bytes:Array.from(bytes.entries()).filter(([i,n])=>n!==source.bytes[i]).map(([i,n])=>({byte_offset:i,before_byte:source.bytes[i],after_byte:n})),scope:'authored-decoration-removal-only',gameplay_verified:false}};
}

export async function qualifyWorldDecorationRemovalReview(value,source,placementId){
  const before=source.metadata;
  if(!exact(value,['schema_version','project_path','scene','source_key','source_record','placement_id','current_map_sha256',
      'proposed_map_sha256','proposed_map_base64','before_binding','binding','audit','read_only','project_changed','gameplay_verified','build_ready','review_key'])||
      value.schema_version!=='legaia.worldmap-decoration-removal-review.v1'||value.project_path!==before.project_path||value.scene!==before.scene||
      value.source_key!==before.source_key||!same(value.source_record,before.source_record)||value.placement_id!==placementId||
      value.current_map_sha256!==before.current_map_sha256||!same(value.before_binding,before.binding)||
      value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||value.build_ready!==false||!hash(value.review_key))
    fail('Removal Review changed its Current identity or read-only scope.');
  const removed=await removeWorldDecoration(source,placementId);
  if(!same(value.binding,removed.binding)||!same(value.audit,removed.audit)||!equalWorldPlacementBytes(decode(value.proposed_map_base64),removed.bytes)||
      value.proposed_map_sha256!==await placementDigest(removed.bytes))fail('Removal Review differs from complete independent donor rebase and literal byte replay.');
  return structuredClone(value);
}

export async function relocateWorldDecoration(source,placementId,targetCell){
  const binding=structuredClone(source.metadata.binding),floor=source.metadata.floor_lut,scene=source.metadata.scene;
  const matches=binding?.operations.flatMap(op=>op.requests).filter(r=>r.placement_id===placementId)??[];
  const before=source.metadata.authored_allocations.find(a=>a.placement_id===placementId);
  if(matches.length!==1||!before||!Number.isInteger(targetCell)||!source.inventory.target_cells.includes(targetCell))
    fail('Choose a retained decoration and an unoccupied native walk cell.');
  const selected=matches[0],previous=selected.target_cell,rebases=[];
  for(const op of binding.operations)for(const request of op.requests)
    if(request.placement_id!==placementId&&request.donor_cell===previous){
      rebases.push({placement_id:request.placement_id,before_donor_cell:previous,after_donor_cell:targetCell});request.donor_cell=targetCell;
    }
  selected.target_cell=targetCell;
  let canonical=source.retailBytes;
  for(const op of binding.operations){const allocated=await allocateWorldPlacements(canonical,floor,scene,op.requests);canonical=allocated.bytes;op.proposed_map_sha256=allocated.audit.proposed_sha256;}
  const replayed=await replayWorldPlacementAllocations(source.retailBytes,floor,scene,binding,source.metadata.source_record);
  const bytes=await composeWorldPlacementTransforms(source.retailBytes,replayed.bytes,floor,scene,source.authoredRecords);
  const literal=source.bytes.slice(),oldAt=0x8000+previous*2,newAt=0x8000+targetCell*2,recordAt=selected.record_index*32;
  const view=new DataView(source.bytes.buffer,source.bytes.byteOffset,source.bytes.byteLength),word=view.getUint16(newAt,true),terrainAt=(word&511)*32+20;
  literal.set(source.retailBytes.subarray(oldAt,oldAt+2),oldAt);
  new DataView(literal.buffer).setUint16(newAt,(word&~511)|selected.record_index,true);
  literal.set(source.bytes.subarray(terrainAt,terrainAt+4),recordAt+20);
  if(!equalWorldPlacementBytes(bytes,literal))fail('Cell relocation changed offsets or unrelated native bytes.');
  const old=await decodeWorldPlacementSeeds(source.bytes,floor,scene),next=await decodeWorldPlacementSeeds(bytes,floor,scene);
  const destinationId=`scene://${scene}/worldmap/placements/${targetCell.toString(16).padStart(4,'0')}`;
  const survivors=old.placements.filter(p=>p.entity_id!==before.native_seed.entity_id);
  if(next.placements.length!==old.placements.length||!same(old.unresolved,next.unresolved)||!same(old.coverage.excluded,next.coverage.excluded)||
      survivors.some(p=>!same(p,next.placements.find(n=>n.entity_id===p.entity_id))))fail('Cell relocation changed another native seed or footprint binding.');
  const after=replayed.allocations.find(a=>a.placement_id===placementId);
  if(!same(after?.native_seed,next.placements.find(p=>p.entity_id===destinationId)))fail('Cell relocation has no complete final native seed.');
  return {binding,bytes,audit:{before:structuredClone(before),after,rebased_donors:rebases,
    changed_bytes:Array.from(bytes.entries()).filter(([i,n])=>n!==source.bytes[i]).map(([i,n])=>({byte_offset:i,before_byte:source.bytes[i],after_byte:n})),
    scope:'authored-decoration-native-cell-only',gameplay_verified:false}};
}

export async function qualifyWorldDecorationCellReview(value,source,placementId,targetCell){
  const before=source.metadata;
  if(!exact(value,['schema_version','project_path','scene','source_key','source_record','placement_id','target_cell','current_map_sha256',
      'proposed_map_sha256','proposed_map_base64','before_binding','binding','audit','read_only','project_changed','gameplay_verified','build_ready','review_key'])||
      value.schema_version!=='legaia.worldmap-decoration-cell-review.v1'||value.project_path!==before.project_path||value.scene!==before.scene||
      value.source_key!==before.source_key||!same(value.source_record,before.source_record)||value.placement_id!==placementId||value.target_cell!==targetCell||
      value.current_map_sha256!==before.current_map_sha256||!same(value.before_binding,before.binding)||
      value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||value.build_ready!==false||!hash(value.review_key))
    fail('Cell Review changed its Current owner, destination or read-only scope.');
  const moved=await relocateWorldDecoration(source,placementId,targetCell);
  if(!same(value.binding,moved.binding)||!same(value.audit,moved.audit)||!equalWorldPlacementBytes(decode(value.proposed_map_base64),moved.bytes)||
      value.proposed_map_sha256!==await placementDigest(moved.bytes))fail('Cell Review differs from independent lineage replay and literal native patch.');
  return structuredClone(value);
}

export async function reassignWorldDecorationModel(source,placementId,model){
  const binding=structuredClone(source.metadata.binding),before=source.metadata.authored_allocations.find(a=>a.placement_id===placementId);
  const requests=binding?.operations.flatMap(op=>op.requests)??[],matches=requests.filter(r=>r.placement_id===placementId);
  if(matches.length!==1||!before||!Number.isInteger(model)||model<1||model>511||model===before.model_pool_index)fail('Choose a changed native model for one retained decoration.');
  const retained=new Map(source.metadata.authored_allocations.map(a=>[a.placement_id,a.model_pool_index])),pinned=[];
  for(const request of requests)if(request.placement_id!==placementId&&request.donor_cell===before.target_cell){
    request.model_pool_index=retained.get(request.placement_id);pinned.push({placement_id:request.placement_id,model_pool_index:request.model_pool_index});
  }
  matches[0].model_pool_index=model;binding.schema_version='legaia.worldmap-placement-allocation-ledger.v2';
  let canonical=source.retailBytes;
  for(const op of binding.operations){const result=await allocateWorldPlacements(canonical,source.metadata.floor_lut,source.metadata.scene,op.requests);canonical=result.bytes;op.proposed_map_sha256=result.audit.proposed_sha256;}
  const replayed=await replayWorldPlacementAllocations(source.retailBytes,source.metadata.floor_lut,source.metadata.scene,binding,source.metadata.source_record);
  const bytes=await composeWorldPlacementTransforms(source.retailBytes,replayed.bytes,source.metadata.floor_lut,source.metadata.scene,source.authoredRecords);
  const literal=source.bytes.slice();new DataView(literal.buffer).setUint16(before.record_index*32+16,model,true);
  if(!equalWorldPlacementBytes(bytes,literal))fail('Model assignment changed another model, transform or native byte.');
  return {binding,bytes,audit:{before:structuredClone(before),after:replayed.allocations.find(a=>a.placement_id===placementId),retained_child_models:pinned,
    changed_bytes:Array.from(bytes.entries()).filter(([i,n])=>n!==source.bytes[i]).map(([i,n])=>({byte_offset:i,before_byte:source.bytes[i],after_byte:n})),
    scope:'authored-decoration-model-only',gameplay_verified:false}};
}

export async function qualifyWorldDecorationModelReview(value,source,placementId,model,current){
  const before=source.metadata,assetId=`asset://${before.scene}/worldmap/models/${String(model).padStart(4,'0')}`;
  const asset=current?.scene_graph?.assets.find(a=>a.asset_id===assetId);
  if(!exact(value,['schema_version','project_path','scene','source_key','source_record','placement_id','model_pool_index','asset_id','model_source_record',
      'before_binding','binding','current_map_sha256','proposed_map_sha256','proposed_map_base64','audit','read_only','project_changed','gameplay_verified','build_ready','review_key'])||
      value.schema_version!=='legaia.worldmap-decoration-model-review.v1'||value.project_path!==before.project_path||value.scene!==before.scene||
      value.source_key!==before.source_key||!same(value.source_record,before.source_record)||value.placement_id!==placementId||value.model_pool_index!==model||
      value.asset_id!==assetId||!asset?.preview?.vertices?.length||!asset.preview.triangles?.length||!same(value.model_source_record,asset.source_record)||
      value.current_map_sha256!==before.current_map_sha256||!same(value.before_binding,before.binding)||current.project_source_key!==before.source_key||
      current.representation!=='current-source'||!same(current.placement_authoring?.allocation_binding,before.binding)||
      value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||value.build_ready!==false||!hash(value.review_key))
    fail('Model Review changed its Current identity, model asset or read-only scope.');
  const assigned=await reassignWorldDecorationModel(source,placementId,model);
  if(!same(value.binding,assigned.binding)||!same(value.audit,assigned.audit)||!equalWorldPlacementBytes(decode(value.proposed_map_base64),assigned.bytes)||
      value.proposed_map_sha256!==await placementDigest(assigned.bytes))fail('Model Review differs from independent child retention and literal native replay.');
  return structuredClone(value);
}
export function worldDecorationGroupSelection(source,ids,entity,mode='toggle'){
  const rows=source?.metadata?.authored_allocations;
  if(!Array.isArray(rows)||!Array.isArray(ids)||ids.length>32||new Set(ids).size!==ids.length||!['toggle','add'].includes(mode)||entity?.placement_scope!=='authored_spawn_seed')throw Error('Viewport groups require retained Current decorations and up to 32 unique members.');
  const id=entity.authored_placement?.placement_id,owned=rows.filter(r=>r.placement_id===id);
  if(owned.length!==1||entity.entity_id!==`scene://${source.metadata.scene}/worldmap/authored-placements/${id?.split('/').pop()}`||owned[0].record_index!==entity.authored_placement.record_index||owned[0].target_cell!==entity.authored_placement.target_cell||Array.from(ids).some(member=>rows.filter(r=>r.placement_id===member).length!==1))throw Error('Viewport decoration membership does not match the qualified Current source.');
  const result=new Set(ids);if(mode==='toggle'&&result.has(id))result.delete(id);else result.add(id);
  if(result.size>32)throw Error('A decoration group supports at most 32 members; selection was unchanged.');
  return [...result].sort();
}

export function worldDecorationGroupBoxSelection(source,ids,entities,extend=false){
  if(!Array.isArray(source?.metadata?.authored_allocations)||!Array.isArray(entities)||entities.length>512||typeof extend!=='boolean')throw Error('Invalid bounded decoration box selection.');
  // Validate existing members even when replacing or clearing the selection.
  if(!Array.isArray(ids)||ids.length>32||new Set(ids).size!==ids.length||Array.from(ids).some(id=>source?.metadata?.authored_allocations?.filter(r=>r.placement_id===id).length!==1))throw Error('Existing decoration group is not qualified.');
  let result=extend?[...ids]:[];
  for(const entity of entities)result=worldDecorationGroupSelection(source,result,entity,'add');
  return result.sort();
}

function decorationPositionOrigin(source,placementId){
  const rows=source?.metadata?.authored_allocations?.filter(r=>r.placement_id===placementId),floor=source?.metadata?.floor_lut;
  if(rows?.length!==1||!(source.bytes instanceof Uint8Array)||source.bytes.length!==0x12000||!Array.isArray(floor)||floor.length!==16||floor.some(n=>!Number.isInteger(n)||n< -32768||n>32767))fail('Native position requires one qualified retained decoration and its complete floor source.');
  const row=rows[0],cell=row.target_cell,record=row.record_index;
  if(!Number.isInteger(cell)||cell<0||cell>16383||!Number.isInteger(record)||record<4||record>511)fail('Native position owner is outside the MAP cell or record domain.');
  const view=new DataView(source.bytes.buffer,source.bytes.byteOffset,source.bytes.byteLength),origin={x:(cell%128)*128+64,y:-floor[source.bytes[0x4000+cell]&15],z:Math.floor(cell/128)*128+64};
  const current={x:origin.x+view.getInt16(record*32,true),y:origin.y+view.getInt16(record*32+2,true),z:origin.z-view.getInt16(record*32+4,true)};
  if((view.getUint16(0x8000+cell*2,true)&511)!==record||row.native_seed?.source_cell!==cell||row.native_seed?.object_record_index!==record||!same(current,row.native_seed?.source_position))fail('Native position differs from the retained Current cell, record or floor.');
  return origin;
}
export function worldDecorationNativePosition(source,placementId,values){
  if(!validValues(values))fail('Native position requires signed16 offsets and native yaw.');
  const origin=decorationPositionOrigin(source,placementId);
  return {x:origin.x+values.offset.x,y:origin.y+values.offset.y,z:origin.z-values.offset.z};
}
export function worldDecorationValuesAtPosition(source,placementId,position,yaw){
  if(!exact(position,['x','y','z'])||Object.values(position).some(n=>!Number.isSafeInteger(n)))fail('Enter complete integer native world XYZ coordinates.');
  const origin=decorationPositionOrigin(source,placementId),values={offset:{x:position.x-origin.x,y:position.y-origin.y,z:origin.z-position.z},yaw_units:yaw};
  if(!validValues(values))fail('Native position exceeds the retained cell’s signed16 offset range. Move Cell is a separate reviewed edit.');
  return values;
}
