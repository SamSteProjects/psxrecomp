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
