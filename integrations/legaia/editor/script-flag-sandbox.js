// Temporary single-context simulation. No scheduler, runtime access or project writes.
import {analyzeScriptFlow} from './script-flow-overview.js';
const clone=structuredClone,limit=256,word=v=>Number.isSafeInteger(v)&&v>=0&&v<=0xffffffff;
const widths={local:16,global:32,context:32};
const mask=bank=>bank==='local'?65535:0xffffffff;
export function parseSandboxWords(inputs){
 if(!inputs||Object.keys(inputs).length!==3||!Object.keys(widths).every(k=>Object.hasOwn(inputs,k)))throw Error('Supply local, global and context hypothetical words.');
 return Object.fromEntries(Object.entries(widths).map(([bank,width])=>{
  const s=inputs[bank];if(typeof s!=='string')throw Error('Hypothetical words must be hexadecimal text or blank.');
  if(!s.trim())return [bank,null];const v=s.trim().replace(/^0x/i,'');
  if(!new RegExp('^[a-fA-F0-9]{1,'+(width/4)+'}$').test(v))throw Error(bank+' requires at most '+width/4+' hexadecimal digits; blank means unknown.');return [bank,parseInt(v,16)];
 }));
}
export function createScriptFlagSandbox(report){
 const flow=analyzeScriptFlow(report),nodes=new Map([...report.instructions,...(report.unvisited_instructions??[])].map(r=>[r.pc,clone(r)]));
 for(const row of [...report.dialogues,...(report.unvisited_dialogues??[])])nodes.set(row.pc,{...clone(row),mnemonic:'DIALOGUE_SEGMENT',target_context:null,successors:[]});
 let state=null,history=[],initial=null;
 function snapshot(){return clone({state,initial,history,limit,entry_pc:flow.entry_pc,entry_decoded:nodes.has(flow.entry_pc)});}
 function start(pc,inputs){
  if(!nodes.has(pc))throw Error('Choose a decoded instruction for sandbox entry.');
  if(!inputs||Object.keys(inputs).length!==3||!Object.keys(widths).every(k=>Object.hasOwn(inputs,k)))throw Error('Sandbox requires exactly three hypothetical flag banks.');
  const banks={};for(const bank of Object.keys(widths)){const v=inputs[bank];if(v!==null&&(!word(v)||v>mask(bank)))throw Error('Hypothetical '+bank+' word exceeds its known width.');banks[bank]={value:v??0,known:v===null?0:mask(bank)};}
  state={pc,banks,status:'ready',reason:null};initial={pc,inputs:clone(inputs)};history=[];return snapshot();
 }
 function step(){
  if(!state||state.status!=='ready')throw Error('Start or reset a ready sandbox before stepping.');
  if(history.length>=limit){state.status='step_limit';state.reason='Bounded sandbox step limit reached.';return snapshot();}
  const before=clone(state),row=nodes.get(state.pc);let next=null,effect=null,reason=null,status='ready';
  if(!row){status='undecoded';reason='No qualified decoded instruction at this boundary.';}
  else if(row.target_context!==null){status='unsupported';reason='Extended or missing dispatch context is unresolved.';}
  else {
   const m=/^(LFLAG|GFLAG|CFLAG)_(SET|CLEAR|TEST)$/.exec(row.mnemonic),a=row.operands;
   if(m){
    const bank={LFLAG:'local',GFLAG:'global',CFLAG:'context'}[m[1]],op=m[2],base={LFLAG:0x2b,GFLAG:0x2e,CFLAG:0x31}[m[1]],bit=a?.bit;
    if(row.opcode!==base+{SET:0,CLEAR:1,TEST:2}[op]||row.length!==2||!Number.isSafeInteger(a?.raw_operand)||a.raw_operand<0||a.raw_operand>255||bit!==(a.raw_operand&31)||row.successors.length!==1||row.successors[0].pc!==row.pc+2||row.successors[0].condition!=='encoded_continuation'||op==='TEST'&&a.can_wait_for_flag!==true){status='unsupported';reason='Flag instruction metadata is not qualified.';}
    else if(bank==='local'&&bit>=16){status='unsupported';reason='Local flag bits above 15 have unresolved bank-width semantics.';}
    else if(bank==='context'&&bit===8&&op==='SET'){status='unsupported';reason='Context flag bit 8 also copies an actor field; that side effect is not simulated.';}
    else if(bank==='context'&&bit===10&&op==='CLEAR'){status='unsupported';reason='Clearing context flag bit 10 changes halt lifecycle; scheduler resume is not simulated.';}
    else{
     const b=state.banks[bank],flag=(2**bit)>>>0;effect={bank,bit,operation:op.toLowerCase()};
     if(op==='TEST'){
      if((b.known&flag)===0){status='unknown_flag';reason='The tested hypothetical bit is unknown.';}
      else if((b.value&flag)===0){status='flag_wait';reason='Test waits at this PC while the hypothetical bit is clear; external resume is not simulated.';}
      else next=row.pc+2;
     }else{b.value=(op==='SET'?b.value|flag:b.value&~flag)>>>0;b.known=(b.known|flag)>>>0;next=row.pc+2;}
    }
   }else if(row.mnemonic==='FLAG_WORD_BRANCH'){
    const bank={actor_flags:'context',actor_local_flags:'local',global_story_word:'global'}[a?.flag_word],sub={actor_flags:0xa0,actor_local_flags:0xa1,global_story_word:0xa2}[a?.flag_word],raw=a?.bit_encoded,delta=a?.delta,target=Number.isSafeInteger(delta)?(row.pc+3+delta)&65535:null;
    if(!bank||row.opcode!==0x4c||row.length!==5||a.sub_op!==sub||!Number.isSafeInteger(raw)||raw<0||raw>255||!Number.isSafeInteger(delta)||delta< -32768||delta>32767||a.target!==target||row.successors.length!==2||row.successors[0].pc!==target||row.successors[0].condition!=='flag_bit_set'||row.successors[1].pc!==row.pc+5||row.successors[1].condition!=='flag_bit_clear'){status='unsupported';reason='Flag-word branch metadata is not qualified.';}
    else if(bank==='local'&&(raw&31)>=16){status='unsupported';reason='Local flag bits above 15 have unresolved bank-width semantics.';}
    else{
     const bit=raw&31,flag=(2**bit)>>>0,b=state.banks[bank],known=(b.known&flag)!==0,set=known?(b.value&flag)!==0:null;effect={bank,bit,operation:'branch_test',tested_value:set,successor_index:set===null?null:set?0:1};
     if(!known){status='unknown_flag';reason='Branch predicate depends on an unknown hypothetical bit; no successor is chosen.';}
     else next=row.successors[effect.successor_index].pc;
    }
   }else if(row.mnemonic==='NOP'&&[0x21,0x24,0x25,0x48].includes(row.opcode)&&row.length===1&&row.successors.length===1&&row.successors[0].pc===row.pc+1&&row.successors[0].condition==='encoded_continuation')next=row.pc+1;
   else if(row.mnemonic==='JMP_REL'&&row.opcode===0x26&&row.length===3&&Number.isSafeInteger(a?.delta)&&a.delta>=-32768&&a.delta<=32767&&row.successors.length===1&&row.successors[0].condition==='unconditional'&&row.successors[0].pc===((row.pc+1+a.delta)&65535))next=row.successors[0].pc;
   else{status='unsupported';reason='This instruction requires semantics or host effects outside the flag sandbox.';}
  }
  if(next!==null){state.pc=next;if(!nodes.has(next)){status='undecoded';reason='Continuation leaves the qualified instruction set; no effects are skipped.';}}
  state.status=status;state.reason=reason;history.push({before,after:clone(state),mnemonic:row?.mnemonic??null,effect});
  if(state.status==='ready'&&history.length===limit){state.status='step_limit';state.reason='Bounded sandbox step limit reached.';history.at(-1).after=clone(state);}
  return snapshot();
 }
 return {snapshot,start,step,has:pc=>nodes.has(pc),back(){if(history.length)state=history.pop().before;return snapshot();},reset(){state=null;initial=null;history=[];return snapshot();},run(){while(state?.status==='ready'&&history.length<limit)step();return snapshot();}};
}
export function mountScriptFlagSandbox(host,{report,selection,current,busy,selectInstruction,onError}){
 const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;},section=el('details'),tools=el('div'),status=el('p'),values=el('div'),inputs={};section.dataset.flagSandbox='';tools.className='script-walkthrough-tools';status.setAttribute('role','status');
 section.append(el('summary','Simulate hypothetical flag words'),el('p','Temporary single-context sandbox. Blank inputs mean unknown bits. It stops before unsupported instructions, unresolved contexts and host side effects. No runtime or project values change.'));
 for(const [bank,width] of Object.entries(widths)){const label=el('label',bank+' word (hex; '+width+' bits)'),input=el('input');input.type='text';input.maxLength=width/4+2;input.placeholder='Unknown';input.setAttribute('aria-label','Hypothetical '+bank+' flag word');inputs[bank]=input;label.append(input);section.append(label);}
 const start=el('button','Start flag sandbox at selection'),entry=el('button','Start flag sandbox at entry'),step=el('button','Simulate one instruction'),run=el('button','Simulate until boundary'),back=el('button','Back one simulated instruction'),reset=el('button','Reset flag sandbox');for(const b of [start,entry,step,run,back,reset])b.type='button';tools.append(start,entry,step,run,back,reset);section.append(tools,status,values);host.append(section);
 let engine=null,disposed=false;try{engine=createScriptFlagSandbox(report);}catch(error){status.textContent=error.message;}
 function update(){
  if(disposed)return;const fresh=current(),blocked=!fresh||busy();if(!fresh)engine?.reset();const s=engine?.snapshot();start.disabled=blocked||!engine?.has(selection());entry.disabled=blocked||!s?.entry_decoded;step.disabled=run.disabled=blocked||s?.state?.status!=='ready';back.disabled=blocked||!s?.history.length;reset.disabled=blocked||!s?.state;for(const input of Object.values(inputs))input.disabled=blocked;
  values.replaceChildren();if(!fresh){status.textContent='Source context changed; reopen inspection.';return;}if(!s)return;
  status.textContent=s.state?`${s.history.length} of ${limit} simulated instructions · 0x${s.state.pc.toString(16).toUpperCase().padStart(4,'0')} · ${s.state.status}${s.state.reason?' · '+s.state.reason:''}`:'Choose hypothetical words, then start at a decoded instruction.';
  const allDecisions=s.history.filter(r=>r.effect?.operation==='branch_test'),decisions=allDecisions.slice(-16);if(allDecisions.length>decisions.length)values.append(el('p',`Showing last ${decisions.length} of ${allDecisions.length} hypothetical branch decisions.`));for(const row of decisions){const e=row.effect;values.append(el('p',`Branch 0x${row.before.pc.toString(16).toUpperCase().padStart(4,'0')} · ${e.bank} bit ${e.bit} ${e.tested_value===null?'unknown; no choice':e.tested_value?'set':'clear'}${e.successor_index===null?'':` → 0x${row.after.pc.toString(16).toUpperCase().padStart(4,'0')}`}`));}
  if(s.state)for(const [bank,b] of Object.entries(s.state.banks))values.append(el('p',bank+' value 0x'+b.value.toString(16).toUpperCase().padStart(widths[bank]/4,'0')+' · known mask 0x'+b.known.toString(16).toUpperCase().padStart(widths[bank]/4,'0')));
 }
 function act(fn){if(disposed||!current()||busy()||!engine)return;try{const s=fn();update();if(s.state&&engine.has(s.state.pc))selectInstruction(s.state.pc,false);}catch(error){status.textContent=error.message;onError(error);}}
 const words=()=>parseSandboxWords(Object.fromEntries(Object.entries(inputs).map(([k,n])=>[k,n.value??''])));start.onclick=()=>act(()=>engine.start(selection(),words()));entry.onclick=()=>act(()=>engine.start(engine.snapshot().entry_pc,words()));step.onclick=()=>act(()=>engine.step());run.onclick=()=>act(()=>engine.run());back.onclick=()=>act(()=>engine.back());reset.onclick=()=>act(()=>engine.reset());update();
 return {update,dispose(){disposed=true;engine?.reset();section.remove();},get snapshot(){return engine?.snapshot()??null;}};
}
