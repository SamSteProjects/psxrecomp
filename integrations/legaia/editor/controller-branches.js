import {mountControllerBranchWalkthrough} from './script-branch-walkthrough.js';
import {mountScriptFlowOverview} from './script-flow-overview.js';
import {mountScriptNodeLayers} from './script-node-layers.js';
import {scriptBranchContext,decodeControllerBranchSnapshot,inspectBranchReport,qualifyBranchSourceBoundaries} from './script-branches.js';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const fail=m=>{throw Error(m);},pc=v=>'0x'+v.toString(16).padStart(4,'0');
export function decodeControllerBranchReview(raw,snapshot,id,value){
 const t=snapshot.targets.find(t=>t.semantic_id===id),destination=value?.target_pc??t?.target_pc;
 if(!t||value!==null&&(!value||Object.keys(value).length!==1||!Number.isSafeInteger(value.target_pc)||!snapshot.destinations.some(d=>d.pc===value.target_pc))||raw?.schema_version!==snapshot.schema_version||raw.owner_id!==snapshot.owner_id||raw.operand_id!==id||!same(raw.value,value)||raw.state_key!==snapshot.state_key||raw.source_record_sha256!==snapshot.source_record_sha256||raw.current_record_sha256!==snapshot.current_record_sha256||!hash(raw.proposed_record_sha256)||!hash(raw.review_key)||raw.project_changed!==false||raw.gameplay_verified!==false||typeof raw.no_op!=='boolean'||typeof raw.native_bytes_changed!=='boolean'||!same(raw.source_report,snapshot.source_report)||!same(raw.current_report,snapshot.current_report)||!same(raw.targets,snapshot.targets)||!same(raw.destinations,snapshot.destinations))fail('Controller branch Review differs from the source or chosen destination.');
 const nodes=inspectBranchReport(raw.proposed_report),current=inspectBranchReport(snapshot.current_report);
 qualifyBranchSourceBoundaries(nodes,inspectBranchReport(snapshot.source_report));
 if(raw.proposed_report.stops.length)fail('Controller proposal has unresolved paths.');
 const offsets=raw.changed_decoded_byte_offsets;
 if(!Array.isArray(offsets)||offsets.length>2||new Set(offsets).size!==offsets.length||offsets.some(n=>!Number.isSafeInteger(n)||!Number.isSafeInteger(t.decoded_byte_offset)||n!==t.decoded_byte_offset&&n!==t.decoded_byte_offset+1)||raw.native_bytes_changed!==(offsets.length>0)||raw.native_bytes_changed!==(raw.current_record_sha256!==raw.proposed_record_sha256)||raw.no_op&&(raw.native_bytes_changed||raw.current_record_sha256!==raw.proposed_record_sha256))fail('Controller branch Review has invalid byte evidence.');
 for(const [key,expected] of [['newly_unreachable_source_pcs',[...current.keys()].filter(p=>!nodes.has(p))],['newly_reached_source_pcs',[...nodes.keys()].filter(p=>!current.has(p))]])if(!same(raw[key],expected.sort((a,b)=>a-b)))fail('Controller branch reachability differs from decoded paths.');
 const proposed=nodes.get(t.pc);
 if(proposed&&proposed.successors.filter(e=>e.pc===destination&&e.condition===t.condition).length!==1)fail('Controller proposal differs from its encoded destination.');
 return structuredClone(raw);
}
const el=(tag,label='')=>{const n=document.createElement(tag);n.textContent=label;return n;};
export function mountControllerBranches(host,{owner,getContext,busy,setBusy,api,reopen,focusPc=null,getProjectSourceKey=()=>null,onError=()=>{}}){
 const context=scriptBranchContext(getContext());
 if(owner!==context.sceneId+'/controllers/man-p1/0000')fail('Controller branches require their dedicated scene owner.');
 const section=el('section');section.dataset.controllerBranches='';section.style.overflowWrap='anywhere';
 section.append(el('h3','Controller Branch Destinations'),el('p','Choose an encoded source destination. Decoded reachability does not establish gameplay execution.'));
 const status=el('p','Verifying controller branches…'),source=el('select'),destination=el('select'),layers=el('p'),assessment=el('pre');
 status.setAttribute('role','status');source.setAttribute('aria-label','Controller source branch');destination.setAttribute('aria-label','Proposed controller destination');
 source.style.maxWidth=destination.style.maxWidth='100%';assessment.style.whiteSpace='pre-wrap';assessment.style.overflowWrap='anywhere';
 const actions=el('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';const buttons={};
 for(const [id,label] of [['review','Review branch'],['reset','Review reset to Retail'],['discard','Discard branch draft'],['apply','Apply reviewed branch']]){const b=el('button',label);b.type='button';b.dataset.controllerBranchAction=id;buttons[id]=b;actions.append(b);}
 const boundary=el('select');boundary.setAttribute('aria-label','Controller flow boundary');boundary.style.maxWidth='100%';
 const flowHost=el('div');flowHost.dataset.controllerBranchFlow='';
 flowHost.append(el('h4','Current and Reviewed Proposed Flow'),el('p','Choose a source boundary to compare encoded operands and successors. Unvisited boundaries retain their source bytes; gameplay execution remains unknown.'),boundary);
 section.append(status,source,layers,destination,actions,assessment,flowHost);host.append(section);
 const nodeLayers=mountScriptNodeLayers(flowHost);
 const chooseBoundary=pc=>{if(!fresh()||busy()||pending||!snapshot?.destinations.some(d=>d.pc===pc))return false;boundary.value=String(pc);drawFlow();return true;};
 const currentFlow=mountScriptFlowOverview(flowHost,{label:'Current controller encoded flow',title:'Current Controller Flow Overview',selectInstruction:chooseBoundary});
 const proposedHost=el('div');proposedHost.dataset.controllerProposedFlow='';flowHost.append(proposedHost);
 const proposedFlow=mountScriptFlowOverview(proposedHost,{label:'Reviewed Proposed controller encoded flow',title:'Reviewed Proposed Controller Flow Overview',selectInstruction:chooseBoundary});

 let snapshot=null,accepted=null,pending=false,disposed=false,generation=0,abort=null;
 const fresh=()=>{try{return !disposed&&same(context,scriptBranchContext(getContext()));}catch{return false;}};
 const walkthrough=mountControllerBranchWalkthrough(flowHost,{owner,getContext,getProjectSourceKey,current:fresh,busy,selection:()=>Number(boundary.value),selectInstruction:chooseBoundary,onError,
  request:async(route,body,signal)=>{const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),raw=await response.json();if(!response.ok||raw.error)fail(raw.error||'Controller walkthrough source could not be verified.');return raw;},
  decodeSnapshot:decodeControllerBranchSnapshot,decodeReview:(raw,s,id,value)=>({review:decodeControllerBranchReview(raw,s,id,value)})});
 const row=()=>snapshot?.targets.find(t=>t.semantic_id===source.value);
 function invalidate(){generation++;abort?.abort();accepted=null;assessment.textContent='';drawFlow();}
 function updateState(){walkthrough.updateState();const disabled=!fresh()||context.mode!=='edit'||pending||busy()||!snapshot?.supported;source.disabled=destination.disabled=disabled;boundary.disabled=!fresh()||pending||busy()||!snapshot;buttons.review.disabled=disabled||!row();buttons.reset.disabled=disabled||!row()?.authored_value;buttons.discard.disabled=disabled;buttons.apply.disabled=disabled||!accepted||accepted.no_op; if(!fresh()){invalidate();section.hidden=true;}}
 function drawFlow(){
  walkthrough.sync(snapshot,accepted);
  if(!fresh()||!snapshot){nodeLayers.clear('Controller flow source changed. Reopen inspection.');proposedHost.hidden=true;return;}
  const selected=Number(boundary.value);
  nodeLayers.update(snapshot.source_report,snapshot.current_report,accepted?.proposed_report??null,Number.isSafeInteger(selected)&&snapshot.destinations.some(d=>d.pc===selected)?selected:null);
  if(snapshot.current_report)currentFlow.update(snapshot.current_report);else currentFlow.update(snapshot.source_report,{label:'Retail controller source · Current unavailable'});
  proposedHost.hidden=!accepted;
  if(accepted)proposedFlow.update(accepted.proposed_report);
 }
 function render(){const t=row();accepted=null;assessment.textContent='';destination.value=String(t?.current_target_pc??'');layers.textContent=t?`Retail ${pc(t.target_pc)} · Current ${pc(t.current_target_pc)} · Authored ${t.authored_value?pc(t.authored_value.target_pc):'None'}`:'';boundary.value=String(t?.pc??snapshot?.destinations[0]?.pc??'');drawFlow();updateState();}
 async function request(route,body,decode){if(!fresh()||pending||busy())return false;const own=++generation;pending=true;abort=new AbortController();setBusy(true);updateState();try{const r=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:abort.signal}),raw=await r.json();if(!fresh()||own!==generation)return false;if(!r.ok||raw.error)fail(raw.error||'Controller branch request failed');decode(raw);return true;}catch(e){if(fresh()&&own===generation&&e.name!=='AbortError'){status.textContent=e.message;onError(e);}return false;}finally{pending=false;setBusy(false);updateState();}}
 const ready=request('/api/controller-branches',{entity:owner},raw=>{snapshot=decodeControllerBranchSnapshot(raw,owner,context);for(const t of snapshot.targets){const o=el('option',`${pc(t.pc)} · ${t.mnemonic} · ${t.condition}`);o.value=t.semantic_id;source.append(o);}for(const d of snapshot.destinations){const o=el('option',`${pc(d.pc)} · ${d.mnemonic}`);o.value=String(d.pc);destination.append(o);const b=el('option',`${pc(d.pc)} · ${d.mnemonic}`);b.value=String(d.pc);boundary.append(b);}source.value=(snapshot.targets.find(t=>t.pc===focusPc)??snapshot.targets[0])?.semantic_id??'';render();status.textContent=snapshot.reason??`${snapshot.targets.length} qualified branches. Review before Apply.`;});
 boundary.onchange=()=>drawFlow();
 source.onchange=()=>{invalidate();render();};destination.onchange=()=>{invalidate();updateState();};
 async function review(value){const t=row();if(!t)return false;invalidate();return request('/api/controller-branch-review',{entity:owner,operand_id:t.semantic_id,value},raw=>{accepted=decodeControllerBranchReview(raw,snapshot,t.semantic_id,value);assessment.textContent=`Current ${pc(t.current_target_pc)} → Proposed ${pc(value?.target_pc??t.target_pc)}\n${accepted.changed_decoded_byte_offsets.length} changed bytes · ${accepted.newly_unreachable_source_pcs.length} newly unvisited boundaries · ${accepted.newly_reached_source_pcs.length} newly reached boundaries`;status.textContent=accepted.no_op?'No authored change.':'Review complete. Explicit Apply is required.';drawFlow();});}
 buttons.review.onclick=()=>buttons.review.disabled?false:review({target_pc:Number(destination.value)});buttons.reset.onclick=()=>buttons.reset.disabled?false:review(null);buttons.discard.onclick=()=>{if(buttons.discard.disabled)return false;invalidate();render();return true;};
 buttons.apply.onclick=async()=>{if(buttons.apply.disabled||!fresh()||pending||busy())return false;const proposal=structuredClone(accepted),focus=row().pc;pending=true;updateState();try{const success=await api('/api/command',{type:'set_controller_branch',entity_id:owner,operand_id:proposal.operand_id,value:proposal.value,review_key:proposal.review_key});accepted=null;const now=getContext();if(success!==true||disposed||['projectPath','sceneId','mode'].some(k=>now[k]!==context[k]))return false;await reopen(focus);return true;}catch(e){if(!disposed){status.textContent=e.message;onError(e);}return false;}finally{pending=false;accepted=null;drawFlow();updateState();}};
 return {ready,updateState,dispose(){if(disposed)return;disposed=true;invalidate();walkthrough.dispose();nodeLayers.dispose();currentFlow.dispose();proposedFlow.dispose();section.remove();}};
}
