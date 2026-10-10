import {worldmapHierarchyRows} from './worldmap-scene.js';
const scenes=['map01','map02','map03'];
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const fail=m=>{throw new Error(m);};
export const validValues=v=>v&&Object.keys(v).sort().join(',')==='offset,yaw_units'&&v.offset&&Object.keys(v.offset).sort().join(',')==='x,y,z'&&Object.values(v.offset).every(n=>Number.isSafeInteger(n)&&n>=-32768&&n<=32767)&&Number.isSafeInteger(v.yaw_units)&&v.yaw_units>=0&&v.yaw_units<4096;
export function decodeWorldPlacements(value,scene,key){
  if(value?.schema_version!=='legaia.worldmap-placement-authoring.v1'||value.scene!==scene||!scenes.includes(scene)||!hash(key)||value.source_key!==key||value.gameplay_verified!==false||value.project_changed!==false||!hash(value.current_map_sha256)||!value.source_record||!['source_disc_sha256','source_map_sha256','source_floor_lut_sha256'].every(k=>hash(value.source_record[k]))||value.source_record.scene!==scene||!Array.isArray(value.records)||value.records.length>512||!Array.isArray(value.limitations)||value.limitations.some(s=>typeof s!=='string'||s.length>4096))fail('World placement source or coverage is invalid. Inspect again.');
  const ids=new Set(),entities=new Set();
  for(const row of value.records){if(!/^\d{4}$/.test(row.record_id)||Number(row.record_id)!==row.object_record_index||row.object_record_index>=512||ids.has(row.record_id)||!hash(row.source_record_sha256)||!validValues(row.retail_values)||!validValues(row.current_values)||row.authored_values!==null&&!validValues(row.authored_values)||typeof row.writable!=='boolean'||!Number.isSafeInteger(row.source_cell_count)||row.source_cell_count<1||row.source_cell_count>16384||!Array.isArray(row.placements)||!row.placements.length||row.placements.length>512||row.placements.length>row.source_cell_count||row.writable&&row.placements.length!==row.source_cell_count)fail('World placement record scope is invalid.');ids.add(row.record_id);for(const p of row.placements){if(p.object_record_index!==row.object_record_index||p.source_record_sha256!==row.source_record_sha256||p.entity_id!==`scene://${scene}/worldmap/placements/${p.source_cell.toString(16).padStart(4,'0')}`||!Number.isSafeInteger(p.source_cell)||p.source_cell<0||p.source_cell>=16384||entities.has(p.entity_id))fail('World placement record has invalid or duplicate source cells.');entities.add(p.entity_id);}}
  if(entities.size>512)fail('World placement entities exceed the qualified budget.');
  const review=value.review;if(review){const row=value.records.find(r=>r.record_id===review.record_id);if(!row||!row.writable||!hash(review.review_key)||!hash(review.candidate_map_sha256)||typeof review.shared_record!=='boolean'||typeof review.no_op!=='boolean'||!validValues(review.proposed_values)||review.values!==null&&!validValues(review.values)||!Array.isArray(review.changed_bytes)||review.changed_bytes.length>8||!Array.isArray(review.affected_source_entities)||JSON.stringify(review.affected_source_entities)!==JSON.stringify(row.placements.map(p=>p.entity_id))||row.source_cell_count>1&&!review.shared_record&&!review.no_op&&review.values!==null)fail('World placement review does not cover its shared source owner.');const at=row.object_record_index*32,seen=new Set();for(const b of review.changed_bytes){if(![0,1,2,3,4,5,10,11].includes(b.byte_offset-at)||seen.has(b.byte_offset)||![b.before_byte,b.after_byte].every(n=>Number.isSafeInteger(n)&&n>=0&&n<=255)||b.before_byte===b.after_byte)fail('World placement review writes outside its source transform fields.');seen.add(b.byte_offset);}}
  return structuredClone(value);
}
export function worldPlacementLayers(row,{review=null,draft=null}={}){
  if(!row||!validValues(row.retail_values)||!validValues(row.current_values)||row.authored_values!==null&&!validValues(row.authored_values)||draft!==null&&!validValues(draft)||review!==null&&(review.record_id!==row.record_id||!validValues(review.proposed_values)))fail('World placement comparison does not match its record.');
  return structuredClone({retail:row.retail_values,current:row.current_values,authored:row.authored_values,reviewed:review?.proposed_values??null,draft});
}
export function placementSceneView(base,report,proposed=false){
  const rows=new Map(report.records.map(r=>[r.object_record_index,r]));
  return {...base,entities:base.entities.map(entity=>{if(entity.placement_scope==='source_ground')return entity;const row=rows.get(entity.object_record_index);if(!row||row.source_record_sha256!==entity.source_record_sha256||!row.placements.some(p=>p.entity_id===entity.entity_id))fail('World geometry and transform owner disagree.');const v=proposed&&report.review?.record_id===row.record_id?report.review.proposed_values:row.current_values,b=row.retail_values,p={x:entity.source_position.x+v.offset.x-b.offset.x,y:entity.source_position.y+v.offset.y-b.offset.y,z:entity.source_position.z-v.offset.z+b.offset.z};const angle=v.yaw_units*Math.PI*2/4096,c=Math.cos(angle),s=Math.sin(angle);return {...entity,model_to_scene:[c,0,s,p.x,0,-1,0,-p.y,-s,0,c,p.z,0,0,0,1],authored_source_position:p};})};
}

export function worldPlacementComparison(base,geometry,placements){
  if(!geometry||!placements||geometry.scene!==placements.scene||geometry.project_source_key!==placements.source_key||!hash(placements.source_key)||geometry.source_record?.map_sha256!==placements.source_record?.source_map_sha256||geometry.source_record?.floor_lut_sha256!==placements.source_record?.source_floor_lut_sha256||geometry.source_record?.disc_sha256!==placements.source_record?.source_disc_sha256)fail('Retail and Current world placement sources differ.');
  return placementSceneView(base,placements);
}

// Build rows identify native source records, not imported field-scene entities.
export function worldPlacementBuildOwner(change){
  if(change?.scope!=='worldmap-source-record-transform-only')return null;
  const scene=change.scene,index=change.record_index,recordId=String(index).padStart(4,'0'),ownerId=`worldmap://${scene}/placements/records/${recordId}`;
  const field=change.field,axis=field?.startsWith('world_placement.offset.')?field.slice(-1):null;
  const integer=v=>Number.isSafeInteger(v)&&(axis?v>=-32768&&v<=32767:v>=0&&v<4096);
  const affected=change.affected_source_entities;
  if(!scenes.includes(scene)||!Number.isSafeInteger(index)||index<0||index>=512||change.owner_id!==ownerId||change.asset_id!==ownerId||!['world_placement.offset.x','world_placement.offset.y','world_placement.offset.z','world_placement.yaw_units'].includes(field)||!integer(change.before)||!integer(change.after)||!hash(change.source_record_sha256)||!Array.isArray(affected)||!affected.length||affected.length>512||new Set(affected).size!==affected.length||affected.some(id=>typeof id!=='string'||!id.startsWith(`scene://${scene}/worldmap/placements/`)||!/^[0-3][0-9a-f]{3}$/.test(id.slice(`scene://${scene}/worldmap/placements/`.length))))fail('World placement Build change lacks exact source ownership.');
  return {scene,assetId:`worldmap://${scene}/placements`,ownerId,recordId,recordIndex:index,sourceRecordHash:change.source_record_sha256,affectedEntityIds:[...affected]};
}
export function worldPlacementBuildTarget(change,authoredAssets){
  const ownership=worldPlacementBuildOwner(change);if(!ownership)return null;
  const {scene,ownerId,recordId,recordIndex:index,affectedEntityIds:affected}=ownership,axis=change.field.startsWith('world_placement.offset.')?change.field.slice(-1):null;
  const owners=(authoredAssets??[]).filter(a=>a.id===ownership.assetId);
  const asset=owners[0],binding=asset?.authored?.WorldMapPlacements,entries=binding?.entries,entry=entries?.[recordId];
  if(owners.length!==1||asset.kind!=='worldmap'||asset.scene_id!==null||asset.source_scene!==scene||binding.scene!==scene||Object.keys(binding).sort().join(',')!=='entries,scene,source_disc_sha256,source_floor_lut_sha256,source_map_sha256'||!['source_disc_sha256','source_map_sha256','source_floor_lut_sha256'].every(k=>hash(binding[k]))||!entries||Array.isArray(entries)||Object.keys(entries).length<1||Object.keys(entries).length>512||asset.placement_record_count!==Object.keys(entries).length||!entry||Object.keys(entry).sort().join(',')!=='shared_record,source_record_sha256,values'||!validValues(entry.values)||typeof entry.shared_record!=='boolean'||entry.source_record_sha256!==change.source_record_sha256||(axis?entry.values.offset[axis]:entry.values.yaw_units)!==change.after||affected.length>1&&!entry.shared_record)fail('World placement values differ from this Build report. Rebuild to inspect current changes.');
  return {...ownership,entries:{[recordId]:structuredClone(entry)}};
}

export function worldPlacementExportTarget(report,recordId,anchorEntityId,scope){
  if(!scenes.includes(report?.scene)||!hash(report.source_key)||!['source-scene','ground','selected'].includes(scope))fail('World placement export scope or source is invalid.');
  if(scope!=='selected')return {scope,entityId:null};
  const matches=report.records?.filter(r=>r.record_id===recordId),row=matches?.[0];
  if(matches?.length!==1||!row?.placements?.some(p=>p.entity_id===anchorEntityId)||typeof anchorEntityId!=='string'||!anchorEntityId.startsWith(`scene://${report.scene}/worldmap/placements/`)||!/^[0-3][0-9a-f]{3}$/.test(anchorEntityId.slice(`scene://${report.scene}/worldmap/placements/`.length)))fail('Selected export requires an exact affected source anchor.');
  return {scope,entityId:anchorEntityId};
}

// Visibility changes only the renderer; record ownership and export scope stay complete.
export function worldPlacementVisibility(base,report,recordId,anchorEntityId,scope='scene',ground=true){
  if(!['scene','record','anchor'].includes(scope)||typeof ground!=='boolean'||!Array.isArray(base?.entities)||base.entities.length>513)fail('World placement visibility scope is invalid.');
  const rows=report?.records?.filter(r=>r.record_id===recordId),row=rows?.[0];
  if(rows?.length!==1||!Array.isArray(row.placements)||!row.placements.length||row.placements.length>512)fail('Visibility requires one qualified placement record.');
  const members=new Set(row.placements.map(p=>p.entity_id)),entities=new Map(base.entities.map(e=>[e.entity_id,e]));
  if(members.size!==row.placements.length||entities.size!==base.entities.length||!members.has(anchorEntityId)||[...members].some(id=>{const e=entities.get(id);return !e||e.placement_scope==='source_ground'||e.object_record_index!==row.object_record_index||e.source_record_sha256!==row.source_record_sha256;}))fail('Visibility anchor or record membership changed.');
  return new Set(base.entities.filter(e=>e.placement_scope==='source_ground'?!ground:scope==='record'?!members.has(e.entity_id):scope==='anchor'?e.entity_id!==anchorEntityId:false).map(e=>e.entity_id));
}

export function worldPlacementRecordRows(report,sceneView,query='',scope='all',selectedRecordId=null){
  if(!Array.isArray(report?.records)||report.records.length>512||!['all','authored','shared','writable','unavailable'].includes(scope))fail('World placement record filter is invalid.');
  const ids=new Set(report.records.map(r=>r.record_id));if(ids.size!==report.records.length||selectedRecordId!==null&&!ids.has(selectedRecordId))fail('World record selection lacks unique source ownership.');
  const matched=new Set(worldmapHierarchyRows(sceneView,query).rows.map(r=>r.entityId));
  const matches=row=>(scope==='all'||scope==='authored'&&row.authored_values!==null||scope==='shared'&&row.source_cell_count>1||scope==='writable'&&row.writable||scope==='unavailable'&&!row.writable)&&row.placements.some(p=>matched.has(p.entity_id));
  let matching=0;const rows=[];for(const row of report.records){const match=matches(row);if(match)matching++;if(match||row.record_id===selectedRecordId)rows.push({recordId:row.record_id,matches:match});}
  return {rows,total:report.records.length,matching,selectedOutsideFilter:rows.some(r=>!r.matches)};
}


export function worldPlacementBatchDraft(report,recordIds,delta,shared){
  if(!report||!Array.isArray(report.records)||!report.records.length||report.records.length>512||!Array.isArray(recordIds)||!recordIds.length||recordIds.length>128||recordIds.some((id,i)=>typeof id!=='string'||!/^\d{4}$/.test(id)||Number(id)>=512||i>0&&id<=recordIds[i-1])||!delta||Object.keys(delta).sort().join(',')!=='x,y,yaw_units,z'||!['x','y','z'].every(a=>Number.isSafeInteger(delta[a])&&Math.abs(delta[a])<=65535)||!Number.isSafeInteger(delta.yaw_units)||Math.abs(delta.yaw_units)>4095||typeof shared!=='boolean')fail('Batch preview requires canonical records, bounded integer deltas and shared-cell consent.');
  const candidate=structuredClone(report),ids=new Set(recordIds);
  for(const id of ids){const matches=candidate.records.filter(r=>r.record_id===id);if(matches.length!==1||!matches[0].writable||!validValues(matches[0].current_values)||!Array.isArray(matches[0].placements)||!matches[0].placements.length||matches[0].placements.length!==matches[0].source_cell_count||matches[0].source_cell_count>1&&!shared)fail('Batch preview requires complete qualified record ownership and shared-cell consent.');const row=matches[0],value=row.current_values;row.current_values={offset:Object.fromEntries(['x','y','z'].map(a=>[a,value.offset[a]+delta[a]])),yaw_units:((value.yaw_units+delta.yaw_units)%4096+4096)%4096};if(!validValues(row.current_values))fail('Batch preview would overflow a native source record.');}
  return candidate;
}
