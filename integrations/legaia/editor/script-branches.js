// Encoded source flow only. Branch writers and destination qualification live in the SDK.
import {mountScriptFlowOverview} from './script-flow-overview.js';
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const exact=(value,keys)=>object(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const int=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const text=(value,max=8192)=>typeof value==='string'&&value.length>0&&value.length<=max;
const clone=value=>structuredClone(value);
const canonical=value=>Array.isArray(value)?value.map(canonical):object(value)?Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])])):value;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const fail=message=>{throw new Error(message);};
const pc=value=>'0x'+value.toString(16).toUpperCase().padStart(4,'0');
const valueValid=value=>value===null||exact(value,['target_pc'])&&int(value.target_pc,0,32767);
let nextGraph=0;

export function scriptBranchContext(value){
  if(!exact(value,['projectPath','sceneId','mode','scriptKey'])||!text(value.projectPath,32768)||!/^scene:\/\/[A-Za-z0-9_-]{1,128}$/.test(value.sceneId)||!text(value.mode,32)||!hash(value.scriptKey))fail('Script flow requires the current project, scene, and script state key.');
  return clone(value);
}
function ownerValid(owner,scene){return typeof owner==='string'&&new RegExp('^'+scene.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'/(actors/man-p1|scripts/man-p2)/[0-9]{4}$').test(owner);}
function successors(value){
  if(!Array.isArray(value)||value.length>64||value.some(edge=>!object(edge)||!int(edge.pc,0,65536)||!(edge.condition===null||text(edge.condition,256))))fail('Invalid encoded successor collection.');
}
function inspectReport(report){
  if(!object(report)||!['partial','decoded_supported_paths'].includes(report.status)||!Array.isArray(report.instructions)||report.instructions.length>8192||!Array.isArray(report.dialogues)||report.dialogues.length>8192||!Array.isArray(report.stops)||report.stops.length>8192||!Array.isArray(report.opaque_regions)||report.opaque_regions.length>8192)fail('Script flow inspection is invalid or exceeds its bounds.');
  const nodes=new Map();
  for(const row of report.instructions){
    if(!object(row)||!int(row.pc,0,65535)||!int(row.length,1,65536-row.pc)||!text(row.mnemonic,128)||nodes.has(row.pc))fail('Decoded instruction identities are invalid or duplicated.');
    successors(row.successors);nodes.set(row.pc,{...row,kind:'instruction'});
  }
  for(const row of report.dialogues){
    if(!object(row)||!int(row.pc,0,65535)||!int(row.length,1,65536-row.pc)||typeof row.text!=='string'||row.text.length>65536||nodes.has(row.pc))fail('Decoded dialogue identities are invalid or duplicated.');
    nodes.set(row.pc,{...row,kind:'dialogue',mnemonic:'MES_SEGMENT',successors:[{pc:row.pc+row.length,condition:'encoded_continuation'}]});
  }
  for(const row of report.stops)if(!object(row)||!int(row.pc,0,65536)||!text(row.reason))fail('Invalid decoder stop.');
  for(const row of report.opaque_regions)if(!object(row)||!int(row.pc,0,65535)||!int(row.length,1,65536-row.pc)||!text(row.reason))fail('Invalid opaque source region.');
  return nodes;
}
function sourceBound(nodes,source){
  for(const node of nodes.values()){const original=source.get(node.pc);if(!original||node.kind!==original.kind||node.mnemonic!==original.mnemonic||node.length!==original.length||node.kind==='instruction'&&node.target_context!==original.target_context)fail('An inspected path reaches a new or changed source boundary.');}
}

export function decodeScriptBranchSnapshot(value,owner,context){
  context=scriptBranchContext(context);
  const keys=['schema_version','owner_id','state_key','source_record_sha256','source_report','current_report','targets','destinations','supported','reason','limitations','gameplay_verified'];
  if(!ownerValid(owner,context.sceneId)||!object(value)||!keys.every(key=>Object.hasOwn(value,key))||Object.keys(value).some(key=>!keys.includes(key)&&key!=='review')||value.schema_version!=='legaia.script-branches.v1'||value.owner_id!==owner||value.state_key!==context.scriptKey||!hash(value.source_record_sha256)||typeof value.supported!=='boolean'||!(value.reason===null||text(value.reason))||value.gameplay_verified!==false||!Array.isArray(value.targets)||value.targets.length>4096||!Array.isArray(value.destinations)||value.destinations.length>8192||!Array.isArray(value.limitations)||value.limitations.length>64||value.limitations.some(line=>!text(line)))fail('Script branch sources changed or returned invalid qualification.');
  const source=inspectReport(value.source_report),current=value.current_report===null?null:inspectReport(value.current_report);
  if(current!==null)sourceBound(current,source);
  if(value.current_report===null&&value.supported)fail('Supported branch editing requires a verified Current report.');
  if(value.supported&&(value.source_report.stops.length||value.current_report.stops.length))fail('Branch editing requires verified source and Current paths without decoder stops.');
  const destinations=new Set();
  for(const row of value.destinations){if(!exact(row,['pc','mnemonic'])||!int(row.pc,0,32767)||!text(row.mnemonic,128)||destinations.has(row.pc))fail('Invalid or duplicate qualified destination.');const node=source.get(row.pc);if(!node||node.mnemonic!==row.mnemonic)fail('Qualified destination differs from its decoded source.');destinations.add(row.pc);}
  const ids=new Set(),locations=new Set(),prefix='script://'+owner.slice(8)+'/branch/';
  for(const row of value.targets){
    const node=source.get(row?.pc);
    if(!object(row)||!int(row.pc,0,65535)||row.semantic_id!==prefix+row.pc.toString(16).padStart(4,'0')||ids.has(row.semantic_id)||locations.has(row.pc)||!node||row.mnemonic!==node.mnemonic||!text(row.condition,256)||!['relative_u16','absolute_i16','relative_u16_wrap16','relative_i16_wrap16'].includes(row.encoding)||!int(row.target_pc,0,32767)||!int(row.current_target_pc,0,32767)||!valueValid(row.authored_value)||row.current_target_pc!==(row.authored_value?.target_pc??row.target_pc)||!destinations.has(row.target_pc)||!destinations.has(row.current_target_pc)||JSON.stringify(row).length>16384)fail('Branch identity, source destination, or authored layer is invalid.');
    successors(row.successors);if(!same(row.successors,node.successors)||row.successors.filter(edge=>edge.pc===row.target_pc&&edge.condition===row.condition).length!==1)fail('Branch target differs from its encoded source edges.');
    if(Object.hasOwn(row,'current_successors')){successors(row.current_successors);const effective=current?.get(row.pc);if(effective&&!same(row.current_successors,effective.successors)||row.current_successors.filter(edge=>edge.pc===row.current_target_pc&&edge.condition===row.condition).length!==1)fail('Current branch edges differ from their authored destination.');}
    if(Object.hasOwn(row,'decoded_byte_offset')&&!int(row.decoded_byte_offset,0,4*1024*1024-2)||Object.hasOwn(row,'source_record_sha256')&&row.source_record_sha256!==value.source_record_sha256||Object.hasOwn(row,'owner_id')&&row.owner_id!==owner)fail('Branch source locator differs from its owner.');
    ids.add(row.semantic_id);locations.add(row.pc);
  }
  return clone(value);
}

export function decodeScriptBranchReview(value,snapshot,branchId,requested,context){
  const reviewed=decodeScriptBranchSnapshot(value,snapshot.owner_id,context),review=reviewed.review,target=snapshot.targets.find(row=>row.semantic_id===branchId);
  if(!target||!valueValid(requested)||requested!==null&&!snapshot.destinations.some(row=>row.pc===requested.target_pc)||!same({...reviewed,review:undefined},{...snapshot,review:undefined})||!object(review)||!hash(review.review_key)||review.branch_id!==branchId||!same(review.value,requested)||typeof review.no_op!=='boolean'||!Array.isArray(review.audit)||review.audit.length>1||!Array.isArray(review.source_audit)||review.source_audit.length>4096)fail('Branch review differs from the current source or chosen destination.');
  const proposedNodes=inspectReport(review.proposed_report);
  sourceBound(proposedNodes,inspectReport(snapshot.source_report));
  if(review.proposed_report.stops.length)fail('A branch proposal must preserve qualified decoded paths.');
  const destination=requested?.target_pc??target.target_pc;
  for(const row of review.audit){
    if(!object(row)||row.owner_id!==snapshot.owner_id||row.branch_id!==branchId||row.pc!==target.pc||row.mnemonic!==target.mnemonic||row.field!=='script.branch_target'||row.scope!=='script-branch-target-only'||row.before!==target.current_target_pc||row.after!==destination||row.before===row.after||row.source_record_sha256!==snapshot.source_record_sha256||!hash(row.candidate_record_sha256)||!int(row.byte_offset,0,4*1024*1024-2)||Object.hasOwn(target,'decoded_byte_offset')&&row.byte_offset!==target.decoded_byte_offset||row.byte_length!==2||!Array.isArray(row.changed_byte_offsets)||row.changed_byte_offsets.length<1||row.changed_byte_offsets.length>2||new Set(row.changed_byte_offsets).size!==row.changed_byte_offsets.length||row.changed_byte_offsets.some(offset=>!int(offset,row.byte_offset,row.byte_offset+1)))fail('Branch review has an invalid source byte audit.');
  }
  if(review.no_op&&review.audit.length||review.audit.length===0&&destination!==target.current_target_pc)fail('Branch review change count differs from its destination.');
  for(const key of ['newly_unreachable_source_pcs','newly_reached_source_pcs'])if(!Array.isArray(review[key])||review[key].length>8192||review[key].some(value=>!int(value,0,65535))||new Set(review[key]).size!==review[key].length)fail('Invalid decoded reachability difference.');
  if(review.newly_reached_source_pcs.some(value=>review.newly_unreachable_source_pcs.includes(value)))fail('Conflicting decoded reachability differences.');
  const currentNodes=inspectReport(snapshot.current_report),beforePCs=[...currentNodes.keys()],afterPCs=[...proposedNodes.keys()];
  if(!same([...review.newly_unreachable_source_pcs].sort((a,b)=>a-b),beforePCs.filter(value=>!proposedNodes.has(value)).sort((a,b)=>a-b))||!same([...review.newly_reached_source_pcs].sort((a,b)=>a-b),afterPCs.filter(value=>!currentNodes.has(value)).sort((a,b)=>a-b)))fail('Reachability differences disagree with the inspected Current and Proposed paths.');
  const proposedBranch=proposedNodes.get(target.pc);
  if(proposedBranch&&proposedBranch.successors.filter(edge=>edge.pc===destination&&edge.condition===target.condition).length!==1)fail('The proposed flow differs from its reviewed destination.');
  return clone(reviewed);
}

/** A bounded, explicit one-hop comparison. Omitted nodes are not decoder stops. */
export function scriptBranchNeighborhood(current,proposed,selected){
  const currentNodes=inspectReport(current),proposedNodes=proposed===null?new Map():inspectReport(proposed);
  if(!currentNodes.has(selected)&&!proposedNodes.has(selected))return {nodes:[],edges:[],omitted_edge_count:0,total_node_count:currentNodes.size};
  const edges=new Map();
  const add=(nodes,layer)=>{for(const node of nodes.values())for(const [index,edge] of node.successors.entries()){if(node.pc!==selected&&edge.pc!==selected)continue;const key=JSON.stringify([node.pc,edge.pc,edge.condition,index]);const old=edges.get(key);if(old)old.layer='both';else edges.set(key,{source:node.pc,target:edge.pc,condition:edge.condition,layer});}};
  add(currentNodes,'current');if(proposed!==null)add(proposedNodes,'proposed');
  const ordered=[...edges.values()].sort((a,b)=>a.source-b.source||a.target-b.target||String(a.condition).localeCompare(String(b.condition)));
  const visible=new Set([selected]);for(const edge of ordered){if(visible.size>=21)break;visible.add(edge.source);visible.add(edge.target);}
  const shown=ordered.filter(edge=>visible.has(edge.source)&&visible.has(edge.target));
  const nodes=[...visible].sort((a,b)=>a-b).map(value=>{const node=currentNodes.get(value)??proposedNodes.get(value),stop=[...current.stops,...(proposed?.stops??[])].find(row=>row.pc===value);return {pc:value,mnemonic:node?.mnemonic??'Not decoded in this layer',decoded:!!node,reason:stop?.reason??null,side:value===selected?'selected':shown.some(edge=>edge.source===value&&edge.target===selected)?'incoming':'outgoing'};});
  return {nodes,edges:shown,omitted_edge_count:ordered.length-shown.length,total_node_count:new Set([...currentNodes.keys(),...proposedNodes.keys()]).size};
}

function element(tag,label){const node=document.createElement(tag);if(label!==undefined)node.textContent=label;return node;}
function button(label,action){const node=element('button',label);node.type='button';node.dataset.action=action;return node;}
function svgNode(tag,attributes={},label){const node=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [key,value] of Object.entries(attributes))node.setAttribute(key,String(value));if(label!==undefined)node.textContent=label;return node;}

export function mountScriptBranches(host,{owner,getContext,busy,setBusy,api,selectInstruction,reopen,initialDrafts=new Map(),onDraftChange=()=>{},onError=()=>{}}){
  let context,restoredDrafts;
  try{if(!host||[getContext,busy,setBusy,api,selectInstruction,reopen,onDraftChange,onError].some(callback=>typeof callback!=='function'))fail('Script branch controls require source and lifecycle callbacks.');context=scriptBranchContext(getContext());if(!ownerValid(owner,context.sceneId))fail('Script owner belongs to a different scene.');const prefix='script://'+owner.slice(8)+'/branch/';if(!(initialDrafts instanceof Map)||initialDrafts.size>1024||[...initialDrafts].some(([id,value])=>typeof id!=='string'||!id.startsWith(prefix)||!/^[0-9a-f]{4}$/.test(id.slice(prefix.length))||!valueValid(value)))fail('Pending branch drafts require this source owner and exact destination values.');restoredDrafts=new Map([...initialDrafts].map(([id,value])=>[id,clone(value)]));}catch(error){onError(error);return {ready:Promise.resolve(false),select(){return false;},updateState(){},dispose(){}};}
  const section=element('section');section.className='script-branch-authoring';section.dataset.scriptBranches='';section.append(element('h3','Source flow and branch destinations'));
  const note=element('p','Follow encoded conditions and compare Current with reviewed Proposed edges. These paths do not establish which branch executes in the game.');note.className='field-note';section.append(note);
  const status=element('p','Waiting to verify the script source…');status.setAttribute('role','status');const error=element('p');error.className='dialog-error';error.setAttribute('role','alert');
  const tools=element('div');tools.className='dialog-actions';tools.style.flexWrap='wrap';const layer=element('select');layer.setAttribute('aria-label','Script flow layer');for(const [value,label] of [['current','Current encoded flow'],['retail','Retail source flow']]){const option=element('option',label);option.value=value;layer.append(option);}layer.value='current';const refresh=button('Refresh source flow','refresh');tools.append(layer,refresh);
  const graph=element('div');Object.assign(graph.style,{overflowX:'auto',maxHeight:'420px',overflowY:'auto'});graph.dataset.branchGraph='';const graphStatus=element('p');graphStatus.className='field-note';graphStatus.setAttribute('role','status');const links=element('div');links.className='script-predecessors';links.dataset.branchLinks='';const unknown=element('div');unknown.className='script-warning';unknown.dataset.branchUnknown='';
  const form=element('div');form.dataset.branchForm='';const branchLabel=element('label','Source branch'),branch=element('select');branch.setAttribute('aria-label','Source branch');branchLabel.append(branch);const layers=element('p');layers.className='instruction-operand-layers';
  const filter=element('input');filter.type='search';filter.maxLength=128;filter.placeholder='Offset or instruction';filter.setAttribute('aria-label','Filter qualified branch destinations');const destinationLabel=element('label','Qualified decoded destination'),destination=element('select');destination.setAttribute('aria-label','Qualified branch destination');destinationLabel.append(destination);const destinationStatus=element('p');destinationStatus.className='field-note';
  const actions=element('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';const inspect=button('Inspect destination','inspect-destination'),reviewButton=button('Review destination','review'),reset=button('Review reset to Retail','reset'),discard=button('Discard branch draft','discard'),apply=button('Apply reviewed destination','apply');actions.append(inspect,reviewButton,reset,discard,apply);form.append(branchLabel,layers,filter,destinationLabel,destinationStatus,actions);
  const unavailableList=element('div');unavailableList.dataset.unavailableBranchDrafts='';unavailableList.className='script-warning';unavailableList.hidden=true;
  const overviewHost=element('div'),proposedOverviewHost=element('div');
  const assessment=element('div');assessment.dataset.branchReview='';section.append(status,error,tools,overviewHost,proposedOverviewHost,graph,graphStatus,links,unknown,form,unavailableList,assessment);host.append(section);
  let snapshot=null,accepted=null,activeId=null,selectedPC=null,pending=null,controller=null,busyOwner=null,generation=0,disposed=false,stale=false,started=false;
  const drafts=restoredDrafts,unavailableDrafts=new Map(),graphId='script-branch-arrow-'+(++nextGraph);let resolveReady;const ready=new Promise(resolve=>resolveReady=resolve);
  const overview=mountScriptFlowOverview(overviewHost,{selectInstruction:offset=>{if(current()&&pending===null&&busy()===false)selectNode(offset);}});
  const proposedOverview=mountScriptFlowOverview(proposedOverviewHost,{selectInstruction:offset=>{if(current()&&pending===null&&busy()===false)selectNode(offset);}});
  const current=()=>{try{return !disposed&&!stale&&same(context,scriptBranchContext(getContext()));}catch{return false;}};
  const coreCurrent=()=>{try{const value=scriptBranchContext(getContext());return !disposed&&['projectPath','sceneId','mode'].every(key=>value[key]===context[key]);}catch{return false;}};
  const target=()=>snapshot?.targets.find(row=>row.semantic_id===activeId)??null;
  const value=()=>drafts.has(activeId)?drafts.get(activeId):target()?{target_pc:target().current_target_pc}:undefined;
  const reviewed=()=>current()&&accepted?.branch_id===activeId&&same(accepted.value,value());
  const notifyDrafts=()=>onDraftChange(new Map([...drafts].map(([id,value])=>[id,clone(value)])));
  const release=token=>{if(busyOwner===token){busyOwner=null;setBusy(false);}};
  function invalidate(){generation++;controller?.abort();controller=null;if(pending!=='apply')pending=null;if(busyOwner)release(busyOwner);accepted=null;assessment.replaceChildren();}
  function showError(value){error.textContent=value?.message??String(value);onError(value instanceof Error?value:new Error(String(value)));}
  function updateState(){
    if(!disposed&&!stale&&!current()){stale=true;invalidate();status.textContent='Project, scene, mode, or script state changed. Reopen this script.';}
    const available=current(),blocked=!available||pending!==null||busy()!==false,editable=available&&context.mode==='edit'&&snapshot?.supported&&snapshot.current_report!==null;
    const row=target(),chosen=value(),valid=chosen===null||valueValid(chosen)&&snapshot?.destinations.some(item=>item.pc===chosen.target_pc);
    layer.disabled=!snapshot;refresh.disabled=blocked;branch.disabled=filter.disabled=destination.disabled=blocked||!editable||!row;inspect.disabled=!available||!row||!valid||chosen===null;reviewButton.disabled=blocked||!editable||!row||!valid;reset.disabled=blocked||!editable||!row||row.authored_value===null;discard.disabled=blocked||!drafts.has(activeId);apply.disabled=blocked||!editable||!reviewed()||accepted?.no_op;form.hidden=!snapshot?.targets.length;
    for(const node of unavailableList.children)if(node.dataset.action==='discard-unavailable')node.disabled=blocked;
    if(!started&&available&&busy()===false){started=true;void load().then(result=>{resolveReady?.(result);resolveReady=null;});}
  }
  async function request(route,body,signal){const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});const result=await response.json();if(!response.ok||result?.error)fail(result?.error??'Script branch inspection failed.');return result;}
  async function run(kind,work){
    if(!current()||pending!==null||busy()!==false)return false;const token={},ticket=++generation;pending=kind;controller=new AbortController();const signal=controller.signal;busyOwner=token;setBusy(true);error.textContent='';updateState();const valid=()=>current()&&generation===ticket&&!signal.aborted;
    try{return await work(signal,valid);}catch(error){if(valid()&&error?.name!=='AbortError')showError(error);return false;}finally{if(generation===ticket){pending=null;controller=null;}release(token);if(!disposed)updateState();}
  }
  function notifySelection(offset){const result=selectInstruction(offset);if(result===false)status.textContent='This source boundary is not displayed in the instruction table’s current decoded path.';}
  function renderUnavailable(){
    unavailableList.replaceChildren();unavailableList.hidden=unavailableDrafts.size===0;if(!unavailableDrafts.size)return;
    unavailableList.append(element('p','Pending branch drafts are unavailable in this verified snapshot. Discard each explicitly before project actions.'));
    for(const [id,reason] of unavailableDrafts){unavailableList.append(element('p',`${pc(parseInt(id.slice(-4),16))} · ${reason}`));const discard=button(`Discard unavailable branch draft ${pc(parseInt(id.slice(-4),16))}`,'discard-unavailable');discard.dataset.branchId=id;discard.onclick=()=>{if(discard.disabled||!current()||pending!==null||busy()!==false)return false;invalidate();drafts.delete(id);unavailableDrafts.delete(id);notifyDrafts();renderUnavailable();renderFields();draw();updateState();return true;};unavailableList.append(discard);}
  }
  function qualifyDrafts(){
    unavailableDrafts.clear();
    for(const [id,value] of drafts){const row=snapshot?.targets.find(target=>target.semantic_id===id);if(!row){unavailableDrafts.set(id,'This source branch no longer qualifies for destination authoring.');continue;}if(value===null&&row.authored_value===null||value!==null&&value.target_pc===row.current_target_pc){drafts.delete(id);continue;}if(value!==null&&!snapshot.destinations.some(destination=>destination.pc===value.target_pc))unavailableDrafts.set(id,`Destination ${pc(value.target_pc)} is no longer a qualified source boundary.`);}
    notifyDrafts();renderUnavailable();
  }
  function setBranch(id,notify=false){if(!snapshot?.targets.some(row=>row.semantic_id===id))return false;if(activeId!==id){invalidate();activeId=id;}selectedPC=target().pc;renderFields();draw();updateState();if(notify)notifySelection(selectedPC);return true;}
  function select(offset){if(!snapshot)return false;const source=inspectReport(snapshot.source_report),present=source.has(offset)||snapshot.current_report!==null&&inspectReport(snapshot.current_report).has(offset)||accepted&&inspectReport(accepted.proposed_report).has(offset);if(!present)return false;const row=snapshot.targets.find(item=>item.pc===offset);if(row&&row.semantic_id!==activeId)setBranch(row.semantic_id);selectedPC=offset;draw();return true;}
  function selectNode(offset){if(select(offset))notifySelection(offset);}
  function renderFields(){
    branch.replaceChildren();for(const row of snapshot?.targets??[]){const option=element('option',`${pc(row.pc)} · ${row.mnemonic} · ${row.condition}`);option.value=row.semantic_id;branch.append(option);}branch.value=activeId??'';
    const row=target();if(!row){layers.textContent='No source-qualified branch destinations are available.';destination.replaceChildren();return;}
    layers.textContent=`Retail ${pc(row.target_pc)} · Authored ${row.authored_value===null?'inherit':pc(row.authored_value.target_pc)} · Current ${pc(row.current_target_pc)} · ${row.condition}`;
    renderDestinations();
  }
  function renderDestinations(){
    destination.replaceChildren();const chosen=value(),offset=chosen===null?target()?.target_pc:chosen?.target_pc,query=filter.value.trim().toLowerCase();let rows=(snapshot?.destinations??[]).filter(row=>!query||`${pc(row.pc)} ${row.pc} ${row.mnemonic}`.toLowerCase().includes(query));const count=rows.length;rows=rows.slice(0,256);if(offset!==undefined&&!rows.some(row=>row.pc===offset)){const selected=snapshot?.destinations.find(row=>row.pc===offset);if(selected)rows=[selected,...rows.slice(0,255)];}
    for(const row of rows){const option=element('option',`${pc(row.pc)} · ${row.mnemonic}`);option.value=String(row.pc);destination.append(option);}destination.value=offset===undefined?'':String(offset);destinationStatus.textContent=`${count} qualified destination(s)${count>256?' · showing 256; filter by offset or instruction':''}. Only SDK-qualified source instruction or atomic MES starts are selectable; opaque bytes remain excluded.`;
  }
  function draw(){
    graph.replaceChildren();links.replaceChildren();unknown.replaceChildren();if(!snapshot)return;
    let retail=layer.value==='retail'||snapshot.current_report===null,base=retail?snapshot.source_report:snapshot.current_report,proposal=!retail&&reviewed()?accepted.proposed_report:null,nodes=inspectReport(base),fallback=false;
    if(selectedPC!==null&&!nodes.has(selectedPC)&&!(proposal&&inspectReport(proposal).has(selectedPC))&&inspectReport(snapshot.source_report).has(selectedPC)){retail=true;fallback=true;base=snapshot.source_report;proposal=null;nodes=inspectReport(base);layer.value='retail';}
    if(selectedPC===null||!nodes.has(selectedPC)&&!(proposal&&inspectReport(proposal).has(selectedPC)))selectedPC=nodes.keys().next().value??null;
    if(retail&&selectedPC!==null&&snapshot.current_report!==null&&!inspectReport(snapshot.current_report).has(selectedPC))fallback=true;
    overview.update(base,{label:retail?'Retail source flow':'Current encoded flow'});
    proposedOverviewHost.hidden=!proposal;
    if(proposal)proposedOverview.update(proposal,{label:'Reviewed Proposed encoded flow'});
    unknown.hidden=base.stops.length===0&&base.opaque_regions.length===0;
    for(const row of base.stops.slice(0,32))unknown.append(element('p',`${pc(row.pc)} · Decoder stop: ${row.reason}`));for(const row of base.opaque_regions.slice(0,32))unknown.append(element('p',`${pc(row.pc)} · ${row.length} opaque source bytes: ${row.reason}`));if(base.stops.length>32||base.opaque_regions.length>32)unknown.append(element('p','Additional unresolved regions remain in the source inspection.'));
    if(selectedPC===null){graphStatus.textContent='No decoded source boundaries are available. Opaque bytes remain unresolved.';return;}
    const neighborhood=scriptBranchNeighborhood(base,proposal,selectedPC),left=neighborhood.nodes.filter(row=>row.side==='incoming'),right=neighborhood.nodes.filter(row=>row.side==='outgoing'),height=Math.max(210,80+Math.max(left.length,right.length)*76),positions=new Map([[selectedPC,{x:270,y:height/2-24}]]);
    left.forEach((row,index)=>positions.set(row.pc,{x:8,y:32+index*76}));right.forEach((row,index)=>positions.set(row.pc,{x:534,y:32+index*76}));
    const svg=svgNode('svg',{viewBox:`0 0 720 ${height}`,role:'img','aria-label':retail?'Retail source flow neighborhood':'Current and reviewed Proposed flow neighborhood'});Object.assign(svg.style,{width:'100%',minWidth:'600px',display:'block'});const defs=svgNode('defs');for(const [suffix,color] of [['current','#9bc7dd'],['proposed','#efb775'],['both','#a0d4ae']]){const marker=svgNode('marker',{id:graphId+'-'+suffix,viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:6,markerHeight:6,orient:'auto-start-reverse'});marker.append(svgNode('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:color}));defs.append(marker);}svg.append(defs);
    for(const [index,edge] of neighborhood.edges.entries()){
      const from=positions.get(edge.source),to=positions.get(edge.target),color=edge.layer==='proposed'?'#efb775':edge.layer==='both'?'#a0d4ae':'#9bc7dd';const x1=from.x+174,y1=from.y+24,x2=to.x,y2=to.y+24,loop=edge.source===edge.target,d=loop?`M ${from.x+120} ${from.y} C ${from.x+200} ${from.y-60}, ${from.x-20} ${from.y-60}, ${from.x+48} ${from.y}`:`M ${x1} ${y1} C ${(x1+x2)/2} ${y1+index%3*6}, ${(x1+x2)/2} ${y2}, ${x2} ${y2}`;svg.append(svgNode('path',{d,fill:'none',stroke:color,'stroke-width':2,'stroke-dasharray':edge.layer==='proposed'?'6 3':'none','marker-end':`url(#${graphId}-${edge.layer})`}));
      const label=retail?'Retail':edge.layer==='both'?'Current / Proposed':edge.layer==='current'?'Current':'Proposed';const link=element('button',`${label} ${pc(edge.source)} → ${pc(edge.target)} · ${edge.condition??'encoded edge'}`);link.type='button';link.dataset.edgeLayer=retail?'retail':edge.layer;link.disabled=!neighborhood.nodes.find(row=>row.pc===edge.target)?.decoded;link.onclick=()=>selectNode(edge.target);links.append(link);
    }
    for(const row of neighborhood.nodes){const position=positions.get(row.pc),group=svgNode('g',{transform:`translate(${position.x},${position.y})`,role:row.decoded?'button':'img','aria-label':`${pc(row.pc)} ${row.mnemonic}${row.reason?' · '+row.reason:''}`,tabindex:row.decoded?0:-1});group.dataset.pc=String(row.pc);group.append(svgNode('rect',{width:174,height:48,rx:5,fill:row.side==='selected'?'#29463c':'#172123',stroke:row.decoded?'#a0d4ae':'#d6aa5e'}),svgNode('text',{x:8,y:17,fill:'#d8e3dd','font-size':12},pc(row.pc)),svgNode('text',{x:8,y:35,fill:'#d8e3dd','font-size':10},row.mnemonic.slice(0,27)));if(row.decoded){group.onclick=()=>selectNode(row.pc);group.onkeydown=event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();selectNode(row.pc);}};}svg.append(group);}
    graph.append(svg);graphStatus.textContent=`${fallback?'Selected source boundary is not decoded in Current; displaying Retail source. ':''}${retail?'Retail source':'Current'+(proposal?' / reviewed Proposed':'')} · selected ${pc(selectedPC)} · ${neighborhood.nodes.length} displayed nodes of ${neighborhood.total_node_count} decoded boundaries. ${neighborhood.omitted_edge_count} neighboring edge(s) omitted by the display limit. Undecoded targets remain marked; reachability is not runtime execution.`;
  }
  async function load(){const result=await run('load',async(signal,valid)=>{status.textContent='Verifying source branch boundaries…';const raw=await request('/api/script-branches',{entity:owner},signal);if(!valid())return false;snapshot=decodeScriptBranchSnapshot(raw,owner,context);qualifyDrafts();activeId=[...drafts.keys()].find(id=>!unavailableDrafts.has(id))??snapshot.targets[0]?.semantic_id??null;selectedPC=target()?.pc??snapshot.source_report.instructions[0]?.pc??null;layer.children[0].disabled=snapshot.current_report===null;layer.value=snapshot.current_report===null?'retail':'current';renderFields();draw();status.textContent=snapshot.reason??`${snapshot.targets.length} qualified branch destination(s). Review before Apply.`;return true;});if(!result&&current()){snapshot=null;activeId=null;for(const id of drafts.keys())unavailableDrafts.set(id,'The source could not be verified; this draft cannot be applied.');renderUnavailable();notifyDrafts();draw();status.textContent='Source flow could not be verified. Pending drafts require explicit discard.';updateState();}return result;}
  async function reviewValue(requested){
    if(!current()||context.mode!=='edit'||!snapshot?.supported||!target()||!valueValid(requested)||requested!==null&&!snapshot.destinations.some(row=>row.pc===requested.target_pc)||pending!==null||busy()!==false)return false;invalidate();const id=activeId,row=target();unavailableDrafts.delete(id);if(requested===null&&row.authored_value===null||requested!==null&&requested.target_pc===row.current_target_pc)drafts.delete(id);else drafts.set(id,clone(requested));notifyDrafts();renderUnavailable();renderDestinations();
    return run('review',async(signal,valid)=>{status.textContent='Reviewing the encoded destination…';const raw=await request('/api/script-branch-review',{entity:owner,branch_id:id,value:clone(requested)},signal);if(!valid()||activeId!==id)return false;const decoded=decodeScriptBranchReview(raw,snapshot,id,requested,context);accepted=decoded.review;assessment.replaceChildren();assessment.append(element('p',`Current ${pc(row.current_target_pc)} → Proposed ${pc(requested?.target_pc??row.target_pc)} · ${row.condition}`),element('p',`${accepted.audit.reduce((sum,item)=>sum+item.changed_byte_offsets.length,0)} changed source bytes · ${accepted.newly_unreachable_source_pcs.length} newly unvisited decoded instruction(s) · ${accepted.newly_reached_source_pcs.length} newly reached decoded instruction(s).`));for(const [key,label] of [['newly_unreachable_source_pcs','Newly unvisited'],['newly_reached_source_pcs','Newly reached']])for(const offset of accepted[key].slice(0,64)){const inspect=button(`${label}: inspect ${pc(offset)}`,'inspect-reachability');inspect.onclick=()=>selectNode(offset);assessment.append(inspect);}status.textContent=accepted.no_op?'This destination makes no authored change.':accepted.audit.length?'Review complete. Explicit Apply is required.':'Review complete. The authored layer changes without changing source bytes.';draw();return true;});
  }
  branch.onchange=()=>{if(!current()||pending==='apply')return;setBranch(branch.value,true);};filter.oninput=()=>{renderDestinations();updateState();};layer.onchange=()=>draw();destination.onchange=()=>{if(!current()||pending==='apply'||!target())return;const offset=Number(destination.value);if(!snapshot.destinations.some(row=>row.pc===offset))return;invalidate();unavailableDrafts.delete(activeId);if(offset===target().current_target_pc)drafts.delete(activeId);else drafts.set(activeId,{target_pc:offset});notifyDrafts();renderUnavailable();draw();updateState();};
  inspect.onclick=()=>{if(inspect.disabled)return false;notifySelection(value()?.target_pc??target().target_pc);return true;};reviewButton.onclick=()=>reviewValue(value());reset.onclick=()=>reset.disabled?false:reviewValue(null);discard.onclick=()=>{if(discard.disabled)return false;invalidate();drafts.delete(activeId);unavailableDrafts.delete(activeId);notifyDrafts();renderUnavailable();renderFields();status.textContent='Branch draft discarded. Current encoded flow is unchanged.';draw();updateState();return true;};refresh.onclick=()=>{if(refresh.disabled)return false;invalidate();return load();};
  apply.onclick=async()=>{
    if(apply.disabled||!reviewed()||accepted.no_op||pending!==null||busy()!==false)return false;const id=activeId,review=clone(accepted),focus=target().pc;pending='apply';error.textContent='';updateState();
    try{const success=await api('/api/command',{type:'set_branch',entity:owner,branch_id:id,value:clone(review.value),review_key:review.review_key});if(success!==true){if(current()){accepted=null;assessment.replaceChildren();status.textContent='Apply failed. Review the destination again.';}return false;}if(!coreCurrent())return false;drafts.delete(id);notifyDrafts();pending=null;await reopen(focus);return true;}catch(error){if(coreCurrent()){accepted=null;showError(error);}return false;}finally{if(!disposed){pending=null;updateState();}}
  };
  function dispose(){if(disposed)return;disposed=true;invalidate();pending=null;resolveReady?.(false);resolveReady=null;overview.dispose();proposedOverview.dispose();section.remove();}
  updateState();return {ready,select,updateState,dispose};
}
