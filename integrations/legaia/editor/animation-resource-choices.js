import {MAX_SOURCE_ENTITIES} from './scene-limits.js';

// Catalog witnesses qualify the pairing; SDK components choose its initial layer.
export function animationResourceChoices(record,actors){
 if(record?.type!=='animation'||typeof record.id!=='string'||!record.id.startsWith('animation://')||typeof record.sceneId!=='string'||!Array.isArray(record.data?.bindings)||!Array.isArray(actors)||actors.length>MAX_SOURCE_ENTITIES)throw Error('Animation assignment preview requires current SDK actors and catalog bindings.');
 const choices=[],seen=new Set(),bindings=record.data.bindings;
 for(const actor of actors){
  if(typeof actor?.id!=='string'||!actor.id.startsWith(record.sceneId+'/actors/')||seen.has(actor.id))throw Error('Animation assignment preview has ambiguous source actors.');
  seen.add(actor.id);const appearance=actor.components?.ActorAppearance,animation=actor.components?.ActorAnimation;
  if(!appearance||!animation)continue;
  const witnessed=(id,asset)=>typeof asset==='string'&&bindings.some(binding=>binding.actor_semantic_id===id&&binding.model_asset_semantic_id===asset);
  const entity={id:actor.id,name:actor.name},retail=animation.imported?.animation_asset_id===record.id&&witnessed(actor.id,appearance.imported?.asset_id);
  const current=animation.effective?.animation_asset_id===record.id&&animation.effective?.source_kind!=='allocated_record'&&witnessed(animation.effective?.donor_entity_id,appearance.effective?.asset_id);
  const currentClip=animation.authored?.animation_asset_id?'authored-initial-animation':appearance.authored?.donor_entity_id?'authored-appearance':'scene-header';
  if(retail)choices.push({key:actor.id+'|retail',entity,assetId:appearance.imported.asset_id,clipId:'scene-header',layer:current&&currentClip==='scene-header'&&appearance.imported.asset_id===appearance.effective.asset_id?'Retail + Current initial':'Retail initial'});
  if(current&&!(retail&&currentClip==='scene-header'&&appearance.imported.asset_id===appearance.effective.asset_id))choices.push({key:actor.id+'|current',entity,assetId:appearance.effective.asset_id,clipId:currentClip,layer:'Current initial'});
 }
 return choices;
}
