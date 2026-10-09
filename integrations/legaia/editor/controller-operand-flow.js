import {mountScriptFlowOverview} from './script-flow-overview.js';
import {mountScriptNodeLayers} from './script-node-layers.js';

// Already-qualified controller DTOs only; no execution, draft sampling or writes.
export function mountControllerOperandFlow(host,{current,busy}){
 const el=(tag,text='')=>{const n=document.createElement(tag);n.textContent=text;return n;};
 const root=el('section');root.dataset.controllerOperandFlow='';root.style.overflowWrap='anywhere';
 const boundary=el('select'),note=el('p');boundary.setAttribute('aria-label','Controller operand flow boundary');boundary.style.maxWidth='100%';
 root.append(el('h4','Current and Reviewed Proposed Operand Flow'),el('p','Compare encoded instructions before Apply. Conditions, runtime scheduling and gameplay effects are not evaluated.'),boundary,note);host.append(root);
 const layers=mountScriptNodeLayers(root),proposedHost=el('div');proposedHost.dataset.controllerOperandProposed='';
 let snapshot=null,review=null,disposed=false;
 const choose=pc=>{if(disposed||!current()||busy()||!snapshot?.source_report.instructions.concat(snapshot.source_report.dialogues).some(n=>n.pc===pc))return false;boundary.value=String(pc);return draw();};
 const currentFlow=mountScriptFlowOverview(root,{title:'Current Operand Flow Overview',label:'Current controller encoded flow',selectInstruction:choose});root.append(proposedHost);
 const proposedFlow=mountScriptFlowOverview(proposedHost,{title:'Reviewed Proposed Operand Flow Overview',label:'Reviewed Proposed controller encoded flow',selectInstruction:choose});
 const display=r=>r===null?null:{...r,instructions:[...r.instructions,...(r.unvisited_instructions??[])],dialogues:[...r.dialogues,...(r.unvisited_dialogues??[])]};
 function clear(){snapshot=review=null;root.hidden=true;layers.clear('Operand flow source unavailable.');}
 function draw(){
  if(disposed||!current()||!snapshot){clear();return false;}
  root.hidden=false;const pc=Number(boundary.value),proposed=review?.proposed_report??null;
  const retained=r=>(r?.unvisited_instructions??[]).concat(r?.unvisited_dialogues??[]).some(n=>n.pc===pc);
  note.textContent=`Current: ${retained(snapshot.current_report)?'retained boundary, unvisited from encoded entry':'decoded source path'} · Proposed: ${proposed?(retained(proposed)?'retained boundary, unvisited from encoded entry':'decoded source path'):'Not reviewed'}. Execution remains unknown.`;
  const qualified=layers.update(snapshot.source_report,display(snapshot.current_report),display(proposed),pc)!==false&&currentFlow.update(snapshot.current_report);
  proposedHost.hidden=!review;
  if(!qualified||review&&!proposedFlow.update(proposed)){clear();throw Error('Controller operand flow reports could not be qualified.');}
  updateState();return true;
 }
 function updateState(){boundary.disabled=disposed||!current()||busy()||!snapshot;if(!current())clear();}
 boundary.onchange=()=>{if(!boundary.disabled)draw();};
 clear();return{sync(source,proposal,pc){if(disposed)return false;snapshot=source;review=proposal;if(!source){clear();return false;}boundary.replaceChildren();const rows=[...source.source_report.instructions,...source.source_report.dialogues].sort((a,b)=>a.pc-b.pc);for(const row of rows){const option=el('option',`0x${row.pc.toString(16).toUpperCase().padStart(4,'0')} · ${row.mnemonic??'Dialogue'}`);option.value=String(row.pc);boundary.append(option);}boundary.value=String(rows.some(r=>r.pc===pc)?pc:rows[0]?.pc??'');if(!rows.length){clear();return false;}return draw();},updateState,dispose(){if(disposed)return;disposed=true;layers.dispose();currentFlow.dispose();proposedFlow.dispose();root.remove();}};
}
