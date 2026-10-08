import {MAX_SOURCE_ENTITIES} from './scene-limits.js';
import {mergeScenePlacementSelection} from './scene-placement-selection.js';
import {mountModelPlacementUsers} from './model-placement-users.js';

// Effective initial SDK assignment only. Scripts may choose another runtime clip.
export function animationPlacementIdsForAsset(rows,assetId,eligible,sceneId){
  if(!Array.isArray(rows)||rows.length>MAX_SOURCE_ENTITIES||typeof sceneId!=='string'||!sceneId||typeof assetId!=='string'||!assetId||assetId.length>1024||!(eligible instanceof Set))throw Error('Current animation actor source is unavailable.');
  const seen=new Set(),ids=[];
  for(const row of rows){
    const id=row?.id,assignment=row?.components?.ActorAnimation?.effective;
    if(typeof id!=='string'||!id.startsWith(sceneId+'/actors/')||id.length>1024||seen.has(id)||!assignment||!Object.hasOwn(assignment,'animation_asset_id'))throw Error('Animation users have ambiguous actor identities or missing Current assignments.');
    seen.add(id);const clip=assignment.animation_asset_id;
    if(clip!==null&&(typeof clip!=='string'||!clip||clip.length>1024))throw Error('Current initial clip identity is invalid.');
    if(clip===assetId&&eligible.has(id))ids.push(id);
  }
  return mergeScenePlacementSelection([],ids,eligible);
}

export function mountAnimationPlacementUsers(host,options){
  return mountModelPlacementUsers(host,{...options,kind:'animation',
    resolveIds:context=>animationPlacementIdsForAsset(context.rows,options.assetId,context.eligible,context.sceneId),
    description:'Current initial animation assignments of imported actors in the active authored scene, including hidden actors. NPC drafts, imported usage, shared channel contributions and runtime script-selected clips remain separate.'});
}
