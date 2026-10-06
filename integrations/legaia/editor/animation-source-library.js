import {decodeRetainedAnimationAsset} from './retained-animation-assets.js';
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function decodeAnimationSourceLibrary(value,path){
  if(!object(value)||value.schema_version!=='legaia.animation-source-library.v1'||value.project_path!==path||!hash(value.library_key)||!['edit','live'].includes(value.mode)||value.project_changed!==false||value.historical_inputs!==true||!Array.isArray(value.imports)||value.imports.length>32||value.receipt_count!==value.imports.length)throw new Error('Animation input library differs from the current project.');
  const seen=new Set(),sizes=new Map();
  for(const r of value.imports){
    if(!object(r)||r.schema_version!=='legaia.animation-source.v1'||!['imported','retained'].includes(r.kind)||typeof r.scene_id!=='string'||!r.scene_id.startsWith('scene://')||r.scene_id.length>160||typeof r.target_id!=='string'||r.target_id.length>512||!hash(r.receipt_key)||seen.has(r.receipt_key)||!hash(r.glb_sha256)||!hash(r.candidate_sha256)||!hash(r.review_key)||!Number.isSafeInteger(r.byte_length)||r.byte_length<28||r.byte_length>32*1024*1024||!object(r.binding)||r.binding.scene_id!==r.scene_id||r.animation_index!==null&&(!Number.isSafeInteger(r.animation_index)||r.animation_index<0||r.animation_index>=64))throw new Error('Invalid animation input library receipt.');
    if(r.kind==='imported'&&(r.binding.entity_id!==r.target_id||!r.target_id.startsWith(r.scene_id+'/actors/')||r.source_frame_indices!==null)||r.kind==='retained'&&(r.binding.record_id!==r.target_id||!Array.isArray(r.source_frame_indices)||!r.source_frame_indices.length||r.source_frame_indices.length>4096||r.source_frame_indices.some(v=>!Number.isSafeInteger(v)||v<0||v>65535)))throw new Error('Animation input library identity or mapping changed.');
    if(sizes.has(r.glb_sha256)&&sizes.get(r.glb_sha256)!==r.byte_length)throw new Error('Animation input library has conflicting file sizes.');seen.add(r.receipt_key);sizes.set(r.glb_sha256,r.byte_length);
  }
  const total=[...sizes.values()].reduce((a,b)=>a+b,0);
  if(total>64*1024*1024||value.registered_byte_length!==total||value.distinct_glb_count!==sizes.size)throw new Error('Animation input library exceeds its budget or has invalid totals.');
  return structuredClone(value);
}
export function filterAnimationSourceLibrary(rows,search='',scene=''){
  const terms=search.toLowerCase().trim().split(/\s+/).filter(Boolean);
  return rows.filter(r=>(!scene||r.scene_id===scene)&&terms.every(t=>[r.scene_id,r.target_id,r.kind,r.glb_sha256,r.receipt_key,r.candidate_sha256].join(' ').toLowerCase().includes(t)));
}
export function decodeLibraryRemoval(value,catalog,record){
  const shared=catalog.imports.filter(r=>r.glb_sha256===record.glb_sha256).length;
  if(!object(value)||value.schema_version!=='legaia.animation-library-removal.v1'||value.project_path!==catalog.project_path||value.library_key!==catalog.library_key||value.receipt_key!==record.receipt_key||value.glb_sha256!==record.glb_sha256||value.scene_id!==record.scene_id||value.target_id!==record.target_id||value.kind!==record.kind||!hash(value.review_key)||value.native_content_changed!==false||value.source_file_deleted!==false||value.receipt_count_before!==catalog.receipt_count||value.receipt_count_after!==catalog.receipt_count-1||value.registered_bytes_released!==(shared===1?record.byte_length:0))throw new Error('Animation library removal differs from its reviewed input.');
  return structuredClone(value);
}
export function decodeAnimationSourceComparison(value,catalog,record){
  const prefix='animation://'+record.scene_id.split('://')[1]+'/',clip=record.kind==='imported'?record.binding.animation_id:prefix+'authored-record/'+record.target_id;
  if(!object(value)||value.schema_version!=='legaia.animation-source-native-comparison.v1'||value.project_path!==catalog.project_path||value.library_key!==catalog.library_key||value.receipt_key!==record.receipt_key||value.scene_id!==record.scene_id||value.target_id!==record.target_id||value.kind!==record.kind||value.clip_id!==clip||value.comparison_scope!==(record.kind==='imported'?'imported_shared_clip':'retained_capture')||value.historical_candidate_sha256!==record.candidate_sha256||!hash(value.current_sha256)||!Number.isSafeInteger(value.current_byte_length)||value.current_byte_length<1||value.current_byte_length>4*1024*1024||!Number.isSafeInteger(value.frame_count)||value.frame_count<1||value.frame_count>65535||!Number.isSafeInteger(value.object_count)||value.object_count<1||value.object_count>64||typeof value.active_in_native_bank!=='boolean'||record.kind==='imported'&&value.active_in_native_bank!==true||value.matches_current!==(value.current_sha256===record.candidate_sha256)||value.project_changed!==false||value.native_content_changed!==false)throw new Error('Native animation comparison differs from the saved input context.');
  return structuredClone(value);
}
export async function navigateAnimationSource({record,catalog,getState,readLibrary,changeScene,refreshAssets,getAssets,openActor,openClip,busy=()=>false}){
  const held=structuredClone(record),path=catalog.project_path,key=catalog.library_key,mode=catalog.mode;
  const current=()=>getState().project?.path===path&&getState().project?.mode===mode;
  const qualify=async()=>{if(busy()||!current())throw new Error('Project changed before animation input navigation.');const fresh=decodeAnimationSourceLibrary(await readLibrary(path),path);if(!current()||fresh.mode!==mode||fresh.library_key!==key||!fresh.imports.some(row=>same(row,held)))throw new Error('Saved animation input changed. Refresh the library.');};
  await qualify();if(getState().scene?.id!==held.scene_id&&!await changeScene(held.scene_id))throw new Error('The animation input source scene could not be opened.');
  await qualify();if(getState().scene?.id!==held.scene_id)throw new Error('Animation input scene changed during navigation.');
  if(held.kind==='imported'){
    const entities=getState().scene?.entities;if(!Array.isArray(entities)||entities.filter(row=>row.id===held.target_id).length!==1)throw new Error('The saved input source actor is absent from its current scene.');
    await openActor(held.target_id);return true;
  }
  await refreshAssets();await qualify();if(getState().scene?.id!==held.scene_id)throw new Error('Animation input scene changed during navigation.');
  const matches=getAssets().filter(row=>row.type==='animation'&&row.sceneId===held.scene_id&&row.data?.scope==='authored-retained'&&row.data?.retained_record?.record_id===held.target_id);
  if(matches.length!==1)throw new Error('The saved input retained clip is absent from the current asset catalog.');
  const clip=matches[0];decodeRetainedAnimationAsset(clip);await openClip(clip);return true;
}
function save(content,type,name){let url,link;try{url=URL.createObjectURL(new Blob([content],{type}));link=el('a');link.href=url;link.download=name;document.body.append(link);link.click();}finally{link?.remove();if(url)URL.revokeObjectURL(url);}}
export function mountAnimationSourceLibrary({after,getState,busy,setBusy,onApplied,onOpen=null,onError=()=>{}}){
  const button=el('button','Project animation inputs');button.id='project-animation-inputs';after.after(button);
  button.onclick=()=>openAnimationSourceLibrary({getState,busy,setBusy,onApplied,onOpen,onError});return {button};
}
export async function openAnimationSourceLibrary({getState,busy=()=>false,setBusy=()=>{},onApplied=()=>{},onOpen=null,onError=()=>{}}){
  const path=getState().project?.path,mode=getState().project?.mode;if(typeof path!=='string'||!path||busy())return false;
  const dialog=el('dialog');dialog.id='animation-source-library-dialog';dialog.className='project-dialog';Object.assign(dialog.style,{width:'min(900px,94vw)',maxHeight:'90vh',overflowY:'auto'});
  const status=el('p','Verifying saved animation inputs…'),error=el('p'),search=el('input'),scene=el('select'),list=el('div'),refresh=el('button','Refresh animation inputs'),close=el('button','Close animation inputs');status.setAttribute('role','status');error.setAttribute('role','alert');search.setAttribute('aria-label','Search animation inputs');search.placeholder='Scene, target, kind or hash';scene.setAttribute('aria-label','Animation input scene');refresh.type=close.type='button';
  dialog.append(el('h2','Project animation inputs'),el('p','Saved external authoring inputs across all recorded scenes. These are historical receipts; later native edits can make their original bindings stale. Export a fresh binding and Review before authoring again.'),search,scene,refresh,status,error,list,close);document.body.append(dialog);
  let closed=false,pending=false,removing=false,controller=null,catalog=null;const controls=[];
  const current=()=>!closed&&getState().project?.path===path&&getState().project?.mode===mode;
  function update(){for(const n of [...controls,search,scene,refresh])n.disabled=pending||!current()||busy();close.disabled=removing;}
  function dispose(){if(closed||removing)return;closed=true;controller?.abort();if(dialog.open)dialog.close();dialog.remove();}
  async function post(route,body,signal){const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),value=await response.json();if(!response.ok||value?.error)throw new Error(value?.error??'Animation input request failed.');return value;}
  async function run(work){if(!current()||pending||busy())return false;pending=true;setBusy(true);controller=new AbortController();error.textContent='';update();try{return await work(controller.signal);}catch(e){if(current()&&e?.name!=='AbortError'){error.textContent=e.message??String(e);onError(e);}return false;}finally{pending=false;controller=null;setBusy(false);update();}}
  const request=record=>({expected_project_path:path,expected_library_key:catalog.library_key,receipt_key:record.receipt_key});
  async function recover(record,part,signal){const held=catalog,data=decodeAnimationSourceLibrary(await post('/api/animation-library-download',request(record),signal),path);if(!current())return false;
    if(data.library_key!==held.library_key||!same(data.selected,record)||!data.imports.some(r=>same(r,record))||typeof data.glb_base64!=='string'||data.glb_base64.length>44739244)throw new Error('Saved animation input changed. Refresh the library.');
    const raw=atob(data.glb_base64),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));if(bytes.length!==record.byte_length)throw new Error('Saved animation input size changed.');const actual=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');if(!current())return false;if(actual!==record.glb_sha256)throw new Error('Saved animation input hash changed.');
    const prefix='animation-input-'+record.receipt_key.slice(0,12);if(part==='glb')save(bytes,'model/gltf-binary',prefix+'.glb');else save(JSON.stringify(part==='binding'?record.binding:record,null,2)+'\n','application/json',prefix+(part==='binding'?'.binding.json':'.receipt.json'));status.textContent='Saved input verified and downloaded.';return true;
  }
  function render(){list.replaceChildren();controls.length=0;if(!catalog)return;
    const rows=filterAnimationSourceLibrary(catalog.imports,search.value,scene.value);status.textContent=`${rows.length} of ${catalog.receipt_count} receipts · ${catalog.distinct_glb_count} distinct GLBs · ${catalog.registered_byte_length} registered bytes.`;
    if(!rows.length)list.append(el('p',catalog.receipt_count?'No inputs match these filters.':'No retained animation inputs in this project.'));
    for(const record of rows){const section=el('section');section.dataset.receiptKey=record.receipt_key;Object.assign(section.style,{borderTop:'1px solid #364146',padding:'12px 0',overflowWrap:'anywhere'});section.append(el('p',`${record.scene_id} · ${record.kind==='retained'?'Retained clip':'Imported actor'} · ${record.target_id}`),el('p',`GLB ${record.glb_sha256} · ${record.byte_length} bytes · clip ${record.animation_index??'implicit single/static'}`),el('p',`Reviewed native result ${record.candidate_sha256}`));
      const actions=el('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';
      for(const [part,label] of [['glb','Download saved animation GLB'],['binding','Download saved animation binding'],['receipt','Download saved animation receipt']]){const b=el('button',label);b.type='button';b.onclick=()=>run(signal=>recover(record,part,signal));controls.push(b);actions.append(b);}
      if(typeof onOpen==='function'){const open=el('button',record.kind==='imported'?'Open source actor':'Open retained source clip');open.type='button';open.onclick=async()=>{const held=catalog;const verified=await run(async signal=>{const value=decodeAnimationSourceLibrary(await post('/api/animation-source-library',{expected_project_path:path},signal),path);if(!current())return false;if(value.mode!==mode||value.library_key!==held.library_key||!value.imports.some(r=>same(r,record)))throw new Error('Saved animation input changed. Refresh the library.');return true;});if(!verified||!current())return;dispose();try{await onOpen(structuredClone(record),structuredClone(held));}catch(e){onError(e);}};controls.push(open);actions.append(open);}
      const comparison=el('p'),compare=el('button','Compare current native clip');compare.type='button';compare.onclick=()=>run(async signal=>{comparison.textContent='';const held=catalog;const value=await post('/api/animation-library-native-comparison',request(record),signal);if(!current()||catalog!==held)return false;const report=decodeAnimationSourceComparison(value,held,record);comparison.textContent=`${report.matches_current?'Historical result matches current native clip content.':'Historical result differs from current native clip content.'} ${report.comparison_scope==='imported_shared_clip'?'Saved shared clip; actor assignment is separate.':report.active_in_native_bank?'Retained capture is active in the authored bank.':'Retained capture is retired; it is absent from the authored bank.'} ${report.clip_id} · ${report.frame_count} frames · ${report.object_count} rigid objects · ${report.current_sha256}. Export a fresh binding before editing.`;return true;});controls.push(compare);actions.append(compare);section.append(comparison);
      const detail=el('p');if(mode==='edit'){const review=el('button','Review input removal'),apply=el('button','Remove reviewed input');review.type=apply.type='button';apply.hidden=true;let held=null;
        review.onclick=()=>run(async signal=>{held=null;apply.hidden=true;const value=await post('/api/animation-library-removal-review',request(record),signal);if(!current())return false;held=decodeLibraryRemoval(value,catalog,record);detail.textContent=`${held.receipt_count_before} → ${held.receipt_count_after} receipts · ${held.registered_bytes_released} registered bytes freed. Native animation content and the local GLB file stay intact. Undo restores the receipt.`;apply.hidden=false;return true;});
        apply.onclick=()=>{const reviewed=held;if(!reviewed)return false;return run(async signal=>{removing=true;update();try{const next=await post('/api/animation-library-remove',{...request(record),review_key:reviewed.review_key},signal);if(!current()||held!==reviewed)return false;if(!object(next?.project)||next.project.path!==path||next.project.mode!=='edit')throw new Error('Input removal returned invalid project state.');held=null;await onApplied(next);await load(signal);return true;}catch(e){held=null;apply.hidden=true;throw e;}finally{removing=false;update();}});};controls.push(review,apply);actions.append(review,apply);
      }section.append(actions,detail);list.append(section);
    }update();
  }
  async function load(signal){const value=await post('/api/animation-source-library',{expected_project_path:path},signal);if(!current())return false;catalog=decodeAnimationSourceLibrary(value,path);if(catalog.mode!==mode)throw new Error('Animation input library mode changed.');const selected=scene.value;scene.replaceChildren();const all=el('option','All recorded scenes');all.value='';scene.append(all);for(const id of [...new Set(catalog.imports.map(r=>r.scene_id))].sort()){const option=el('option',id);option.value=id;scene.append(option);}scene.value=[...scene.options].some(o=>o.value===selected)?selected:'';render();return true;}
  search.oninput=scene.onchange=()=>{if(!pending)render();};refresh.onclick=()=>run(load);close.onclick=dispose;dialog.oncancel=e=>{if(removing)e.preventDefault();else dispose();};dialog.onclose=dispose;dialog.showModal();const ready=run(load);return {dialog,ready,dispose};
}
