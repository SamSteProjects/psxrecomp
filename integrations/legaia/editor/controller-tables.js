import {controllerSnapshotRequest} from './controller-workspace-snapshot.js';
import {compactControllerAuthoring} from './controller-authoring-availability.js';
import {controllerAuthoringFocus} from './controller-authoring-focus.js';
import {mountControllerOperandFlow} from './controller-operand-flow.js';
import {scriptBranchContext,inspectBranchReport,qualifyBranchSourceBoundaries} from './script-branches.js';
const fields=Array.from({length:16},(_,i)=>'word_'+i),hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v),fail=m=>{throw Error(m);};
const canonical=v=>Array.isArray(v)?v.map(canonical):v!==null&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v,same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const values=v=>v!==null&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===1&&Array.isArray(v.signed_words)&&v.signed_words.length===16&&v.signed_words.every(w=>Number.isSafeInteger(w)&&w>=-32768&&w<=32767);
const fieldValue=(v,k)=>v.signed_words[Number(k.slice(5))];
const fieldName=k=>'Signed Word '+k.slice(5);
const nodes=r=>inspectBranchReport({...r,instructions:[...r.instructions,...(r.unvisited_instructions??[])],dialogues:[...r.dialogues,...(r.unvisited_dialogues??[])]});
const pc=v=>'0x'+v.toString(16).toUpperCase().padStart(4,'0');
function tableCopy(node){
 const header=node?.target_context===null?1:2;
 if(!node||node.mnemonic!=='FIELD_TABLE_COPY'||node.length!==header+33||typeof node.raw_hex!=='string'||!/^[a-f0-9]+$/.test(node.raw_hex)||node.raw_hex.length!==node.length*2||!Number.isSafeInteger(node.byte_offset)||node.byte_offset<0||header===2&&(!Number.isSafeInteger(node.target_context)||node.target_context<0||node.target_context>255))fail('Controller table-copy instruction evidence is invalid.');
 const bytes=node.raw_hex.match(/../g).map(v=>parseInt(v,16));
 if(bytes[0]!== (header===1?0x4c:0xcc)||header===2&&bytes[1]!==node.target_context||bytes[header]!==0x9e||node.operands?.sub_op!==bytes[header])fail('Controller table-copy opcode or dispatch context changed.');
 const word=at=>{const raw=bytes[at]|(bytes[at+1]<<8);return raw>=32768?raw-65536:raw;};
 const v={signed_words:Array.from({length:16},(_,i)=>word(header+1+2*i))};
 if(!same(node.operands?.signed_words,v.signed_words)||!same(node.successors,[{pc:node.pc+node.length,condition:'encoded_continuation'}]))fail('Controller table-copy operands differ from their bytes.');
 return v;
}
export function decodeControllerTableCopySnapshot(raw,owner,context){
 context=scriptBranchContext(context);
 if(owner!==context.sceneId+'/controllers/man-p1/0000'||raw?.schema_version!=='legaia.controller-table-copies.v1'||raw.owner_id!==owner||raw.state_key!==context.scriptKey||!hash(raw.source_record_sha256)||!hash(raw.current_record_sha256)||raw.gameplay_verified!==false||!Array.isArray(raw.targets)||raw.targets.length>1024||raw.supported!==(raw.targets.length>0)||!Array.isArray(raw.limitations)||raw.source?.owner_id!==owner||raw.source.record_kind!=='man_partition_1_scene_controller'||raw.source.runtime_execution!=='not_asserted')fail('Controller table-copy snapshot source changed.');
 const source=nodes(raw.source_report),current=nodes(raw.current_report);qualifyBranchSourceBoundaries(current,source);
 if(current.size!==source.size)fail('Controller table-copy snapshot lost retained source boundaries.');
 const seen=new Set();
 for(const t of raw.targets){
  const original=source.get(t.pc),now=current.get(t.pc),v=tableCopy(original),cv=tableCopy(now),header=original.target_context===null?1:2;
  if(seen.has(t.semantic_id)||t.semantic_id!==owner.replace('scene://','script://')+'/table-copy/'+t.pc.toString(16).padStart(4,'0')||t.owner_id!==owner||t.mnemonic!==original.mnemonic||t.sub_op!==original.operands.sub_op||t.target_context!==original.target_context||t.source_record_sha256!==raw.source_record_sha256||t.decoded_byte_offset!==original.byte_offset+header+1||now.byte_offset!==original.byte_offset||now.raw_hex.slice(0,(header+1)*2)!==original.raw_hex.slice(0,(header+1)*2)||!values(t.values)||!same(t.values,v)||!values(t.current_values)||!same(t.current_values,cv)||!(t.authored_values===null||values(t.authored_values))||!same(cv,t.authored_values??v))fail('Controller table-copy target differs from its source or Current bytes.');seen.add(t.semantic_id);
 }
 if(!raw.source_report.stops.length&&raw.targets.length!==[...source.values()].filter(n=>n.mnemonic==='FIELD_TABLE_COPY').length)fail('Controller table-copy snapshot omitted a source target.');
 if(raw.targets.length&&raw.source_report.stops.length)fail('Controller table-copy authoring contains unknown source paths.');
 return structuredClone(raw);
}
export function decodeControllerTableCopyReview(raw,snapshot,id,value){
 const target=snapshot.targets.find(t=>t.semantic_id===id);
 if(!target||!(value===null||values(value))||raw?.schema_version!==snapshot.schema_version||raw.owner_id!==snapshot.owner_id||raw.operand_id!==id||!same(raw.value,value)||raw.state_key!==snapshot.state_key||raw.source_record_sha256!==snapshot.source_record_sha256||raw.current_record_sha256!==snapshot.current_record_sha256||!hash(raw.proposed_record_sha256)||!hash(raw.review_key)||raw.project_changed!==false||raw.gameplay_verified!==false||typeof raw.no_op!=='boolean'||typeof raw.native_bytes_changed!=='boolean'||!same(raw.source_report,snapshot.source_report)||!same(raw.current_report,snapshot.current_report))fail('Controller table-copy Review differs from the source or draft.');
 const current=nodes(snapshot.current_report),proposed=nodes(raw.proposed_report);qualifyBranchSourceBoundaries(proposed,nodes(snapshot.source_report));
 if(current.size!==proposed.size||raw.proposed_report.stops.length)fail('Controller table-copy Review changed source boundaries.');
 const changed=[];
 for(const [at,before] of current){const after=proposed.get(at);if(!after||!same(before.successors,after.successors)||before.byte_offset!==after.byte_offset||at!==target.pc&&before.raw_hex!==after.raw_hex)fail('Controller table-copy Review changed unrelated instructions.');if(at===target.pc){const v=tableCopy(after);if(!same(v,value??target.values))fail('Controller table-copy Proposed values differ from the draft.');const a=before.raw_hex.match(/../g),b=after.raw_hex.match(/../g);for(let i=0;i<a.length;i++)if(a[i]!==b[i])changed.push(before.byte_offset+i);}}
 if(changed.some(at=>at<target.decoded_byte_offset||at>=target.decoded_byte_offset+32)||!same(raw.changed_decoded_byte_offsets,changed)||raw.native_bytes_changed!==(changed.length>0)||raw.native_bytes_changed!==(raw.current_record_sha256!==raw.proposed_record_sha256)||raw.no_op&&raw.native_bytes_changed)fail('Controller table-copy Review byte evidence differs from its proposal.');
 return structuredClone(raw);
}
const el=(tag,text='')=>{const n=document.createElement(tag);n.textContent=text;return n;};
export function mountControllerTables(host,{owner,getContext,busy,setBusy,api,reopen,focusPc=null,initialSnapshot=null,onError=()=>{}}){
 const context=scriptBranchContext(getContext());if(owner!==context.sceneId+'/controllers/man-p1/0000')fail('Controller table-copy controls require their source owner.');
 const section=el('section');section.dataset.controllerTables='';section.style.overflowWrap='anywhere';
 const source=el('select'),status=el('p','Verifying table copies…'),layers=el('p'),assessment=el('pre'),inputs={};source.setAttribute('aria-label','Controller table-copy request');source.style.maxWidth='100%';status.setAttribute('role','status');assessment.style.whiteSpace='pre-wrap';
 section.append(el('h3','Controller Table Copies'),el('p','Edit sixteen signed words (−32768–32767). Word meanings, runtime table bindings and visible effects remain unresolved.'),status,source,layers);
 const fieldGrid=el('div');fieldGrid.style.cssText='display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,180px),1fr));gap:12px';section.append(fieldGrid);
 for(const key of fields){const label=el('label',fieldName(key)),input=el('input');input.type='text';input.inputMode='numeric';input.maxLength=6;input.setAttribute('aria-label','Proposed '+fieldName(key));input.style.cssText='width:100%;box-sizing:border-box';inputs[key]=input;label.append(input);fieldGrid.append(label);}
 const actions=el('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';const buttons={};for(const [id,text] of [['review','Review table copy'],['reset','Review table-copy reset to Retail'],['discard','Discard table-copy draft'],['apply','Apply reviewed table copy']]){const b=el('button',text);b.type='button';b.dataset.controllerTableAction=id;buttons[id]=b;actions.append(b);}section.append(actions,assessment);host.append(section);
 let snapshot=null,accepted=null,pending=false,disposed=false,generation=0,abort=null,resetDraft=false;
 const flow=mountControllerOperandFlow(section,{getContext,current:()=>fresh(),busy:()=>pending||busy()});
 const fresh=()=>{try{return !disposed&&same(context,scriptBranchContext(getContext()));}catch{return false;}},row=()=>snapshot?.targets.find(t=>t.semantic_id===source.value);
 const choice=()=>{if(resetDraft)return null;const v={signed_words:Array(16).fill(0)};for(const key of fields){if(!(/^-?\d{1,5}$/).test(inputs[key].value))return undefined;const n=Number(inputs[key].value);v.signed_words[Number(key.slice(5))]=n;}return values(v)?v:undefined;};
 const invalidate=()=>{generation++;abort?.abort();accepted=null;assessment.textContent='';if(snapshot)flow.sync(snapshot,null,row()?.pc??null);};
 function updateState(){flow.updateState();const blocked=!fresh()||context.mode!=='edit'||pending||busy()||!row();source.disabled=blocked;for(const input of Object.values(inputs))input.disabled=blocked;buttons.review.disabled=blocked||choice()===undefined;buttons.reset.disabled=blocked||!row()?.authored_values;buttons.discard.disabled=blocked;buttons.apply.disabled=blocked||!accepted||accepted.no_op||!same(accepted.value,choice());if(!fresh()){invalidate();section.hidden=true;}}
 function render(){const t=row();resetDraft=false;for(const key of fields)inputs[key].value=t?String(fieldValue(t.current_values,key)):'';layers.textContent=t?`Retail: ${fields.map(k=>fieldValue(t.values,k)).join(', ')} · Current: ${fields.map(k=>fieldValue(t.current_values,k)).join(', ')} · Authored: ${t.authored_values?'Present':'None'}`:'';flow.sync(snapshot,null,t?.pc??null);updateState();}
 async function request(route,body,decode){if(!fresh()||pending||busy())return false;const ticket=++generation;pending=true;abort=new AbortController();setBusy(true);updateState();try{const response=await controllerSnapshotRequest(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:abort.signal},initialSnapshot,'/api/controller-table-copies'),raw=await response.json();if(!fresh()||ticket!==generation)return false;if(!response.ok||raw.error)fail(raw.error||'Controller table-copy request failed');decode(raw);return true;}catch(e){if(fresh()&&ticket===generation&&e.name!=='AbortError'){status.textContent=e.message;onError(e);}return false;}finally{pending=false;setBusy(false);updateState();}}
 const ready=request('/api/controller-table-copies',{entity:owner},raw=>{snapshot=decodeControllerTableCopySnapshot(raw,owner,context);for(const t of snapshot.targets){const option=el('option',pc(t.pc)+' · Table Copy');option.value=t.semantic_id;source.append(option);}source.value=(snapshot.targets.find(t=>t.pc===focusPc)??snapshot.targets[0])?.semantic_id??'';render();status.textContent=snapshot.reason??`${snapshot.targets.length} source-qualified table copies. Review before Apply.`;compactControllerAuthoring(section,snapshot,status);});
 source.onchange=()=>{if(source.disabled)return;invalidate();render();};
 for(const input of Object.values(inputs))input.oninput=()=>{if(!fresh()||input.disabled)return;invalidate();resetDraft=false;status.textContent=choice()===undefined?'Enter sixteen whole signed words −32768–32767.':'Draft changed. Review before Apply.';updateState();};
 async function review(value){const t=row();if(!t)return false;invalidate();return request('/api/controller-table-copy-review',{entity:owner,operand_id:t.semantic_id,value},raw=>{accepted=decodeControllerTableCopyReview(raw,snapshot,t.semantic_id,value);try{flow.sync(snapshot,accepted,t.pc);}catch(error){accepted=null;throw error;}assessment.textContent=`${accepted.changed_decoded_byte_offsets.length} changed bytes · opcode, context and successors retained.\nProposed: ${fields.map(k=>fieldValue(value??t.values,k)).join(', ')}`;status.textContent=accepted.no_op?'No authored change.':'Review complete. Explicit Apply is required.';});}
 buttons.review.onclick=()=>buttons.review.disabled?false:review(choice());buttons.reset.onclick=()=>{if(buttons.reset.disabled)return false;resetDraft=true;for(const key of fields)inputs[key].value=String(fieldValue(row().values,key));return review(null);};buttons.discard.onclick=()=>{if(buttons.discard.disabled)return false;invalidate();render();return true;};
 buttons.apply.onclick=async()=>{if(buttons.apply.disabled||!fresh()||pending||busy())return false;const proposal=structuredClone(accepted),focus=row().pc;pending=true;updateState();try{const success=await api('/api/command',{type:'set_controller_table_copy',entity_id:owner,operand_id:proposal.operand_id,value:proposal.value,review_key:proposal.review_key});accepted=null;assessment.textContent='';flow.sync(snapshot,null,focus);if(success!==true)return false;const now=scriptBranchContext(getContext());if(disposed||['projectPath','sceneId','mode'].some(k=>now[k]!==context[k]))return false;pending=false;await reopen(focus);return true;}catch(e){if(fresh()){status.textContent=e.message;onError(e);}return false;}finally{pending=false;updateState();}};
 const navigation=controllerAuthoringFocus({current:()=>fresh()&&context.mode==='edit',busy:()=>pending||busy(),targets:()=>snapshot?.targets,source,select:target=>{invalidate();source.value=target.semantic_id;render();status.textContent='Source selected. Review before Apply.';}});
 return {...navigation,ready,updateState,hasDraft:()=>!!(row()&&(resetDraft||accepted||pending||!same(choice(),row().current_values))),dispose(){if(disposed)return;disposed=true;invalidate();flow.dispose();section.remove();}};
}
