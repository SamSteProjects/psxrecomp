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
export function parseSandboxSignedTicks(text,{unknown=false}={}){
 if(typeof text!=='string')throw Error('Simulated ticks require signed decimal text.');const v=text.trim();if(unknown&&!v)return null;
 if(!/^-?(0|[1-9][0-9]{0,4})$/.test(v)||Number(v)< -32768||Number(v)>32767)throw Error('Simulated ticks require an integer from -32768 to 32767.');return Number(v);
}
export function createScriptFlagSandbox(report){
 const flow=analyzeScriptFlow(report),nodes=new Map([...report.instructions,...(report.unvisited_instructions??[])].map(r=>[r.pc,clone(r)]));
 for(const row of [...report.dialogues,...(report.unvisited_dialogues??[])])nodes.set(row.pc,{...clone(row),mnemonic:'DIALOGUE_SEGMENT',target_context:null,successors:[]});
 let state=null,history=[],initial=null;
 function snapshot(){return clone({state,initial,history,limit,entry_pc:flow.entry_pc,entry_decoded:nodes.has(flow.entry_pc)});}
 function start(pc,inputs,{waitAccumulator=null}={}){
  if(!nodes.has(pc))throw Error('Choose a decoded instruction for sandbox entry.');
  if(!inputs||Object.keys(inputs).length!==3||!Object.keys(widths).every(k=>Object.hasOwn(inputs,k)))throw Error('Sandbox requires exactly three hypothetical flag banks.');
  const banks={};for(const bank of Object.keys(widths)){const v=inputs[bank];if(v!==null&&(!word(v)||v>mask(bank)))throw Error('Hypothetical '+bank+' word exceeds its known width.');banks[bank]={value:v??0,known:v===null?0:mask(bank)};}
  if(waitAccumulator!==null&&(!Number.isSafeInteger(waitAccumulator)||waitAccumulator< -32768||waitAccumulator>32767))throw Error('Initial wait accumulator must be signed16 or unknown.');
  state={pc,banks,wait_accumulator:waitAccumulator,status:'ready',reason:null};initial={pc,inputs:clone(inputs),wait_accumulator:waitAccumulator};history=[];return snapshot();
 }
 function step(frameDelta=null,ticking=false){
  if(!state||!(state.status==='ready'||ticking&&state.status==='waiting_ticks'))throw Error('Start or reset a ready sandbox before stepping.');
  if(ticking&&(!Number.isSafeInteger(frameDelta)||frameDelta< -32768||frameDelta>32767))throw Error('A simulated tick delta must be signed16.');
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
      else if((b.value&flag)===0){status='flag_wait';reason='Test waits at this PC while the hypothetical bit is clear; supply an explicit hypothetical bit assumption to re-evaluate it.';}
      else next=row.pc+2;
     }else{b.value=(op==='SET'?b.value|flag:b.value&~flag)>>>0;b.known=(b.known|flag)>>>0;next=row.pc+2;}
    }
   }else if(row.mnemonic==='WAIT_FRAMES'){
    const target=a?.duration_ticks;
    if(row.opcode!==0x4a||row.length!==3||!Number.isSafeInteger(target)||target<0||target>32767||a.timing_units!=='host_frame_delta_ticks'||a.accumulator_width!=='signed16'||row.successors.length!==1||row.successors[0].pc!==row.pc+3||row.successors[0].condition!=='encoded_continuation'){status='unsupported';reason='Wait instruction metadata or target exceeds qualified signed16 timing semantics.';}
    else if(state.wait_accumulator===null){status='unknown_wait';reason='Initial wait accumulator is unknown. Restart with an explicit hypothetical accumulator.';}
    else if(frameDelta===null){status='waiting_ticks';reason='Frame wait staged. Supply one explicit hypothetical tick delta; no time advances automatically.';effect={operation:'wait_ticks',duration_ticks:target,delta_ticks:null,accumulator_before:state.wait_accumulator,accumulator_after:state.wait_accumulator,completed:null};}
    else{
     const prior=state.wait_accumulator,accum=Math.max(-32768,Math.min(32767,prior+frameDelta)),complete=accum>=target;effect={operation:'wait_ticks',duration_ticks:target,delta_ticks:frameDelta,accumulator_before:prior,accumulated_ticks:accum,accumulator_after:complete?0:accum,completed:complete};state.wait_accumulator=effect.accumulator_after;
     if(complete)next=row.pc+3;else{status='waiting_ticks';reason='Hypothetical accumulator is below the wait target. Supply another explicit tick to resume.';}
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
  if(['ready','waiting_ticks'].includes(state.status)&&history.length===limit){state.status='step_limit';state.reason='Bounded sandbox step limit reached.';history.at(-1).after=clone(state);}
  return snapshot();
 }
 function assumeFlag(bank,bit,value){
  if(!state||!['ready','flag_wait','unknown_flag'].includes(state.status))throw Error('Only ready or flag-blocked sandboxes accept hypothetical bit assumptions.');
  if(!Object.hasOwn(widths,bank)||!Number.isSafeInteger(bit)||bit<0||bit>=widths[bank]||![true,false,null].includes(value))throw Error('Supply a known bank, an in-range bit and set, clear or unknown assumption.');
  if(history.length>=limit)throw Error('Bounded sandbox step limit reached.');
  const before=clone(state),b=state.banks[bank],flag=(2**bit)>>>0;
  b.value=(value===true?b.value|flag:b.value&~flag)>>>0;b.known=(value===null?b.known&~flag:b.known|flag)>>>0;
  state.status='ready';state.reason=null;
  if(history.length+1===limit){state.status='step_limit';state.reason='Bounded sandbox step limit reached.';}
  history.push({before,after:clone(state),mnemonic:null,effect:{operation:'assume_flag',bank,bit,value}});return snapshot();
 }
 return {snapshot,start,assumeFlag,step:()=>step(),tick(delta){if(state?.status!=='waiting_ticks')throw Error('Only a staged frame wait can consume a hypothetical tick.');return step(delta,true);},has:pc=>nodes.has(pc),back(){if(history.length)state=history.pop().before;return snapshot();},reset(){state=null;initial=null;history=[];return snapshot();},run(){while(state?.status==='ready'&&history.length<limit)step();return snapshot();}};
}
