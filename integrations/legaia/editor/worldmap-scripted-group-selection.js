import {nativeWorldPlacementMatches} from './worldmap-current-placements.js';
export function scriptedGroupSelection(source,current,entities,mode){
 const fail=()=>{throw Error('Viewport group requires qualified saved scripted Current owners.');};
 if(!source?.binding||!Array.isArray(source.authored_scripted_placements)||!source.authored_scripted_placements.length||source.authored_scripted_placements.length>32||!Array.isArray(current)||!Array.isArray(entities)||entities.length>512||!['replace','add','toggle'].includes(mode))fail();
 const owners=new Map(source.authored_scripted_placements.map(a=>[a.placement_id,a]));
 if(owners.size!==source.authored_scripted_placements.length||current.length>32||new Set(current).size!==current.length||current.some(id=>!owners.has(id)))fail();
 const picked=new Set();
 for(const e of entities){const a=owners.get(e?.authored_placement?.placement_id);if(!a||e.placement_scope!=='authored_scripted_seed'||e.authored_placement_kind!=='scripted'||e.native_entity_id!==a.native_seed.entity_id||e.entity_id!==`scene://${source.scene}/worldmap/authored-placements/${a.placement_id.split('/').pop()}`||!nativeWorldPlacementMatches(e.authored_placement,a))fail();picked.add(a.placement_id);}
 const result=new Set(mode==='replace'?[]:current);for(const id of picked){if(mode==='toggle'&&result.has(id))result.delete(id);else result.add(id);}if(result.size>32)fail();return [...result].sort();
}
