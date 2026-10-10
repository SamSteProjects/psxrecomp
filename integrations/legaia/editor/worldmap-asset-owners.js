// Connect a qualified source model group to complete native record owners.
import {validValues} from './worldmap-placement-state.js';
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),fail=m=>{throw Error(m);};
export function worldPlacementAssetOwners(geometry,placements,entityId,projectPath){
 const scene=geometry?.scene,key=geometry?.project_source_key,s=geometry?.source_record,p=placements?.source_record;
 if(!['map01','map02','map03'].includes(scene)||!hash(key)||placements?.scene!==scene||placements.source_key!==key||!hash(placements.current_map_sha256)||!s||!p||p.scene!==scene||[['disc_sha256','source_disc_sha256'],['map_sha256','source_map_sha256'],['floor_lut_sha256','source_floor_lut_sha256']].some(([a,b])=>!hash(s[a])||s[a]!==p[b])||typeof projectPath!=='string'||!projectPath||projectPath.length>4096)fail('World geometry and owner sources differ. Inspect again.');
 const entities=geometry.scene_graph?.entities,records=placements.records;
 if(!Array.isArray(entities)||entities.length<1||entities.length>513||new Set(entities.map(e=>e.entity_id)).size!==entities.length||!Array.isArray(records)||records.length<1||records.length>512||new Set(records.map(r=>r.record_id)).size!==records.length)fail('World source ownership is conflicting or outside its bounds.');
 const selected=entities.find(e=>e.entity_id===entityId);
 if(!selected||selected.placement_scope!=='source_spawn_seed'||!selected.asset_id?.startsWith(`asset://${scene}/worldmap/models/`)||!/^asset:\/\/map0[123]\/worldmap\/models\/[0-9a-f]{4}$/.test(selected.asset_id)||!geometry.scene_graph.assets?.some(a=>a.asset_id===selected.asset_id))fail('Choose a qualified source model instance. Ground has no placement owner.');
 const members=entities.filter(e=>e.asset_id===selected.asset_id),owners=new Map();
 if(!members.length||members.length>512)fail('Source model membership exceeds the owner selection limit.');
 for(const member of members){const matches=records.filter(r=>r.object_record_index===member.object_record_index&&r.source_record_sha256===member.source_record_sha256&&r.placements?.some(p=>p.entity_id===member.entity_id&&p.source_cell===member.source_cell));if(member.placement_scope!=='source_spawn_seed'||!hash(member.source_record_sha256)||matches.length!==1)fail('A model instance has missing or conflicting native ownership.');owners.set(matches[0].record_id,matches[0]);}
 if(owners.size>128)fail('Select a model with at most 128 complete source owners.');
 const rows=[...owners.values()].sort((a,b)=>a.record_id.localeCompare(b.record_id)),owned=new Set(),targets=[];
 for(const row of rows){const ids=row.placements.map(p=>p.entity_id).sort(),native=entities.filter(e=>e.object_record_index===row.object_record_index&&e.source_record_sha256===row.source_record_sha256).map(e=>e.entity_id).sort();
  if(!row.writable||row.record_id!==String(row.object_record_index).padStart(4,'0')||!validValues(row.current_values)||row.source_cell_count!==ids.length||!same(ids,native)||new Set(ids).size!==ids.length||ids.some(id=>owned.has(id)))fail('A model owner omits source cells or is not writable.');
  ids.forEach(id=>owned.add(id));targets.push({recordId:row.record_id,recordIndex:row.object_record_index,sourceRecordHash:row.source_record_sha256,currentValues:structuredClone(row.current_values),ownedEntityIds:ids,sourceCellCount:row.source_cell_count});
 }
 if(owned.size>512)fail('Complete model owner scope exceeds 512 source seeds.');
 const first=rows[0],target={scene,entityId:first.placements[0].entity_id,recordIndex:first.object_record_index,sourceRecordHash:first.source_record_sha256,sourceKey:key,projectPath,sourceRecord:structuredClone(p),currentMapHash:placements.current_map_sha256,completeKingdom:false,recordTargets:targets};
 return {target,assetId:selected.asset_id,assetInstanceIds:members.map(e=>e.entity_id).sort(),ownerIds:rows.map(r=>r.record_id),ownedEntityIds:[...owned].sort()};
}
