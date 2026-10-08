import {decodeAnimationOperandSource,decodeAnimationOperandReview,mountAnimationOperands} from './script-animation-operands.js';
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.keys(x).sort().map(k=>[k,x[k]])):x),same=(a,b)=>canonical(a)===canonical(b);
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const fail=message=>{throw Error(message);};
export function decodeNpcAnimationOperandSource(value,id,state){
 const draft=state.actor_drafts?.[id],key=state.project_copy_source_key;
 if(!draft||draft.scene_id!==state.scene?.id||value?.schema_version!=='legaia.npc-animation-operands-source.v1'||value.entity_id!==id||value.scene_id!==draft.scene_id||value.project_source_key!==key||!hash(key)||!same(value.draft,draft)||value.gameplay_verified!==false||value.animation_playback!=='not_asserted')fail('NPC animation source changed. Reopen the editor.');
 const source=decodeAnimationOperandSource({...value.options,schema_version:'legaia.script-animation-operands.v1',owner_id:draft.donor_entity_id,state_key:key,unresolved_overrides:[],gameplay_verified:false},draft.donor_entity_id,key);
 const known=new Set();for(const target of source.targets){known.add(target.semantic_id);if(!same(target.authored_values,draft.animation_operands?.entries?.[target.semantic_id]??null))fail('NPC animation source differs from owned arguments.');}
 if(Object.keys(draft.animation_operands?.entries??{}).some(key=>!known.has(key)))fail('NPC animation binding is unresolved.');
 return structuredClone(value);
}
export function npcAnimationOperandRequest(source,id,values){
 const row=source.options.targets.find(r=>r.semantic_id===id);if(!row)fail('Select a qualified NPC animation instruction.');
 const entries=structuredClone(source.draft.animation_operands?.entries??{});
 if(values===null||same(values,row.values))delete entries[id];else entries[id]=structuredClone(values);
 return {entity_id:source.entity_id,entries};
}
export function npcCurrentAnimationSelection(value,source,pc,state){
 const accepted=decodeNpcAnimationOperandSource(source,value.entity_id,state),row=accepted.options.targets.find(r=>r.pc===pc),instruction=[...value.inspection.instructions,...(value.inspection.unvisited_instructions??[])].find(r=>r.pc===pc);
 if(state.project?.mode!=='edit'||state.capabilities?.npc_animation_operand_authoring!==true||value.schema_version!=='legaia.npc-current-script.v1'||value.project_source_key!==source.project_source_key||!same(value.draft,source.draft)||!row||!instruction||instruction.mnemonic!==row.mnemonic||instruction.length!==row.instruction_length||instruction.target_context!==row.target_context||row.source_record_sha256!==value.donor.inspection.record.sha256)fail('Select a qualified Current NPC animation instruction in Edit mode.');
 const header=row.target_context===null?1:2,raw=Uint8Array.from(row.raw_instruction_hex.match(/../g),v=>parseInt(v,16)),spec=row.mnemonic==='SET_MODEL_ANIMATION'?[['model_id',3],['animation_frame',2],['tween_frames',2]]:[['animation_operand',1]];
 let at=header+1;for(const [key,width] of spec){if(instruction.operands?.[key]!==row.effective_values[key])fail('Current NPC animation values differ from their source.');for(let i=0;i<width;i++)raw[at+i]=Math.floor(row.effective_values[key]/2**(i*8))%256;at+=width;}
 const expected=[...raw].map(v=>v.toString(16).padStart(2,'0')).join('');if(instruction.raw_hex!==expected||value.inspection.record.raw_hex.slice(pc*2,(pc+raw.length)*2)!==expected)fail('Current NPC animation bytes differ from owned arguments.');
 return {entity_id:value.entity_id,animation_operand_id:row.semantic_id,pc,values:structuredClone(row.effective_values)};
}
async function recordHash(record){
 if(typeof record?.raw_hex!=='string'||record.raw_hex.length!==record.byte_length*2||record.raw_hex.length>131072||!/^(?:[a-f0-9]{2})+$/.test(record.raw_hex)||!hash(record.sha256))fail('NPC animation record bytes are invalid.');
 const bytes=Uint8Array.from(record.raw_hex.match(/../g),v=>parseInt(v,16)),digest=await crypto.subtle.digest('SHA-256',bytes);
 if([...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('')!==record.sha256)fail('NPC animation record hash differs from its bytes.');
}
export async function decodeNpcAnimationOperandReview(value,source,id,values,state){
 decodeNpcAnimationOperandSource(source,source.entity_id,state);
 const request=npcAnimationOperandRequest(source,id,values),draft=source.draft,proposed=structuredClone(draft),target=source.options.targets.find(r=>r.semantic_id===id);
 if(Object.keys(request.entries).length)proposed.animation_operands={donor_entity_id:draft.donor_entity_id,entries:request.entries};else delete proposed.animation_operands;
 if(value?.schema_version!=='legaia.npc-animation-operands-review.v1'||value.entity_id!==source.entity_id||value.project_source_key!==source.project_source_key||!same(value.request,request)||!same(value.current,draft)||!same(value.proposed,proposed)||!hash(value.review_key)||value.gameplay_verified!==false||value.animation_playback!=='not_asserted')fail('NPC animation Review differs from the requested clone edit.');
 const before=value.current_inspection,after=value.proposed_inspection;
 await recordHash(before?.record);await recordHash(after?.record);
 for(const key of ['record_index','byte_offset','byte_length','script_offset','local_count'])if(before.record[key]!==after.record[key])fail('NPC animation Review changed record ownership.');
 const header=target.target_context===null?1:2;
 if(!Number.isSafeInteger(before.record.script_offset)||before.record.script_offset<0||target.pc<before.record.script_offset||before.record.byte_offset+target.pc+header+1!==target.decoded_byte_offset||before.record.record_index!==Number(draft.donor_entity_id.split('/').at(-1))||before.record.byte_offset+target.pc+target.instruction_length>source.options.source.decoded_man_size||before.actor_semantic_id!==draft.donor_entity_id||after.actor_semantic_id!==draft.donor_entity_id||before.semantic_id!==after.semantic_id||!same(before.source_record,after.source_record))fail('NPC animation Review changed its donor binding.');
 const changed=[];for(let at=0;at<before.record.byte_length;at++){const a=before.record.raw_hex.slice(at*2,at*2+2),b=after.record.raw_hex.slice(at*2,at*2+2);if(a!==b){if(at<target.pc||at>=target.pc+target.instruction_length)fail('NPC animation Review changed another instruction or header.');changed.push(before.record.byte_offset+at);}}
 const normalized=decodeAnimationOperandSource({...source.options,schema_version:'legaia.script-animation-operands.v1',owner_id:draft.donor_entity_id,state_key:source.project_source_key,unresolved_overrides:[],gameplay_verified:false},draft.donor_entity_id,source.project_source_key);
 const result={...normalized,target,review:{review_key:value.review_key,animation_operand_id:id,values,no_op:same(draft,proposed),current_instruction_hex:before.record.raw_hex.slice(target.pc*2,(target.pc+target.instruction_length)*2),proposed_instruction_hex:after.record.raw_hex.slice(target.pc*2,(target.pc+target.instruction_length)*2),changed_byte_offsets:changed,current_record_sha256:before.record.sha256,proposed_record_sha256:after.record.sha256},current_report:before,proposed_report:after};
 // The source editor's decoder independently checks native widths, dispatch,
 // exact values and all unrelated decoded/opaque instruction evidence.
 return decodeAnimationOperandReview(result,normalized,id,values);
}
export function openNpcAnimationOperands({entityId,getState,isBusy,canEdit,api,request=fetch,focusPc,onReturn,onApplied}){
 if(isBusy()||!canEdit())return;
 const key=getState().project_copy_source_key,dialog=document.createElement('dialog');dialog.id='npc-animation-operands-dialog';dialog.style.cssText='width:min(820px,calc(100vw - 32px));max-width:calc(100vw - 32px);max-height:calc(100vh - 32px);overflow:auto;overflow-wrap:anywhere';
 const title=document.createElement('h2');title.textContent='NPC Animation Script Arguments';const note=document.createElement('p');note.textContent='Arguments belong to this NPC. Retail donor and sibling clones retain their own values. Model/clip identity, timing and playback remain unverified.';
 const host=document.createElement('div'),status=document.createElement('p');status.setAttribute('role','status');status.textContent='Qualifying Retail donor arguments…';const close=document.createElement('button');close.type='button';close.textContent='Close NPC Animation Arguments';close.onclick=()=>dialog.close();dialog.append(title,note,status,host,close);document.body.append(dialog);dialog.showModal();
 const controller=new AbortController(),drafts=new Map();let component=null,disposed=false,reviewed=null,pending=false;
 const current=()=>!disposed&&dialog.open&&canEdit()&&getState().project_copy_source_key===key;
 const post=async(path,body)=>{const response=await request(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal}),text=await response.text();if(new TextEncoder().encode(text).length>4194304)fail('NPC animation response exceeds 4 MiB.');const value=JSON.parse(text);if(!response.ok||value.error)fail(value.error??'NPC animation authoring refused.');return value;};
 const timer=setInterval(()=>component?.updateState(),300);
 dialog.addEventListener('close',()=>{disposed=true;controller.abort();clearInterval(timer);component?.dispose();drafts.clear();reviewed=null;dialog.remove();},{once:true});
 if(typeof onReturn==='function'){const back=document.createElement('button');back.type='button';back.textContent='Return to Current NPC Script';back.onclick=()=>{if(current()&&!pending&&!isBusy()){dialog.close();onReturn();}};dialog.append(back);}
 const ready=(async()=>{try{const source=decodeNpcAnimationOperandSource(await post('/api/npc-animation-operands-source',{entity_id:entityId}),entityId,getState());if(!current())return;
  const rawSource={...source.options,schema_version:'legaia.script-animation-operands.v1',owner_id:source.draft.donor_entity_id,state_key:key,unresolved_overrides:[],gameplay_verified:false};
  component=mountAnimationOperands(host,{source:rawSource,owner:source.draft.donor_entity_id,stateKey:key,current,busy:()=>pending||isBusy(),drafts,onDraftChange(){reviewed=null;},onError(error){status.textContent=error.message;},selectInstruction(){},
   requestReview:async({animation_operand_id:id,values})=>{pending=true;try{const body=npcAnimationOperandRequest(source,id,values),raw=await post('/api/npc-animation-operands-review',body),decoded=await decodeNpcAnimationOperandReview(raw,source,id,values,getState());if(!current())fail('NPC animation source changed.');reviewed={id,values,body,key:raw.review_key};return decoded;}finally{pending=false;}},
   command:async command=>{if(!current()||!reviewed||command.animation_operand_id!==reviewed.id||command.review_key!==reviewed.key||!same(command.values,reviewed.values))fail('NPC animation proposal changed. Review again.');pending=true;try{return await api('/api/command',{type:'set_actor_draft_animation_operands',entity_id:entityId,entries:reviewed.body.entries,review_key:reviewed.key},{success:'NPC Animation Arguments Updated.'});}finally{pending=false;}},
   reopen:async pc=>{dialog.close();if(typeof onApplied==='function')onApplied();else openNpcAnimationOperands({entityId,getState,isBusy,canEdit,api,request,focusPc:pc,onReturn,onApplied});}});
  component.select(focusPc);status.textContent=source.options.supported?'Select one fixed instruction; Review before Apply.':source.options.reason??'No qualified animation instructions in this donor.';
 }catch(error){if(!disposed)status.textContent=error.message;}})();
 return {dialog,ready,dispose:()=>dialog.close()};
}
