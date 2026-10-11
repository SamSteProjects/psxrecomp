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
