import {animationOperandSpecs as animationSpecs,animationOperandValuesValid as animationValid,decodeAnimationOperandInstruction as animationDecode} from './script-animation-operands.js';
const color='EFFECT_COLOR_INTENSITY';
const model='SET_ACTOR_MODEL';
const flagOpcodes=Object.fromEntries(['LFLAG','GFLAG','CFLAG'].flatMap((bank,b)=>['SET','CLEAR','TEST'].map((operation,o)=>[bank+'_'+operation,0x2b+3*b+o])));
const flag=mnemonic=>Object.hasOwn(flagOpcodes,mnemonic);
const operandSpecs={...animationSpecs,[color]:[['red',1,'Effect Red Argument'],['green',1,'Effect Green Argument'],['blue',1,'Effect Blue Argument'],['intensity',2,'Effect Intensity Argument']],[model]:[['model_selector_signed',2,'Signed Model Selector Argument']]};
for(const mnemonic of Object.keys(flagOpcodes))operandSpecs[mnemonic]=[['bit',1,'Flag Bit Argument']];
const signed=field=>['intensity','model_selector_signed'].includes(field);
const minimum=field=>signed(field)?-32768:0,maximum=(field,width,mnemonic)=>field==='bit'?(mnemonic.startsWith('LFLAG_')?15:31):signed(field)?32767:2**(8*width)-1;
function valuesValid(mnemonic,values){
 if(![color,model].includes(mnemonic)&&!flag(mnemonic))return animationValid(mnemonic,values);
 return exact(values,operandSpecs[mnemonic].map(([field])=>field))&&operandSpecs[mnemonic].every(([field,width])=>Number.isSafeInteger(values[field])&&values[field]>=minimum(field)&&values[field]<=maximum(field,width,mnemonic))&&!(mnemonic==='CFLAG_SET'&&values.bit===8||mnemonic==='CFLAG_CLEAR'&&values.bit===10);
}
function decodeInstruction(target,encoded){
 if(![color,model].includes(target.mnemonic)&&!flag(target.mnemonic))return animationDecode(target,encoded);
 const raw=Uint8Array.from(encoded.match(/../g)??[],v=>parseInt(v,16)),extended=target.target_context!==null,header=extended?2:1;
 if(flag(target.mnemonic)){
  if(raw.length!==header+1||raw.length!==target.instruction_length||(raw[0]>=128)!==extended||extended&&raw[1]!==target.target_context||(raw[0]&127)!==flagOpcodes[target.mnemonic])fail('Flag dispatch or actor context changed.');
  return {values:{bit:raw[header]&31}};
 }
 const modelTarget=target.mnemonic===model;
 if(raw.length!==header+(modelTarget?3:6)||raw.length!==target.instruction_length||(raw[0]>=128)!==extended||extended&&raw[1]!==target.target_context||(modelTarget?((raw[0]&127)!==0x4c||raw[header]!==0x50):((raw[0]&127)!==0x34||raw[header]>>4!==0)))fail('Instruction dispatch or actor context changed.');
 if(modelTarget){const unsigned=raw[header+1]+256*raw[header+2];return {values:{model_selector_signed:unsigned>=32768?unsigned-65536:unsigned}};}
 const at=header+1,unsigned=raw[at+3]+256*raw[at+4];return {values:{red:raw[at],green:raw[at+1],blue:raw[at+2],intensity:unsigned>=32768?unsigned-65536:unsigned}};
}
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),fail=message=>{throw Error(message);};
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const bytes=v=>{if(typeof v!=='string'||v.length>2*1024*1024||!/^[A-Za-z0-9+/]*={0,2}$/.test(v))fail('World script byte witness is invalid.');return Uint8Array.from(atob(v),c=>c.charCodeAt(0));};
const hex=v=>Array.from(v,n=>n.toString(16).padStart(2,'0')).join('');
const hash=async v=>hex(new Uint8Array(await crypto.subtle.digest('SHA-256',v)));
const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
export async function qualifyWorldScriptOperands(v,record,key,path){
 const keys=['schema_version','project_path','source_key','script_id','source_record','entry_pc','source_instance_ids','record_base64','current_record_base64','targets','limitations','project_changed','gameplay_verified'];
 if(!exact(v,keys)||v.schema_version!=='legaia.world-script-animation-operands.v1'||v.project_path!==path||v.source_key!==key||v.script_id!==record.id||record.kind!=='script'||!same(v.source_record,record.source_record)||!same(v.source_instance_ids,record.source_instance_ids)||v.project_changed!==false||v.gameplay_verified!==false||!Array.isArray(v.targets)||v.targets.length>1024||!Array.isArray(v.limitations)||v.limitations.length>256||v.limitations.some(s=>typeof s!=='string'||s.length>8192))fail('World instruction argument source is stale or invalid.');
 const retail=bytes(v.record_base64),current=bytes(v.current_record_base64),expected=retail.slice(),used=new Set();
 if(retail.length!==v.source_record.byte_length||current.length!==retail.length||await hash(retail)!==v.source_record.sha256||v.entry_pc!==2+2*retail[0]||v.entry_pc!==record.entry_pc||v.entry_pc>retail.length)fail('World script record bytes or header differ from the source asset.');
 for(const t of v.targets){
  if(!exact(t,['pc','mnemonic','target_context','retail_values','authored_values','current_values'])||!Number.isSafeInteger(t.pc)||t.pc<v.entry_pc||t.pc>=retail.length||used.has(t.pc)||!valuesValid(t.mnemonic,t.retail_values)||!(t.authored_values===null||valuesValid(t.mnemonic,t.authored_values))||!same(t.current_values,t.authored_values??t.retail_values)||!(t.target_context===null||Number.isSafeInteger(t.target_context)&&t.target_context>=0&&t.target_context<=255))fail('World instruction argument target is invalid.');
  const spec=operandSpecs[t.mnemonic],header=t.target_context===null?1:2,size=header+(flag(t.mnemonic)?1:1+spec.reduce((n,[,w])=>n+w,0)),span=retail.slice(t.pc,t.pc+size),decoded=decodeInstruction({...t,instruction_length:size},hex(span));
  if(!same(decoded.values,t.retail_values))fail('World instruction arguments differ from source instruction bytes.');
  for(let n=t.pc;n<t.pc+size;n++){if(used.has(n))fail('World instruction spans overlap.');used.add(n);}
  if(flag(t.mnemonic)){const at=t.pc+header;expected[at]=(retail[at]&224)|t.current_values.bit;}
  else {let offset=t.pc+header+1;for(const [field,width] of spec){const value=t.current_values[field];for(let n=0;n<width;n++)expected[offset+n]=Math.floor(value/2**(8*n))&255;offset+=width;}}
 }
 if(hex(expected)!==hex(current))fail('World Current script witness changes unsupported bytes.');
 return structuredClone(v);
}
export function qualifyWorldScriptReview(v,source,target,values,shared){
 const keys=['schema_version','project_path','source_key','script_id','pc','mnemonic','retail_values','current_values','proposed_values','source_instance_ids','shared','current_man_sha256','candidate_man_sha256','changes','compression','no_op','project_changed','gameplay_verified','review_key'];
 if(!exact(v,keys)||v.schema_version!=='legaia.world-script-animation-review.v1'||v.project_path!==source.project_path||v.source_key!==source.source_key||v.script_id!==source.script_id||v.pc!==target.pc||v.mnemonic!==target.mnemonic||!same(v.retail_values,target.retail_values)||!same(v.current_values,target.current_values)||!same(v.proposed_values,values)||!same(v.source_instance_ids,source.source_instance_ids)||v.shared!==shared||source.source_instance_ids.length>1&&!shared||v.project_changed!==false||v.gameplay_verified!==false||typeof v.no_op!=='boolean'||!['current_man_sha256','candidate_man_sha256','review_key'].every(k=>typeof v[k]==='string'&&/^[0-9a-f]{64}$/.test(v[k]))||!valuesValid(target.mnemonic,values))fail('World operand Review differs from its source or draft.');
 const spec=operandSpecs[target.mnemonic],relative=target.pc+(target.target_context===null?1:2)+(flag(target.mnemonic)?0:1),start=source.source_record.byte_offset+relative,changes=[];let offset=start;
 if(flag(target.mnemonic)){const high=bytes(source.record_base64)[relative]&224,a=high|target.current_values.bit,b=high|values.bit;if(a!==b)changes.push({decoded_byte_offset:start,before_byte:a,after_byte:b});}
 else for(const [field,width] of spec){for(let n=0;n<width;n++){const a=Math.floor(target.current_values[field]/2**(8*n))&255,b=Math.floor(values[field]/2**(8*n))&255;if(a!==b)changes.push({decoded_byte_offset:offset+n,before_byte:a,after_byte:b});}offset+=width;}
 if(!same(v.changes,changes)||v.no_op!==(changes.length===0)||!v.compression||v.compression.decoded_size!==source.source_record.man_slot.decoded_byte_length||v.compression.original_encoded_size!==source.source_record.man_slot.compressed_bytes_consumed||!Number.isSafeInteger(v.compression.new_encoded_size)||v.compression.new_encoded_size<1||v.compression.new_encoded_size>v.compression.original_encoded_size)fail('World operand Review changes unrelated bytes or exceeds its source span.');
 return structuredClone(v);
}
export function mountWorldScriptOperands({host,record,key,path,current,busy,setBusy,api,onApplied,onError}){
 const section=node('section');section.dataset.worldScriptOperands='';const open=node('button','Edit World Instruction Arguments');section.append(open);host.append(section);let source=null,review=null,disposed=false,pending=null,generation=0,target=null,inputs={},shared=null,reviewButton=null,applyButton=null,status=null;
 const valid=()=>!disposed&&current();
 const update=()=>{open.disabled=!valid()||busy();if(reviewButton)reviewButton.disabled=!valid()||busy()||!target;if(applyButton)applyButton.disabled=!valid()||busy()||!review||review.no_op;};
 const clearReview=()=>{generation++;review=null;if(status)status.textContent='Draft changed. Review before Apply.';update();};
 const values=()=>{const result={};for(const [field,width] of operandSpecs[target.mnemonic]){const text=inputs[field].value;if(!/^-?\d+$/.test(text))fail('Enter an integer for each instruction argument.');const v=Number(text);if(!Number.isSafeInteger(v)||v<minimum(field)||v>maximum(field,width,target.mnemonic))fail('Instruction argument exceeds its encoded domain.');result[field]=v;}if(!valuesValid(target.mnemonic,result))fail('This flag bit has an unsupported native side effect or width.');return result;};
 async function request(route,body){const controller=new AbortController();pending=controller;setBusy(true);update();try{const r=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal}),text=await r.text();if(new TextEncoder().encode(text).length>4*1024*1024)fail('World script operand response exceeds its budget.');const v=JSON.parse(text);if(!r.ok)fail(v.error||'World script operation failed.');if(!valid()||pending!==controller)fail('World script source changed during request.');return v;}finally{if(pending===controller){pending=null;setBusy(false);update();}}}
 function render(){
  section.replaceChildren(node('h3','World Instruction Arguments'),node('p','Retail / Authored / Current arguments. Encoded IDs do not establish model or clip identity. RGB/intensity are native arguments; visual effects remain unverified. Signed model selectors do not resolve to model assets; values at least 240 select high-pool dispatch. Flag bits are encoded arguments, not live values or named story flags; local bits above 15 and context SET8/CLEAR10 are unsupported.'));const select=node('select');select.setAttribute('aria-label','World instruction');for(const t of source.targets){const option=node('option',t.mnemonic+' · PC '+t.pc.toString(16).padStart(4,'0'));option.value=String(t.pc);select.append(option);}section.append(select);const fields=node('div');section.append(fields);const sharedLabel=node('label','Apply to every source object sharing this script');shared=node('input');shared.type='checkbox';shared.setAttribute('aria-label','Shared World script consent');shared.onchange=clearReview;sharedLabel.prepend(shared);sharedLabel.hidden=source.source_instance_ids.length<2;section.append(sharedLabel);status=node('p');section.append(status);reviewButton=node('button','Review World Arguments');applyButton=node('button','Apply World Arguments');section.append(reviewButton,applyButton);
  const choose=()=>{target=source.targets.find(t=>t.pc===Number(select.value))??null;fields.replaceChildren();inputs={};if(target)for(const [field,width,label] of operandSpecs[target.mnemonic]){const row=node('label',label),input=node('input');input.type='number';input.min=String(minimum(field));input.max=String(maximum(field,width,target.mnemonic));input.step='1';input.value=String(target.current_values[field]);input.setAttribute('aria-label','World '+label);input.oninput=clearReview;Object.assign(input.style,{display:'block',width:'100%',minWidth:'0'});row.append(input,node('small',`Retail ${target.retail_values[field]} · Authored ${target.authored_values?.[field]??'None'} · Current ${target.current_values[field]}`));fields.append(row);inputs[field]=input;}clearReview();if(!target)status.textContent='No reached supported fixed instruction arguments in this source record.';};select.onchange=choose;choose();
  reviewButton.onclick=async()=>{if(reviewButton.disabled)return;try{const wanted=values(),consent=shared.checked,ticket=generation,raw=await request('/api/world-script-animation-review',{script_id:record.id,source_key:key,pc:target.pc,values:wanted,shared:consent});const q=qualifyWorldScriptReview(raw,source,target,wanted,consent);if(!valid()||ticket!==generation)return;review=q;status.textContent=q.no_op?'Current arguments unchanged.':`${q.changes.length} source MAN bytes will change for ${q.source_instance_ids.length} source object(s). Gameplay unverified.`;update();}catch(e){review=null;if(status)status.textContent=e.message;onError(e);update();}};
  applyButton.onclick=async()=>{if(applyButton.disabled)return;try{const wanted=values();qualifyWorldScriptReview(review,source,target,wanted,shared.checked);const result=await api('/api/command',{type:'set_world_script_animation_operands',script_id:record.id,source_key:key,pc:target.pc,values:wanted,shared:shared.checked,review_key:review.review_key});if(result)onApplied(result);}catch(e){onError(e);}};
 }
 open.onclick=async()=>{if(open.disabled)return;try{const v=await request('/api/world-script-animation-operands',{script_id:record.id,source_key:key});const q=await qualifyWorldScriptOperands(v,record,key,path);if(!valid())return;source=q;render();}catch(e){onError(e);}};update();return {update,dispose(){disposed=true;pending?.abort();if(pending){pending=null;setBusy(false);}section.remove();}};
}
