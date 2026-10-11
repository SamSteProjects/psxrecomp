import {worldMapTriggerTables,worldManRecordSpans} from './worldmap-scripted-placement-replay.js';
import {placementDigest} from './worldmap-placement-replay.js';
import {nativeWorldPlacementMatches} from './worldmap-current-placements.js';
const fail=()=>{throw Error('Scripted bind differs from qualified Current native ownership.');};
const ordered=v=>Array.isArray(v)?v.map(ordered):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,ordered(v[k])])):v;
const same=(a,b)=>JSON.stringify(ordered(a))===JSON.stringify(ordered(b));
const bytes=v=>Uint8Array.from(atob(v),c=>c.charCodeAt(0));
export async function qualifyScriptedWorldBind(value,current,entity,path){
 const source=current?.placement_source,allocation=source?.authored_scripted_placements?.find(a=>a.placement_id===entity?.authored_placement?.placement_id);
 if(current?.representation!=='current-scripted-placement-source'||entity?.placement_scope!=='authored_scripted_seed'||!allocation||value?.schema_version!=='legaia.worldmap-scripted-bind.v1')fail();
 if(entity.entity_id!==`scene://${current.scene}/worldmap/authored-placements/${allocation.placement_id.split('/').pop()}`||entity.native_entity_id!==allocation.native_seed.entity_id||!nativeWorldPlacementMatches(entity.authored_placement,allocation)||Object.entries(allocation.native_seed).some(([k,v])=>!['entity_id','placement_scope'].includes(k)&&!nativeWorldPlacementMatches(entity[k],v,k)))fail();
 const map=bytes(source.current_map_base64),man=bytes(source.current_man_base64),retail=bytes(source.source_man_base64),anchor=allocation.native_seed.source_anchor;
 if(await placementDigest(map)!==source.current_map_sha256||await placementDigest(man)!==source.current_man_sha256||await placementDigest(retail)!==source.source_man_sha256)fail();
 const primary=worldMapTriggerTables(map.slice(65536)).tables[1],fallback=worldMapTriggerTables(bytes(source.fallback_base64)).tables[1];
 const hits=[];for(const [name,t] of [['primary',primary],['fallback',fallback]])t.rows.forEach((row,index)=>{if(row[0]===anchor.col&&row[1]===anchor.row)hits.push({name,row,index,at:65536+t.at+4*index});});
 if(hits.length!==1||hits[0].name!=='primary')fail();
 const h=hits[0],span=worldManRecordSpans(man)[h.row[2]],original=worldManRecordSpans(retail)[h.row[2]];
 if(!span||span.partition!==0||!same(span,original))fail();
 const headerLength=2+2*man[span.at];if(headerLength>span.length)fail();
 const script={id:`script://${current.scene}/worldmap/man-p0/${String(span.index).padStart(4,'0')}`,partition:0,record_index:span.index,flat_record_index:h.row[2],byte_offset:span.at,byte_length:span.length,retail_sha256:await placementDigest(retail.slice(span.at,span.at+span.length)),current_sha256:await placementDigest(man.slice(span.at,span.at+span.length)),entry_pc:headerLength,header_sha256:await placementDigest(man.slice(span.at,span.at+headerLength)),encoded_animation_selector:man[span.at+headerLength-1]};
 if(script.id!==allocation.script_id)fail();
 const expected={schema_version:'legaia.worldmap-scripted-bind.v1',project_path:path,scene:current.scene,source_key:current.project_source_key,entity_id:entity.entity_id,native_entity_id:allocation.native_seed.entity_id,placement_id:allocation.placement_id,anchor,source_record:source.source_record,source_man_sha256:source.source_man_sha256,current_map_sha256:source.current_map_sha256,current_man_sha256:source.current_man_sha256,trigger:{id:`trigger://${current.scene}/field-map/primary/kind-1/${String(h.index).padStart(4,'0')}`,table_source:'primary',record_index:h.index,byte_offset:h.at,sha256:await placementDigest(h.row),encoded:{tile_x:h.row[0],tile_z:h.row[1],record_index:h.row[2],gate:h.row[3]}},script,shared_script:true,runtime_activation:'not_evaluated',animation_clip:'not_resolved',read_only:true,project_changed:false,gameplay_verified:false};
 if(!same(value,expected))fail();return structuredClone(expected);
}
