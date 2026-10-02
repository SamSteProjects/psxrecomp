const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const exact=(value,keys)=>object(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const text=(value,max=8192)=>typeof value==='string'&&value.length>0&&value.length<=max;
const fail=message=>{throw new Error('Invalid source facing report: '+message);};
const sectorValues=(value,empty=false)=>exact(value,empty?[]:['sector'])&&(empty||integer(value.sector,0,7));
const bytes=(value,length)=>typeof value==='string'&&value.length===length*2&&/^[0-9a-f]+$/.test(value)?Array.from({length},(_,index)=>parseInt(value.slice(index*2,index*2+2),16)):null;
const hex=value=>'0x'+value.toString(16).padStart(4,'0');
const describe=sector=>`Sector ${sector} · 12-bit ${sector*512} · ${sector*45}°`;

function sourceContext(report,owner){
  const match=typeof owner==='string'&&/^scene:\/\/([A-Za-z0-9_-]{1,128})\/(actors\/man-p1|scripts\/man-p2)\/([0-9]{4})$/.exec(owner);
  if(!match||!object(report)||report.read_only!==true||!['legaia.actor-script-inspection.v1','legaia.partition-two-script-inspection.v1','legaia.trigger-script-inspection.v1'].includes(report.schema_version))fail('owner or inspection identity');
  const script=owner.replace(/^scene:\/\//,'script://'),source=report.source_record,record=report.record;
  if((report.semantic_id??report.script_id)!==script||(Object.hasOwn(report,'script_id')&&report.script_id!==script)||(Object.hasOwn(report,'actor_semantic_id')&&report.actor_semantic_id!==owner)||(Object.hasOwn(report,'owner_id')&&report.owner_id!==owner))fail('inspection belongs to a different source owner');
  const partition=match[2]==='actors/man-p1'?1:2,recordKind=partition===1?'man_partition_1_actor_placement':'man_partition_2_script';
  if(!object(source)||!object(record)||!hash(record.sha256)||(Object.hasOwn(source,'sha256')&&source.sha256!==record.sha256)||!integer(source.byte_offset,0,4*1024*1024)||!integer(source.byte_length,1,65536)||source.byte_offset+source.byte_length>4*1024*1024||record.byte_offset!==source.byte_offset||record.byte_length!==source.byte_length||!integer(record.script_offset,0,record.byte_length)||(Object.hasOwn(source,'partition')?source.partition!==partition:source.record_kind!==recordKind)||(Object.hasOwn(source,'record_kind')&&source.record_kind!==recordKind)||source.record_index!==Number(match[3])||!text(source.byte_coordinate_space,128))fail('source record hash, extent or partition');
  if(Object.hasOwn(source,'prot_entry_name')&&source.prot_entry_name!==match[1])fail('source scene');
  if(Object.hasOwn(record,'raw_hex')&&!bytes(record.raw_hex,record.byte_length))fail('record byte payload');
  if(!Array.isArray(report.instructions)||report.instructions.length>4096||report.instructions.some(node=>!object(node)||!integer(node.pc,record.script_offset,record.byte_length-1))||new Set(report.instructions.map(node=>node.pc)).size!==report.instructions.length)fail('decoded instruction identities');
  return {script,source,record,digest:record.sha256,nodes:new Map(report.instructions.map(node=>[node.pc,node]))};
}

function targetSource(target,context,owner){
  const keys=['semantic_id','owner_id','pc','mnemonic','target_context','decoded_byte_offset','source_record_sha256','before_raw','preservation_mask','values','authored_values','effective_values'];
  if(!exact(target,keys)||target.owner_id!==owner||!integer(target.pc,0,65535)||target.semantic_id!==context.script+'/facing/'+target.pc.toString(16).padStart(4,'0')||!['NPC_RUN','CAM_CFG'].includes(target.mnemonic)||!(target.target_context===null||integer(target.target_context,0,255))||target.source_record_sha256!==context.digest||!integer(target.before_raw,0,255)||target.preservation_mask!==240||!sectorValues(target.values)||!(sectorValues(target.authored_values)||sectorValues(target.authored_values,true))||!sectorValues(target.effective_values)||target.effective_values.sector!==(target.authored_values.sector??target.values.sector))fail('target identity or authored layers');
  const node=context.nodes.get(target.pc),header=target.target_context===null?1:2,length=header+(target.mnemonic==='NPC_RUN'?5:2),opcode=target.mnemonic==='NPC_RUN'?0x4c:0x38;
  if(!node||node.mnemonic!==target.mnemonic||node.opcode!==opcode||node.target_context!==target.target_context||node.length!==length||node.byte_offset!==context.source.byte_offset+target.pc||target.pc+length>context.source.byte_length)fail('target differs from decoded instruction');
  const raw=bytes(node.raw_hex,length),operands=node.operands;
  if(!raw||raw[0]!==(header===2?opcode|0x80:opcode)||(header===2&&raw[1]!==target.target_context)||!object(operands)||operands.encoded_hex!==node.raw_hex.slice(header*2))fail('instruction header or raw operands');
  if(Object.hasOwn(context.record,'raw_hex')&&context.record.raw_hex.slice(target.pc*2,(target.pc+length)*2)!==node.raw_hex)fail('instruction differs from raw source record');
  const relative=header+(target.mnemonic==='NPC_RUN'?3:0),before=raw[relative];
  if(target.mnemonic==='NPC_RUN'){
    if(raw[header]!==0x51||operands.sub_op!==0x51||operands.x_encoded!==raw[header+1]||operands.z_encoded!==raw[header+2]||operands.depth_encoded!==before||operands.move_id!==raw[header+4]||((raw[header+1]&127)===127&&(raw[header+2]&127)===127))fail('NPC_RUN operands or parked target');
  }else if((raw[header+1]&0x7f)!==0)fail('CAM_CFG has unresolved halt-acquire behavior');
  if(target.decoded_byte_offset!==context.source.byte_offset+target.pc+relative||target.before_raw!==before||(before&15)>7||target.values.sector!==(before&15))fail('facing byte or low nibble');
}

export function decodeScriptFacing(report,owner){
  const context=sourceContext(report,owner),authoring=report.facing_authoring;
  if(!object(authoring)||typeof authoring.supported!=='boolean'||!(authoring.reason===null||text(authoring.reason))||!Array.isArray(authoring.targets)||authoring.targets.length>1024||!Array.isArray(authoring.unavailable)||authoring.unavailable.length>4096||!Array.isArray(authoring.unresolved_overrides)||authoring.unresolved_overrides.length>1024||authoring.supported!==(authoring.targets.length>0))fail('authoring collections');
  if(!Array.isArray(report.stops)||report.stops.length>4096||authoring.targets.length&&report.stops.length)fail('source paths contain unresolved stops');
  const seen=new Set();
  for(const target of authoring.targets){targetSource(target,context,owner);if(seen.has(target.semantic_id))fail('duplicate target');seen.add(target.semantic_id);}
  for(const row of authoring.unavailable)if(!object(row)||!integer(row.pc,0,65535)||!['NPC_RUN','CAM_CFG'].includes(row.mnemonic)||!text(row.reason))fail('unavailable instruction reason');
  for(const id of authoring.unresolved_overrides){if(typeof id!=='string'||!id.startsWith(context.script+'/facing/')||!/^\/[0-9a-f]{4}$/.test(id.slice((context.script+'/facing').length))||seen.has(id))fail('unresolved override identity');seen.add(id);}
  return structuredClone(authoring);
}

function element(tag,label){const node=document.createElement(tag);if(label!==undefined)node.textContent=label;return node;}

function compass(){
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 128 128');svg.setAttribute('role','img');svg.classList.add('facing-compass');
  const make=(tag,attributes,label)=>{const node=document.createElementNS(svg.namespaceURI,tag);for(const [key,value] of Object.entries(attributes))node.setAttribute(key,String(value));if(label!==undefined)node.textContent=label;return node;};
  const title=make('title',{},'Instruction operand preview'),circle=make('circle',{cx:64,cy:64,r:43,fill:'none',stroke:'currentColor','stroke-opacity':0.4});svg.append(title,circle);
  for(let sector=0;sector<8;sector++){const radians=sector*Math.PI/4;svg.append(make('text',{x:64+54*Math.sin(radians),y:68-54*Math.cos(radians),'text-anchor':'middle','font-size':12,fill:'currentColor'},String(sector)));}
  const arrow=make('g',{'data-facing-arrow':''});arrow.append(make('path',{d:'M 64 92 L 64 35 M 50 49 L 64 35 L 78 49',fill:'none',stroke:'currentColor','stroke-width':5,'stroke-linecap':'round','stroke-linejoin':'round'}));svg.append(arrow);
  return {svg,update(sector){const valid=integer(sector,0,7);arrow.setAttribute('visibility',valid?'visible':'hidden');if(valid)arrow.setAttribute('transform',`rotate(${sector*45} 64 64)`);const label=valid?'Instruction operand preview · '+describe(sector):'Instruction operand preview · enter an integer sector from 0 to 7';svg.setAttribute('aria-label',label);title.textContent=label;}};
}

export function mountScriptFacing(host,{report,owner,current,busy,setBusy,api,reopen,onError,drafts=new Map(),onDraftChange=()=>{}}){
  let authoring;
  try{if(!host||[current,busy,setBusy,api,reopen,onError,onDraftChange].some(callback=>typeof callback!=='function')||!(drafts instanceof Map))fail('editor guards');authoring=decodeScriptFacing(report,owner);}catch(error){if(typeof onError==='function')onError(error);return {updateState(){},dispose(){}};}
  const section=element('section');section.className='facing-authoring';section.dataset.scriptFacing='';
  const heading=element('h3','Script facing operands'),note=element('p','Edit the facing sector in a decoded instruction. Retail, Authored and Effective values remain separate. The preview shows this operand only; the executing branch, runtime actor and initial or current heading remain unknown. Gameplay remains unverified.');note.className='field-note';section.append(heading,note);
  if(authoring.reason)section.append(element('p',authoring.reason));
  for(const row of authoring.unavailable){const message=element('p',`${row.mnemonic} at ${hex(row.pc)}: ${row.reason}`);message.className='field-note';section.append(message);}
  const status=element('p');status.className='dialog-error';status.setAttribute('role','alert');section.append(status);
  let disposed=false,pending=false,generation=0;
  const controls=[],rows=[];
  const validContext=()=>!disposed&&current()===true;
  const editable=()=>validContext()&&!pending&&busy()===false;
  function updateState(){const canEdit=editable();for(const item of controls)item.disabled=!canEdit;for(const row of rows)row.update(canEdit);}
  async function send(id,type,values){
    if(!editable())return false;
    const ticket=++generation;pending=true;status.textContent='';updateState();
    try{
      const success=await api('/api/command',{type,entity_id:owner,facing_id:id,...(type==='set_facing_target'?{values}:{})});
      if(disposed||generation!==ticket||current()!==true)return false;
      if(success!==true){status.textContent='Facing edit was rejected. The draft remains available; inspect the current source before retrying.';return false;}
      drafts.delete(id);onDraftChange();pending=false;updateState();await reopen();return true;
    }catch(error){if(!disposed&&generation===ticket&&current()===true){status.textContent=error.message;onError(error);}return false;}
    finally{if(!disposed&&generation===ticket){pending=false;updateState();}}
  }
  for(const id of authoring.unresolved_overrides){const clear=element('button','Clear unresolved facing '+id);clear.type='button';clear.dataset.clearFacing=id;clear.onclick=()=>send(id,'clear_facing_target');section.append(clear);controls.push(clear);}
  for(const target of authoring.targets){
    const form=element('form');form.className='facing-entry';form.dataset.facingId=target.semantic_id;
    const title=element('h4',`${target.mnemonic} at ${hex(target.pc)}`),layers=element('table');layers.className='facing-layers';
    const layerHeading=element('tr');for(const label of ['Layer','Facing sector','12-bit angle','Degrees'])layerHeading.append(element('th',label));layers.append(layerHeading);
    for(const [label,value] of [['Retail',target.values.sector],['Authored',target.authored_values.sector],['Effective',target.effective_values.sector]]){const tr=element('tr');tr.append(element('th',label),element('td',value===undefined?'None · inherit':String(value)),element('td',value===undefined?'—':String(value*512)),element('td',value===undefined?'—':String(value*45)+'°'));layers.append(tr);}
    const preview=compass(),previewLabel=element('p','Instruction operand preview · sector 0 is at the top of this diagram.');previewLabel.className='field-note';
    const previewValue=element('p');previewValue.className='facing-preview-value';const label=element('label','Facing sector'),input=element('input');input.type='number';input.required=true;input.min='0';input.max='7';input.step='1';input.value=String(drafts.get(target.semantic_id)?.sector??target.effective_values.sector);input.setAttribute('aria-label','Facing sector at '+hex(target.pc));input.dataset.runInput=target.semantic_id;label.append(input);
    if(target.target_context!==null){const context=element('p','Encoded actor context '+target.target_context+' · runtime binding unresolved');context.className='field-note';form.append(context);}
    const apply=element('button','Apply facing'),clear=element('button','Clear facing override'),discard=element('button','Discard facing draft');apply.type='submit';clear.type=discard.type='button';
    const diagnostics=element('details'),summary=element('summary','Source operand details'),source=element('pre');source.className='diagnostic-detail';source.textContent=`Source byte ${target.decoded_byte_offset}: 0x${target.before_raw.toString(16).padStart(2,'0')}\nPreserve mask 0xf0: the high nibble is unchanged. Only sectors 0–7 in the low nibble are authored.\nSource record SHA-256: ${target.source_record_sha256}`;diagnostics.append(summary,source);
    form.append(title,layers,preview.svg,previewLabel,previewValue,label,apply,clear,discard,diagnostics);
    const value=()=>typeof input.value==='string'&&input.value.trim()!==''&&integer(Number(input.value),0,7)?Number(input.value):null;
    const row={update(canEdit){const sector=value();input.disabled=!canEdit;apply.disabled=!canEdit||sector===null;clear.disabled=!canEdit||!Object.hasOwn(target.authored_values,'sector');discard.disabled=!canEdit;discard.hidden=!drafts.has(target.semantic_id);preview.update(sector);previewValue.textContent=sector===null?'Enter an integer sector from 0 to 7.':describe(sector)+(drafts.has(target.semantic_id)?' · Unsaved draft':' · Effective operand');}};
    input.oninput=()=>{if(!editable())return;drafts.set(target.semantic_id,{sector:input.value});onDraftChange();updateState();};
    form.onsubmit=event=>{event.preventDefault();const sector=value();if(apply.disabled||sector===null||!editable())return false;return send(target.semantic_id,'set_facing_target',{sector});};
    clear.onclick=()=>{if(clear.disabled)return false;return send(target.semantic_id,'clear_facing_target');};
    discard.onclick=()=>{if(!editable())return false;drafts.delete(target.semantic_id);input.value=String(target.effective_values.sector);onDraftChange();updateState();return true;};
    section.append(form);rows.push(row);
  }
  host.append(section);updateState();
  return {updateState,dispose(){if(disposed)return;disposed=true;generation++;section.remove();}};
}
