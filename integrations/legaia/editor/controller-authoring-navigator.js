// Navigation consumes qualified control targets; it never interprets native operands.
export function controllerAuthoringTargets(rows,controls){
 if(!Array.isArray(rows)||rows.length>4096||!Array.isArray(controls)||controls.length>32)throw Error('Controller navigator bounds changed.');
 const seen=new Set();
 for(const row of rows){if(!Number.isSafeInteger(row.pc)||row.pc<0||row.pc>65535||seen.has(row.pc)||typeof row.mnemonic!=='string')throw Error('Controller navigator boundary changed.');seen.add(row.pc);}
 const kinds=new Set();
 return controls.map(control=>{
  if(typeof control.kind!=='string'||!control.kind||kinds.has(control.kind)||typeof control.label!=='string'||typeof control.canFocus!=='function'||typeof control.focusPc!=='function')throw Error('Controller navigator control changed.');kinds.add(control.kind);
  return {control,rows:rows.filter(row=>control.canFocus(row.pc)).map(row=>({pc:row.pc,mnemonic:row.mnemonic}))};
 }).filter(group=>group.rows.length);
}
export function mountControllerAuthoringNavigator(host,{rows,controls,current,busy,selectSource}){
 const groups=controllerAuthoringTargets(rows,controls),create=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
 const section=create('section'),heading=create('h3','Controller Editing Navigator'),family=create('select'),target=create('select'),open=create('button','Open Selected Controls'),status=create('p');
 section.dataset.controllerAuthoringNavigator='';family.setAttribute('aria-label','Controller Editing Family');target.setAttribute('aria-label','Controller Editing Target');status.setAttribute('role','status');open.type='button';
 section.style.cssText='border:1px solid #45605e;padding:12px;margin-bottom:12px';
 const bar=create('div');bar.style.cssText='display:flex;flex-wrap:wrap;gap:8px';family.style.maxWidth=target.style.maxWidth='100%';
 for(const group of groups){const option=create('option',`${group.control.label} (${group.rows.length})`);option.value=group.control.kind;family.append(option);}
 const group=()=>groups.find(g=>g.control.kind===family.value),selection=()=>group()?.rows.find(row=>String(row.pc)===target.value);
 const valid=()=>current()&&!busy(),updateState=()=>{const row=selection();family.disabled=!valid()||!groups.length;target.disabled=!valid()||!row;open.disabled=!valid()||!row||!group().control.canFocus(row.pc);};
 const render=()=>{target.replaceChildren();for(const row of group()?.rows??[]){const option=create('option',`0x${row.pc.toString(16).toUpperCase().padStart(4,'0')} · ${row.mnemonic.replaceAll('_',' ')}`);option.value=String(row.pc);target.append(option);}updateState();};
 family.onchange=()=>{if(valid())render();};target.onchange=updateState;
 open.onclick=()=>{const row=selection(),g=group();if(!valid()||!row||!g.control.canFocus(row.pc))return;if(selectSource(row.pc,false)&&g.control.focusPc(row.pc))status.textContent=`Opened ${g.control.label} at PC 0x${row.pc.toString(16).toUpperCase().padStart(4,'0')}. Review before Apply.`;};
 status.textContent=groups.length?'Choose a supported family and encoded target. Navigation does not change project data.':'No source-qualified editing targets in this controller.';
 bar.append(family,target,open);section.append(heading,bar,status);host.prepend(section);render();return {updateState};
}
