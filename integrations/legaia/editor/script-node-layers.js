// Selected encoded boundaries only. No script execution or draft operand simulation.
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const pcText=value=>'0x'+value.toString(16).toUpperCase().padStart(4,'0');
const canonical=value=>Array.isArray(value)?value.map(canonical):object(value)?Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])])):value;
const text=value=>value===undefined?'Absent':JSON.stringify(canonical(value));
const fail=message=>{throw new Error(message);};

function selected(report,pc){
  if(report===null)return{status:'inspection_unavailable',node:null};
  if(!object(report)||!['partial','decoded_supported_paths'].includes(report.status)||!['instructions','dialogues','stops','opaque_regions'].every(key=>Array.isArray(report[key])&&report[key].length<=8192))fail('Selected script inspection exceeds its supported bounds.');
  const instructions=report.instructions.filter(row=>row.pc===pc),dialogues=report.dialogues.filter(row=>row.pc===pc),rows=[...instructions,...dialogues];
  if(rows.length>1)fail('Selected script boundary is ambiguous.');
  if(!rows.length)return{status:'boundary_not_decoded',node:null};
  const row=rows[0],kind=instructions.length?'instruction':'dialogue';
  if(!object(row)||!integer(row.pc,0,65535)||!integer(row.length,1,65536-row.pc)||typeof row.raw_hex!=='string'||row.raw_hex.length!==row.length*2||!/^[0-9a-f]+$/.test(row.raw_hex))fail('Selected script bytes differ from the decoded boundary.');
  const node={kind,pc:row.pc,length:row.length,raw_hex:row.raw_hex};
  if(kind==='instruction'){
    if(typeof row.mnemonic!=='string'||row.mnemonic.length<1||row.mnemonic.length>128||!object(row.operands)||Object.keys(row.operands).length>128||JSON.stringify(row.operands).length>131072||!Array.isArray(row.successors)||row.successors.length>64||!(row.target_context===null||integer(row.target_context,0,255)))fail('Selected instruction operands or dispatch context are invalid.');
    for(const edge of row.successors)if(!object(edge)||!integer(edge.pc,0,65536)||!(edge.condition===null||typeof edge.condition==='string'&&edge.condition.length<=256))fail('Selected instruction has an invalid encoded successor.');
    Object.assign(node,{mnemonic:row.mnemonic,target_context:row.target_context,operands:structuredClone(row.operands),successors:structuredClone(row.successors)});
  }else{
    if(typeof row.text!=='string'||row.text.length>65536)fail('Selected message exceeds its bounded decoded text.');
    Object.assign(node,{mnemonic:'MES_SEGMENT',target_context:null,operands:{text:row.text},successors:[{pc:pc+row.length,condition:'encoded_continuation'}]});
  }
  return{status:'decoded',node};
}

export function scriptNodeLayers(source,current,proposed,pc){
  if(!integer(pc,0,65535))fail('Choose a bounded script record PC.');
  const layers={retail:selected(source,pc),current:selected(current,pc),proposed:selected(proposed,pc)},original=layers.retail.node;
  if(!original)fail('Choose an original decoded instruction or message boundary.');
  for(const key of ['current','proposed']){const n=layers[key].node;if(n&&['kind','pc','length','mnemonic','target_context'].some(field=>n[field]!==original[field]))fail('Selected authored path changed its original source boundary.');}
  const difference=(left,right)=>{
    if(!left||!right)return null;
    const result=[];for(let i=0;i<left.length;i++){const a=left.raw_hex.slice(i*2,i*2+2),b=right.raw_hex.slice(i*2,i*2+2);if(a!==b)result.push({pc:pc+i,before:a,after:b});}return result;
  };
  const fields=['Instruction','Dispatch context','Encoded length',...new Set(Object.values(layers).flatMap(layer=>Object.keys(layer.node?.operands??{})).sort()),'Encoded successors'];
  const value=(node,field)=>!node?undefined:field==='Instruction'?node.mnemonic:field==='Dispatch context'?node.target_context:field==='Encoded length'?node.length:field==='Encoded successors'?node.successors:node.operands[field];
  return {pc,mnemonic:original.mnemonic,layers,rows:fields.map(field=>({field,...Object.fromEntries(Object.entries(layers).map(([key,layer])=>[key,layer.node?text(value(layer.node,field)):layer.status==='inspection_unavailable'?(key==='proposed'?'Not reviewed':'Inspection unavailable'):'Boundary not decoded']))})),retail_to_current:difference(original,layers.current.node),current_to_proposed:difference(layers.current.node,layers.proposed.node)};
}

export function mountScriptNodeLayers(host){
  const root=document.createElement('section');root.className='script-node-layers';root.dataset.scriptNodeLayers='';host.append(root);
  function clear(reason='Choose a decoded source boundary to inspect its operand layers.'){root.replaceChildren();const status=document.createElement('p');status.className='field-note';status.setAttribute('role','status');status.textContent=reason;root.append(status);}
  function update(source,current,proposed,pc){
    if(pc===null){clear();return;}
    let report;try{report=scriptNodeLayers(source,current,proposed,pc);}catch(error){clear(`Selected operand layers unavailable: ${error.message}`);return false;}root.replaceChildren();
    const title=document.createElement('h4');title.textContent=`Selected ${pcText(pc)} · ${report.mnemonic}`;
    const note=document.createElement('p');note.className='field-note';note.textContent='Retail is the imported boundary. Current composes applied project operands and branches. Proposed contains the selected reviewed change; other pending form drafts are not included. An undecoded boundary does not mean its retained bytes were removed or that the instruction cannot execute.';
    const wrap=document.createElement('div');wrap.className='script-table-wrap';const table=document.createElement('table'),head=document.createElement('thead'),header=document.createElement('tr');
    for(const label of ['Field','Retail','Current','Reviewed Proposed']){const th=document.createElement('th');th.textContent=label;header.append(th);}head.append(header);
    const body=document.createElement('tbody');for(const row of report.rows){const tr=document.createElement('tr');tr.dataset.operandField=row.field;for(const key of ['field','retail','current','proposed']){const td=document.createElement('td');td.textContent=row[key];td.style.whiteSpace='pre-wrap';td.style.overflowWrap='anywhere';tr.append(td);}body.append(tr);}table.append(head,body);wrap.append(table);
    const delta=document.createElement('p');delta.className='field-note';delta.dataset.nodeByteDifferences='';delta.textContent=`Retail → Current: ${report.retail_to_current===null?'not comparable on decoded paths':report.retail_to_current.length+' changed bytes'}. Current → reviewed Proposed: ${report.current_to_proposed===null?'not comparable or not reviewed':report.current_to_proposed.length+' changed bytes'}. These are static encoded differences, not runtime observations.`;
    const raw=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Selected encoded bytes and differences';raw.append(summary);
    for(const [key,label] of [['retail','Retail'],['current','Current'],['proposed','Reviewed Proposed']]){const line=document.createElement('p');line.textContent=label;const pre=document.createElement('pre');pre.className='diagnostic-detail';pre.textContent=report.layers[key].node?.raw_hex??(key==='proposed'&&report.layers[key].status==='inspection_unavailable'?'Not reviewed':report.layers[key].status);pre.style.overflowWrap='anywhere';raw.append(line,pre);}
    const differences=document.createElement('pre');differences.className='diagnostic-detail';differences.textContent=JSON.stringify({retail_to_current:report.retail_to_current,current_to_proposed:report.current_to_proposed},null,2);raw.append(differences);
    root.append(title,note,wrap,delta,raw);
  }
  clear();return{clear,update,dispose(){root.remove();}};
}
