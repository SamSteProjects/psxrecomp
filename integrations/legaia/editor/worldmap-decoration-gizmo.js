import {mountPlacementGizmo,sourceOffsetDirections} from './worldmap-placement-gizmo.js';
import {validValues} from './worldmap-placement-state.js';

export function worldDecorationDraftPosition(entity,draft){
  if(!entity||entity.placement_scope!=='authored_spawn_seed'||entity.entity_id!==draft?.entityId||!validValues(draft.base)||!validValues(draft.values)||draft.values.yaw_units!==draft.base.yaw_units||!Array.isArray(entity.model_to_scene)||entity.model_to_scene.length!==16||entity.model_to_scene.some(n=>!Number.isFinite(n)))throw Error('Decoration translation requires one qualified Current owner and native offsets.');
  const delta=Object.fromEntries(['x','y','z'].map(axis=>[axis,draft.values.offset[axis]-draft.base.offset[axis]]));
  if(Object.values(delta).every(n=>n===0))return null;
  return {x:entity.model_to_scene[3]+delta.x,y:entity.model_to_scene[7]-delta.y,z:entity.model_to_scene[11]-delta.z};
}

export function mountWorldDecorationGizmo({host,getDraft,getEntity,getView,getContext,allowed,renderer,setDraft,onError}){
  let before=null;
  const available=()=>allowed()&&getDraft()?.enabled===true&&!!getEntity();
  const position=()=>{const draft=getDraft(),entity=getEntity();if(!draft||!entity)return null;return worldDecorationDraftPosition(entity,draft)??{x:entity.model_to_scene[3],y:entity.model_to_scene[7],z:entity.model_to_scene[11]};};
  function axes(){
    if(!available())return {};
    const pivot=position(),view=getView(),start=renderer().projectPoint(pivot,view),units=Math.max(64,view.camera.distance*.22),result={};
    if(!start)return result;
    for(const [axis,direction] of Object.entries(sourceOffsetDirections)){
      const end=renderer().projectPoint({x:pivot.x+direction.x*units,y:pivot.y+direction.y*units,z:pivot.z+direction.z*units},view);
      if(end&&Math.hypot(end.x-start.x,end.y-start.y)>=4)result[axis]={start,end,units};
    }
    return result;
  }
  return mountPlacementGizmo({host,idPrefix:'world-decoration',getAxes:axes,
    getContext:()=>JSON.stringify([getContext(),getDraft()?.entityId,getDraft()?.sourceKey,getDraft()?.enabled,getDraft()?.step]),
    getValues:()=>getDraft().values,getStep:()=>getDraft().step,allowed:available,
    onBegin:()=>{before=structuredClone(getDraft().values);},
    onPreview:values=>{if(!setDraft(values))throw Error('Decoration translation source changed.');},
    onEnd:()=>{before=null;},onCancel:()=>{const prior=before;before=null;if(prior)setDraft(prior,true);},onError});
}
