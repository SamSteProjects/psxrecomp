import {validateControllerSourceEvidence} from './controller-references.js';
// A group identifies encoded operands in one retail script, not a runtime variable.
import {decodeFlagQualification,decodeControllerFlagQualification} from './flag-qualification.js';
const MAX_REFERENCES=16384, PAGE_SIZE=50;
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const text=(value,max=8192)=>typeof value==='string'&&value.length>0&&value.length<=max;
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&[Object.prototype,null].includes(Object.getPrototypeOf(value));
const scopes={local:'dispatch_context_local_flags',global:'host_global_flags',context:'dispatch_context_flags',system:'system_bank_encoded_selector',extra:'host_extra_flags'};
const fail=message=>{throw new Error(message);};
function detached(value,depth=0,budget={nodes:0,characters:0}){
  if(depth>12||++budget.nodes>400000)fail('Flag metadata exceeds the inspector bound.');
  if(value===null||typeof value==='boolean')return value;
  if(typeof value==='number'){if(!Number.isFinite(value))fail('Invalid flag metadata number.');return value;}
  if(typeof value==='string'){
    budget.characters+=value.length;
    if(value.length>8192||budget.characters>8*1024*1024)fail('Flag metadata text exceeds the inspector bound.');
    return value;
  }
  if(Array.isArray(value)){
    if(value.length>MAX_REFERENCES)fail('Flag metadata list exceeds the inspector bound.');
    return value.map(row=>detached(row,depth+1,budget));
  }
  if(!object(value)||Object.keys(value).length>128)fail('Invalid flag metadata object.');
  return Object.fromEntries(Object.entries(value).map(([key,child])=>{
    if(!text(key,256)||['raw_hex','encoded_hex','raw_bytes','payload','tokens','rgba'].includes(key))fail('Flag resources require bounded metadata only.');
    budget.characters+=key.length;
    return [key,detached(child,depth+1,budget)];
  }));
}
function sourceIdentity(value){
  if(!text(value.script_id,512))fail('Flag group requires a source-qualified script identity.');
  const match=/^script:\/\/([A-Za-z0-9_-]+)\/(actors\/man-p1|scripts\/man-p2|controllers\/man-p1)\/([0-9]{4})$/.exec(value.script_id);
  if(!match)fail('Flag group requires a source-qualified script identity.');
  const controller=match[2]==='controllers/man-p1';if(controller&&match[3]!=='0000')fail('Invalid scene controller record identity.');
  const partition=match[2]==='scripts/man-p2'?2:1;
  if(value.partition!==partition||value.owner_id!=='scene://'+value.script_id.slice(9))fail('Flag owner differs from its source script.');
  return {sceneId:'scene://'+match[1],partition,recordIndex:Number(match[3]),controller};
}
function validIndex(value,bank){return integer(value,0,bank==='system'?0xffff:31);}
function instruction(reference){
  const bit=/^(LFLAG|GFLAG|CFLAG|SYSFLAG)_(SET|CLEAR|TEST)$/.exec(reference.mnemonic);
  if(bit)return {bank:{LFLAG:'local',GFLAG:'global',CFLAG:'context',SYSFLAG:'system'}[bit[1]],operation:bit[2].toLowerCase(),authorable:bit[1]!=='SYSFLAG'};
  if(reference.mnemonic==='FLAG_WORD_BRANCH'&&['local','global','context'].includes(reference.bank))return {bank:reference.bank,operation:'test',authorable:false};
  if(reference.mnemonic==='COND_JMP')return {bank:'extra',operation:'test',authorable:false};
  fail('Unsupported encoded flag reference.');
}
export function decodeFlagResource(data){
  const value=detached(data);
  if(!object(value)||value.asset_kind!=='flag'||value.read_only!==true||value.grouping_layer!=='retail'||!text(value.semantic_id,512)||value.id!==value.semantic_id||!text(value.script_name,512)||!Object.hasOwn(scopes,value.bank)||value.scope!==scopes[value.bank]||!validIndex(value.index,value.bank)||!(value.extended_target===null||integer(value.extended_target,0,255))||value.runtime_binding!=='unresolved'||value.runtime_value!==null)fail('Invalid source-qualified flag resource.');
  const identity=sourceIdentity(value),context=value.extended_target===null?'current':`extended-${value.extended_target}`;
  if(value.semantic_id!==value.script_id.replace('script://','flag-reference://')+`/${context}/${value.bank}/${value.index}`)fail('Flag identity must retain its retail script, context, bank and selector.');
  if(!['decoded_supported_paths','partial'].includes(value.script_status)||!object(value.source_record)||!Object.keys(value.source_record).length)fail('Flag source script or provenance is unavailable.');
  const source=value.source_record;
  if(identity.controller){const p=validateControllerSourceEvidence(value.controller_source_evidence,identity.sceneId);if(JSON.stringify(p.source_record)!==JSON.stringify(source))fail('Controller flag source cannot contain actor authoring.');}else if(Object.hasOwn(value,'controller_source_evidence'))fail('Actor flag cannot use controller source evidence.');
  for(const [key,min,max] of [['byte_offset',0,0xffffffff],['byte_length',1,65536],['record_index',0,9999],['partition',1,2]])if(Object.hasOwn(source,key)&&!integer(source[key],min,max))fail('Invalid flag source record bounds.');
  if(Object.hasOwn(source,'partition')&&source.partition!==identity.partition||Object.hasOwn(source,'record_index')&&source.record_index!==identity.recordIndex)fail('Flag source record differs from its script identity.');
  if(Object.hasOwn(source,'sha256')&&(typeof source.sha256!=='string'||!/^[0-9a-f]{64}$/.test(source.sha256)))fail('Invalid flag source record hash.');
  if(Object.hasOwn(source,'prot_entry_name')&&source.prot_entry_name!==identity.sceneId.slice(8))fail('Flag provenance names another scene.');
  if(!Array.isArray(value.references)||!integer(value.references.length,1,MAX_REFERENCES)||value.reference_count!==value.references.length||!integer(value.authored_reference_count,0,value.reference_count))fail('Flag reference counts exceed their source coverage.');
  const seen=new Set();let authored=0;
  for(const reference of value.references){
    if(!object(reference)||!integer(reference.pc,0,65535)||seen.has(reference.pc)||!integer(reference.byte_offset,0,0xffffffff)||!text(reference.mnemonic,64)||reference.bank!==value.bank||reference.scope!==value.scope||reference.extended_target!==value.extended_target||reference.index!==value.index||reference.retail_index!==value.index||reference.runtime_value!==null||Object.hasOwn(reference,'runtime_binding')&&reference.runtime_binding!=='unresolved')fail('Invalid flag instruction site or retail layer.');
    seen.add(reference.pc);
    if(Object.hasOwn(source,'byte_offset')&&reference.byte_offset!==source.byte_offset+reference.pc||Object.hasOwn(source,'byte_length')&&reference.pc>=source.byte_length)fail('Flag instruction site is outside its source record.');
    const decoded=instruction(reference),system=decoded.bank==='system'&&reference.extended_target===null&&reference.index<=4095&&reference.authored_index!==null,operandId=identity.controller&&reference.authored_index===null?null:system?`${value.script_id}/system-flag/${reference.pc.toString(16).padStart(4,'0')}`:decoded.authorable?`${value.script_id}/flag-bit/${reference.pc.toString(16).padStart(4,'0')}`:null;
    if(decoded.bank!==value.bank||decoded.operation!==reference.operation||reference.flag_operand_id!==operandId||reference.context_resolution!==(value.extended_target===null?'current_script_context':'extended_target_unresolved')||reference.index_semantics!==(value.bank==='system'?'encoded_selector_not_resolved_runtime_bit':'operand_masked_to_five_bits')||reference.status!==(value.bank==='local'&&value.index>=16?'bank_width_unresolved':'encoded_reference'))fail('Flag instruction interpretation differs from its encoded reference.');
    if(reference.authored_index!==null&&(!decoded.authorable&&!system||!integer(reference.authored_index,0,system?4095:31)))fail('Invalid authored flag operand annotation.');
    const qualified=Object.hasOwn(reference,'authored_qualification');if(qualified)(identity.controller?decodeControllerFlagQualification:decodeFlagQualification)(reference.authored_qualification,{owner_id:value.owner_id,operand_id:reference.flag_operand_id,source_record_sha256:source.sha256,pc:reference.pc,mnemonic:reference.mnemonic,extended_target:reference.extended_target,retail_index:reference.retail_index,authored_index:reference.authored_index});
    if(identity.controller&&reference.authored_index!==null&&!qualified)fail('Authored controller flags require native qualification.');
    if(identity.controller&&reference.authored_index===null&&qualified)fail('Controller qualification requires an authored selector.');
    if(system&&!qualified)fail('Authored system selector lacks native qualification.');
    if(reference.authored_index!==null&&(value.script_status!=='decoded_supported_paths'&&!qualified||value.bank==='local'&&(value.index>=16||reference.authored_index>=16)||reference.mnemonic==='CFLAG_SET'&&(value.index===8||reference.authored_index===8)||reference.mnemonic==='CFLAG_CLEAR'&&(value.index===10||reference.authored_index===10)))fail('Authored flag annotation exceeds verified script, width or context-selector support.');
    if(reference.effective_index!==(reference.authored_index??reference.retail_index))fail('Effective flag selector differs from its operand layers.');
    authored+=reference.authored_index!==null;
  }
  if(authored!==value.authored_reference_count)fail('Authored flag reference count is inconsistent.');
  const coverage=value.coverage;
  if(!object(coverage)||!integer(coverage.script_count,1,1024)||!integer(coverage.partial_script_count,0,coverage.script_count)||!integer(coverage.unavailable_script_count,0,coverage.script_count)||coverage.partial_script_count+coverage.unavailable_script_count>coverage.script_count||value.script_status==='partial'&&coverage.partial_script_count===0||!Array.isArray(value.limitations)||value.limitations.length>64||!value.limitations.every(row=>text(row)))fail('Invalid flag inspection coverage or limitations.');
  return value;
}
export function flagResourceNavigationAllowed(data,pc,{current,busy,canInspect,open=true,pending=false}={}){
  if(open!==true||pending!==false||current!==true||busy!==false||canInspect!==true||data?.read_only!==true||data.grouping_layer!=='retail'||!Array.isArray(data.references))return false;
  return pc===null||integer(pc,0,65535)&&data.references.some(reference=>reference.pc===pc);
}
const pcLabel=pc=>'0x'+pc.toString(16).padStart(4,'0').toUpperCase();
const words=value=>value.replaceAll('_',' ');
function element(tag,value,className){const node=document.createElement(tag);if(value!==undefined)node.textContent=value;if(className)node.className=className;return node;}
function property(host,label,value){const row=element('dl',undefined,'property');row.style.gridTemplateColumns='135px 1fr';row.append(element('dt',label),element('dd',value));host.append(row);}
export function openFlagResource({record,current,busy,canInspect,onInspect,onError=()=>{}}){
  let data;
  try{
    if(typeof current!=='function'||typeof busy!=='function'||typeof canInspect!=='function'||typeof onInspect!=='function')fail('Flag inspection navigation requires editor context guards.');
    if(busy()||!current())return null;
    data=decodeFlagResource(record?.data);
    const sceneId='scene://'+data.script_id.slice(9).split('/')[0];
    if(record.type!=='flag'||record.id!==data.semantic_id||record.sceneId!==sceneId||!text(record.label,512)||!text(record.source,512))fail('Flag resource differs from its catalog selection.');
  }catch(error){onError(error);return null;}
  const dialog=element('dialog');dialog.id='flag-resource-dialog';dialog.className='project-dialog';dialog.style.width='min(1040px,calc(100vw - 35px))';dialog.style.maxHeight='90vh';dialog.style.overflow='auto';
  const heading=element('div',undefined,'dialog-heading'),close=element('button','×');close.type='button';close.setAttribute('aria-label','Close flag resource');heading.append(element('h2',record.label),close);dialog.append(heading);
  dialog.append(element('p','Read-only encoded operand references within one retail script. Runtime variable binding and live values are unresolved; authored/current encoded selectors are separate from runtime state. Matching selectors in other scripts are separate source groups.'));
  property(dialog,'Stable source ID',data.semantic_id);property(dialog,'Source scene',record.source);property(dialog,'Script',data.script_name);property(dialog,'Source owner',data.owner_id);property(dialog,'Bank / retail index',`${data.bank} / ${data.index}`);property(dialog,'Scope',words(data.scope));property(dialog,'Dispatch context',data.extended_target===null?'Current script context':`Extended target ${data.extended_target} · unresolved`);
  property(dialog,'Inspection',data.script_status==='partial'?'Partial inspection · unknown or unvisited paths remain outside coverage':'Decoded supported paths · execution is not established');
  property(dialog,'Operand sites',`${data.reference_count} decoded · ${data.authored_reference_count} authored annotations · grouped by retail index`);
  property(dialog,'Scene coverage',`${data.coverage.script_count} scripts · ${data.coverage.partial_script_count} partial · ${data.coverage.unavailable_script_count} unavailable`);
  property(dialog,'Runtime values','Unavailable · source binding unresolved');
  const sites=[...data.references].sort((a,b)=>a.pc-b.pc),actions=element('div',undefined,'dialog-actions');actions.style.flexWrap='wrap';actions.style.justifyContent='flex-start';
  const parent=element('button','Inspect parent script'),first=element('button','Inspect first operand'),last=element('button','Inspect last operand');for(const button of [parent,first,last])button.type='button';actions.append(parent,first,last);dialog.append(actions);
  const status=element('p');status.setAttribute('role','status');dialog.append(status,element('h3','Retail, authored and effective operand sites'));
  const wrap=element('div',undefined,'script-table-wrap'),table=element('table'),thead=element('thead'),labels=element('tr'),tbody=element('tbody');
  for(const label of ['Script PC','Instruction / operation','Retail','Authored','Effective','Interpretation','Source script'])labels.append(element('th',label));thead.append(labels);table.append(thead,tbody);wrap.append(table);dialog.append(wrap);
  const paging=element('div',undefined,'dialog-actions'),previous=element('button','Previous sites'),pageLabel=element('span'),next=element('button','Next sites');previous.type=next.type='button';paging.style.alignItems='center';paging.append(previous,pageLabel,next);dialog.append(paging);
  const limitations=element('section');limitations.append(element('h3','Source limits'));const list=element('ul');for(const note of data.limitations)list.append(element('li',note));limitations.append(list);dialog.append(limitations);
  const provenance=element('details'),summary=element('summary','Source provenance'),pre=element('pre',JSON.stringify({script_id:data.script_id,source_record:data.source_record,grouping_layer:data.grouping_layer,runtime_binding:data.runtime_binding},null,2),'diagnostic-detail');provenance.append(summary,pre);dialog.append(provenance);
  const error=element('p',undefined,'dialog-error');error.setAttribute('role','alert');dialog.append(error);
  let generation=0,pending=false,page=0,siteButtons=[];
  function gates(){return {current:current()===true,busy:busy()!==false,canInspect:canInspect()===true,open:dialog.open,pending};}
  function update(){
    const context=gates(),allowed=pc=>flagResourceNavigationAllowed(data,pc,context);parent.disabled=!allowed(null);first.disabled=!allowed(sites[0].pc);last.disabled=!allowed(sites.at(-1).pc);for(const [button,pc] of siteButtons)button.disabled=!allowed(pc);
    previous.disabled=pending||page===0;next.disabled=pending||(page+1)*PAGE_SIZE>=sites.length;
    status.textContent=!context.current?'Catalog context changed. Reopen this resource to navigate.':context.busy?'Another editor operation is in progress.':!context.canInspect?'Source script inspection is unavailable in the current editor context.':pending?'Opening verified source script…':'Inspect the parent script or a decoded operand at its exact source PC.';
  }
  async function inspect(pc){
    if(!flagResourceNavigationAllowed(data,pc,gates())){update();return false;}
    const token=++generation;pending=true;error.textContent='';update();
    try{const result=await onInspect(pc);if(token!==generation||!dialog.open)return false;if(result===false){error.textContent='Source script inspection could not be opened.';return false;}dialog.close();return true;}
    catch(cause){if(token===generation&&dialog.open){error.textContent=cause.message??String(cause);onError(cause);}return false;}
    finally{if(token===generation&&dialog.open){pending=false;update();}}
  }
  function render(){
    tbody.replaceChildren();siteButtons=[];
    for(const reference of sites.slice(page*PAGE_SIZE,(page+1)*PAGE_SIZE)){
      const row=element('tr');for(const value of [pcLabel(reference.pc),`${reference.mnemonic}\n${reference.operation}`,String(reference.retail_index),reference.authored_index===null?'None':String(reference.authored_index),String(reference.effective_index),`${words(reference.status)}\n${words(reference.index_semantics)}\n${words(reference.context_resolution)}${reference.authored_qualification?'\nNative authoring operand independently qualified; script coverage unchanged.':''}`])row.append(element('td',value));
      const cell=element('td'),button=element('button',`Inspect ${pcLabel(reference.pc)}`);button.type='button';button.onclick=()=>inspect(reference.pc);cell.append(button);row.append(cell);tbody.append(row);siteButtons.push([button,reference.pc]);
    }
    pageLabel.textContent=`Sites ${page*PAGE_SIZE+1}–${Math.min((page+1)*PAGE_SIZE,sites.length)} of ${sites.length}`;update();
  }
  parent.onclick=()=>inspect(null);first.onclick=()=>inspect(sites[0].pc);last.onclick=()=>inspect(sites.at(-1).pc);
  previous.onclick=()=>{if(!pending&&page>0){page--;render();}};next.onclick=()=>{if(!pending&&(page+1)*PAGE_SIZE<sites.length){page++;render();}};close.onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{generation++;pending=false;for(const button of [parent,first,last,previous,next,close,...siteButtons.map(([button])=>button)])button.onclick=null;siteButtons=[];dialog.remove();},{once:true});
  document.body.append(dialog);dialog.showModal();render();return dialog;
}
