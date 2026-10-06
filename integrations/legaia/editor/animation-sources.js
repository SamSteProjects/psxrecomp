// Historical inputs are recoverable files, never an authorization to replay edits.
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v),hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
function context(get){const v=get();if(!object(v)||typeof v.projectPath!=='string'||typeof v.sceneId!=='string'||!hash(v.sourceKey))throw new Error('Animation source recovery requires current project context.');return {projectPath:v.projectPath,sceneId:v.sceneId,sourceKey:v.sourceKey,mode:v.mode};}
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function decodeAnimationSources(value,request){
  if(!object(value)||value.schema_version!=='legaia.animation-sources.v1'||value.scene_id!==request.scene_id||value.target_id!==request.target_id||value.kind!==request.kind||value.project_source_key!==request.expected_source_key||value.project_changed!==false||value.historical_inputs!==true||!Array.isArray(value.imports)||value.imports.length>32)throw new Error('Animation source catalog differs from this target or project.');
  const seen=new Set();
  for(const r of value.imports){if(!object(r)||r.schema_version!=='legaia.animation-source.v1'||r.scene_id!==request.scene_id||r.target_id!==request.target_id||r.kind!==request.kind||!hash(r.receipt_key)||seen.has(r.receipt_key)||!hash(r.glb_sha256)||!hash(r.candidate_sha256)||!hash(r.review_key)||!Number.isSafeInteger(r.byte_length)||r.byte_length<28||r.byte_length>32*1024*1024||!object(r.binding)||r.binding.scene_id!==request.scene_id||r.animation_index!==null&&(!Number.isSafeInteger(r.animation_index)||r.animation_index<0||r.animation_index>=64))throw new Error('Invalid retained animation input receipt.');seen.add(r.receipt_key);}
  return structuredClone(value);
}
function download(content,type,name){let url,link;try{url=URL.createObjectURL(new Blob([content],{type}));link=el('a');link.href=url;link.download=name;document.body.append(link);link.click();}finally{link?.remove();if(url)URL.revokeObjectURL(url);}}
export async function openAnimationSources({getContext,targetId,kind,onError=()=>{}}){
  const captured=context(getContext),request={scene_id:captured.sceneId,target_id:targetId,kind,expected_source_key:captured.sourceKey};
  const dialog=el('dialog');dialog.className='project-dialog';Object.assign(dialog.style,{width:'min(760px,94vw)',maxHeight:'90vh',overflowY:'auto'});
  const list=el('div'),status=el('p','Verifying original inputs…'),error=el('p'),close=el('button','Close sources');close.type='button';status.setAttribute('role','status');error.setAttribute('role','alert');
  dialog.append(el('h2','Retained animation inputs'),el('p','These are historical external authoring inputs. The native clip may have changed since import. Recover files for external editing; export a fresh binding and Review before applying again.'),list,status,error,close);document.body.append(dialog);
  let closed=false,pending=false,controller=null;const controls=[];
  const current=()=>{try{return !closed&&same(captured,context(getContext));}catch{return false;}};
  const update=()=>{for(const n of controls)n.disabled=pending||!current();};
  function dispose(){if(closed)return;closed=true;controller?.abort();if(dialog.open)dialog.close();dialog.remove();}
  async function post(path,body,signal){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),v=await r.json();if(!r.ok||v?.error)throw new Error(v?.error??'Animation input recovery failed.');return v;}
  async function run(work){if(!current()||pending)return false;pending=true;controller=new AbortController();const signal=controller.signal;error.textContent='';update();try{return await work(signal);}catch(e){if(current()&&e?.name!=='AbortError'){error.textContent=e.message??String(e);onError(e);}return false;}finally{pending=false;controller=null;update();}}
  async function recover(record,part){return run(async signal=>{
    const response=await post('/api/animation-source-download',{...request,receipt_key:record.receipt_key},signal);if(!current())return false;
    const data=decodeAnimationSources(response,request);if(!same(data.selected,record)||!data.imports.some(r=>same(r,record))||typeof data.glb_base64!=='string'||data.glb_base64.length>44739244)throw new Error('Recovered animation source differs from its receipt.');
    const raw=atob(data.glb_base64),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));if(bytes.length!==record.byte_length)throw new Error('Recovered animation input size changed.');
    const actual=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');if(!current())return false;if(actual!==record.glb_sha256)throw new Error('Recovered animation input hash changed.');
    const prefix='animation-input-'+record.receipt_key.slice(0,12);
    if(part==='glb')download(bytes,'model/gltf-binary',prefix+'.glb');else download(JSON.stringify(part==='binding'?record.binding:record,null,2)+'\n','application/json',prefix+(part==='binding'?'.binding.json':'.receipt.json'));
    status.textContent='Original input verified and downloaded. Re-export a fresh binding before applying.';return true;
  });}
  close.onclick=dispose;dialog.oncancel=dispose;dialog.onclose=dispose;dialog.showModal();
  const ready=run(async signal=>{const response=await post('/api/animation-sources',request,signal);if(!current())return false;const data=decodeAnimationSources(response,request);
    for(const record of data.imports){const section=el('section');section.append(el('p',`${record.glb_sha256.slice(0,12)} · ${record.byte_length} bytes · clip ${record.animation_index??'implicit single/static'} · native result ${record.candidate_sha256.slice(0,12)}`));
      for(const [part,label] of [['glb','Download original animation GLB'],['binding','Download original animation binding'],['receipt','Download animation import receipt']]){const button=el('button',label);button.type='button';button.onclick=()=>recover(record,part);controls.push(button);section.append(button);}list.append(section);
    }status.textContent=data.imports.length?`${data.imports.length} historical input receipts. Imported retail data is unchanged.`:'No retained animation inputs for this target.';return true;});
  return {dialog,ready,dispose};
}
