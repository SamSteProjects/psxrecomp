import {decodeMeshSources,qualifyMeshSourceDownload} from './model-mesh-sources.js';
import {decodeMeshSettings} from './model-mesh-settings.js';
const el=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;};
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const fail=message=>{throw Error(message);};
export function decodeMeshLibrary(value,path){
  const fields=['schema_version','project_path','mode','library_key','imports','receipt_count','distinct_glb_count','registered_byte_length','project_changed','historical_inputs','selected','content_base64'];
  if(!value||Object.keys(value).some(k=>!fields.includes(k))||value.schema_version!=='legaia.mesh-source-library.v1'||value.project_path!==path||!hash(value.library_key)||!['edit','live'].includes(value.mode)||value.project_changed!==false||value.historical_inputs!==true||!Array.isArray(value.imports)||value.imports.length>128||value.receipt_count!==value.imports.length)fail('Mesh input library differs from Current project.');
  const groups=new Map(),seen=new Set(),sizes=new Map();
  for(const row of value.imports){
    if(!row||Object.keys(row).sort().join(',')!=='receipt,scene_id'||typeof row.scene_id!=='string'||!/^scene:\/\/[a-z0-9_]+$/.test(row.scene_id)||row.scene_id.length>160||typeof row.receipt?.asset_id!=='string'||!row.receipt.asset_id.startsWith(`asset://${row.scene_id.slice(8)}/models/`))fail('Mesh input source owner differs from its scene.');
    const r=row.receipt;if(seen.has(r.receipt_key))fail('Duplicate mesh input receipt.');seen.add(r.receipt_key);decodeMeshSettings(r.recipe);
    if(sizes.has(r.glb_sha256)&&sizes.get(r.glb_sha256)!==r.byte_length)fail('Conflicting mesh input lengths.');sizes.set(r.glb_sha256,r.byte_length);
    if(!groups.has(r.asset_id))groups.set(r.asset_id,[]);groups.get(r.asset_id).push(r);
  }
  for(const [asset,imports] of groups)decodeMeshSources({schema_version:'legaia.model-mesh-sources.v1',asset_id:asset,project_source_key:value.library_key,imports,project_changed:false},asset,value.library_key);
  const total=[...sizes.values()].reduce((a,b)=>a+b,0);if(total>64*1024*1024||value.registered_byte_length!==total||value.distinct_glb_count!==sizes.size)fail('Mesh input library budget or totals changed.');
  return structuredClone(value);
}
export function filterMeshLibrary(rows,search='',scene=''){
  const terms=search.toLowerCase().trim().split(/\s+/).filter(Boolean);
  return rows.filter(row=>(!scene||scene===row.scene_id)&&terms.every(term=>[row.scene_id,row.receipt.asset_id,row.receipt.glb_sha256,row.receipt.receipt_key,row.receipt.recipe.kind].join(' ').toLowerCase().includes(term)));
}
export async function qualifyMeshLibraryDownload(value,catalog,record,current){
  const fresh=decodeMeshLibrary(value,catalog.project_path);
  if(!current()||fresh.mode!==catalog.mode||fresh.library_key!==catalog.library_key||!same(value.selected,record)||!fresh.imports.some(row=>same(row,record)))fail('Mesh input library changed before recovery.');
  const asset=record.receipt.asset_id;
  return qualifyMeshSourceDownload({schema_version:'legaia.model-mesh-sources.v1',asset_id:asset,project_source_key:fresh.library_key,imports:fresh.imports.filter(row=>row.receipt.asset_id===asset).map(row=>row.receipt),selected:value.selected.receipt,content_base64:value.content_base64,project_changed:false},asset,fresh.library_key,record.receipt,current);
}
export function decodeMeshComparison(value,catalog,row){
  const fields=['schema_version','project_path','library_key','receipt_key','scene_id','asset_id','historical_candidate_sha256','current_sha256','current_byte_length','matches_current','imported_face_count','active_imported_face_count','retired_imported_face_count','comparison_scope','face_content_match_asserted','project_changed','native_content_changed','gameplay_verified'];
  const count=v=>Number.isSafeInteger(v)&&v>=0&&v<=512;
  if(!value||Object.keys(value).length!==fields.length||fields.some(k=>!Object.hasOwn(value,k))||value.schema_version!=='legaia.mesh-source-native-comparison.v1'||value.project_path!==catalog.project_path||value.library_key!==catalog.library_key||value.receipt_key!==row.receipt.receipt_key||value.scene_id!==row.scene_id||value.asset_id!==row.receipt.asset_id||value.historical_candidate_sha256!==row.receipt.proposed_sha256||!hash(value.current_sha256)||!Number.isSafeInteger(value.current_byte_length)||value.current_byte_length<1||value.current_byte_length>4*1024*1024||value.matches_current!==(value.current_sha256===row.receipt.proposed_sha256)||!count(value.imported_face_count)||value.imported_face_count<1||!count(value.active_imported_face_count)||!count(value.retired_imported_face_count)||value.active_imported_face_count+value.retired_imported_face_count!==value.imported_face_count||value.matches_current&&value.retired_imported_face_count!==0||value.comparison_scope!=='complete_native_model_and_imported_face_lifetime'||value.face_content_match_asserted!==false||value.project_changed!==false||value.native_content_changed!==false||value.gameplay_verified!==false)fail('Mesh comparison differs from the Current source and import receipt.');
  return structuredClone(value);
}
export async function navigateMeshSource({record,catalog,getState,readLibrary,changeScene,openModel,busy=()=>false}){
  const held=structuredClone(record),path=catalog.project_path,mode=catalog.mode,key=catalog.library_key;
  const current=()=>getState().project?.path===path&&getState().project?.mode===mode;
  const qualify=async()=>{if(busy()||!current())fail('Project changed before mesh input navigation.');const fresh=decodeMeshLibrary(await readLibrary(path),path);if(!current()||fresh.mode!==mode||fresh.library_key!==key||!fresh.imports.some(row=>same(row,held)))fail('Mesh input changed. Refresh the library.');};
  await qualify();if(getState().scene?.id!==held.scene_id&&!await changeScene(held.scene_id))fail('Mesh input source scene could not be opened.');await qualify();
  const state=getState();if(busy()||!current()||state.scene?.id!==held.scene_id||!state.assets?.some(asset=>asset.id===held.receipt.asset_id))fail('Mesh input target is absent from its source scene.');
  await openModel(held.receipt.asset_id,state.model_overrides?.[held.receipt.asset_id]?'authored':'imported');return true;
}
function save(content,type,name){let url,link;try{url=URL.createObjectURL(new Blob([content],{type}));link=el('a');link.href=url;link.download=name;document.body.append(link);link.click();}finally{link?.remove();if(url)URL.revokeObjectURL(url);}}
export function mountMeshSourceLibrary({after,...options}){const button=el('button','Project mesh inputs');button.id='project-mesh-inputs';after.after(button);button.onclick=()=>openMeshSourceLibrary(options);return {button};}
export async function openMeshSourceLibrary({getState,busy=()=>false,setBusy=()=>{},onOpen=null,onError=()=>{}}){
  const path=getState().project?.path,mode=getState().project?.mode;if(typeof path!=='string'||!path||busy())return false;
  const dialog=el('dialog');dialog.id='mesh-source-library-dialog';dialog.className='project-dialog';Object.assign(dialog.style,{width:'min(900px,94vw)',maxHeight:'90vh',overflowY:'auto'});
  const status=el('p','Verifying retained mesh inputs…'),error=el('p'),search=el('input'),scene=el('select'),refresh=el('button','Refresh mesh inputs'),close=el('button','Close mesh inputs'),list=el('div');status.setAttribute('role','status');error.setAttribute('role','alert');search.setAttribute('aria-label','Search mesh inputs');search.placeholder='Scene, model, single/batch or hash';scene.setAttribute('aria-label','Mesh input scene');
  dialog.append(el('h2','Project mesh inputs'),el('p','Original GLBs and settings retained by native mesh imports across project scenes. Historical settings are editable input: choose Current donors and obtain a fresh Review before applying again.'),search,scene,refresh,status,error,list,close);document.body.append(dialog);
  let closed=false,pending=false,controller=null,catalog=null,ownedBusy=false;const controls=[];
  const current=()=>!closed&&getState().project?.path===path&&getState().project?.mode===mode;
  function release(){if(ownedBusy){ownedBusy=false;setBusy(false);}}
  function update(){for(const node of [...controls,search,scene,refresh])node.disabled=pending||!current()||busy();}
  function dispose(){if(closed)return;closed=true;controller?.abort();release();dialog.remove();}
  async function post(route,body,signal){const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),value=await response.json();if(!response.ok||value.error)fail(value.error??'Mesh input request failed.');return value;}
  async function run(work,ownBusy=true){if(pending||busy()||!current())return false;pending=true;controller=new AbortController();if(ownBusy){ownedBusy=true;setBusy(true);}error.textContent='';update();try{return await work(controller.signal);}catch(cause){if(!closed&&current()&&cause.name!=='AbortError'){error.textContent=cause.message;onError(cause);}return false;}finally{pending=false;controller=null;release();if(!closed)update();}}
  function render(){list.replaceChildren();controls.length=0;const rows=filterMeshLibrary(catalog.imports,search.value,scene.value);status.textContent=`${rows.length} of ${catalog.receipt_count} receipts · ${catalog.distinct_glb_count} distinct GLBs · ${catalog.registered_byte_length.toLocaleString()} bytes. No project change.`;
    for(const row of rows){const r=row.receipt,card=el('section');card.style.cssText='border-top:1px solid #405650;padding:12px 0;overflow-wrap:anywhere';card.append(el('h3',`${row.scene_id} · ${r.asset_id}`),el('p',`${r.recipe.kind} import · ${r.byte_length.toLocaleString()} bytes · native operations ${r.first_operation}–${r.first_operation+r.operation_count-1}`),el('p',`GLB SHA-256: ${r.glb_sha256}`));
      for(const [kind,label] of [['glb','Download original GLB'],['settings','Download import settings JSON'],['receipt','Download import receipt']]){const button=el('button',label);controls.push(button);card.append(button);button.onclick=()=>run(async signal=>{const value=await post('/api/mesh-library-download',{expected_project_path:path,expected_library_key:catalog.library_key,receipt_key:r.receipt_key},signal),qualified=await qualifyMeshLibraryDownload(value,catalog,row,current);if(!current())return false;const stem=`mesh-${r.glb_sha256.slice(0,12)}-${r.receipt_key.slice(0,12)}`;if(kind==='glb')save(qualified.bytes,'model/gltf-binary',stem+'.glb');else save(JSON.stringify(kind==='settings'?qualified.record.recipe:qualified.record,null,2),'application/json',stem+`-${kind}.json`);return true;});}
      const comparison=el('p'),compare=el('button','Compare Current native model');comparison.setAttribute('role','status');controls.push(compare);card.append(compare,comparison);
      compare.onclick=()=>run(async signal=>{comparison.textContent='';const value=decodeMeshComparison(await post('/api/mesh-library-native-comparison',{expected_project_path:path,expected_library_key:catalog.library_key,receipt_key:r.receipt_key},signal),catalog,row);if(!current())return false;comparison.textContent=`${value.matches_current?'Whole native model matches the historical import result.':'Whole native model differs from the historical import result.'} ${value.active_imported_face_count} of ${value.imported_face_count} imported faces remain active; ${value.retired_imported_face_count} retired. Active identity does not assert unchanged face content. Gameplay is unverified.`;return true;});
      if(typeof onOpen==='function'){const button=el('button','Open Current model');controls.push(button);card.append(button);button.onclick=()=>run(async()=>{if(await onOpen(structuredClone(row),structuredClone(catalog))!==false&&current()){dialog.close();return true;}return false;},false);}
      const details=el('details');details.append(el('summary','Historical import settings'),el('pre',JSON.stringify(r.recipe,null,2)));card.append(details);list.append(card);
    }if(!rows.length)list.append(el('p',catalog.receipt_count?'No matching mesh inputs.':'No retained mesh inputs.'));update();
  }
  async function load(){return run(async signal=>{const value=decodeMeshLibrary(await post('/api/mesh-source-library',{expected_project_path:path},signal),path);if(!current()||value.mode!==mode)return false;catalog=value;const selected=scene.value;scene.replaceChildren(el('option','All source scenes'));scene.firstChild.value='';for(const id of new Set(catalog.imports.map(row=>row.scene_id))){const option=el('option',id);option.value=id;scene.append(option);}scene.value=selected;if(!scene.value)scene.value='';render();return true;});}
  search.oninput=scene.onchange=()=>{if(catalog&&!pending&&current())render();};refresh.onclick=load;close.onclick=()=>dialog.close();dialog.onclose=dispose;dialog.showModal();await load();return dialog;
}
