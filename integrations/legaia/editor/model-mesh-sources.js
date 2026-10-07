// Read-only recovery of original inputs retained by reviewed native imports.
import {decodeMeshAnimationPose} from './model-mesh-settings.js';
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const exact=(v,fields)=>object(v)&&Object.keys(v).length===fields.length&&fields.every(k=>Object.hasOwn(v,k));
const integer=(v,low,high)=>Number.isSafeInteger(v)&&v>=low&&v<=high;
const canonical=v=>Array.isArray(v)?v.map(canonical):object(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const fields=['schema_version','asset_id','glb_sha256','byte_length','first_operation','operation_count','operations_sha256','input_sha256','proposed_sha256','recipe','receipt_key'];
function recipe(value){
  const common=['kind','material_colors','scene_index','uv_set','source_scale','source_offset','source_rotation'];
  if(value?.kind==='single'&&Object.hasOwn(value,'animation_pose')){decodeMeshAnimationPose(value.animation_pose);common.push('animation_pose');}
  if(!exact(value,[...common,...(value?.kind==='single'?['donor_face_id','new_group','replace_group','replace_object','preserve_primitives','primitive_index']:['mappings','replace_objects'])])||!['single','batch'].includes(value.kind))throw Error('Invalid retained mesh import settings.');
  const encoded=JSON.stringify(value);if(new TextEncoder().encode(encoded).length>128*1024)throw Error('Retained mesh import settings exceed their budget.');
}
export function decodeMeshSources(value,asset,key){
  if(value?.schema_version!=='legaia.model-mesh-sources.v1'||value.asset_id!==asset||value.project_source_key!==key||!hash(key)||value.project_changed!==false||!Array.isArray(value.imports)||value.imports.length>32)throw Error('Mesh source catalogue differs from Current.');
  const receipts=new Set();let end=0;
  for(const row of value.imports){
    if(!exact(row,fields)||row.asset_id!==asset||row.schema_version!=='legaia.model-mesh-source.v1'||!['glb_sha256','operations_sha256','input_sha256','proposed_sha256','receipt_key'].every(k=>hash(row[k]))||!integer(row.byte_length,28,32*1024*1024)||!integer(row.first_operation,end,65536)||!integer(row.operation_count,1,64)||receipts.has(row.receipt_key))throw Error('Invalid retained mesh source receipt.');
    recipe(row.recipe);receipts.add(row.receipt_key);end=row.first_operation+row.operation_count;
  }
  return structuredClone(value);
}
export async function qualifyMeshSourceDownload(value,asset,key,expected,current){
  decodeMeshSources(value,asset,key);
  const row=value.imports.find(r=>r.receipt_key===expected.receipt_key);
  if(!row||!same(row,expected)||!same(value.selected,expected)||typeof value.content_base64!=='string'||value.content_base64.length>Math.ceil(expected.byte_length/3)*4||!current())throw Error('Downloaded mesh source receipt or Current context changed.');
  const bytes=Uint8Array.from(atob(value.content_base64),c=>c.charCodeAt(0));
  if(bytes.length!==expected.byte_length)throw Error('Downloaded mesh source length changed.');
  const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
  if(digest!==expected.glb_sha256||!current())throw Error('Downloaded mesh source or Current context changed.');
  return {bytes,record:structuredClone(row)};
}
function save(bytes,name,type){const url=URL.createObjectURL(new Blob([bytes],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export async function openMeshSources({assetId,key,current,onError=()=>{}}){
  const dialog=document.createElement('dialog');dialog.className='diagnostic-dialog';
  const heading=document.createElement('h2');heading.textContent='Retained mesh sources';
  const note=document.createElement('p');note.textContent='Original GLBs and import settings from Current native mesh imports. Downloaded settings describe the historical import. Choose Current donors and review again before a new Apply.';
  const status=document.createElement('p');status.role='status';status.textContent='Checking retained inputs…';
  const list=document.createElement('section'),close=document.createElement('button');close.textContent='Close';
  const controller=new AbortController();let pending=false;const buttons=[];
  close.onclick=()=>dialog.close();dialog.onclose=()=>{controller.abort();dialog.remove();};
  dialog.append(heading,note,status,list,close);document.body.append(dialog);dialog.showModal();
  const live=()=>dialog.isConnected&&!controller.signal.aborted&&current();
  async function request(route,extra={}){
    if(!live())throw Error('Current model context changed.');
    const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},signal:controller.signal,body:JSON.stringify({asset_id:assetId,source_key:key,...extra})}),value=await response.json();
    if(!response.ok)throw Error(value.error||'Mesh source recovery failed.');
    if(!live())throw Error('Current model context changed.');return decodeMeshSources(value,assetId,key);
  }
  function controls(){for(const button of buttons)button.disabled=pending||!live();}
  function failure(error){if(dialog.isConnected&&!controller.signal.aborted){status.textContent=error.message;if(live())onError(error);}}
  async function download(row,kind){
    if(pending||!live())return;pending=true;controls();status.textContent='Verifying original GLB and import receipt…';
    try{
      const value=await request('/api/model-mesh-source-download',{receipt_key:row.receipt_key});
      const result=await qualifyMeshSourceDownload(value,assetId,key,row,live);
      if(!live())throw Error('Current model context changed before download.');
      if(kind==='glb')save(result.bytes,`${row.glb_sha256}.glb`,'model/gltf-binary');
      else save(JSON.stringify(kind==='settings'?result.record.recipe:result.record,null,2),`${row.receipt_key}.${kind==='settings'?'settings':'receipt'}.json`,'application/json');
      status.textContent=kind==='glb'?'Original GLB downloaded.':kind==='settings'?'Verified historical import settings downloaded. Choose Current donors and review before reuse.':'Verified import receipt downloaded.';
    }catch(error){failure(error);}
    finally{pending=false;controls();}
  }
  try{
    const value=await request('/api/model-mesh-sources');status.textContent=value.imports.length?`${value.imports.length} retained import(s).`:'No retained original GLBs in Current. Older imports may contain native geometry only.';
    for(const [i,row] of value.imports.entries()){
      const host=document.createElement('section'),label=document.createElement('p'),settings=document.createElement('details'),summary=document.createElement('summary'),code=document.createElement('pre');
      label.textContent=`Import ${i+1} | ${row.recipe.kind} | ${row.byte_length} bytes | GLB ${row.glb_sha256}`;summary.textContent='Import settings';code.textContent=JSON.stringify(row.recipe,null,2);code.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere';settings.append(summary,code);host.append(label,settings);
      for(const [kind,label] of [['glb','Download original GLB'],['settings','Download import settings JSON'],['receipt','Download import receipt']]){const button=document.createElement('button');button.textContent=label;button.onclick=()=>download(row,kind);buttons.push(button);host.append(button);}
      list.append(host);
    }
  }catch(error){failure(error);}
  return dialog;
}
