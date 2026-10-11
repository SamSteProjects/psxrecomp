import {qualifyWorldScriptOperands} from './world-script-animation-operands.js';
const fail=message=>{throw Error(message);};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const bytes=v=>Uint8Array.from(atob(v),c=>c.charCodeAt(0));
const hex=v=>Array.from(v,n=>n.toString(16).padStart(2,'0')).join('');
export function locateWorldScriptPc(graph,pc,recordLength){
 if(!Number.isSafeInteger(pc)||pc<0||pc>65535)fail('Enter a script PC from 0000 to ffff.');
 if(pc>=recordLength)return {kind:pc===recordLength?'record_end':'outside_record',pc};
 if(pc<graph.entry_pc)return {kind:'header',pc};
 for(const kind of ['instructions','dialogues','opaque_regions']){
  const row=graph[kind].find(r=>pc>=r.pc&&pc<r.pc+r.length);
  if(row)return {kind,pc:row.pc,offset:pc-row.pc};
 }
 fail('Script PC has no qualified record ownership.');
}
function qualifyGraph(graph,data,source){
 if(!exact(graph,['status','entry_pc','instructions','dialogues','opaque_regions','stops'])||!['partial','decoded_supported_paths'].includes(graph.status)||graph.entry_pc!==source.entry_pc)fail('World instruction graph has an invalid source entry or status.');
 const used=new Uint8Array(data.length);
 for(const family of ['instructions','dialogues','opaque_regions']){
  if(!Array.isArray(graph[family])||graph[family].length>4096)fail('World instruction graph exceeds its row budget.');
  for(const row of graph[family]){
   if(!Number.isSafeInteger(row.pc)||!Number.isSafeInteger(row.length)||row.pc<source.entry_pc||row.length<1||row.pc+row.length>data.length||row.byte_offset!==source.source_record.byte_offset+row.pc||row.raw_hex!==hex(data.slice(row.pc,row.pc+row.length)))fail('World graph row differs from its exact record bytes.');
   for(let n=row.pc;n<row.pc+row.length;n++){if(used[n])fail('World graph record ownership overlaps.');used[n]=1;}
   if(family==='instructions'){
    if(typeof row.mnemonic!=='string'||row.mnemonic.length>128||row.opcode!==(data[row.pc]&127)||!row.operands||typeof row.operands!=='object'||Array.isArray(row.operands)||!Array.isArray(row.successors)||row.successors.length>8||!(row.target_context===null||Number.isSafeInteger(row.target_context)&&row.target_context>=0&&row.target_context<=255))fail('World instruction metadata is invalid.');
    for(const edge of row.successors)if(!exact(edge,['pc','condition'])||!Number.isSafeInteger(edge.pc)||edge.pc<0||edge.pc>65535||typeof edge.condition!=='string'||edge.condition.length>256)fail('World static branch edge is invalid.');
    // Message-picker leads mask bit 7 without introducing an actor context.
    const header=(data[row.pc]&128)&&![0x27,0x28,0x29].includes(row.opcode)?2:1;
    if(row.length<header||row.target_context!==(header===2?data[row.pc+1]:null)||row.operands.encoded_hex!==hex(data.slice(row.pc+header,row.pc+row.length)))fail('World instruction context or encoded operands differ from bytes.');
   }
  }
 }
 if(used.slice(source.entry_pc).some(n=>!n)||!Array.isArray(graph.stops)||graph.stops.length>4096||(graph.opaque_regions.length||graph.stops.length)&&graph.status!=='partial')fail('World graph coverage or unknown regions are inconsistent.');
}
export async function qualifyWorldScriptInspection(value,record,key,path){
 if(!exact(value,['schema_version','source','retail_graph','current_graph','read_only','project_changed','gameplay_verified'])||value.schema_version!=='legaia.world-script-inspection.v1'||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false)fail('World script inspection is invalid or writable.');
 const source=await qualifyWorldScriptOperands(value.source,record,key,path),retail=bytes(source.record_base64),current=bytes(source.current_record_base64);
 qualifyGraph(value.retail_graph,retail,source);qualifyGraph(value.current_graph,current,source);
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
 if(!same(expected,value.current_graph))fail('Current graph changed unrelated instructions, analysis or branch edges.');
 return structuredClone(value);
}
const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
export function mountWorldScriptInspection({host,record,key,path,current,busy,setBusy,onError,onEdit}){
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
     location.textContent=found.kind==='header'?'PC belongs to the source record header.':found.kind==='record_end'?'PC is the end of this record; no instruction exists here.':found.kind==='outside_record'?'PC is outside this source record; no target is inferred.':`${found.kind==='instructions'?'Instruction':found.kind==='dialogues'?'Dialogue record':'Opaque region'} at ${found.pc.toString(16).padStart(4,'0')} · byte offset within row ${found.offset}. Static source ownership only.`;
     if(element){highlighted=element;const details=element.closest('details');if(details)details.open=true;element.style.outline='2px solid currentColor';element.dataset.worldPcFocused='';element.focus({preventScroll:true});element.scrollIntoView({block:'center'});}
    }catch(error){location.textContent=error.message;}
   };
   locate.onclick=()=>{if(!/^[0-9a-fA-F]{1,4}$/.test(pcInput.value)){location.textContent='Enter one to four hexadecimal digits.';return;}navigate(parseInt(pcInput.value,16));};pcInput.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();locate.click();}};
   const table=node('table');table.dataset.worldCurrentInstructions='';Object.assign(table.style,{width:'100%',tableLayout:'fixed'});const heading=node('tr');for(const label of ['PC / Instruction','Retail / Current Bytes','Arguments / Branches'])heading.append(node('th',label));table.append(heading);
   const targets=new Map(value.source.targets.map(t=>[t.pc,t]));
   for(let i=0;i<value.retail_graph.instructions.length;i++){
    const retail=value.retail_graph.instructions[i],now=value.current_graph.instructions[i],target=targets.get(now.pc),row=node('tr');row.dataset.worldInstructionPc=String(now.pc);row.dataset.authored=String(retail.raw_hex!==now.raw_hex);
    const identity=node('td',now.pc.toString(16).padStart(4,'0')+' · '+now.mnemonic),encoded=node('td',`Retail ${retail.raw_hex}\nCurrent ${now.raw_hex}`),detail=node('td');
    if(target){detail.append(node('p',`Retail ${JSON.stringify(target.retail_values)}\nAuthored ${target.authored_values===null?'None':JSON.stringify(target.authored_values)}\nCurrent ${JSON.stringify(target.current_values)}`));const edit=node('button','Edit Arguments');edit.dataset.worldInstructionEdit=String(now.pc);Object.assign(edit.style,{whiteSpace:'normal',maxWidth:'100%',overflowWrap:'anywhere'});edit.onclick=()=>{if(valid()&&!busy())onEdit(now.pc);};detail.append(edit);}
    else detail.append(node('p',`Read-only SDK operands ${JSON.stringify(now.operands)}`));
    for(const edge of now.successors){const jump=node('button',`${edge.condition} → ${edge.pc.toString(16).padStart(4,'0')}`);jump.dataset.worldBranchPc=String(edge.pc);Object.assign(jump.style,{whiteSpace:'normal',maxWidth:'100%',overflowWrap:'anywhere'});jump.onclick=()=>navigate(edge.pc);detail.append(jump);}
    row.tabIndex=-1;locations.set('instructions:'+now.pc,row);
    for(const cell of [identity,encoded,detail])Object.assign(cell.style,{overflowWrap:'anywhere',whiteSpace:'pre-wrap',verticalAlign:'top'});row.append(identity,encoded,detail);table.append(row);
   }
   output.append(table);status.textContent=`${value.current_graph.instructions.length} Current instructions · ${value.current_graph.instructions.filter((r,i)=>r.raw_hex!==value.retail_graph.instructions[i].raw_hex).length} authored instructions · ${value.current_graph.opaque_regions.length} opaque regions · ${value.current_graph.stops.length} decoder stops. No script executed or project changed.`;
   for(const family of ['dialogues','opaque_regions','stops']){
    if(!value.current_graph[family].length)continue;
    const details=node('details'),summary=node('summary',`${family==='opaque_regions'?'Opaque Regions':family==='stops'?'Decoder Stops':'Dialogue Records'} (${value.current_graph[family].length})`);details.append(summary);
    for(const row of value.current_graph[family]){const body=node('pre',JSON.stringify(row,null,2));Object.assign(body.style,{whiteSpace:'pre-wrap',overflowWrap:'anywhere'});body.tabIndex=-1;body.addEventListener('focus',()=>{details.open=true;});details.append(body);if(family!=='stops')locations.set(family+':'+row.pc,body);}
    output.append(details);
   }
  }catch(error){if(error.name!=='AbortError'&&valid()){status.textContent=error.message;onError(error);}}
  finally{if(pending===controller){pending=null;setBusy(false);update();}}
 };update();return {update,dispose(){disposed=true;pending?.abort();if(pending){pending=null;setBusy(false);}section.remove();}};
}
