import {scriptedGroupSelection} from './worldmap-scripted-group-selection.js';
import {selectionBounds} from './scene-selection-bounds.js';
export function scriptedGroupDisplay(entities,draft){
 const {source,ids,delta}=draft??{};if(!source||!Array.isArray(ids)||ids.length<2||!delta||Object.keys(delta).sort().join(',')!=='x,y,yaw_units,z'||['x','y','z'].some(a=>!Number.isSafeInteger(delta[a])||Math.abs(delta[a])>65535)||!Number.isSafeInteger(delta.yaw_units)||Math.abs(delta.yaw_units)>4095)throw Error('Scripted group draft requires bounded native deltas.');
 const selected=ids.map(id=>{const hits=entities.filter(e=>e.authored_placement?.placement_id===id);if(hits.length!==1)throw Error('Scripted group draft owner is missing or ambiguous.');return hits[0];});
 scriptedGroupSelection(source,ids,selected,'replace');const positions=new Map(),transforms=new Map(),points=[],view=new DataView(draft.current.buffer,draft.current.byteOffset,draft.current.byteLength);
 for(const e of selected){const at=e.authored_placement.record_index*32;for(const [i,axis] of ['x','y','z'].entries()){const n=view.getInt16(at+i*2,true)+delta[axis];if(n<-32768||n>32767)throw Error('Scripted group draft exceeds a selected native offset.');}
  if(!Array.isArray(e.model_to_scene)||e.model_to_scene.length!==16||e.model_to_scene.some(n=>!Number.isFinite(n))||e.source_rotation_psx.x!==0||e.source_rotation_psx.z!==0||(view.getUint16(at+10,true)&4095)!==(e.source_rotation_psx.y&4095))throw Error('Scripted group display lacks qualified native orientation.');
  const p={x:e.model_to_scene[3]+delta.x,y:e.model_to_scene[7]-delta.y,z:e.model_to_scene[11]-delta.z};points.push(p);if(delta.x||delta.y||delta.z)positions.set(e.entity_id,p);
  if(delta.yaw_units){const angle=((view.getUint16(at+10,true)&4095)+delta.yaw_units)*Math.PI/2048,c=Math.cos(angle),s=Math.sin(angle);transforms.set(e.entity_id,[c,0,s,p.x,0,-1,0,p.y,-s,0,c,p.z,0,0,0,1]);}
 }
 return {positions,transforms,pivot:selectionBounds(points).target};
}
