import {animationGlbContext} from './animation-glb.js';
import {decodeAnimationRecordLibrary} from './animation-record-library.js';

const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const assignment=actor=>actor?.components?.ActorAllocatedAnimation?.authored??null;

// Resolve only the assigned UUID. A retained capture may belong to another
// actor sharing the same model, so donor actor identity is not the target.
export async function resolveActorAnimationGlbTarget({entityId,getActor,getContext,fetcher=fetch}){
  const context=animationGlbContext(getContext()),actor=getActor();
  if(actor?.id!==entityId)throw new Error('Selected actor changed. Reopen animation GLB editing.');
  const captured=structuredClone(assignment(actor));
  if(captured===null)return null;
  const keys=['model_asset_id','record_id','record_sha256','scene_id'];
  if(typeof captured!=='object'||Array.isArray(captured)||!same(Object.keys(captured).sort(),keys)||captured.scene_id!==context.sceneId)
    throw new Error('Allocated animation assignment is invalid for this scene.');
  const response=await fetcher('/api/animation-record-library',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene_id:context.sceneId,expected_source_key:context.sourceKey})});
  const value=await response.json();
  if(!same(context,animationGlbContext(getContext()))||getActor()?.id!==entityId||!same(captured,assignment(getActor())))
    throw new Error('Actor, assignment or source changed. Reopen animation GLB editing.');
  if(!response.ok||value?.error)throw new Error(value?.error??'Could not verify assigned animation.');
  const library=decodeAnimationRecordLibrary(value,context),row=library.records.find(row=>row.record_id===captured.record_id);
  if(!row?.active||row.record_sha256!==captured.record_sha256||row.donor_asset_id!==captured.model_asset_id)
    throw new Error('Assigned clip differs from the current retained library. Reopen animation GLB editing.');
  return row;
}
