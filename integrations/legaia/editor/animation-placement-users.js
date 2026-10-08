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

export function draftAnimationPlacementIds(bindings,references,drafts,sceneId,eligible){
  if(!Array.isArray(bindings)||bindings.length>MAX_SOURCE_ENTITIES||!Array.isArray(references)||references.length>2048||!drafts||typeof drafts!=='object'||Array.isArray(drafts)||Object.keys(drafts).length>128||typeof sceneId!=='string'||!sceneId||!(eligible instanceof Set))throw Error('NPC initial animation evidence is unavailable.');
  const pairs=new Set();
  for(const binding of bindings){
    if(typeof binding?.actor_semantic_id!=='string'||!binding.actor_semantic_id.startsWith(sceneId+'/actors/')||typeof binding.model_asset_semantic_id!=='string'||!binding.model_asset_semantic_id||!Number.isInteger(binding.initial_animation_id)||binding.initial_animation_id<1||binding.initial_animation_id>255)throw Error('NPC animation catalog binding is unresolved.');
    const pair=JSON.stringify([binding.actor_semantic_id,binding.model_asset_semantic_id]);if(pairs.has(pair))throw Error('NPC animation catalog binding is duplicated.');pairs.add(pair);
  }
  const seen=new Set(),ids=[];
  for(const ref of references){
    if(ref?.kind!=='draft_initial_model_assignment'||ref.scene_id!==sceneId)continue;
    const draft=drafts[ref.source_id],donor=draft?.appearance?.donor_entity_id??draft?.donor_entity_id;
    if(typeof ref.source_id!=='string'||!ref.source_id.startsWith('authored-actor://')||seen.has(ref.source_id)||draft?.scene_id!==sceneId||ref.effective!==true||ref.imported!==false||ref.runtime_binding!=='not_asserted'||ref.effective_donor_id!==donor||typeof ref.target_id!=='string'||!ref.target_id)throw Error('NPC animation reference differs from its current retail witness.');
    seen.add(ref.source_id);
    if(pairs.has(JSON.stringify([donor,ref.target_id]))&&eligible.has(ref.source_id))ids.push(ref.source_id);
  }
  return mergeScenePlacementSelection([],ids,eligible);
}

export function currentAnimationPlacementIds(context,assetId){
  const imported=animationPlacementIdsForAsset(context.rows,assetId,context.eligible,context.sceneId);
  const drafts=draftAnimationPlacementIds(context.bindings??[],context.references??[],context.drafts??{},context.sceneId,context.eligible);
  return mergeScenePlacementSelection([],imported.concat(drafts),context.eligible);
}

export function mountAnimationPlacementUsers(host,options){
  return mountModelPlacementUsers(host,{...options,kind:'animation',
    resolveIds:context=>currentAnimationPlacementIds(context,options.assetId),
    description:'Current initial animation assignments of imported actors and verified NPC draft retail witnesses in the active authored scene, including hidden actors. Imported usage, shared channel contributions and runtime script-selected clips remain separate.'});
}
