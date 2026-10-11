import {mountPlacementYaw} from './worldmap-placement-yaw.js';
import {mountPlacementGizmo,sourceOffsetDirections} from './worldmap-placement-gizmo.js';
import {validValues} from './worldmap-placement-state.js';
import {selectionBounds} from './scene-selection-bounds.js';

export function worldDecorationGroupDisplay(entities,draft){
  const {ids,delta,source}=draft??{},requests=source?.metadata?.binding?.operations?.flatMap(op=>op.requests);
  if(!Array.isArray(ids)||!ids.length||ids.length>32||new Set(ids).size!==ids.length||!requests||!delta||Object.keys(delta).sort().join(',')!=='x,y,yaw_units,z'||Object.values(delta).some(n=>!Number.isInteger(n))||['x','y','z'].some(a=>Math.abs(delta[a])>65535)||Math.abs(delta.yaw_units)>4095)throw Error('Group display requires bounded retained native identities and integer deltas.');
  const positions=new Map(),transforms=new Map(),points=[];
  for(const id of ids){
    const owned=requests.filter(r=>r.placement_id===id),matches=entities.filter(e=>e.placement_scope==='authored_spawn_seed'&&e.authored_placement?.placement_id===id);
    if(owned.length!==1||matches.length!==1||matches[0].authored_placement.record_index!==owned[0].record_index||matches[0].entity_id!==`scene://${source.metadata.scene}/worldmap/authored-placements/${id.split('/').pop()}`)throw Error('Group native owner is missing or ambiguous.');
    const entity=matches[0],base=owned[0].values,values={offset:Object.fromEntries(['x','y','z'].map(a=>[a,base?.offset?.[a]+delta[a]])),yaw_units:((base?.yaw_units+delta.yaw_units)%4096+4096)%4096},item={entityId:entity.entity_id,base,values};
    const position=worldDecorationDraftPosition(entity,{...item,values:{...values,yaw_units:base?.yaw_units}}),matrix=worldDecorationDraftTransform(entity,item);
    if(position)positions.set(entity.entity_id,position);if(matrix)transforms.set(entity.entity_id,matrix);
    points.push(position??{x:entity.model_to_scene[3],y:entity.model_to_scene[7],z:entity.model_to_scene[11]});
  }
  return {positions,transforms,pivot:selectionBounds(points).target};
}

export function mountWorldDecorationGroupGizmo({host,getDraft,getEntities,getView,getContext,allowed,renderer,setDraft,onError}){
  let before=null;
  const available=()=>allowed()&&getDraft()?.enabled===true;
  function axes(){
    if(!available()||getDraft().mode!=='translate')return {};
    let pivot;try{pivot=worldDecorationGroupDisplay(getEntities(),getDraft()).pivot;}catch{return {};}
    const view=getView(),start=renderer().projectPoint(pivot,view),units=Math.max(64,view.camera.distance*.22),result={};if(!start)return result;
    for(const [axis,direction] of Object.entries(sourceOffsetDirections)){
      const end=renderer().projectPoint({x:pivot.x+direction.x*units,y:pivot.y+direction.y*units,z:pivot.z+direction.z*units},view);
      if(end&&Math.hypot(end.x-start.x,end.y-start.y)>=4)result[axis]={start,end,units};
    }return result;
  }
  const options={host,idPrefix:'world-decoration-group',range:'world-delta',
    getContext:()=>JSON.stringify([getContext(),getDraft()?.ids,getDraft()?.sourceKey,getDraft()?.enabled,getDraft()?.mode,getDraft()?.step,getDraft()?.yawStep]),
    onBegin:()=>{before=structuredClone(getDraft().delta);},onPreview:values=>{const delta={...values.offset,yaw_units:getDraft().mode==='yaw'?values.yaw_units:getDraft().delta.yaw_units};worldDecorationGroupDisplay(getEntities(),{...getDraft(),delta});if(!setDraft(delta))throw Error('Decoration group source changed.');},
    onEnd:()=>{before=null;},onCancel:()=>{const prior=before;before=null;if(prior)setDraft(prior,true);},onError};
  function rotation(){
    if(!available()||getDraft().mode!=='yaw')return null;
    let pivot;try{pivot=worldDecorationGroupDisplay(getEntities(),getDraft()).pivot;}catch{return null;}
    const view=getView(),radius=Math.max(64,view.camera.distance*.22),center=renderer().projectPoint(pivot,view),at=angle=>renderer().projectPoint({x:pivot.x+Math.cos(angle)*radius,y:pivot.y,z:pivot.z-Math.sin(angle)*radius},view);
    const points=Array.from({length:64},(_,i)=>at(i*Math.PI/32)),heading=at(getDraft().delta.yaw_units*Math.PI/2048);
    if(!center||!heading||points.some(p=>!p))return null;
    return {center,heading,points,plane:{pivot,radius,width:view.width,height:view.height,matrix:Array.from(renderer().viewMatrix(view))}};
  }
  const translation=mountPlacementGizmo({...options,getAxes:axes,allowed:()=>available()&&getDraft().mode==='translate',getStep:()=>getDraft().step,getValues:()=>({offset:Object.fromEntries(['x','y','z'].map(a=>[a,getDraft().delta[a]])),yaw_units:0})});
  const yaw=mountPlacementYaw({...options,getRotation:rotation,allowed:()=>available()&&getDraft().mode==='yaw',getStep:()=>getDraft().yawStep,getValues:()=>({offset:Object.fromEntries(['x','y','z'].map(a=>[a,getDraft().delta[a]])),yaw_units:getDraft().delta.yaw_units})});
  return {update(){translation.update();yaw.update();},cancel(reason){translation.cancel(reason);yaw.cancel(reason);},isActive:()=>translation.isActive()||yaw.isActive(),dispose(){translation.dispose();yaw.dispose();}};
}

export function worldDecorationDraftPosition(entity,draft){
  if(!entity||entity.placement_scope!=='authored_spawn_seed'||entity.entity_id!==draft?.entityId||!validValues(draft.base)||!validValues(draft.values)||draft.values.yaw_units!==draft.base.yaw_units||!Array.isArray(entity.model_to_scene)||entity.model_to_scene.length!==16||entity.model_to_scene.some(n=>!Number.isFinite(n)))throw Error('Decoration translation requires one qualified Current owner and native offsets.');
  const delta=Object.fromEntries(['x','y','z'].map(axis=>[axis,draft.values.offset[axis]-draft.base.offset[axis]]));
  if(Object.values(delta).every(n=>n===0))return null;
  return {x:entity.model_to_scene[3]+delta.x,y:entity.model_to_scene[7]-delta.y,z:entity.model_to_scene[11]-delta.z};
}

export function worldDecorationDraftTransform(entity,draft){
  if(!validValues(draft?.base)||!validValues(draft?.values)||entity?.source_rotation_psx?.x!==0||entity?.source_rotation_psx?.z!==0||!Number.isSafeInteger(entity.source_rotation_psx.y)||entity.source_rotation_psx.y<0||entity.source_rotation_psx.y>65535||(entity.source_rotation_psx.y&4095)!==draft.base.yaw_units)throw Error('Decoration yaw requires a qualified un-tilted Current native seed.');
  const position=worldDecorationDraftPosition(entity,{...draft,values:{...draft.values,yaw_units:draft.base.yaw_units}})??{x:entity.model_to_scene[3],y:entity.model_to_scene[7],z:entity.model_to_scene[11]};
  if(draft.values.yaw_units===draft.base.yaw_units)return null;
  const angle=draft.values.yaw_units*2*Math.PI/4096,c=Math.cos(angle),s=Math.sin(angle);
  return [c,0,s,position.x,0,-1,0,position.y,-s,0,c,position.z,0,0,0,1];
}

export function mountWorldDecorationGizmo({host,getDraft,getEntity,getView,getContext,allowed,renderer,setDraft,onError}){
  let before=null;
  const available=()=>allowed()&&getDraft()?.enabled===true&&!!getEntity();
  const position=()=>{const draft=getDraft(),entity=getEntity();if(!draft||!entity)return null;return worldDecorationDraftPosition(entity,{...draft,values:{...draft.values,yaw_units:draft.base.yaw_units}})??{x:entity.model_to_scene[3],y:entity.model_to_scene[7],z:entity.model_to_scene[11]};};
  function axes(){
    if(!available()||getDraft().mode!=='translate')return {};
    const pivot=position(),view=getView(),start=renderer().projectPoint(pivot,view),units=Math.max(64,view.camera.distance*.22),result={};
    if(!start)return result;
    for(const [axis,direction] of Object.entries(sourceOffsetDirections)){
      const end=renderer().projectPoint({x:pivot.x+direction.x*units,y:pivot.y+direction.y*units,z:pivot.z+direction.z*units},view);
      if(end&&Math.hypot(end.x-start.x,end.y-start.y)>=4)result[axis]={start,end,units};
    }
    return result;
  }
  const options={host,idPrefix:'world-decoration',
    getContext:()=>JSON.stringify([getContext(),getDraft()?.entityId,getDraft()?.sourceKey,getDraft()?.enabled,getDraft()?.mode,getDraft()?.step,getDraft()?.yawStep]),
    getValues:()=>getDraft().values,onBegin:()=>{before=structuredClone(getDraft().values);},
    onPreview:values=>{if(!setDraft(values))throw Error('Decoration transform source changed.');},
    onEnd:()=>{before=null;},onCancel:()=>{const prior=before;before=null;if(prior)setDraft(prior,true);},onError};
  function rotation(){
    if(!available()||getDraft().mode!=='yaw')return null;
    const pivot=position(),view=getView(),radius=Math.max(64,view.camera.distance*.22),center=renderer().projectPoint(pivot,view),at=angle=>renderer().projectPoint({x:pivot.x+Math.cos(angle)*radius,y:pivot.y,z:pivot.z-Math.sin(angle)*radius},view);
    const points=Array.from({length:64},(_,i)=>at(i*Math.PI/32)),heading=at(getDraft().values.yaw_units*Math.PI/2048);
    if(!center||!heading||points.some(p=>!p))return null;
    return {center,heading,points,plane:{pivot,radius,width:view.width,height:view.height,matrix:Array.from(renderer().viewMatrix(view))}};
  }
  const translation=mountPlacementGizmo({...options,getAxes:axes,getStep:()=>getDraft().step,allowed:()=>available()&&getDraft().mode==='translate'});
  const yaw=mountPlacementYaw({...options,getRotation:rotation,getStep:()=>getDraft().yawStep,allowed:()=>available()&&getDraft().mode==='yaw'});
  return {update(){translation.update();yaw.update();},cancel(reason){translation.cancel(reason);yaw.cancel(reason);},isActive:()=>translation.isActive()||yaw.isActive(),dispose(){translation.dispose();yaw.dispose();}};
}
