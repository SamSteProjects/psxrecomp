import {qualifyWorldScriptGraph} from './world-script-graph.js';
const fail=message=>{throw Error(message);};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const families={JMP_REL:[0,'unconditional'],COND_JMP:[2,'test_passed'],BBOX_TEST:[4,'outside_box'],SYSFLAG_TEST:[1,'flag_set'],FLAG_WORD_BRANCH:[2,'flag_bit_set'],FIELD_68_BRANCH:[1,'field_68_zero'],ACTOR_SEARCH_BRANCH:[3,'search_match'],ACTOR_RECT_BRANCH:[5,'dispatch_position_outside_rect'],ACTOR_LOOKUP_BRANCH:[2,'actor_lookup_missing'],VALUE_COMPARE_BRANCH:[4,'comparison_true']};
function layout(node,data){
 const spec=families[node.mnemonic];if(!spec)fail('Unsupported World branch byte family.');
 const op=data[node.pc]&127,header=node.target_context===null?1:2,sub=data[node.pc+header];
 const valid=node.mnemonic==='JMP_REL'?op===0x26:node.mnemonic==='COND_JMP'?op===0x42:node.mnemonic==='BBOX_TEST'?op===0x4d:node.mnemonic==='SYSFLAG_TEST'?header===1&&op>=0x70&&op<=0x7f:node.mnemonic==='VALUE_COMPARE_BRANCH'?op===0x4e&&(data[node.pc+header+1]>>4)<12&&(data[node.pc+header+1]&15)<=1:op===0x4c&&(node.mnemonic==='FLAG_WORD_BRANCH'?[0xa0,0xa1,0xa2].includes(sub):sub===({FIELD_68_BRANCH:0x8c,ACTOR_SEARCH_BRANCH:0x8d,ACTOR_RECT_BRANCH:0xe4,ACTOR_LOOKUP_BRANCH:0xeb})[node.mnemonic]);
 const at=node.pc+header+spec[0];if(!valid||at+2>node.pc+node.length)fail('World branch operation or owned word differs from source bytes.');
 return {at,condition:spec[1],target:(at+data[at]+256*data[at+1])&65535};
}
export function worldBranchTarget(node,data){
 if(!families[node.mnemonic]||node.mnemonic==='SYSFLAG_TEST'&&node.target_context!==null)return null;
 const decoded=layout(node,data);return {pc:node.pc,mnemonic:node.mnemonic,target_context:node.target_context,operand_pc:decoded.at,width:2,condition:decoded.condition,encoding:['FLAG_WORD_BRANCH','FIELD_68_BRANCH','ACTOR_SEARCH_BRANCH'].includes(node.mnemonic)?'relative_i16_wrap16':'relative_u16_wrap16',target_pc:decoded.target};
}
export function applyQualifiedWorldBranchBytes(source,retail,fixed){
 qualifyWorldScriptGraph(source.branch_source_graph,retail,source);
 if(source.branch_source_graph.stops.length)fail('World branch source has decoder stops.');
 const destinations=source.branch_source_graph.instructions.map(r=>({pc:r.pc,mnemonic:r.mnemonic})).concat(source.branch_source_graph.dialogues.map(r=>({pc:r.pc,mnemonic:'MES_SEGMENT'}))).filter(r=>r.pc>=source.entry_pc&&r.pc<=32767).sort((a,b)=>a.pc-b.pc);
 if(!same(destinations,source.branch_destinations)||!Array.isArray(source.branch_changes)||!source.branch_changes.length||source.branch_changes.length>1024)fail('World branch destinations or edit budget differ from source ownership.');
 const allowed=new Set(destinations.map(r=>r.pc)),result=fixed.slice(),used=new Set();
 for(const edit of source.branch_changes){
  if(!exact(edit,['pc','mnemonic','target_context','operand_pc','condition','retail_target_pc','authored_target_pc']))fail('World branch byte witness has invalid fields.');
  const node=source.branch_source_graph.instructions.find(r=>r.pc===edit.pc);if(!node||node.mnemonic!==edit.mnemonic||node.target_context!==edit.target_context)fail('World branch differs from its original source anchor.');
  const decoded=layout(node,retail),edge=node.successors.filter(e=>e.condition===decoded.condition);
  if(edit.operand_pc!==decoded.at||edit.condition!==decoded.condition||edit.retail_target_pc!==decoded.target||edge.length!==1||edge[0].pc!==decoded.target||!allowed.has(decoded.target)||!Number.isSafeInteger(edit.authored_target_pc)||!allowed.has(edit.authored_target_pc)||edit.authored_target_pc===decoded.target)fail('World branch target or word ownership differs from source bytes.');
  const at=decoded.at;if(used.has(at)||used.has(at+1)||fixed[at]!==retail[at]||fixed[at+1]!==retail[at+1])fail('World branch overlaps fixed arguments or another branch.');used.add(at);used.add(at+1);
  const word=(edit.authored_target_pc-at)&65535;result[at]=word&255;result[at+1]=word>>8;
 }
 return result;
}

export function updateWorldBranchGraph(source,retail,current,graph){
 for(const edit of source.branch_changes){
  const row=graph.instructions.find(r=>r.pc===edit.pc),decoded=layout(row,retail),at=decoded.at,args=row.operands;
  const before=retail[at]+256*retail[at+1],after=current[at]+256*current[at+1],signed=n=>n>=32768?n-65536:n;
  const fields=['ACTOR_RECT_BRANCH','ACTOR_LOOKUP_BRANCH'].includes(row.mnemonic)?{target_word:[before,after],target_word_pc:[at,at],target_pc:[decoded.target,edit.authored_target_pc]}:row.mnemonic==='VALUE_COMPARE_BRANCH'?{delta_u16:[before,after],encoded_target:[decoded.target,edit.authored_target_pc]}:{delta:[signed(before),signed(after)]};
  if(['FLAG_WORD_BRANCH','FIELD_68_BRANCH','ACTOR_SEARCH_BRANCH'].includes(row.mnemonic))fields.target=[decoded.target,edit.authored_target_pc];
  for(const [field,[original,value]] of Object.entries(fields)){if(args[field]!==original)fail('World branch graph analysis differs from its source word.');args[field]=value;}
  row.successors.find(e=>e.condition===edit.condition).pc=edit.authored_target_pc;
  const header=row.target_context===null?1:2;row.raw_hex=Array.from(current.slice(row.pc,row.pc+row.length),n=>n.toString(16).padStart(2,'0')).join('');args.encoded_hex=row.raw_hex.slice(header*2);
 }
}

export function reachedWorldBranchGraph(graph,data,source){
 const instructions=new Map(graph.instructions.map(r=>[r.pc,r])),dialogues=new Map(graph.dialogues.map(r=>[r.pc,r])),reached=new Set(),queue=[graph.entry_pc];
 while(queue.length){
  const pc=queue.shift();if(reached.has(pc)||pc===data.length)continue;
  const instruction=instructions.get(pc),dialogue=dialogues.get(pc);if(!instruction&&!dialogue)fail('World Current path leaves original source boundaries.');
  reached.add(pc);if(reached.size>8192)fail('World Current graph exceeds its traversal budget.');
  queue.push(...(instruction?instruction.successors.map(e=>e.pc):[pc+dialogue.length]));
 }
 const result={status:'decoded_supported_paths',entry_pc:graph.entry_pc,instructions:graph.instructions.filter(r=>reached.has(r.pc)),dialogues:graph.dialogues.filter(r=>reached.has(r.pc)),opaque_regions:[],stops:[]},owned=new Uint8Array(data.length);
 for(const row of [...result.instructions,...result.dialogues])owned.fill(1,row.pc,row.pc+row.length);
 for(let pc=graph.entry_pc;pc<data.length;){if(owned[pc]){pc++;continue;}const start=pc;while(pc<data.length&&!owned[pc])pc++;result.opaque_regions.push({pc:start,byte_offset:source.source_record.byte_offset+start,length:pc-start,raw_hex:Array.from(data.slice(start,pc),n=>n.toString(16).padStart(2,'0')).join(''),reason:'Unsupported, unvisited or ambiguous bytes; no instruction width inferred.'});}
 if(result.opaque_regions.length)result.status='partial';
 const dormantInstructions=graph.instructions.filter(r=>!reached.has(r.pc)),dormantDialogues=graph.dialogues.filter(r=>!reached.has(r.pc));result.unreachable_source_pcs=[...dormantInstructions,...dormantDialogues].map(r=>r.pc).sort((a,b)=>a-b);result.unvisited_instructions=dormantInstructions;result.unvisited_dialogues=dormantDialogues;
 return result;
}
