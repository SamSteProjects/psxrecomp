import {modelGlbContext} from './model-glb.js';
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v),hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
export function decodeModelSources(value,request){
  if(!object(value)||value.schema_version!=='legaia.model-sources.v1'||value.asset_id!==request.asset_id||typeof value.scene_id!=='string'||!/^scene:\/\/[A-Za-z0-9_-]{1,128}$/.test(value.scene_id)||value.project_source_key!==request.expected_source_key||!Array.isArray(value.imports)||value.imports.length>32||value.project_changed!==false||value.historical_inputs!==true)throw new Error('Model input recovery context changed.');
  const seen=new Set();
  for(const row of value.imports){
    if(!object(row)||row.schema_version!=='legaia.model-source.v1'||row.asset_id!==request.asset_id||row.scene_id!==value.scene_id||!hash(row.receipt_key)||seen.has(row.receipt_key)||!hash(row.glb_sha256)||!hash(row.candidate_sha256)||!hash(row.review_key)||!Number.isSafeInteger(row.byte_length)||row.byte_length<28||row.byte_length>32*1024*1024||!object(row.binding)||row.binding.asset_id!==row.asset_id||row.binding.scene_id!==row.scene_id||new TextEncoder().encode(JSON.stringify(row.binding)).length>128*1024)throw new Error('Invalid retained model input receipt.');seen.add(row.receipt_key);
  }
  return structuredClone(value);
}
export function decodeModelSourceRemoval(value,request,record,projectPath){
  if(!object(value)||value.schema_version!=='legaia.model-source-removal.v1'||value.asset_id!==request.asset_id||value.project_source_key!==request.expected_source_key||value.scene_id!==record.scene_id||value.project_path!==projectPath||value.receipt_key!==record.receipt_key||value.glb_sha256!==record.glb_sha256||!hash(value.review_key)||!hash(value.collection_key)||!hash(value.native_key)||value.native_content_changed!==false||value.source_file_deleted!==false||!Number.isSafeInteger(value.receipt_count_before)||value.receipt_count_before<1||value.receipt_count_before>32||value.receipt_count_after!==value.receipt_count_before-1||!Number.isSafeInteger(value.shared_blob_receipts)||value.shared_blob_receipts<1||value.shared_blob_receipts>value.receipt_count_before||value.registered_bytes_released!==(value.shared_blob_receipts===1?record.byte_length:0))throw new Error('Model source removal differs from its reviewed receipt.');
  return structuredClone(value);
}
function download(content,type,name){let url,link;try{url=URL.createObjectURL(new Blob([content],{type}));link=el('a');link.href=url;link.download=name;document.body.append(link);link.click();}finally{link?.remove();if(url)URL.revokeObjectURL(url);}}
export async function openModelSources({assetId,getContext,busy,setBusy,onError=()=>{},onApplied=null}){
  const captured=modelGlbContext(getContext()),request={asset_id:assetId,expected_source_key:captured.sourceKey};
  const dialog=el('dialog');dialog.id='model-source-dialog';dialog.className='project-dialog';Object.assign(dialog.style,{width:'min(760px,94vw)',maxHeight:'90vh',overflowY:'auto'});
  const list=el('div'),status=el('p','Verifying original model inputs…'),error=el('p'),close=el('button','Close model inputs');close.type='button';error.setAttribute('role','alert');status.setAttribute('role','status');
  dialog.append(el('h2','Retained model inputs'),el('p','Historical external authoring inputs. Recover the original GLB, binding and receipt for editing. Export a fresh binding and Review before applying again; an old receipt cannot authorize replay.'),list,status,error,close);document.body.append(dialog);
  let closed=false,pending=false,controller=null,owner=null,removing=false;const controls=[];
  const current=()=>{try{return !closed&&same(captured,modelGlbContext(getContext()));}catch{return false;}};
  const update=()=>{for(const n of controls)n.disabled=pending||!current()||busy()!==false;close.disabled=removing;};
  function release(token){if(owner===token){owner=null;setBusy(false);}}
  function dispose(){if(closed||removing)return;closed=true;controller?.abort();if(owner)release(owner);if(dialog.open)dialog.close();dialog.remove();}
  async function post(route,body,signal){const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),value=await response.json();if(!response.ok||value?.error)throw new Error(value?.error??'Model input recovery failed.');return value;}
  async function run(work){if(!current()||pending||busy()!==false)return false;const token={};pending=true;owner=token;setBusy(true);controller=new AbortController();const signal=controller.signal;error.textContent='';update();try{return await work(signal);}catch(e){if(current()&&e?.name!=='AbortError'){error.textContent=e.message??String(e);onError(e);}return false;}finally{pending=false;controller=null;release(token);update();}}
  async function recover(record,part){return run(async signal=>{
    const response=await post('/api/model-source-download',{...request,receipt_key:record.receipt_key},signal);if(!current())return false;
    const value=decodeModelSources(response,request);if(!same(value.selected,record)||!value.imports.some(row=>same(row,record))||typeof value.glb_base64!=='string'||value.glb_base64.length>44739244)throw new Error('Recovered model input differs from its receipt.');
    const bytes=Uint8Array.from(atob(value.glb_base64),c=>c.charCodeAt(0));if(bytes.length!==record.byte_length)throw new Error('Recovered model input size changed.');
    const actual=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');if(!current())return false;if(actual!==record.glb_sha256)throw new Error('Recovered model input hash changed.');
    const prefix='model-input-'+record.receipt_key.slice(0,12);
    if(part==='glb')download(bytes,'model/gltf-binary',prefix+'.glb');else download(JSON.stringify(part==='binding'?record.binding:record,null,2)+'\n','application/json',prefix+(part==='binding'?'.binding.json':'.receipt.json'));
    status.textContent='Original model input verified and downloaded. Export a fresh binding before applying.';return true;
  });}
  close.onclick=dispose;dialog.oncancel=event=>{if(removing)event.preventDefault();else dispose();};dialog.onclose=dispose;dialog.showModal();
  const ready=run(async signal=>{const response=await post('/api/model-sources',request,signal);if(!current())return false;const value=decodeModelSources(response,request);if(value.scene_id!==captured.sceneId)throw new Error('Model input scene changed.');
    for(const record of value.imports){const section=el('section');section.append(el('p',`${record.glb_sha256.slice(0,12)} · ${record.byte_length} bytes · native result ${record.candidate_sha256.slice(0,12)}`));
      if(record.binding.external_object_nodes)section.append(el('p',`Original object mapping: ${record.binding.external_object_nodes.join(', ')}`));
      for(const [part,label] of [['glb','Download original model GLB'],['binding','Download original model binding'],['receipt','Download model import receipt']]){const button=el('button',label);button.type='button';button.onclick=()=>recover(record,part);controls.push(button);section.append(button);}
      if(typeof onApplied==='function'){
        let reviewed=null;const review=el('button','Review model input removal'),apply=el('button','Remove reviewed model input'),details=el('p');review.type=apply.type='button';apply.hidden=true;
        review.onclick=()=>run(async signal=>{reviewed=null;apply.hidden=true;const value=await post('/api/model-source-removal-review',{...request,receipt_key:record.receipt_key},signal);if(!current())return false;reviewed=decodeModelSourceRemoval(value,request,record,captured.projectPath);details.textContent=`Remove this receipt from Current: ${value.receipt_count_before} → ${value.receipt_count_after} receipts, ${value.registered_bytes_released} registered bytes freed. The native model and original GLB file stay intact. Undo restores the receipt.`;apply.hidden=false;return true;});
        apply.onclick=()=>{const held=reviewed;if(!held)return false;return run(async signal=>{removing=true;update();try{const value=await post('/api/model-source-remove',{...request,receipt_key:record.receipt_key,review_key:held.review_key},signal);if(!current()||reviewed!==held)return false;if(!object(value?.project)||value.project.mode!=='edit')throw new Error('Model input removal returned invalid project state.');reviewed=null;removing=false;await onApplied(value);dispose();return true;}catch(error){reviewed=null;apply.hidden=true;throw error;}finally{removing=false;update();}});};
        controls.push(review,apply);section.append(review,apply,details);
      }list.append(section);
    }status.textContent=value.imports.length?`${value.imports.length} historical model input receipts.`:'No retained model inputs for this asset.';return true;});
  return {dialog,ready,dispose};
}
