/** Import readiness is structural metadata qualification, never runtime proof. */
export function decodeSceneCatalog(value,offset,prefix,limit=16){
 const int=(n,max)=>Number.isInteger(n)&&n>=0&&n<=max,fail=()=>{throw new Error('Invalid scene import readiness response.');};
 if(value?.schema_version!=='legaia.scene-catalog.v2'||value.qualification!=='metadata_import_not_rendering_or_gameplay'||value.offset!==offset||value.limit!==limit||!int(offset,65536)||!int(limit,128)||!limit||typeof prefix!=='string'||value.source?.serial!=='SCUS-94254'||!/^sha256:[a-f0-9]{64}$/.test(value.source.disc_identity)||!Array.isArray(value.scenes)||!Array.isArray(value.unsupported_blocks)||!int(value.total_blocks,65536)||offset>value.total_blocks&&value.scanned_blocks!==0||!int(value.scanned_blocks,limit)||value.scanned_blocks!==Math.min(limit,Math.max(0,value.total_blocks-offset))||value.scenes.length+value.unsupported_blocks.length!==value.scanned_blocks||value.next_offset!==(offset+value.scanned_blocks<value.total_blocks?offset+value.scanned_blocks:null))fail();
 const names=new Set();
 for(const row of [...value.scenes,...value.unsupported_blocks]){
  if(typeof row?.name!=='string'||!row.name.startsWith(prefix)||!row.name.length||row.name.length>128||names.has(row.name))fail();names.add(row.name);
 }
 for(const row of value.scenes){
  if(row.semantic_id!=='scene://'+row.name||row.placement_status!=='supported'||!['descriptor_man','raw_streaming_man'].includes(row.man_source_kind)||!int(row.actor_count,8192)||!int(row.prot_entry_start,65536)||!int(row.prot_entry_end_exclusive,65536)||row.prot_entry_end_exclusive<=row.prot_entry_start||!int(row.bundle_entry,65536)||row.bundle_entry<row.prot_entry_start||row.bundle_entry>=row.prot_entry_end_exclusive)fail();
  if(row.import_status==='supported'){
   if(row.import_reason!==null||!int(row.scene_model_count,65536)||!int(row.global_model_count,65536)||!row.global_model_count||!int(row.unresolved_actor_model_count,row.actor_count)||row.model_resolution_status!==(row.unresolved_actor_model_count?'unresolved':'resolved'))fail();
  }else if(row.import_status!=='unsupported'||typeof row.import_reason!=='string'||!row.import_reason||row.model_resolution_status!=='unavailable'||[row.scene_model_count,row.global_model_count,row.unresolved_actor_model_count].some(n=>n!==null))fail();
 }
 for(const row of value.unsupported_blocks)if(typeof row.reason!=='string'||!row.reason)fail();
 return structuredClone(value);
}
