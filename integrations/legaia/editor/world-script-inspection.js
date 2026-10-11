import {qualifyWorldScriptGraph as qualifyGraph} from './world-script-graph.js';
import {qualifyWorldScriptOperands} from './world-script-animation-operands.js';
import {updateWorldBranchGraph,reachedWorldBranchGraph,worldBranchTarget} from './world-script-branch-bytes.js';
const fail=message=>{throw Error(message);};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const bytes=v=>Uint8Array.from(atob(v),c=>c.charCodeAt(0));
const hex=v=>Array.from(v,n=>n.toString(16).padStart(2,'0')).join('');
export function locateWorldScriptPc(graph,pc,recordLength){
 if(!Number.isSafeInteger(pc)||pc<0||pc>65535)fail('Enter a script PC from 0000 to ffff.');
 if(pc>=recordLength)return {kind:pc===recordLength?'record_end':'outside_record',pc};
 if(pc<graph.entry_pc)return {kind:'header',pc};
 for(const kind of ['instructions','dialogues','unvisited_instructions','unvisited_dialogues','opaque_regions']){
  const row=(graph[kind]||[]).find(r=>pc>=r.pc&&pc<r.pc+r.length);
  if(row)return {kind,pc:row.pc,offset:pc-row.pc};
 }
 fail('Script PC has no qualified record ownership.');
}
export async function qualifyWorldScriptInspection(value,record,key,path){
 if(!exact(value,['schema_version','source','retail_graph','current_graph','read_only','project_changed','gameplay_verified'])||!['legaia.world-script-inspection.v1','legaia.world-script-inspection.v2'].includes(value.schema_version)||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false)fail('World script inspection is invalid or writable.');
 const source=await qualifyWorldScriptOperands(value.source,record,key,path),retail=bytes(source.record_base64),current=bytes(source.current_record_base64);
 const branched=source.schema_version==='legaia.world-script-operands.v2';if(branched!==(value.schema_version==='legaia.world-script-inspection.v2'))fail('World graph and argument witness versions differ.');
 qualifyGraph(value.retail_graph,retail,source);
 if(branched){
  const keys=['status','entry_pc','instructions','dialogues','opaque_regions','stops'];if(!exact(value.current_graph,[...keys,'unreachable_source_pcs','unvisited_instructions','unvisited_dialogues']))fail('World branch graph has invalid retained source fields.');
  qualifyGraph(Object.fromEntries(keys.map(k=>[k,value.current_graph[k]])),current,source);
 }else qualifyGraph(value.current_graph,current,source);
 const expected=structuredClone(value.retail_graph),targets=new Map(source.targets.map(t=>[t.pc,t]));
 for(const row of expected.instructions){
  const target=targets.get(row.pc);if(!target)continue;
  if(row.mnemonic!==target.mnemonic||row.target_context!==target.target_context)fail('World graph instruction differs from its qualified argument target.');
  const header=target.target_context===null?1:2,args=row.operands,values=target.current_values;
  // Decode the authorable fields independently; preserve every other SDK
  // analysis field, including unresolved semantics and branch metadata.
  if(target.mnemonic==='EFFECT_COLOR_INTENSITY'){if(!same(args.rgb,[target.retail_values.red,target.retail_values.green,target.retail_values.blue])||args.intensity!==target.retail_values.intensity)fail('Retail color graph values differ from bytes.');args.rgb=[values.red,values.green,values.blue];args.intensity=values.intensity;}
  else if(target.mnemonic==='MOVE_TO'){if(!same(args.world_xz,[target.retail_values.x,target.retail_values.z])||!same(args.encoded_xz,Array.from(retail.slice(row.pc+header,row.pc+header+2)))||!same(args.target_position,{x:target.retail_values.x,y:null,z:target.retail_values.z}))fail('Retail movement analysis differs from source bytes.');args.world_xz=[values.x,values.z];args.target_position={x:values.x,y:null,z:values.z};args.encoded_xz=Array.from(current.slice(row.pc+header,row.pc+header+2));}
  else {
   for(const [field,value] of Object.entries(target.retail_values))if(args[field]!==value)fail('Retail graph arguments differ from bytes.');
   Object.assign(args,values);
   if(target.mnemonic==='SET_ACTOR_MODEL'){if(args.model_selector_u16!==(target.retail_values.model_selector_signed&65535)||args.high_pool_flag!==(target.retail_values.model_selector_signed>=240))fail('Retail model selector analysis differs from encoded values.');args.model_selector_u16=values.model_selector_signed&65535;args.high_pool_flag=values.model_selector_signed>=240;}
   if(Object.hasOwn(values,'bit')){if(args.raw_operand!==retail[row.pc+header])fail('Retail flag mask differs from bytes.');args.raw_operand=current[row.pc+header];}
  }
  row.opcode=current[row.pc]&127;row.raw_hex=hex(current.slice(row.pc,row.pc+row.length));args.encoded_hex=hex(current.slice(row.pc+header,row.pc+row.length));
 }
 if(branched)updateWorldBranchGraph(source,retail,current,expected);
 const expectedCurrent=branched?reachedWorldBranchGraph(expected,current,source):expected;
 if(!same(expectedCurrent,value.current_graph))fail('Current graph changed unrelated instructions, analysis, branch edges or dormant source ownership.');
 return structuredClone(value);
}
const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
export function mountWorldScriptInspection({host,record,key,path,current,busy,setBusy,onError,onEdit,onEditBranch}){
 const section=node('section'),open=node('button','Inspect Retail / Current Instructions'),status=node('p'),output=node('div');section.dataset.worldScriptInspection='';section.append(open,status,output);host.append(section);let disposed=false,pending=null;
 const valid=()=>!disposed&&current(),update=()=>{open.disabled=!valid()||busy();};
 open.onclick=async()=>{
  if(open.disabled||busy())return;const controller=new AbortController();pending=controller;setBusy(true);update();
  try{
   const response=await fetch('/api/world-script-inspection',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({script_id:record.id,source_key:key}),signal:controller.signal}),text=await response.text();
   if(new TextEncoder().encode(text).length>32*1024*1024)fail('World script inspection exceeds its response budget.');const raw=JSON.parse(text);if(!response.ok)fail(raw.error||'World script inspection failed.');
   const value=await qualifyWorldScriptInspection(raw,record,key,path);if(!valid()||pending!==controller)return;
   output.replaceChildren(node('p','SDK static analysis. Decoded branches are possibilities, not an execution trace. Opaque bytes and decoder stops remain unknown.'));
   const locator=node('div'),label=node('label','Script PC (Hex)'),pcInput=node('input'),locate=node('button','Locate PC'),location=node('p'),locations=new Map();let highlighted=null;
   pcInput.setAttribute('aria-label','World Script PC (Hex)');pcInput.value=value.source.entry_pc.toString(16).padStart(4,'0');pcInput.maxLength=4;Object.assign(pcInput.style,{width:'100%',minWidth:'0'});label.append(pcInput);locator.append(label,locate,location);output.append(locator);
   const navigate=pc=>{
    if(!valid()||busy())return;
    try{
     const found=locateWorldScriptPc(value.current_graph,pc,value.source.source_record.byte_length);
     if(highlighted){highlighted.style.outline='';highlighted.removeAttribute('data-world-pc-focused');highlighted=null;}
     pcInput.value=pc.toString(16).padStart(4,'0');
     const element=locations.get(found.kind+':'+found.pc);
     location.textContent=found.kind==='header'?'PC belongs to the source record header.':found.kind==='record_end'?'PC is the end of this record; no instruction exists here.':found.kind==='outside_record'?'PC is outside this source record; no target is inferred.':`${found.kind==='instructions'?'Instruction':found.kind==='dialogues'?'Dialogue record':found.kind==='unvisited_instructions'?'Dormant source instruction':found.kind==='unvisited_dialogues'?'Dormant source dialogue':'Opaque region'} at ${found.pc.toString(16).padStart(4,'0')} · byte offset within row ${found.offset}. Static source ownership only.`;
     if(element){highlighted=element;const details=element.closest('details');if(details)details.open=true;element.style.outline='2px solid currentColor';element.dataset.worldPcFocused='';element.focus({preventScroll:true});element.scrollIntoView({block:'center'});}
    }catch(error){location.textContent=error.message;}
   };
   locate.onclick=()=>{if(!/^[0-9a-fA-F]{1,4}$/.test(pcInput.value)){location.textContent='Enter one to four hexadecimal digits.';return;}navigate(parseInt(pcInput.value,16));};pcInput.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();locate.click();}};
   const table=node('table');table.dataset.worldCurrentInstructions='';Object.assign(table.style,{width:'100%',tableLayout:'fixed'});const heading=node('tr');for(const label of ['PC / Instruction','Retail / Current Bytes','Arguments / Branches'])heading.append(node('th',label));table.append(heading);
   const targets=new Map(value.source.targets.map(t=>[t.pc,t]));
   const currentInstructions=new Map([...value.current_graph.instructions,...(value.current_graph.unvisited_instructions||[])].map(r=>[r.pc,r])),reached=new Set(value.current_graph.instructions.map(r=>r.pc)),branchEdits=new Map((value.source.branch_changes||[]).map(r=>[r.pc,r]));
   const sourceBytes=bytes(value.source.record_base64),sourceDestinations=new Set([...value.retail_graph.instructions,...value.retail_graph.dialogues].filter(r=>r.pc<=32767).map(r=>r.pc));
   for(let i=0;i<value.retail_graph.instructions.length;i++){
    const retail=value.retail_graph.instructions[i],now=currentInstructions.get(retail.pc),target=targets.get(now.pc),row=node('tr');row.dataset.worldInstructionPc=String(now.pc);row.dataset.authored=String(retail.raw_hex!==now.raw_hex);row.dataset.worldStaticReached=String(reached.has(now.pc));
    const identity=node('td',now.pc.toString(16).padStart(4,'0')+' · '+now.mnemonic),encoded=node('td',`Retail ${retail.raw_hex}\nCurrent ${now.raw_hex}`),detail=node('td');
    if(value.schema_version==='legaia.world-script-inspection.v2')identity.append(node('p',reached.has(now.pc)?'Reached by Current static graph':'Dormant source instruction · retained Current bytes'));
    const branchEdit=branchEdits.get(now.pc);if(branchEdit)detail.append(node('p',`Branch ${branchEdit.condition}\nRetail destination ${branchEdit.retail_target_pc.toString(16).padStart(4,'0')}\nAuthored / Current destination ${branchEdit.authored_target_pc.toString(16).padStart(4,'0')}`));
    const branchTarget=value.retail_graph.stops.length?null:worldBranchTarget(retail,sourceBytes);if(onEditBranch&&branchTarget&&branchTarget.pc<=32767&&sourceDestinations.has(branchTarget.target_pc)){const edit=node('button','Edit Destination');edit.dataset.worldBranchEdit=String(now.pc);Object.assign(edit.style,{whiteSpace:'normal',maxWidth:'100%'});edit.onclick=()=>{if(valid()&&!busy())onEditBranch(now.pc);};detail.append(edit);}
    if(target){detail.append(node('p',`Retail ${JSON.stringify(target.retail_values)}\nAuthored ${target.authored_values===null?'None':JSON.stringify(target.authored_values)}\nCurrent ${JSON.stringify(target.current_values)}`));const edit=node('button','Edit Arguments');edit.dataset.worldInstructionEdit=String(now.pc);Object.assign(edit.style,{whiteSpace:'normal',maxWidth:'100%',overflowWrap:'anywhere'});edit.onclick=()=>{if(valid()&&!busy())onEdit(now.pc);};detail.append(edit);}
    else detail.append(node('p',`Read-only SDK operands ${JSON.stringify(now.operands)}`));
    for(const edge of now.successors){const jump=node('button',`${edge.condition} → ${edge.pc.toString(16).padStart(4,'0')}`);jump.dataset.worldBranchPc=String(edge.pc);Object.assign(jump.style,{whiteSpace:'normal',maxWidth:'100%',overflowWrap:'anywhere'});jump.onclick=()=>navigate(edge.pc);detail.append(jump);}
    row.tabIndex=-1;locations.set((reached.has(now.pc)?'instructions:':'unvisited_instructions:')+now.pc,row);
    for(const cell of [identity,encoded,detail])Object.assign(cell.style,{overflowWrap:'anywhere',whiteSpace:'pre-wrap',verticalAlign:'top'});row.append(identity,encoded,detail);table.append(row);
   }
   output.append(table);status.textContent=`${value.current_graph.instructions.length} Current static instructions · ${(value.current_graph.unvisited_instructions||[]).length} dormant source instructions · ${value.retail_graph.instructions.filter(r=>currentInstructions.get(r.pc).raw_hex!==r.raw_hex).length} authored instructions · ${value.current_graph.opaque_regions.length} unvisited or opaque regions · ${value.current_graph.stops.length} decoder stops. No script executed or project changed.`;
   for(const family of ['dialogues','unvisited_dialogues','opaque_regions','stops']){
    if(!value.current_graph[family]?.length)continue;
    const details=node('details'),summary=node('summary',`${family==='opaque_regions'?'Unvisited or Opaque Regions':family==='stops'?'Decoder Stops':family==='unvisited_dialogues'?'Dormant Source Dialogue Records':'Dialogue Records'} (${value.current_graph[family].length})`);details.append(summary);
    for(const row of value.current_graph[family]){const body=node('pre',JSON.stringify(row,null,2));Object.assign(body.style,{whiteSpace:'pre-wrap',overflowWrap:'anywhere'});body.tabIndex=-1;body.addEventListener('focus',()=>{details.open=true;});details.append(body);if(family!=='stops')locations.set(family+':'+row.pc,body);}
    output.append(details);
   }
  }catch(error){if(error.name!=='AbortError'&&valid()){status.textContent=error.message;onError(error);}}
  finally{if(pending===controller){pending=null;setBusy(false);update();}}
 };update();return {update,dispose(){disposed=true;pending?.abort();if(pending){pending=null;setBusy(false);}section.remove();}};
}
