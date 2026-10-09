import {CONTROLLER_BUILD_TARGETS} from './controller-build-navigation.js';
import {controllerResetEntries} from './controller-component-reset.js';
const kinds=Object.fromEntries(Object.values(CONTROLLER_BUILD_TARGETS).map(([family,kind])=>[family,kind]));
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v),object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const canonical=v=>Array.isArray(v)?v.map(canonical):object(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v,same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const fail=()=>{throw Error('Controller operand file or Review differs from its source or supplied entries.');};
export function decodeControllerOperandFile(file,source){
 if(!object(file)||!same(Object.keys(file).sort(),['schema_version','scene_id','owner_id','source_import_sha256','source_record_sha256','components'].sort())||file.schema_version!=='legaia.controller-operand-file.v1'||file.owner_id!==source.owner_id||file.scene_id!==source.scene_id||file.source_record_sha256!==source.source_record_sha256||!hash(file.source_import_sha256)||!object(file.components))fail();
 let count=0;
 for(const [family,value] of Object.entries(file.components)){
  if(!Object.hasOwn(kinds,family)||!object(value)||!same(Object.keys(value),['entries'])||!object(value.entries)||!Object.keys(value.entries).length)fail();
  for(const [id,fields] of Object.entries(value.entries)){const prefix=source.owner_id.replace('scene://','script://')+'/'+kinds[family]+'/';if(!id.startsWith(prefix)||!/^[a-f0-9]{4}$/.test(id.slice(prefix.length))||!(fields===null||object(fields)))fail();count++;}
 }
 if(count>256)fail();return structuredClone(file);
}
export function controllerOperandSource(families,owner,key){
 const first=Object.values(families)[0];if(!/^scene:\/\/[A-Za-z0-9_-]{1,128}\/controllers\/man-p1\/0000$/.test(owner)||!same(Object.keys(families).sort(),Object.keys(kinds).sort())||!first||!hash(key)||first.owner_id!==owner||first.state_key!==key||!hash(first.source_record_sha256)||!hash(first.current_record_sha256))fail();
 const before={};for(const [family,snapshot] of Object.entries(families)){if(!Object.hasOwn(kinds,family)||snapshot.owner_id!==owner||snapshot.state_key!==key||snapshot.source_record_sha256!==first.source_record_sha256||snapshot.current_record_sha256!==first.current_record_sha256)fail();const entries=controllerResetEntries(snapshot);if(Object.keys(entries).length)before[family]={source_record_sha256:first.source_record_sha256,entries};}
 return {owner_id:owner,scene_id:owner.split('/controllers/')[0],state_key:key,source_record_sha256:first.source_record_sha256,current_record_sha256:first.current_record_sha256,before:Object.keys(before).length?before:null,families:structuredClone(families)};
}
export function decodeControllerOperandReview(raw,file,source){
 decodeControllerOperandFile(file,source);const after=structuredClone(source.before??{}),rows=[];
 for(const family of Object.keys(file.components).sort()){
  const entries=structuredClone(after[family]?.entries??{});
  for(const id of Object.keys(file.components[family].entries).sort()){
   const target=source.families[family]?.targets.find(t=>t.semantic_id===id);if(!target)fail();const fields=file.components[family].entries[id],before=structuredClone(entries[id]??null);
   if(fields===null||same(fields,target.values))delete entries[id];else entries[id]=structuredClone(fields);
   const value=entries[id]??null;rows.push({component:family,operand_id:id,before,after:structuredClone(value),changed:!same(before,value)});
  }
  if(Object.keys(entries).length)after[family]={source_record_sha256:source.source_record_sha256,entries};else delete after[family];
 }
 const proposed=Object.keys(after).length?after:null,offsets=raw?.changed_decoded_byte_offsets;
 if(raw?.schema_version!=='legaia.controller-operand-review.v1'||raw.owner_id!==source.owner_id||raw.scene_id!==source.scene_id||raw.state_key!==source.state_key||raw.source_import_sha256!==file.source_import_sha256||raw.source_record_sha256!==source.source_record_sha256||raw.current_record_sha256!==source.current_record_sha256||!hash(raw.proposed_record_sha256)||!hash(raw.review_key)||raw.project_changed!==false||raw.gameplay_verified!==false||!same(raw.before,source.before)||!same(raw.after,proposed)||!same(raw.entries,rows)||raw.change_count!==rows.filter(r=>r.changed).length||raw.no_op!==same(source.before,proposed)||!Array.isArray(offsets)||offsets.some((v,i)=>!Number.isSafeInteger(v)||v<0||i>0&&v<=offsets[i-1])||raw.native_bytes_changed!==(offsets.length>0)||raw.native_bytes_changed!==(raw.current_record_sha256!==raw.proposed_record_sha256))fail();
 return structuredClone(raw);
}
const el=(tag,text='')=>{const node=document.createElement(tag);node.textContent=text;return node;};
export function mountControllerOperandFiles(host,{families,owner,getKey,current,busy,setBusy,api,reopen,onError=()=>{}}){
 const source=controllerOperandSource(families,owner,getKey()),section=el('section'),status=el('p','Choose a source-bound file, then Review before Apply.'),evidence=el('pre'),input=el('input'),actions=el('div');section.dataset.controllerOperandFiles='';input.type='file';input.accept='.json,application/json';input.setAttribute('aria-label','Controller Operand JSON');status.setAttribute('role','status');evidence.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere';
 const download=el('button','Download Controller Operand JSON'),review=el('button','Review Controller Operand File'),discard=el('button','Discard Controller File Proposal'),apply=el('button','Apply Reviewed Controller Operands');actions.className='dialog-actions';actions.style.flexWrap='wrap';for(const b of [download,review,discard,apply])b.type='button';input.style.maxWidth='100%';actions.append(download,review,discard,apply);section.append(el('h3','Controller Operand Files'),el('p','Transfer authored operands for this source controller. Supplied entries merge into the project; null inherits Retail. Other entries remain authored. Apply creates one Undo step.'),input,actions,status,evidence);host.prepend(section);
 let accepted=null,content=null,pending=false,disposed=false,generation=0,abort=null;
 const fresh=()=>!disposed&&current()&&getKey()===source.state_key;
 const withdraw=()=>{generation++;abort?.abort();accepted=null;content=null;evidence.textContent='';};
 function updateState(){const blocked=!fresh()||pending||busy();download.disabled=input.disabled=blocked;review.disabled=blocked||!input.files?.[0]||input.files[0].size>65536;discard.disabled=blocked||!accepted;apply.disabled=blocked||!accepted?.change_count;if(!fresh()){withdraw();section.hidden=true;}}
 input.onchange=()=>{withdraw();status.textContent=input.files?.[0]?.size>65536?'Controller file exceeds 64 KiB.':'File changed. Review before Apply.';updateState();};
 discard.onclick=()=>{if(!fresh()||pending||busy())return;withdraw();status.textContent='File proposal discarded.';updateState();};
 async function request(run){if(!fresh()||pending||busy())return;withdraw();const ticket=++generation;pending=true;abort=new AbortController();setBusy(true);updateState();try{await run(()=>fresh()&&ticket===generation,abort.signal);}catch(error){if(fresh()&&ticket===generation&&error.name!=='AbortError'){status.textContent=error.message;onError(error);}}finally{pending=false;setBusy(false);updateState();}}
 download.onclick=()=>request(async(valid,signal)=>{const response=await fetch('/api/controller-operand-export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity:owner}),signal}),raw=await response.json();if(!valid())return;if(!response.ok||raw.error)throw Error(raw.error||'Controller export failed.');const file=decodeControllerOperandFile(raw,source),expected=Object.fromEntries(Object.entries(source.before??{}).map(([family,value])=>[family,{entries:value.entries}]));if(!same(file.components,expected))fail();const url=URL.createObjectURL(new Blob([JSON.stringify(file,null,2)+'\n'],{type:'application/json'})),link=el('a');link.href=url;link.download='controller-operands.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status.textContent='Authored controller operands downloaded.';});
 review.onclick=()=>request(async(valid,signal)=>{const file=input.files?.[0];if(!file||file.size>65536)throw Error('Choose a controller JSON file up to 64 KiB.');const candidate=await file.text();if(!valid())return;if(new TextEncoder().encode(candidate).length>65536)throw Error('Controller file exceeds 64 KiB.');const parsed=decodeControllerOperandFile(JSON.parse(candidate),source),response=await fetch('/api/controller-operand-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity:owner,content:candidate}),signal}),raw=await response.json();if(!valid())return;if(!response.ok||raw.error)throw Error(raw.error||'Controller file Review failed.');accepted=decodeControllerOperandReview(raw,parsed,source);content=candidate;status.textContent=`${accepted.change_count} changed entries · one Undo step. Gameplay remains unverified.`;evidence.textContent=JSON.stringify(accepted.entries,null,2);});
 apply.onclick=async()=>{if(!fresh()||pending||busy()||!accepted?.change_count||content===null)return;const proof=accepted,text=content;pending=true;updateState();try{if(await api('/api/command',{type:'import_controller_operand_file',entity_id:owner,content:text,review_key:proof.review_key},{success:'Controller operands applied. Undo restores the prior entries.'}))await reopen();else{withdraw();status.textContent='File was not applied. Review again.';}}catch(error){withdraw();onError(error);}finally{pending=false;updateState();}};
 updateState();return {updateState,dispose(){disposed=true;withdraw();section.remove();}};
}
