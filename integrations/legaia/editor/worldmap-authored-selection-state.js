import {placementDigest} from './worldmap-placement-replay.js';
import {nativeWorldPlacementMatches as same} from './worldmap-current-placements.js';
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===[...keys].sort().join(',');
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
export async function qualifyAuthoredWorldSelectionReview(value,saved,source){
  const metadata=source.metadata,{review_key,...entry}=saved;
  if(!exact(value,['schema_version','read_only','source_key','selection','review_key'])||value.schema_version!=='legaia.worldmap-authored-selection-review.v1'||value.read_only!==true||
      value.source_key!==metadata.source_key||value.review_key!==review_key||!same(value.selection,entry)||
      !exact(entry,['schema_version','id','name','scene','source_record','placement_ids','bindings'])||entry.schema_version!=='legaia.worldmap-authored-selection.v1'||
      typeof entry.id!=='string'||!/^worldmap-selection:\/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(entry.id)||
      typeof entry.name!=='string'||[...entry.name].length<1||[...entry.name].length>80||entry.name.trim()!==entry.name||
      entry.scene!==metadata.scene||!same(entry.source_record,metadata.source_record)||!Array.isArray(entry.placement_ids)||entry.placement_ids.length<1||entry.placement_ids.length>32||
      entry.placement_ids.some(id=>typeof id!=='string'||!/^placement:\/\/authored\/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(id))||
      !same(entry.placement_ids,[...new Set(entry.placement_ids)].sort())||!exact(entry.bindings,entry.placement_ids))throw Error('Saved authored group differs from its fresh source and canonical membership.');
  for(const id of entry.placement_ids){
    const matches=metadata.authored_allocations.filter(a=>a.placement_id===id),binding=entry.bindings[id];
    if(matches.length!==1||!exact(binding,['record_index','entity_id'])||binding.record_index!==matches[0].record_index||
        binding.entity_id!==`scene://${entry.scene}/worldmap/authored-placements/${id.split('/').pop()}`)throw Error('Saved authored group member was removed or changed native ownership.');
  }
  const digest=await placementDigest(new TextEncoder().encode(JSON.stringify(canonical({project_root:metadata.project_path,worldmap_selection:entry}),null,2)+'\n'));
  if(digest!==review_key)throw Error('Saved authored group metadata digest changed.');
  return entry.placement_ids.slice();
}
