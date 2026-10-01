import assert from 'node:assert/strict';
import {instructionOperandEditors,menuLabelEditors} from '../editor/script-operands.js';
const row={pc:5,mnemonic:'WAIT_FRAMES',target_context:null,operands:{duration_ticks:16}};
const target={pc:5,mnemonic:'WAIT_FRAMES',target_context:null,semantic_id:'script://fixture/actors/man-p1/0001/wait/0005',values:{duration_ticks:16},authored_values:{duration_ticks:17},effective_values:{duration_ticks:17}};
const report={instructions:[row],wait_authoring:{supported:true,targets:[target]}};
const source=JSON.stringify(report),result=instructionOperandEditors(report);
assert.equal(result.get(5).effective.duration_ticks,17);result.get(5).retail.duration_ticks=0;assert.equal(JSON.stringify(report),source);
for(const change of [{target_context:7},{mnemonic:'CFLAG_SET'},{values:{duration_ticks:15}},{effective_values:{duration_ticks:16}},{authored_values:{seconds:1}},{effective_values:{duration_ticks:17,extra:1}}]){
 assert.equal(instructionOperandEditors({...report,wait_authoring:{supported:true,targets:[{...target,...change}]}}).size,0);
}
assert.equal(instructionOperandEditors({...report,wait_authoring:{supported:false,targets:[target]}}).size,0);
assert.equal(instructionOperandEditors({...report,wait_authoring:{supported:true,targets:[target,target]}}).size,0);
assert.equal(instructionOperandEditors({...report,wait_authoring:{supported:true,targets:Array(4097).fill(target)}}).size,0);
for(const [kind,mnemonic,values,operands] of [['flag','CFLAG_SET',{bit:2},{bit:2}],['movement','MOVE_TO',{x:64,z:128},{target_position:{x:64,z:128}}],['movement','EXEC_MOVE',{move_id:9},{move_id:9}]]){
 const r={instructions:[{...row,mnemonic,operands}],[kind+'_authoring']:{supported:true,targets:[{...target,mnemonic,values,authored_values:{},effective_values:values}]}};
 assert.equal(instructionOperandEditors(r).get(5).kind,kind);
}
console.log('Operand layer binding, stale/context/value rejection, bounds, ambiguity and source detachment passed.');

const owner='scene://fixture/actors/man-p1/0001',prefix='script://fixture/actors/man-p1/0001';
const menu={pc:8,mnemonic:'DIALOGUE_PICKER',operands:{option_count:2,options:[
 {index:0,label_pc:13,label_length:5,entry_pc:9,relative_jump:13,encoded_target:22,
  label_tokens:[...'Yes'].map((text,index)=>({pc:14+index,kind:'glyph',length:1,value:text.charCodeAt(0),text}))},
 {index:1,label_pc:18,label_length:4,entry_pc:11,relative_jump:11,encoded_target:22,label_tokens:[]}]}};
const label={kind:'menu_label',actor_id:owner,menu_pc:8,option_index:0,option_count:2,entry_pc:9,relative_jump:13,encoded_target:22,
 pc:14,semantic_id:prefix+'/menu/0008/option/0/run/000e',byte_length:3,max_length:3,text:'Yes',authored_text:'OK',effective_text:'OK '};
const menuReport={semantic_id:prefix,instructions:[menu],dialogue_authoring:{supported:true,actor_id:owner,runs:[label]}};
const original=JSON.stringify(menuReport),labels=menuLabelEditors(menuReport);
assert.equal(labels.get('8:0')[0].effective,'OK ');labels.get('8:0')[0].retail='changed';assert.equal(JSON.stringify(menuReport),original);
for(const update of [{actor_id:'scene://other/actors/man-p1/0001'},{menu_pc:9},{pc:13},{pc:15},{option_index:1},{option_count:4},
 {entry_pc:10},{relative_jump:12},{encoded_target:23},{semantic_id:prefix+'/menu/0008/option/0/run/000f'},
 {byte_length:2},{max_length:4},{text:'^es'},{text:'Y|s'},{text:'No!'},{authored_text:'Long'},{authored_text:'|',effective_text:'|  '},{effective_text:'Yes'}]){
 assert.equal(menuLabelEditors({...menuReport,dialogue_authoring:{...menuReport.dialogue_authoring,runs:[{...label,...update}]}}).size,0);
}
assert.equal(menuLabelEditors({...menuReport,semantic_id:'script://other/actors/man-p1/0001'}).size,0);
assert.equal(menuLabelEditors({...menuReport,instructions:[menu,menu]}).size,0);
assert.equal(menuLabelEditors({...menuReport,dialogue_authoring:{...menuReport.dialogue_authoring,runs:[label,label]}}).size,0);
assert.equal(menuLabelEditors({...menuReport,dialogue_authoring:{...menuReport.dialogue_authoring,runs:Array(1025).fill(label)}}).size,0);
const multiple=structuredClone(menuReport);multiple.instructions[0].operands.options[0].label_length=9;
multiple.instructions[0].operands.options[0].label_tokens.push({pc:17,kind:'spacing',length:2,value:0},...[...'No'].map((text,index)=>({pc:19+index,kind:'glyph',length:1,value:text.charCodeAt(0),text})));
multiple.dialogue_authoring.runs.push({...label,pc:19,semantic_id:prefix+'/menu/0008/option/0/run/0013',byte_length:2,max_length:2,text:'No',authored_text:null,effective_text:'No'});
assert.equal(menuLabelEditors(multiple).get('8:0').length,2);
console.log('Menu label token/owner/option binding, multiple runs, detached layers and ambiguity/bounds rejection passed.');

const partitionTwo=JSON.parse(JSON.stringify(menuReport).replaceAll('actors/man-p1/0001','scripts/man-p2/0000'));
partitionTwo.script_id=partitionTwo.semantic_id;delete partitionTwo.semantic_id;
assert.equal(menuLabelEditors(partitionTwo).get('8:0')[0].effective,'OK ');
assert.equal(menuLabelEditors({...menuReport,instructions:[null]}).size,0);
const badToken=structuredClone(menuReport);badToken.instructions[0].operands.options[0].label_tokens=[null];
assert.equal(menuLabelEditors(badToken).size,0);
