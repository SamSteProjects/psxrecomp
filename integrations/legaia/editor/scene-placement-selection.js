// Eligibility comes from the active, source-bound scene preview.
export function mergeScenePlacementSelection(current,hits,eligible,extend=false){
  if(!Array.isArray(current)||!Array.isArray(hits)||!(eligible instanceof Set)||typeof extend!=='boolean')throw new Error('Invalid scene placement selection input');
  if([...eligible].some(id=>typeof id!=='string'||!id.length))throw new Error('Invalid scene placement eligibility');
  for(const ids of [current,hits]){
    // Indexed iteration also rejects sparse arrays instead of skipping holes.
    for(let index=0;index<ids.length;index++){
      const id=ids[index];
      if(typeof id!=='string'||!id.length||!eligible.has(id))throw new Error('Select only eligible placements from the active scene');
    }
  }
  const result=[...new Set(extend?[...current,...hits]:hits)].sort();
  if(result.length>128)throw new Error('Select at most 128 scene placements');
  return result;
}

// Toggle only rendered hits; selected placements outside the current view remain.
export function invertScenePlacementSelection(current,hits,eligible){
  mergeScenePlacementSelection(current,[],eligible);mergeScenePlacementSelection(hits,[],eligible);
  const chosen=new Set(current);
  for(const id of new Set(hits)){if(chosen.has(id))chosen.delete(id);else chosen.add(id);}
  return mergeScenePlacementSelection([],Array.from(chosen),eligible);
}

export function scenePlacementSelectionKind(ids,{actors,npcs,decorations}){
  if(![actors,npcs,decorations].every(set=>set instanceof Set))throw new Error('Placement kinds require current SDK identity sets.');
  const eligible=new Set([...actors,...npcs,...decorations]);
  for(const id of eligible)if(Number(actors.has(id))+Number(npcs.has(id))+Number(decorations.has(id))!==1)throw new Error('Placement identity has conflicting SDK kinds.');
  const selected=mergeScenePlacementSelection([],ids,eligible);
  if(!selected.length)return 'empty';
  if(selected.every(id=>actors.has(id)))return 'actors';
  if(selected.every(id=>decorations.has(id)))return 'scenery';
  return 'mixed';
}

// Mirrors the SDK preview allowance: 512 source placements + 128 NPC drafts + terrain.
const MAX_MODEL_SELECTION_PREVIEW_ROWS=641;
// Current SDK model bindings, including hidden/unrenderable placements, not mesh similarity.
export function matchingModelPlacementIds(rows,focus,eligible){
  if(!Array.isArray(rows)||rows.length>MAX_MODEL_SELECTION_PREVIEW_ROWS||!(eligible instanceof Set)||!eligible.has(focus))throw new Error('Choose a current scene placement with a model binding.');
  const seen=new Set();
  for(const row of rows){
    if(!row||typeof row.entity_id!=='string'||!row.entity_id.length||row.entity_id.length>1024||seen.has(row.entity_id)||row.asset_id!=null&&(typeof row.asset_id!=='string'||!row.asset_id.length||row.asset_id.length>1024))throw new Error('Invalid current scene model identities.');
    seen.add(row.entity_id);
  }
  const model=rows.find(row=>row.entity_id===focus)?.asset_id;
  if(typeof model!=='string'||!model.length)throw new Error('The selected placement has no qualified model binding.');
  return mergeScenePlacementSelection([],rows.filter(row=>row.asset_id===model&&eligible.has(row.entity_id)).map(row=>row.entity_id),eligible);
}
