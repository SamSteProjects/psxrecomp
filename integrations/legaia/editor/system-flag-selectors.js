// Persistent encoded operands; these controls do not read or write live story flags.
import {scriptBranchContext} from './script-branches.js';
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const index=v=>Number.isSafeInteger(v)&&v>=0&&v<=4095;
const value=v=>object(v)&&Object.keys(v).length===1&&index(v.index);
const draft=v=>value(v)||object(v)&&Object.keys(v).length===1&&typeof v.index==='string'&&v.index.length<=4;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const clone=v=>structuredClone(v);
const fail=m=>{throw new Error(m);};
const identity=(owner,pc)=>'script://'+owner.slice(8)+'/system-flag/'+pc.toString(16).padStart(4,'0');
function report(v){if(!object(v)||!Array.isArray(v.instructions)||v.instructions.length>8192||!Array.isArray(v.stops)||v.stops.length)fail('System selector report has unresolved source paths.');return v;}
export function decodeSystemSelectorSnapshot(raw,owner,context,schema='legaia.system-flag-authoring.v1'){
  if(!object(raw)||raw.schema_version!==schema||raw.owner_id!==owner||raw.state_key!==context.scriptKey||!hash(raw.source_record_sha256)||!hash(raw.current_record_sha256)||raw.gameplay_verified!==false||!Array.isArray(raw.targets)||raw.targets.length>1024||raw.supported!==(raw.targets.length>0))fail('System selector source changed or returned an invalid snapshot.');
  report(raw.current_report);const seen=new Set();
  for(const t of raw.targets){if(!object(t)||!Number.isSafeInteger(t.pc)||t.pc<0||t.pc>65535||t.semantic_id!==identity(owner,t.pc)||seen.has(t.semantic_id)||t.owner_id!==owner||t.source_record_sha256!==raw.source_record_sha256||t.target_context!==null||t.byte_length!==2||t.maximum!==4095||!Number.isSafeInteger(t.decoded_byte_offset)||t.decoded_byte_offset<0||t.decoded_byte_offset>4*1024*1024-2||!['SYSFLAG_SET','SYSFLAG_CLEAR','SYSFLAG_TEST'].includes(t.mnemonic)||!value(t.values)||!index(t.current_index)||!(t.authored_values===null||value(t.authored_values))||t.current_index!==(t.authored_values?.index??t.values.index))fail('System selector target differs from the qualified source.');seen.add(t.semantic_id);const node=raw.current_report.instructions.find(n=>n.pc===t.pc);if(node&&(node.mnemonic!==t.mnemonic||node.operands?.index!==t.current_index))fail('Current selector differs from the decoded instruction.');}
  return clone(raw);
}
export function decodeSystemSelectorReview(raw,snapshot,operand,requested){
  const t=snapshot.targets.find(t=>t.semantic_id===operand);
  if(!t||!object(raw)||raw.schema_version!==snapshot.schema_version||raw.owner_id!==snapshot.owner_id||raw.operand_id!==operand||!same(raw.value,requested)||raw.state_key!==snapshot.state_key||raw.source_record_sha256!==snapshot.source_record_sha256||raw.current_record_sha256!==snapshot.current_record_sha256||!hash(raw.proposed_record_sha256)||!hash(raw.review_key)||typeof raw.no_op!=='boolean'||typeof raw.native_bytes_changed!=='boolean'||raw.project_changed!==false||raw.gameplay_verified!==false||!Array.isArray(raw.changed_decoded_byte_offsets)||raw.changed_decoded_byte_offsets.length>2||raw.changed_decoded_byte_offsets.some(n=>n!==t.decoded_byte_offset&&n!==t.decoded_byte_offset+1))fail('System selector Review differs from the inspected source or draft.');
  report(raw.current_report);report(raw.proposed_report);
  const current=raw.current_report.instructions.find(n=>n.pc===t.pc),proposed=raw.proposed_report.instructions.find(n=>n.pc===t.pc);
  if(!same(raw.current_report,snapshot.current_report)||current&&(current.operands?.index!==t.current_index||current.mnemonic!==t.mnemonic)||proposed&&(proposed.mnemonic!==t.mnemonic||proposed.operands?.index!==(requested===null?t.values.index:requested.index))||!!current!==!!proposed||current&&!same(current.successors,proposed.successors))fail('System selector Review changed operation or continuations.');
  return clone(raw);
}
const el=(tag,text='')=>{const n=document.createElement(tag);n.textContent=text;return n;};
function mountSelectors(host,{protocol,owner,focusPc=null,getContext,busy,setBusy,api,reopen,onDraftChange=()=>{},initialDrafts=new Map(),onError=()=>{}}){
  const context=scriptBranchContext(getContext());
  const prefix='script://'+owner.slice(8)+'/system-flag/';
  if(!owner.startsWith(context.sceneId+'/')||!(initialDrafts instanceof Map)||initialDrafts.size>1024||[...initialDrafts].some(([id,v])=>typeof id!=='string'||!id.startsWith(prefix)||!/^[0-9a-f]{4}$/.test(id.slice(prefix.length))||!(v===null||draft(v))))fail('System selector drafts require the source owner and bounded indices.');
  const drafts=new Map([...initialDrafts].map(([k,v])=>[k,clone(v)]));
  const section=el('section');section.className='system-selector-authoring';section.dataset.systemSelectors='';
  section.append(el('h3','System Flag Selectors'),el('p','Edit the encoded selector index (0–4095). Operation and TEST destinations stay fixed. Story meanings and live flag values remain unknown.'));
  const status=el('p','Verifying source…');status.setAttribute('role','status');const error=el('p');error.className='dialog-error';error.setAttribute('role','alert');
  const selector=el('select');selector.setAttribute('aria-label','Source system selector');
  const input=el('input');input.type='text';input.inputMode='numeric';input.maxLength=4;input.setAttribute('aria-label','Proposed system selector index');
  const layers=el('p'),assessment=el('pre');assessment.style.whiteSpace='pre-wrap';assessment.style.overflowWrap='anywhere';
  const actions=el('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';
  const buttons={};for(const [id,label] of [['review','Review selector'],['reset','Review reset to Retail'],['discard','Discard selector draft'],['apply','Apply reviewed selector']]){const b=el('button',label);b.type='button';b.dataset.systemAction=id;buttons[id]=b;actions.append(b);}
  const inputLabel=el('label','Proposed selector index');inputLabel.append(input);
  section.append(status,error,selector,layers,inputLabel,actions,assessment);host.append(section);
  let snapshot=null,accepted=null,active=null,pending=false,disposed=false,started=false,generation=0,controller=null,token=null,resolveReady;
  const ready=new Promise(resolve=>resolveReady=resolve);
  const current=()=>{try{return !disposed&&same(context,scriptBranchContext(getContext()));}catch{return false;}};
  const row=()=>snapshot?.targets.find(t=>t.semantic_id===active);
  const choice=()=>{const v=drafts.has(active)?drafts.get(active):row()?{index:row().current_index}:undefined;return typeof v?.index==='string'?/^\d{1,4}$/.test(v.index)&&index(Number(v.index))?{index:Number(v.index)}:undefined:v;};
  const notify=()=>onDraftChange(new Map([...drafts].map(([k,v])=>[k,clone(v)])));
  const release=own=>{if(token===own){token=null;setBusy(false);}};
  function invalidate(){generation++;controller?.abort();controller=null;accepted=null;assessment.textContent='';pending=false;if(token)release(token);}
  function fields(){const t=row(),v=drafts.has(active)?drafts.get(active):choice();input.value=v===null?'':v?.index===undefined?'':String(v.index);layers.textContent=t?`Retail: ${t.values.index} · Current: ${t.current_index} · Authored: ${t.authored_values?.index??'none'}`:'';}
  function updateState(){
    const fresh=current(),blocked=!fresh||pending||busy(),editable=fresh&&context.mode==='edit'&&!!row();
    if(!fresh){invalidate();status.textContent='Project, scene, mode or source changed. Reopen this script.';}
    selector.disabled=blocked||!snapshot?.targets.length;input.disabled=blocked||!editable;
    const v=choice();buttons.review.disabled=blocked||!editable||!value(v);buttons.reset.disabled=blocked||!editable||row()?.authored_values===null;buttons.discard.disabled=blocked||!drafts.size;
    buttons.apply.disabled=blocked||!editable||!accepted||!same(accepted.value,v)||accepted.no_op;
    if(!started&&fresh&&!busy()){started=true;void run(async(signal,valid)=>{const raw=await request(protocol.snapshotRoute,{entity:owner},signal);if(!valid())return false;snapshot=decodeSystemSelectorSnapshot(raw,owner,context,protocol.schema);for(const t of snapshot.targets){const option=el('option',`0x${t.pc.toString(16).toUpperCase().padStart(4,'0')} ${t.mnemonic}`);option.value=t.semantic_id;selector.append(option);}active=snapshot.targets.find(t=>drafts.has(t.semantic_id))?.semantic_id??snapshot.targets.find(t=>t.pc===focusPc)?.semantic_id??snapshot.targets[0]?.semantic_id;selector.value=active??'';status.textContent=snapshot.targets.length?`${snapshot.targets.length} source-qualified selectors`:raw.reason??'No qualified system selectors in this source.';fields();return true;}).then(result=>{resolveReady?.(result);resolveReady=null;});}
  }
  async function request(route,body,signal){const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});const result=await response.json();if(!response.ok||result.error)fail(result.error??'System selector request failed.');return result;}
  async function run(work){if(!current()||pending||busy())return false;const ticket=++generation,own={};pending=true;controller=new AbortController();const signal=controller.signal;token=own;setBusy(true);error.textContent='';updateState();const valid=()=>current()&&ticket===generation&&!signal.aborted;try{return await work(signal,valid);}catch(e){if(valid()&&e.name!=='AbortError'){error.textContent=e.message;onError(e);}return false;}finally{if(ticket===generation){pending=false;controller=null;}release(own);if(!disposed)updateState();}}
  selector.onchange=()=>{if(selector.disabled)return;invalidate();active=selector.value;fields();updateState();};
  input.oninput=()=>{if(!current())return;invalidate();drafts.set(active,{index:input.value.slice(0,4)});error.textContent=value(choice())?'':'Enter a whole index from 0 to 4095.';notify();updateState();};
  async function reviewChoice(v){return run(async(signal,valid)=>{const raw=await request(protocol.reviewRoute,{entity:owner,operand_id:active,value:v},signal);if(!valid())return false;accepted=decodeSystemSelectorReview(raw,snapshot,active,v);assessment.textContent=`Current: ${row().current_index}\nProposed: ${v===null?row().values.index:v.index}\nOperation and TEST destinations preserved.\n${accepted.no_op?'No authored change.':'Ready to apply the reviewed authored change.'}`;return true;});}
  buttons.review.onclick=()=>buttons.review.disabled?false:reviewChoice(choice());
  buttons.reset.onclick=()=>{if(buttons.reset.disabled)return false;invalidate();drafts.set(active,null);notify();fields();return reviewChoice(null);};
  buttons.discard.onclick=()=>{if(buttons.discard.disabled)return false;invalidate();drafts.clear();notify();fields();updateState();return true;};
  buttons.apply.onclick=async()=>{
    if(buttons.apply.disabled||pending||busy()||!current())return false;
    const proposal=clone(accepted);pending=true;error.textContent='';updateState();
    try{
      // The shared mutation API owns its busy lock; inspection requests own ours.
      const result=await api('/api/command',{type:protocol.commandType,entity_id:owner,operand_id:active,value:proposal.value,review_key:proposal.review_key});
      accepted=null;assessment.textContent='';
      if(result!==true)return false;
      const now=scriptBranchContext(getContext());
      if(disposed||['projectPath','sceneId','mode'].some(key=>now[key]!==context[key]))return false;
      drafts.delete(proposal.operand_id);notify();pending=false;await reopen(parseInt(proposal.operand_id.slice(-4),16));return true;
    }catch(e){if(current()){error.textContent=e.message;onError(e);}return false;}
    finally{if(!disposed){pending=false;updateState();}}
  };
  updateState();return {ready,updateState,dispose(){if(disposed)return;disposed=true;invalidate();section.remove();resolveReady?.(false);resolveReady=null;}};
}

export function mountSystemSelectors(host,options){return mountSelectors(host,{...options,protocol:{schema:'legaia.system-flag-authoring.v1',snapshotRoute:'/api/system-flag-selectors',reviewRoute:'/api/system-flag-selector-review',commandType:'set_system_flag_selector'}});}
export function mountControllerSystemSelectors(host,options){
 if(!/^scene:\/\/[A-Za-z0-9_-]+\/controllers\/man-p1\/0000$/.test(options.owner))fail('Controller selectors require the dedicated source owner.');
 return mountSelectors(host,{...options,protocol:{schema:'legaia.controller-system-flags.v1',snapshotRoute:'/api/controller-system-flag-selectors',reviewRoute:'/api/controller-system-flag-review',commandType:'set_controller_system_flag_selector'}});
}

export function decodeControllerSystemSelectorSnapshot(raw,owner,context){
 if(!/^scene:\/\/[A-Za-z0-9_-]+\/controllers\/man-p1\/0000$/.test(owner))fail('Controller selector snapshot requires its source owner.');
 return decodeSystemSelectorSnapshot(raw,owner,context,'legaia.controller-system-flags.v1');
}
