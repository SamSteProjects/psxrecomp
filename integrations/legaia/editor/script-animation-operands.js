// Fixed native arguments only; model/clip identity and runtime behavior stay unknown.
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const exact=(v,keys)=>object(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const int=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const canonical=v=>Array.isArray(v)?v.map(canonical):object(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const fail=message=>{throw new Error(message);};
const specs={SET_MODEL_ANIMATION:[['model_id',3,'Encoded Model Argument'],['animation_frame',2,'Animation Frame Argument'],['tween_frames',2,'Tween Frame Argument']],EFFECT_ANIMATION_TRIGGER:[['animation_operand',1,'Effect Animation Argument']]};
const title={SET_MODEL_ANIMATION:'Set Model Animation',EFFECT_ANIMATION_TRIGGER:'Effect Animation Trigger'};
const pc=v=>'0x'+v.toString(16).toUpperCase().padStart(4,'0');
function valuesValid(mnemonic,values){const spec=specs[mnemonic];return !!spec&&exact(values,spec.map(([k])=>k))&&spec.every(([k,width])=>int(values[k],0,2**(width*8)-1));}
function bytes(hex){if(typeof hex!=='string'||hex.length>64||hex.length%2||!/^[0-9a-f]+$/.test(hex))fail('Invalid native animation instruction bytes.');return Uint8Array.from(hex.match(/../g).map(v=>parseInt(v,16)));}
function decodeNative(target,hex){
 const raw=bytes(hex),extended=target.target_context!==null,header=extended?2:1,spec=specs[target.mnemonic];
 if(!spec||raw.length!==header+1+spec.reduce((n,[,width])=>n+width,0)||raw.length!==target.instruction_length||(raw[0]>=128)!==extended||extended&&raw[1]!==target.target_context)fail('Animation instruction layout or actor context changed.');
 if(target.mnemonic==='SET_MODEL_ANIMATION'?((raw[0]&127)!==0x4c||raw[header]!==0x81):((raw[0]&127)!==0x34||raw[header]>>4!==3))fail('Animation instruction dispatch is unsupported.');
 let offset=header+1;const values={};for(const [key,width] of spec){let value=0;for(let i=0;i<width;i++)value+=raw[offset+i]*2**(i*8);values[key]=value;offset+=width;}return {raw,values,header};
}
function targetValid(target,owner,manSize){
 if(!object(target)||!int(target.pc,0,65535)||target.owner_id!==owner||target.semantic_id!=='script://'+owner.slice(8)+'/animation-operands/'+target.pc.toString(16).padStart(4,'0')||!hash(target.source_record_sha256)||!(target.target_context===null||int(target.target_context,0,255))||!int(target.decoded_byte_offset,0,manSize)||!valuesValid(target.mnemonic,target.values))fail('Animation operand target ownership or fields are invalid.');
 const native=decodeNative(target,target.raw_instruction_hex),start=target.decoded_byte_offset-native.header-1;
 if(start<target.pc||start+target.instruction_length>manSize||!same(native.values,target.values))fail('Animation target differs from its native source span.');
 return native;
}
export function decodeAnimationOperandSource(value,owner,stateKey){
 if(typeof owner!=='string'||!/^scene:\/\/[A-Za-z0-9_-]+\/(actors\/man-p1|scripts\/man-p2)\/[0-9]{4}$/.test(owner)||!hash(stateKey)||!object(value)||value.schema_version!=='legaia.script-animation-operands.v1'||value.owner_id!==owner||value.state_key!==stateKey||value.gameplay_verified!==false||typeof value.supported!=='boolean'||!Array.isArray(value.targets)||value.targets.length>1024||!Array.isArray(value.unresolved_overrides)||value.unresolved_overrides.length>1024||!object(value.source)||!hash(value.source.decoded_man_sha256)||!int(value.source.decoded_man_size,1,4*1024*1024)||value.source.scene!==owner.split('/')[2]||value.source.reference_commit!=='d6e64c68ede25813d35db20980da82a1a025549b')fail('Animation operand source is stale or invalid.');
 const ids=new Set(),spans=new Set();
 for(const target of value.targets){const native=targetValid(target,owner,value.source.decoded_man_size);if(ids.has(target.semantic_id)||!(target.authored_values===null||valuesValid(target.mnemonic,target.authored_values))||!valuesValid(target.mnemonic,target.effective_values)||!same(target.effective_values,target.authored_values??target.values))fail('Animation authored/source values are invalid or duplicated.');ids.add(target.semantic_id);const start=target.decoded_byte_offset-native.header-1;for(let i=start;i<start+target.instruction_length;i++){if(spans.has(i))fail('Animation source instructions overlap.');spans.add(i);}}
 if(value.supported!==(value.targets.length>0)||value.unresolved_overrides.some(id=>typeof id!=='string'||ids.has(id))||new Set(value.unresolved_overrides).size!==value.unresolved_overrides.length)fail('Animation target availability is inconsistent.');
 return structuredClone(value);
}
export function currentAnimationSelection(snapshot,rawSource,selectedPC,state){
 const source=decodeAnimationOperandSource(rawSource,snapshot?.owner_id,state.script_authoring_state_key),target=source.targets.find(row=>row.pc===selectedPC);
 const retail=snapshot.source_report?.instructions?.find(row=>row.pc===selectedPC),current=snapshot.current_report?.instructions?.find(row=>row.pc===selectedPC);
 if(state.project?.mode!=='edit'||state.capabilities?.script_animation_operand_authoring!==true||state.scene?.id!=='scene://'+source.source.scene||snapshot.schema_version!=='legaia.script-branches.v1'||snapshot.state_key!==source.state_key||snapshot.gameplay_verified!==false||!target||target.source_record_sha256!==snapshot.source_record_sha256||!retail||!current)fail('Select a qualified Current animation instruction in Edit mode.');
 for(const row of [retail,current])if(row.mnemonic!==target.mnemonic||row.length!==target.instruction_length||row.target_context!==target.target_context)fail('Current animation boundary differs from its source target.');
 if(retail.raw_hex!==target.raw_instruction_hex)fail('Retail animation instruction differs from its source bytes.');
 const native=decodeNative(target,current.raw_hex),original=decodeNative(target,target.raw_instruction_hex);
 if(!same(native.values,target.effective_values)||specs[target.mnemonic].some(([key])=>current.operands?.[key]!==native.values[key])||current.operands?.encoded_hex!==current.raw_hex.slice(native.header*2))fail('Current animation arguments differ from effective native bytes.');
 for(let i=0;i<native.header+1;i++)if(native.raw[i]!==original.raw[i])fail('Current animation dispatch differs from Retail.');
 return {owner_id:source.owner_id,animation_operand_id:target.semantic_id,pc:target.pc,values:structuredClone(native.values)};
}
export function decodeAnimationOperandReview(value,source,id,values){
 const target=source.targets.find(row=>row.semantic_id===id);
 if(!target||!(values===null||valuesValid(target.mnemonic,values))||!object(value)||value.schema_version!==source.schema_version||value.owner_id!==source.owner_id||value.state_key!==source.state_key||value.gameplay_verified!==false||!object(value.review)||!hash(value.review.review_key)||value.review.animation_operand_id!==id||!same(value.review.values,values)||value.source?.decoded_man_sha256!==source.source.decoded_man_sha256)fail('Animation Review differs from its source or request.');
 const keys=['semantic_id','owner_id','pc','mnemonic','target_context','decoded_byte_offset','instruction_length','raw_instruction_hex','values','source_record_sha256'];
 if(!object(value.target)||keys.some(k=>!same(value.target[k],target[k])))fail('Animation Review changed its native target.');
 const current=decodeNative(target,value.review.current_instruction_hex),proposed=decodeNative(target,value.review.proposed_instruction_hex),retail=decodeNative(target,target.raw_instruction_hex),desired=values??target.values;
 if(!same(current.values,target.effective_values)||!same(proposed.values,desired))fail('Animation Review bytes differ from Current/Proposed values.');
 for(let i=0;i<retail.header+1;i++)if(current.raw[i]!==retail.raw[i]||proposed.raw[i]!==retail.raw[i])fail('Animation Review changed opcode, context or selector.');
 const changed=[],start=target.decoded_byte_offset-retail.header-1;
 for(let i=0;i<current.raw.length;i++)if(current.raw[i]!==proposed.raw[i])changed.push(start+i);
 const expectedAuthored=values===null||same(values,target.values)?null:values;
 if(value.review.no_op!==same(target.authored_values,expectedAuthored)||!same(changed,value.review.changed_byte_offsets)||!hash(value.review.current_record_sha256)||!hash(value.review.proposed_record_sha256)||(!changed.length&&value.review.current_record_sha256!==value.review.proposed_record_sha256))fail('Animation Review delta or no-op evidence is inconsistent.');
 const before=value.current_report,after=value.proposed_report;
 for(const report of [before,after])if(!object(report)||!Array.isArray(report.instructions)||report.instructions.length>8192||!Array.isArray(report.dialogues)||!Array.isArray(report.stops)||!Array.isArray(report.opaque_regions))fail('Animation Review instruction reports are invalid.');
 for(const key of ['status','entry_pc','dialogues','stops'])if(!same(before[key],after[key]))fail('Animation Review changed unrelated decoded paths.');
 if(before.opaque_regions.length!==after.opaque_regions.length||before.opaque_regions.length>8192)fail('Animation Review changed opaque region boundaries.');
 for(let i=0;i<before.opaque_regions.length;i++){const region=before.opaque_regions[i],expected=structuredClone(region);if(!object(region)||!int(region.pc,0,65535)||!int(region.length,1,65536)||typeof region.raw_hex!=='string'||region.raw_hex.length!==region.length*2||!/^[0-9a-f]+$/.test(region.raw_hex))fail('Invalid opaque animation Review region.');let hex=region.raw_hex;for(let j=0;j<current.raw.length;j++){const at=target.pc+j-region.pc;if(at>=0&&at<region.length){if(parseInt(hex.slice(at*2,at*2+2),16)!==current.raw[j])fail('Opaque Current instruction differs from byte evidence.');hex=hex.slice(0,at*2)+proposed.raw[j].toString(16).padStart(2,'0')+hex.slice(at*2+2);}}expected.raw_hex=hex;if(!same(expected,after.opaque_regions[i]))fail('Animation Review changed unrelated opaque bytes.');}
 if(before.instructions.length!==after.instructions.length)fail('Animation Review changed reached instruction counts.');
 for(let i=0;i<before.instructions.length;i++){const a=before.instructions[i],b=after.instructions[i];if(!object(a)||!object(b))fail('Invalid animation Review instruction.');const expected=structuredClone(a);if(a.pc===target.pc){expected.raw_hex=value.review.proposed_instruction_hex;expected.operands={...expected.operands,...desired,encoded_hex:value.review.proposed_instruction_hex.slice(proposed.header*2)};if(a.operands?.encoded_hex!==value.review.current_instruction_hex.slice(current.header*2))fail("Current encoded animation operands differ from byte evidence.");if(a.raw_hex!==value.review.current_instruction_hex)fail('Current animation instruction differs from byte evidence.');}if(!same(expected,b))fail('Animation Review changed another instruction or control edge.');}
 return structuredClone(value);
}

export function decodeAnimationOperandUses(value,source,id){
 const query=source.targets.find(row=>row.semantic_id===id);
 if(!query||value?.schema_version!=='legaia.animation-operand-uses.v1'||value.owner_id!==source.owner_id||value.animation_operand_id!==id||value.state_key!==source.state_key||value.scene_id!=='scene://'+source.source.scene||value.read_only!==true||value.gameplay_verified!==false||value.runtime_binding!=='not_asserted'||value.identity_resolution!=='numeric_arguments_only'||value.mnemonic!==query.mnemonic||!same(value.query_values,query.effective_values)||!same(value.source,source.source)||!Array.isArray(value.rows)||!int(value.match_count,0,8192)||value.rows.length!==Math.min(value.match_count,256)||value.truncated!==(value.match_count>256)||!int(value.scanned_target_count,value.match_count,8192)||!int(value.scanned_owner_count,1,16384))fail('Animation argument usage differs from its source query.');
 const seen=new Set();
 for(const row of value.rows){
  const key=row.entity_id+'|'+row.target?.semantic_id;
  if(!['source','npc'].includes(row.kind)||row.kind==='source'&&row.entity_id!==row.donor_entity_id||row.kind==='npc'&&(typeof row.entity_id!=='string'||!row.entity_id.startsWith('authored-actor://'))||seen.has(key))fail('Animation argument usage ownership is invalid or duplicated.');seen.add(key);
  decodeAnimationOperandSource({...source,owner_id:row.donor_entity_id,targets:[row.target],supported:true,unresolved_overrides:[]},row.donor_entity_id,source.state_key);
  const retail=row.target.mnemonic===query.mnemonic&&same(row.target.values,query.effective_values),effective=row.target.mnemonic===query.mnemonic&&same(row.target.effective_values,query.effective_values);
  if(row.retail_match!==retail||row.effective_match!==effective||!retail&&!effective)fail('Animation argument usage does not match its numeric query.');
 }
 return structuredClone(value);
}
export function mountAnimationOperands(host,{source:rawSource,owner,stateKey,current,busy,drafts,onDraftChange,requestReview,command,reopen,onError,selectInstruction,onReturn,requestUses,onInspectUse}){
 const el=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;};
 const root=el('section');root.className='animation-operands-authoring';host.append(root);
 root.append(el('h3','Animation Script Arguments'),el('p','Edit fixed native model/frame/tween or effect arguments. Numeric arguments are not resolved model or clip identities. Playback, valid clip ranges and timing units remain unverified.'));
 if(!rawSource?.supported){root.append(el('p',rawSource?.reason??'No qualified fixed animation arguments in this source.'));return {updateState(){},dispose(){root.remove();},select(){}};}
 const source=decodeAnimationOperandSource(rawSource,owner,stateKey),select=el('select');select.setAttribute('aria-label','Animation Script Instruction');
 if(source.unresolved_overrides.length)root.append(el('p',source.unresolved_overrides.length+' authored target(s) could not be resolved. Use the authored component review to revert retained arguments; Build will refuse unresolved targets.'));
 for(const target of source.targets){const option=el('option',title[target.mnemonic]+' · '+pc(target.pc));option.value=target.semantic_id;select.append(option);}root.append(select);
 const fields=el('div'),comparison=el('div'),actions=el('div'),status=el('p'),proposalView=el('div');fields.className='animation-operand-fields';actions.className='animation-operand-actions';comparison.className='animation-operand-comparison';status.setAttribute('role','status');
 root.append(comparison,fields,actions,status,proposalView);
 const reviewButton=el('button','Review Animation Arguments'),apply=el('button','Apply Reviewed Arguments'),reset=el('button','Review Reset to Retail'),discard=el('button','Discard Animation Draft');
 for(const button of [reviewButton,apply,reset,discard])button.type='button';actions.append(reviewButton,apply,reset,discard);
 const back=onReturn?el('button','Return to Current Script Flow'):null;if(back){back.type='button';back.onclick=()=>{if(active()&&!busy()&&!inflight)onReturn(target.pc);};actions.append(back);}
 const uses=requestUses?el('button','Find Matching Animation Argument Sets'):null,usageOutput=el('div');if(uses){uses.type='button';actions.append(uses);root.append(usageOutput);uses.onclick=async()=>{if(!active()||busy()||inflight)return;const id=target.semantic_id;inflight=true;usageOutput.replaceChildren();updateState();try{const report=decodeAnimationOperandUses(await requestUses({entity_id:owner,animation_operand_id:id,expected_state_key:source.state_key}),source,id);if(!active()||target.semantic_id!==id)return;usageOutput.append(el('p',`${report.match_count} matching numeric argument set(s) · ${report.scanned_target_count} qualified sites examined. Query uses saved Current arguments; local drafts are excluded. Matching numbers do not establish model/clip identity, shared behavior or runtime activation.${report.truncated?' Showing the first 256 matches.':''}`));for(const row of report.rows){const item=el('p',`${row.kind==='npc'?'NPC draft':'Source'} ${row.entity_id} · ${pc(row.target.pc)} · ${row.retail_match?'Retail match ':''}${row.effective_match?'Effective match':''} · Context ${row.target.target_context??'local'}`);item.style.overflowWrap='anywhere';if(onInspectUse){const inspect=el('button','Inspect Matching Instruction');inspect.type='button';inspect.onclick=()=>{if(active()&&!busy()&&!inflight)onInspectUse(structuredClone(row));};item.append(inspect);}usageOutput.append(item);}}catch(error){if(active())onError(error);}finally{inflight=false;updateState();}};}
 let target,inputs={},proposal=null,disposed=false,inflight=false,invalid=false;
 const active=()=>!disposed&&current()&&root.isConnected;
 const values=()=>Object.fromEntries(Object.entries(inputs).map(([k,input])=>[k,Number(input.value)]));
 const valid=()=>Object.values(inputs).every(input=>input.value!==''&&input.checkValidity())&&valuesValid(target.mnemonic,values());
 const summary=(layer,value)=>{const row=el('p');row.append(el('strong',layer+': '));row.append(document.createTextNode(specs[target.mnemonic].map(([key,,label])=>label+' '+value[key]).join(' · ')));return row;};
 function updateState(){if(back)back.disabled=!active()||busy()||inflight;if(uses)uses.disabled=!active()||busy()||inflight;for(const button of usageOutput.querySelectorAll('button'))button.disabled=!active()||busy()||inflight;const editable=active()&&!busy()&&!inflight&&!invalid;select.disabled=!editable;for(const input of Object.values(inputs))input.disabled=!editable;reviewButton.disabled=!editable||!valid();apply.disabled=!editable||!proposal;reset.disabled=!editable||target?.authored_values===null;discard.disabled=!active()||busy()||inflight;discard.hidden=!drafts.has(target?.semantic_id)&&!proposal;if(invalid)status.textContent='Animation authoring was refused; reopen script inspection.';if(!active()){proposal=null;proposalView.replaceChildren();usageOutput.replaceChildren();status.textContent='Project, source or mode changed. Reopen script inspection to edit.';}}
 function renderTarget(){usageOutput.replaceChildren();proposal=null;proposalView.replaceChildren();fields.replaceChildren();comparison.replaceChildren();inputs={};target=source.targets.find(row=>row.semantic_id===select.value);comparison.append(summary('Retail',target.values),summary('Current',target.effective_values));
  let draft=drafts.get(target.semantic_id);if(draft&&draft.state_key!==source.state_key){drafts.delete(target.semantic_id);draft=null;}
  for(const [key,width,labelText] of specs[target.mnemonic]){const label=el('label',labelText),input=el('input');input.type='number';input.required=true;input.step='1';input.min='0';input.max=String(2**(width*8)-1);input.value=draft?.fields[key]??target.effective_values[key];input.setAttribute('aria-label',labelText);input.oninput=()=>{proposal=null;proposalView.replaceChildren();drafts.set(target.semantic_id,{state_key:source.state_key,fields:Object.fromEntries(Object.entries(inputs).map(([k,node])=>[k,node.value]))});status.textContent='Local draft; Review before Apply.';onDraftChange();updateState();};label.append(input);fields.append(label);inputs[key]=input;}
  status.textContent=target.target_context===null?'Original source instruction; runtime activation unknown.':'Encoded actor context '+target.target_context+'; runtime identity unknown.';updateState();}
 async function reviewValues(request){if(!active()||busy()||inflight||invalid)return;proposal=null;proposalView.replaceChildren();const id=target.semantic_id;inflight=true;updateState();try{const result=await requestReview({entity_id:owner,animation_operand_id:id,values:request});if(!active()||target.semantic_id!==id)return;proposal=decodeAnimationOperandReview(result,source,id,request);proposalView.append(summary('Proposed',request??target.values),el('p',proposal.review.changed_byte_offsets.length+' native byte(s) change; instruction dispatch and layout retained.'));status.textContent=proposal.review.no_op?'Reviewed no-op; Apply adds no history.':'Review ready; Apply saves one authored change.';}catch(error){proposal=null;invalid=true;onError(error);}finally{inflight=false;updateState();}}
 reviewButton.onclick=()=>{if(valid())reviewValues(values());};reset.onclick=()=>reviewValues(null);
 apply.onclick=async()=>{if(!active()||busy()||inflight||!proposal)return;const accepted=proposal,id=target.semantic_id;try{if(await command({type:'apply_script_animation_operands',entity_id:owner,animation_operand_id:id,values:accepted.review.values,review_key:accepted.review.review_key})){drafts.delete(id);onDraftChange();await reopen(target.pc);}}catch(error){proposal=null;invalid=true;proposalView.replaceChildren();onError(error);updateState();}};
 discard.onclick=()=>{if(!active()||busy()||inflight)return;drafts.delete(target.semantic_id);renderTarget();onDraftChange();};select.onchange=()=>{renderTarget();selectInstruction?.(target.pc);onDraftChange();};renderTarget();
 return {updateState,dispose(){disposed=true;proposal=null;root.remove();},select(value){const row=source.targets.find(t=>t.pc===value);if(row&&select.value!==row.semantic_id){select.value=row.semantic_id;renderTarget();}}};
}
