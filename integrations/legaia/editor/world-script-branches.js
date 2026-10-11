import {qualifyWorldScriptInspection} from './world-script-inspection.js';
import {worldBranchTarget,updateWorldBranchGraph,reachedWorldBranchGraph} from './world-script-branch-bytes.js';
const fail=message=>{throw Error(message);};
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const bytes=v=>Uint8Array.from(atob(v),c=>c.charCodeAt(0));
const hex=v=>Array.from(v,n=>n.toString(16).padStart(2,'0')).join('');
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const pc=n=>n.toString(16).padStart(4,'0');
function relativeGraph(graph,offset){
 const result=structuredClone(graph);
 for(const family of ['instructions','dialogues','opaque_regions','unvisited_instructions','unvisited_dialogues'])for(const row of result[family]||[]){row.byte_offset-=offset;if(family.includes('dialogues')){delete row.semantic_id;for(const token of row.tokens)token.byte_offset-=offset;}}
 if(!Object.hasOwn(result,'unreachable_source_pcs'))Object.assign(result,{unreachable_source_pcs:[],unvisited_instructions:[],unvisited_dialogues:[]});
 return result;
}
export async function qualifyWorldBranchOptions(v,inspection,record,key,path){
 const q=await qualifyWorldScriptInspection(inspection,record,key,path),source=q.source;
 const keys=['schema_version','project_path','source_key','script_id','source_record','entry_pc','source_instance_ids','retail_record_base64','fixed_record_base64','current_record_base64','branch_options','authored_targets','current_graph','graph_offset_scope','project_changed','gameplay_verified'];
 if(!exact(v,keys)||v.schema_version!=='legaia.world-script-branches.v1'||v.project_path!==path||v.source_key!==key||v.script_id!==record.id||!same(v.source_record,record.source_record)||v.entry_pc!==source.entry_pc||!same(v.source_instance_ids,source.source_instance_ids)||v.retail_record_base64!==source.record_base64||v.current_record_base64!==source.current_record_base64||v.graph_offset_scope!=='source_record_relative'||v.project_changed!==false||v.gameplay_verified!==false||q.retail_graph.stops.length)fail('World branch source differs from the qualified instruction snapshot.');
 const retail=bytes(source.record_base64),current=bytes(source.current_record_base64),destinations=[...q.retail_graph.instructions.map(r=>({pc:r.pc,mnemonic:r.mnemonic})),...q.retail_graph.dialogues.map(r=>({pc:r.pc,mnemonic:'MES_SEGMENT'}))].filter(r=>r.pc>=source.entry_pc&&r.pc<=32767).sort((a,b)=>a.pc-b.pc),allowed=new Set(destinations.map(r=>r.pc));
 const targets=q.retail_graph.instructions.map(r=>worldBranchTarget(r,retail)).filter(r=>r&&r.pc<=32767&&allowed.has(r.target_pc));
 const options={targets,destinations,reason:null,source_record_sha256:source.source_record.sha256,entry_pc:source.entry_pc};
 if(!same(v.branch_options,options)||!v.authored_targets||typeof v.authored_targets!=='object'||Array.isArray(v.authored_targets)||Object.keys(v.authored_targets).length>1024)fail('World branch options or authored coverage differ from original boundaries.');
 const fixed=current.slice();
 for(const [key,values] of Object.entries(v.authored_targets)){
  const target=targets.find(t=>pc(t.pc)===key);if(!target||!exact(values,['target_pc'])||!Number.isSafeInteger(values.target_pc)||!allowed.has(values.target_pc))fail('World authored branch target lacks source ownership.');
  const word=(values.target_pc-target.operand_pc)&65535;if(current[target.operand_pc]!== (word&255)||current[target.operand_pc+1]!==word>>8)fail('World authored destination differs from Current bytes.');
  fixed[target.operand_pc]=retail[target.operand_pc];fixed[target.operand_pc+1]=retail[target.operand_pc+1];
 }
 if(hex(fixed)!==hex(bytes(v.fixed_record_base64))||!same(relativeGraph(q.current_graph,source.source_record.byte_offset),relativeGraph(v.current_graph,0)))fail('World branch fixed baseline or Current graph differs from its complete witness.');
 return {snapshot:structuredClone(v),inspection:q};
}
export function qualifyWorldBranchReview(v,qualified,target,values,shared){
 const source=qualified.snapshot,q=qualified.inspection,s=q.source;
 if(!source.branch_options.targets.some(row=>same(row,target)))fail('World branch Review target is not in its qualified source snapshot.');
 const keys=['schema_version','project_path','source_key','script_id','pc','retail_values','current_values','proposed_values','source_instance_ids','shared','current_man_sha256','candidate_man_sha256','candidate_record_base64','changes','compression','candidate_graph','graph_offset_scope','no_op','project_changed','gameplay_verified','review_key'];
 const authored=source.authored_targets[pc(target.pc)],currentValue=authored||{target_pc:target.target_pc};
 if(!exact(v,keys)||v.schema_version!=='legaia.world-script-branch-review.v1'||v.project_path!==source.project_path||v.source_key!==source.source_key||v.script_id!==source.script_id||v.pc!==target.pc||!same(v.retail_values,{target_pc:target.target_pc})||!same(v.current_values,currentValue)||!same(v.proposed_values,values)||!exact(values,['target_pc'])||!source.branch_options.destinations.some(r=>r.pc===values.target_pc)||!same(v.source_instance_ids,source.source_instance_ids)||typeof shared!=='boolean'||v.shared!==shared||source.source_instance_ids.length>1&&!shared||v.graph_offset_scope!=='source_record_relative'||v.project_changed!==false||v.gameplay_verified!==false||!['current_man_sha256','candidate_man_sha256','review_key'].every(k=>hash(v[k])))fail('World branch Review differs from its qualified source or draft.');
 const current=bytes(source.current_record_base64),candidate=current.slice(),at=target.operand_pc,word=(values.target_pc-at)&65535;candidate[at]=word&255;candidate[at+1]=word>>8;
 const changes=[];for(let n=0;n<current.length;n++)if(current[n]!==candidate[n])changes.push({decoded_byte_offset:s.source_record.byte_offset+n,before_byte:current[n],after_byte:candidate[n]});
 const compression=v.compression,slot=s.source_record.man_slot;
 if(!slot)fail('World branch Review requires source MAN compression provenance.');
 if(hex(bytes(v.candidate_record_base64))!==hex(candidate)||!same(v.changes,changes)||v.no_op!==(changes.length===0)||!compression||compression.decoded_size!==slot.decoded_byte_length||compression.original_encoded_size!==slot.compressed_bytes_consumed||!Number.isSafeInteger(compression.new_encoded_size)||compression.new_encoded_size<1||compression.new_encoded_size>compression.original_encoded_size)fail('World branch Review changes unrelated bytes or exceeds its source span.');
 // Start from the fixed-argument graph: original edges, independently qualified
 // Current nonbranch arguments, and complete retained source ownership.
 const graph=structuredClone(q.retail_graph),full=new Map([...q.current_graph.instructions,...(q.current_graph.unvisited_instructions||[])].map(r=>[r.pc,r]));
 for(const row of graph.instructions){const now=full.get(row.pc);row.opcode=now.opcode;row.operands=structuredClone(now.operands);row.raw_hex=now.raw_hex;}
 // Restore only branch-derived metadata before composing all effective edits.
 const retail=bytes(s.record_base64);
 for(const row of graph.instructions){const layout=worldBranchTarget(row,retail);if(!layout)continue;const original=q.retail_graph.instructions.find(r=>r.pc===row.pc);for(const field of ['delta','target','target_word','target_word_pc','target_pc','delta_u16','encoded_target'])if(Object.hasOwn(original.operands,field))row.operands[field]=original.operands[field];}
 const all=structuredClone(source.authored_targets);if(values.target_pc===target.target_pc)delete all[pc(target.pc)];else all[pc(target.pc)]=values;
 const branch_changes=source.branch_options.targets.filter(t=>all[pc(t.pc)]&&all[pc(t.pc)].target_pc!==t.target_pc).map(t=>({pc:t.pc,operand_pc:t.operand_pc,condition:t.condition,authored_target_pc:all[pc(t.pc)].target_pc}));
 // Raw words for unchanged/reset branches must also reflect the candidate.
 for(const row of graph.instructions){const header=row.target_context===null?1:2;row.raw_hex=hex(candidate.slice(row.pc,row.pc+row.length));row.operands.encoded_hex=row.raw_hex.slice(header*2);}
 updateWorldBranchGraph({branch_changes},retail,candidate,graph);
 if(!same(relativeGraph(reachedWorldBranchGraph(graph,candidate,s),s.source_record.byte_offset),relativeGraph(v.candidate_graph,0)))fail('World branch proposed graph changes unrelated analysis or retained ownership.');
 return structuredClone(v);
}

const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
export function mountWorldScriptBranches({host,record,key,path,current,busy,setBusy,api,onApplied,onError}){
 const section=node('section'),open=node('button','Edit World Branch Destinations');section.dataset.worldScriptBranches='';section.append(open);host.append(section);
 let qualified=null,target=null,review=null,disposed=false,pending=null,generation=0,select=null,destination=null,shared=null,status=null,reviewButton=null,applyButton=null,reset=null;
 const valid=()=>!disposed&&current();
 const update=()=>{const blocked=!valid()||busy();open.disabled=blocked;for(const control of [select,destination,shared,reset])if(control)control.disabled=blocked||!target;if(reviewButton)reviewButton.disabled=blocked||!target;if(applyButton)applyButton.disabled=blocked||!review||review.no_op;};
 const clear=()=>{generation++;review=null;if(status)status.textContent='Draft changed. Review before Apply.';update();};
 const values=()=>{const value=Number(destination.value);if(!qualified.snapshot.branch_options.destinations.some(r=>r.pc===value))fail('Choose an original source destination.');return {target_pc:value};};
 async function request(route,body,signal){const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),text=await response.text();if(new TextEncoder().encode(text).length>32*1024*1024)fail('World branch response exceeds its budget.');const value=JSON.parse(text);if(!response.ok)fail(value.error||'World branch request failed.');return value;}
 async function run(work){if(!valid()||busy())return false;const controller=new AbortController();pending=controller;setBusy(true);update();try{return await work(controller.signal);}catch(error){if(error.name!=='AbortError'&&valid()){if(status)status.textContent=error.message;onError(error);}return false;}finally{if(pending===controller){pending=null;setBusy(false);update();}}}
 function render(){
  const source=qualified.snapshot;section.replaceChildren(node('h3','World Branch Destinations'),node('p','Destinations are original instruction or dialogue starts. These edits change static possibilities; story behavior and termination require gameplay verification. Other authored arguments and dormant source bytes are retained.'));
  select=node('select');select.setAttribute('aria-label','World branch instruction');for(const row of source.branch_options.targets){const option=node('option',pc(row.pc)+' · '+row.mnemonic+' · '+row.condition);option.value=String(row.pc);select.append(option);}Object.assign(select.style,{width:'100%',minWidth:'0'});section.append(select);
  const currentValue=node('p');section.append(currentValue);const label=node('label','Destination PC'),choices=node('select');destination=choices;choices.setAttribute('aria-label','World branch destination');for(const row of source.branch_options.destinations){const option=node('option',pc(row.pc)+' · '+row.mnemonic);option.value=String(row.pc);choices.append(option);}Object.assign(choices.style,{display:'block',width:'100%',minWidth:'0'});choices.onchange=clear;label.append(choices);section.append(label);
  reset=node('button','Use Retail Destination');reset.onclick=()=>{if(reset.disabled)return;choices.value=String(target.target_pc);clear();};section.append(reset);
  const consent=node('label','Apply to every source object sharing this script');shared=node('input');shared.type='checkbox';shared.setAttribute('aria-label','Shared World branch consent');shared.onchange=clear;consent.prepend(shared);consent.hidden=source.source_instance_ids.length<2;section.append(consent);
  status=node('p');reviewButton=node('button','Review World Branch');applyButton=node('button','Apply World Branch');section.append(status,reviewButton,applyButton);
  const choose=()=>{target=source.branch_options.targets.find(t=>t.pc===Number(select.value))||null;if(target){const authored=source.authored_targets[pc(target.pc)];choices.value=String(authored?.target_pc??target.target_pc);currentValue.textContent=`Retail ${pc(target.target_pc)} · Authored ${authored?pc(authored.target_pc):'None'} · Current ${pc(authored?.target_pc??target.target_pc)}`;}clear();if(!target)status.textContent='No supported branch destination words in this source record.';};select.onchange=choose;choose();
  reviewButton.onclick=()=>run(async signal=>{const wanted=values(),consent=shared.checked,ticket=generation,raw=await request('/api/world-script-branch-review',{script_id:record.id,source_key:key,pc:target.pc,values:wanted,shared:consent},signal),q=qualifyWorldBranchReview(raw,qualified,target,wanted,consent);if(!valid()||ticket!==generation)return false;review=q;status.textContent=q.no_op?'Current destination unchanged.':`${q.changes.length} MAN bytes will change. Proposed static graph: ${q.candidate_graph.instructions.length} reached and ${q.candidate_graph.unvisited_instructions.length} dormant source instructions. Gameplay unverified.`;return true;});
  applyButton.onclick=async()=>{if(applyButton.disabled)return;try{const wanted=values(),consent=shared.checked;qualifyWorldBranchReview(review,qualified,target,wanted,consent);const result=await api('/api/command',{type:'set_world_script_branches',script_id:record.id,source_key:key,pc:target.pc,values:wanted,shared:consent,review_key:review.review_key});if(result)onApplied(result);}catch(error){review=null;update();onError(error);}};
 }
 const load=()=>run(async signal=>{const body={script_id:record.id,source_key:key},snapshot=await request('/api/world-script-branches',body,signal),inspection=await request('/api/world-script-inspection',body,signal),q=await qualifyWorldBranchOptions(snapshot,inspection,record,key,path);if(!valid())return false;qualified=q;render();return true;});
 open.onclick=load;update();return {update,async focus(offset){if(!qualified&&!await load())return false;if(!valid()||busy()||!qualified.snapshot.branch_options.targets.some(r=>r.pc===offset))return false;select.value=String(offset);select.onchange();section.scrollIntoView({block:'start'});return true;},dispose(){disposed=true;pending?.abort();if(pending){pending=null;setBusy(false);}section.remove();}};
}
