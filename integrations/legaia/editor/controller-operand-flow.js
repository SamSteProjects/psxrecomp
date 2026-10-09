import {mountScriptFlowOverview} from './script-flow-overview.js';
import {mountScriptNodeLayers} from './script-node-layers.js';
import {mountScriptFlagSandbox} from './script-flag-sandbox.js';

// Already-qualified controller DTOs only; hypothetical simulation never executes runtime code or samples drafts.
export function mountControllerOperandFlow(host,{current,busy}){
 const el=(tag,text='')=>{const n=document.createElement(tag);n.textContent=text;return n;};
 const root=el('section');root.dataset.controllerOperandFlow='';root.style.overflowWrap='anywhere';
 const boundary=el('select'),note=el('p');boundary.setAttribute('aria-label','Controller operand flow boundary');boundary.style.maxWidth='100%';
 root.append(el('h4','Current and Reviewed Proposed Operand Flow'),el('p','Compare encoded instructions before Apply. Hypothetical simulations use explicit inputs; runtime scheduling and gameplay effects remain unverified.'),boundary,note);host.append(root);
 const layers=mountScriptNodeLayers(root),proposedHost=el('div');proposedHost.dataset.controllerOperandProposed='';
 const simulationTools=el('div');simulationTools.className='script-walkthrough-tools';const simulateCurrent=el('button','Simulate Current operands'),simulateProposed=el('button','Simulate reviewed Proposed operands'),simulationNote=el('p'),simulationHost=el('div');simulationHost.dataset.controllerOperandSandbox='';simulateCurrent.type=simulateProposed.type='button';simulationTools.append(simulateCurrent,simulateProposed);root.append(simulationTools,simulationNote,simulationHost);
 let snapshot=null,review=null,disposed=false,sandbox=null,held=null;
 const simulationOwns=()=>!disposed&&current()&&held?.snapshot===snapshot&&(held.kind==='current'||held.review===review);
 function clearSimulation(){sandbox?.dispose();sandbox=null;held=null;simulationHost.replaceChildren();simulationNote.textContent='Temporary simulation uses qualified Current or reviewed Proposed bytes. Local drafts and live state are excluded. Scenario save/replay is unavailable for these operand layers.';}
 function openSimulation(kind){if(disposed||!current()||busy()||!snapshot||kind==='proposed'&&!review)return false;if(held?.kind===kind&&simulationOwns()){sandbox.update();return true;}clearSimulation();const report=kind==='current'?snapshot.current_report:review.proposed_report;held={kind,snapshot,review:kind==='proposed'?review:null};simulationNote.textContent=(kind==='current'?'Current':'Reviewed Proposed')+' encoded operands with explicit hypothetical inputs. No runtime state, project writes or scenario save/replay.';sandbox=mountScriptFlagSandbox(simulationHost,{report,selection:()=>Number(boundary.value),current:simulationOwns,busy,selectInstruction:choose,onError:error=>{simulationNote.textContent=error.message;}});const panel=simulationHost.querySelector?.('[data-flag-sandbox]');panel?.setAttribute('open','');const heading=panel?.querySelector('summary');if(heading)heading.textContent=kind==='current'?'Simulate Current Controller Operands':'Simulate Reviewed Proposed Controller Operands';return true;}
 simulateCurrent.onclick=()=>openSimulation('current');simulateProposed.onclick=()=>openSimulation('proposed');
 const choose=pc=>{if(disposed||!current()||busy()||!snapshot?.source_report.instructions.concat(snapshot.source_report.dialogues).some(n=>n.pc===pc))return false;boundary.value=String(pc);return draw();};
 const currentFlow=mountScriptFlowOverview(root,{title:'Current Operand Flow Overview',label:'Current controller encoded flow',selectInstruction:choose});root.append(proposedHost);
 const proposedFlow=mountScriptFlowOverview(proposedHost,{title:'Reviewed Proposed Operand Flow Overview',label:'Reviewed Proposed controller encoded flow',selectInstruction:choose});
 const display=r=>r===null?null:{...r,instructions:[...r.instructions,...(r.unvisited_instructions??[])],dialogues:[...r.dialogues,...(r.unvisited_dialogues??[])]};
 function clear(){clearSimulation();snapshot=review=null;root.hidden=true;layers.clear('Operand flow source unavailable.');}
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
 function updateState(){const blocked=disposed||!current()||busy()||!snapshot;boundary.disabled=simulateCurrent.disabled=blocked;simulateProposed.disabled=blocked||!review;if(!current())clear();else if(held&&!simulationOwns())clearSimulation();else sandbox?.update();}
 boundary.onchange=()=>{if(!boundary.disabled)draw();};
 clear();return{sync(source,proposal,pc){if(disposed)return false;snapshot=source;review=proposal;if(!source){clear();return false;}boundary.replaceChildren();const rows=[...source.source_report.instructions,...source.source_report.dialogues].sort((a,b)=>a.pc-b.pc);for(const row of rows){const option=el('option',`0x${row.pc.toString(16).toUpperCase().padStart(4,'0')} · ${row.mnemonic??'Dialogue'}`);option.value=String(row.pc);boundary.append(option);}boundary.value=String(rows.some(r=>r.pc===pc)?pc:rows[0]?.pc??'');if(!rows.length){clear();return false;}return draw();},updateState,dispose(){if(disposed)return;disposed=true;clearSimulation();layers.dispose();currentFlow.dispose();proposedFlow.dispose();root.remove();}};
}
