// Source operands retain their dispatch context; no live flag identity is inferred.
const scopes={local:'dispatch_context_local_flags',context:'dispatch_context_flags',global:'host_global_flags',system:'system_bank_encoded_selector',extra:'host_extra_flags'};
const integer=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
const keys=['pc','byte_offset','mnemonic','bank','operation','index','scope','extended_target','context_resolution','index_semantics','status','runtime_value'];
export function decodeControllerFlags(report){
 const rows=report.flag_references,source=report.source_record;
 if(!Array.isArray(rows)||rows.length>4096||report.flag_reference_count!==rows.length)throw Error('Invalid controller flag reference coverage.');
 const expected=report.instructions.filter(row=>/^(LFLAG|GFLAG|CFLAG|SYSFLAG)_(SET|CLEAR|TEST)$/.test(row.mnemonic)||row.mnemonic==='FLAG_WORD_BRANCH'||row.mnemonic==='COND_JMP'&&row.operands?.mode===0);
 if(rows.length!==expected.length)throw Error('Controller flag references omit decoded operands.');
 const sites=new Set(),instructions=new Map(report.instructions.map(row=>[row.pc,row]));
 for(const row of rows){
  const instruction=instructions.get(row.pc);
  if(row===null||typeof row!=='object'||Array.isArray(row)||Object.keys(row).length!==keys.length||!keys.every(k=>Object.hasOwn(row,k))||!Object.hasOwn(scopes,row.bank)||row.scope!==scopes[row.bank]||!['set','clear','test'].includes(row.operation)||!integer(row.pc,report.entry_pc,source.byte_length-1)||row.byte_offset!==source.byte_offset+row.pc||!integer(row.index,0,row.bank==='system'?65535:31)||row.runtime_value!==null||!(row.extended_target===null||integer(row.extended_target,0,255))||row.context_resolution!==(row.extended_target===null?'current_script_context':'extended_target_unresolved')||row.index_semantics!==(row.bank==='system'?'encoded_selector_not_resolved_runtime_bit':'operand_masked_to_five_bits')||row.status!==(row.bank==='local'&&row.index>=16?'bank_width_unresolved':'encoded_reference')||sites.has(row.pc)||instruction?.mnemonic!==row.mnemonic||instruction?.target_context!==row.extended_target)throw Error('Invalid source-qualified controller flag operand.');
  const prefix={local:'LFLAG',context:'CFLAG',global:'GFLAG',system:'SYSFLAG'}[row.bank],args=instruction.operands;
  const direct=prefix&&row.mnemonic===prefix+'_'+row.operation.toUpperCase()&&(row.bank==='system'?args?.index:args?.bit)===row.index;
  const word=row.mnemonic==='FLAG_WORD_BRANCH'&&row.operation==='test'&&({actor_flags:'context',actor_local_flags:'local',global_story_word:'global'})[args?.flag_word]===row.bank&&integer(args?.bit_encoded,0,255)&&(args.bit_encoded&31)===row.index;
  const extra=row.mnemonic==='COND_JMP'&&row.bank==='extra'&&row.operation==='test'&&args?.mode===0&&integer(args?.test,0,255)&&(args.test&31)===row.index;
  if(!direct&&!word&&!extra)throw Error('Controller flag reference differs from its decoded instruction.');
  sites.add(row.pc);
 }
 return structuredClone(rows);
}

export function renderControllerFlags(host,report,focusPc=null){
 const rows=decodeControllerFlags(report),section=document.createElement('section'),heading=document.createElement('h3'),note=document.createElement('p'),filter=document.createElement('select'),body=document.createElement('div');
 heading.textContent='Encoded Flag References';note.textContent=`${rows.length} decoded source operands · Current values and runtime bindings remain unresolved. Only inspected paths contribute references.`;filter.setAttribute('aria-label','Controller flag bank');filter.style.maxWidth='100%';
 for(const bank of ['all',...Object.keys(scopes)]){const option=document.createElement('option');option.value=bank;option.textContent=bank==='all'?'All encoded flag banks':bank[0].toUpperCase()+bank.slice(1)+' bank';filter.append(option);}
 const count=document.createElement('p');count.setAttribute('role','status');section.append(heading,note,filter,count,body);
 const render=()=>{body.replaceChildren();const selected=rows.filter(row=>filter.value==='all'||row.bank===filter.value);count.textContent=`Showing ${selected.length} of ${rows.length} decoded flag references`;
  for(const row of selected){const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');details.dataset.controllerFlagPc=row.pc;summary.textContent=`PC 0x${row.pc.toString(16).padStart(4,'0')} · ${row.bank} ${row.index} · ${row.operation} · ${row.extended_target===null?'controller dispatch context':'extended target '+row.extended_target+' unresolved'}`;pre.style.whiteSpace='pre-wrap';pre.textContent=JSON.stringify(row,null,2);details.append(summary,pre);body.append(details);}
 };filter.onchange=render;const selected=rows.find(row=>row.pc===focusPc);if(selected)filter.value=selected.bank;render();host.append(section);const focused=selected?body.querySelector(`[data-controller-flag-pc="${focusPc}"]`):null;if(focused)focused.open=true;return focused;
}
