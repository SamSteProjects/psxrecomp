import {modelPlacementIdsForAsset} from './scene-placement-selection.js';

// Asset Details owns the record; this adapter owns only the local selection action.
export function mountModelPlacementUsers(host,{assetId,getContext,current,busy,onSelect,onError}){
  const button=host.ownerDocument.createElement('button'),note=host.ownerDocument.createElement('p');
  button.type='button';button.dataset.selectCurrentModelPlacements='';
  note.className='field-note';note.textContent='Current SDK model bindings in the active authored scene, including hidden placements and NPC drafts. Initial imported usage remains separate; gameplay use is unverified.';
  host.append(button,note);
  let disposed=false,pending=false;
  function snapshot(){
    if(disposed||busy()||!current())return null;
    const context=getContext();if(!context)return null;
    if(['projectPath','sceneId','sourceKey','projectSourceKey'].some(key=>typeof context[key]!=='string'||!context[key]))throw new Error('Current model placement source is unavailable.');
    const ids=modelPlacementIdsForAsset(context.rows,assetId,context.eligible);
    return {ids,key:JSON.stringify([context.projectPath,context.sceneId,context.sourceKey,context.projectSourceKey,ids])};
  }
  function synchronize(){
    button.disabled=true;button.textContent='Select current scene placements';button.title='Requires a current authored scene and fresh Asset Details context.';
    try{const value=snapshot();if(value){button.textContent=`Select current scene placements (${value.ids.length})`;button.disabled=pending||!value.ids.length;button.title=value.ids.length?'Select exact current model users for existing placement tools.':'No eligible current scene placements use this SDK model identity.';}}catch(error){button.title=error.message;}
  }
  button.onclick=async()=>{
    if(disposed||pending||button.disabled)return;
    try{
      const value=snapshot();if(!value?.ids.length)return;
      pending=true;synchronize();
      const held=()=>{try{return !disposed&&snapshot()?.key===value.key;}catch{return false;}};
      await onSelect(value.ids.slice(),held);
    }catch(error){if(!disposed&&current())onError(error);}finally{pending=false;synchronize();}
  };
  synchronize();return {synchronize,dispose(){disposed=true;button.disabled=true;}};
}
