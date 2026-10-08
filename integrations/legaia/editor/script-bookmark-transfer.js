import {qualifyScriptBookmark} from './script-bookmark-source.js';
export const SCRIPT_BOOKMARK_TRANSFER_BYTES=64*1024;
const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).sort().join('|')===[...keys].sort().join('|');
const name=value=>{if(typeof value!=='string'||!value.trim()||Array.from(value.trim()).length>80||/[\u0000-\u001f\u007f\ud800-\udfff]/u.test(value))throw Error('Bookmark name requires 1–80 printable Unicode characters.');return value.trim();};
function source(value,state,owner,report){
  if(!exact(value,['id','name','scene_id','import_sha256','owner_id','pc','source_record_sha256','mnemonic'])||!/^bookmark:\/\/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(value.id)||!/^scene:\/\/[a-z0-9]{1,12}$/.test(value.scene_id)||!(/^[0-9a-f]{64}$/).test(value.import_sha256)||value.scene_id!==state.scene?.id||value.import_sha256!==state.actor_selection_source_key||typeof owner!=='string'||owner.length>1024||!owner.startsWith(value.scene_id+'/')||typeof value.mnemonic!=='string'||value.mnemonic.length>128)throw Error('Bookmark transfer differs from the current imported scene.');
  qualifyScriptBookmark(value,owner,report);
  return {...value,name:name(value.name)};
}
export function exportScriptBookmark(row,state,owner,report){
  if(!state.script_bookmarks?.some(value=>value.id===row?.id&&value.review_key===row.review_key&&JSON.stringify(value)===JSON.stringify(row)))throw Error('Choose a current saved script bookmark.');
  const {review_key,...saved}=row;
  return {schema_version:'legaia.script-bookmark-transfer.v1',editor_metadata_only:true,source_bookmark:source(saved,state,owner,report)};
}
export function importScriptBookmark(value,state,owner,report,newName){
  if(!exact(value,['schema_version','editor_metadata_only','source_bookmark'])||value.schema_version!=='legaia.script-bookmark-transfer.v1'||value.editor_metadata_only!==true)throw Error('Choose a supported script bookmark transfer.');
  if(new TextEncoder().encode(JSON.stringify(value)).byteLength>SCRIPT_BOOKMARK_TRANSFER_BYTES)throw Error('Bookmark transfer exceeds 64 KiB.');
  const saved=source(value.source_bookmark,state,owner,report),selected=name(newName);
  if(state.script_bookmarks?.some(row=>row.owner_id===owner&&row.name.toLowerCase()===selected.toLowerCase()))throw Error('Choose a distinct bookmark name for this script.');
  return {type:'create_script_bookmark',owner_id:owner,pc:saved.pc,source_record_sha256:saved.source_record_sha256,name:selected};
}
