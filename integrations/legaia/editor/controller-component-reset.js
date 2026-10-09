import {CONTROLLER_SNAPSHOT_SCHEMAS} from './controller-workspace-snapshot.js';
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const labels={ControllerSystemFlags:'System Flag Selectors',ControllerBranches:'Branches',ControllerTileRects:'Tile Requests',ControllerFades:'Fades',ControllerTableCopies:'Table Copies',ControllerWordTriplets:'Word Triplets',ControllerThreeWords:'Three Words',ControllerSceneBytes:'Scene-State Bytes',ControllerFiveWords:'Five Words',ControllerGlobalBytes:'Global Bytes',ControllerPartySelectors:'Party Selectors'};
export function controllerResetEntries(snapshot){
 const entries={};
 for(const target of snapshot?.targets??[]){const value=target.authored_values??target.authored_value;if(value!==undefined&&value!==null){if(typeof target.semantic_id!=='string'||Object.hasOwn(entries,target.semantic_id))throw Error('Controller reset entries are invalid.');entries[target.semantic_id]=structuredClone(value);}}
 return entries;
}
export function decodeControllerComponentReset(raw,snapshot,component){
 const entries=controllerResetEntries(snapshot),ids=Object.keys(entries).sort();
 if(!Object.hasOwn(CONTROLLER_SNAPSHOT_SCHEMAS,component)||snapshot?.schema_version!==CONTROLLER_SNAPSHOT_SCHEMAS[component]||!ids.length||raw?.schema_version!=='legaia.controller-component-reset.v1'||raw.owner_id!==snapshot.owner_id||raw.component!==component||raw.state_key!==snapshot.state_key||raw.source_record_sha256!==snapshot.source_record_sha256||raw.current_record_sha256!==snapshot.current_record_sha256||!hash(raw.proposed_record_sha256)||!hash(raw.review_key)||raw.project_changed!==false||raw.gameplay_verified!==false||raw.authored?.source_record_sha256!==snapshot.source_record_sha256||!same(raw.authored.entries,entries)||!same(raw.removed_operand_ids,ids)||raw.removed_operand_count!==ids.length||!raw.proposed||Array.isArray(raw.proposed)||Object.hasOwn(raw.proposed,component)||!same(raw.source_report,snapshot.source_report)||!same(raw.current_report,snapshot.current_report)||!Array.isArray(raw.changed_decoded_byte_offsets)||raw.native_bytes_changed!==(raw.changed_decoded_byte_offsets.length>0)||raw.native_bytes_changed!==(raw.current_record_sha256!==raw.proposed_record_sha256))throw Error('Controller component reset Review differs from its current source.');
 const offsets=raw.changed_decoded_byte_offsets;
 if(offsets.some((v,i)=>!Number.isSafeInteger(v)||v<0||i>0&&v<=offsets[i-1]))throw Error('Controller component reset byte evidence is invalid.');
 return structuredClone(raw);
}
const el=(tag,text='')=>{const node=document.createElement(tag);node.textContent=text;return node;};
export function mountControllerComponentReset(host,{families,owner,getKey,current,busy,setBusy,api,reopen,onError=()=>{}}){
 const key=getKey(),section=el('section'),title=el('h3','Reset an Authored Controller Component'),source=el('select'),status=el('p'),evidence=el('pre');
 section.dataset.controllerComponentReset='';source.setAttribute('aria-label','Authored controller component');source.style.maxWidth='100%';status.setAttribute('role','status');evidence.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere';
 for(const [component,snapshot] of Object.entries(families)){const count=Object.keys(controllerResetEntries(snapshot)).length;if(count){const option=el('option',`${labels[component]} · ${count} authored ${count===1?'entry':'entries'}`);option.value=component;source.append(option);}}
 if(!source.children.length)return {updateState(){},dispose(){}};
 const actions=el('div'),review=el('button','Review component reset'),discard=el('button','Discard component reset'),apply=el('button','Reset reviewed controller component');actions.className='dialog-actions';actions.style.flexWrap='wrap';for(const button of [review,discard,apply])button.type='button';
 actions.append(review,discard,apply);section.append(title,el('p','Remove every authored entry in one component and inherit Retail operands. Review the entries before resetting. Undo restores the whole component.'),source,status,actions,evidence);host.prepend(section);
 let accepted=null,pending=false,disposed=false,generation=0,abort=null;
 const fresh=()=>!disposed&&current()&&getKey()===key;
 const withdraw=()=>{generation++;abort?.abort();accepted=null;evidence.textContent='';};
 function updateState(){const blocked=!fresh()||pending||busy();source.disabled=review.disabled=blocked;discard.disabled=blocked||!accepted;apply.disabled=blocked||!accepted;if(!fresh()){withdraw();section.hidden=true;}}
 source.onchange=()=>{withdraw();status.textContent='Component changed. Review before resetting.';updateState();};
 discard.onclick=()=>{if(!fresh()||pending||busy())return;withdraw();status.textContent='Reset proposal discarded.';updateState();};
 review.onclick=async()=>{
  if(!fresh()||pending||busy())return;withdraw();const ticket=++generation,component=source.value;pending=true;abort=new AbortController();setBusy(true);updateState();
  try{const response=await fetch('/api/controller-component-reset-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity:owner,component}),signal:abort.signal}),raw=await response.json();if(!fresh()||ticket!==generation)return;if(!response.ok||raw.error)throw Error(raw.error||'Controller reset Review failed.');accepted=decodeControllerComponentReset(raw,families[component],component);evidence.textContent=JSON.stringify({removed_entries:accepted.authored.entries,changed_MAN_offsets:accepted.changed_decoded_byte_offsets,native_bytes_changed:accepted.native_bytes_changed},null,2);status.textContent=`Reviewed removal of ${accepted.removed_operand_count} authored ${accepted.removed_operand_count===1?'entry':'entries'}. Other components remain authored. Gameplay is unverified.`;}
  catch(error){if(fresh()&&ticket===generation&&error.name!=='AbortError'){status.textContent=error.message;onError(error);}}
  finally{pending=false;setBusy(false);updateState();}
 };
 apply.onclick=async()=>{
  if(!fresh()||pending||busy()||!accepted)return;const proof=accepted;pending=true;updateState();
  try{if(await api('/api/command',{type:'reset_controller_component',entity_id:owner,component:proof.component,review_key:proof.review_key},{success:'Controller component reset. Undo restores all its authored entries.'})){await reopen();}else{withdraw();status.textContent='Reset was not applied. Review again.';}}
  catch(error){withdraw();onError(error);}finally{pending=false;updateState();}
 };
 status.textContent='Choose an authored component to review its removal.';updateState();
 return {updateState,hasDraft:()=>!!accepted||pending,dispose(){disposed=true;withdraw();section.remove();}};
}
