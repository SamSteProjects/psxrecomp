import {decodeWorldPlacementSeeds,placementDigest} from './worldmap-placement-replay.js';
import {nativeWorldPlacementMatches} from './worldmap-current-placements.js';
export async function qualifyWorldFootprint(value,current,entityId,path){
  const meta=current?.placement_authoring;
  if(current?.representation!=='current-source'||!meta||typeof meta.current_map_base64!=='string')throw Error('Footprint inspection requires qualified Current native bytes.');
  const data=Uint8Array.from(atob(meta.current_map_base64),c=>c.charCodeAt(0));
  if(await placementDigest(data)!==meta.current_map_sha256)throw Error('Footprint Current MAP hash differs.');
  const decoded=await decodeWorldPlacementSeeds(data,meta.floor_lut,current.scene),seed=decoded.placements.find(p=>p.entity_id===entityId);
  if(!seed||seed.source_layer!=='placed')throw Error('Choose a resolved placed static-object seed.');
  const view=new DataView(data.buffer),at=seed.object_record_index*32;
  const encoded={offset:{x:view.getInt16(at,true),y:view.getInt16(at+2,true),z:view.getInt16(at+4,true)},
    anchor_delta:{col:view.getInt8(at+6),row:view.getInt8(at+7)},sub_anchor:{x:view.getInt8(at+14),z:view.getInt8(at+15)},flags:view.getUint16(at+18,true)};
  const correction=!!(encoded.flags&8),offset={x:encoded.anchor_delta.col*128+encoded.sub_anchor.x*16,z:encoded.anchor_delta.row*128+encoded.sub_anchor.z*16};
  if(correction){offset.x-=encoded.offset.x;offset.z+=encoded.offset.z;}
  const a=seed.source_anchor,expected={schema_version:'legaia.worldmap-footprint-inspection.v1',project_path:path,scene:current.scene,
    source_key:current.project_source_key,source_record:meta.source_record,current_map_sha256:meta.current_map_sha256,entity_id:entityId,
    source_cell:seed.source_cell,record_index:seed.object_record_index,record_sha256:seed.source_record_sha256,encoded,
    anchor:{col:a.col,row:a.row,cell_index:a.row*128+a.col,cell_flags:a.cell_flags,bind_owner:seed.source_bind_owner},correction,offset,
    centre:{x:seed.source_position.x+offset.x,z:seed.source_position.z+offset.z},source_position:seed.source_position,
    extents:'unknown',runtime_collision:'not_evaluated',interaction_script:'not_resolved',animation:'not_resolved',
    scope:'source-static-footprint-offset-only',read_only:true,project_changed:false,gameplay_verified:false};
  if(!nativeWorldPlacementMatches(value,expected))throw Error('Footprint report differs from independent native bytes, coordinates or unresolved scope.');
  return structuredClone(value);
}
