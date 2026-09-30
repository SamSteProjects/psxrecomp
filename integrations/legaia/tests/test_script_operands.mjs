import assert from 'node:assert/strict';
import {instructionOperandEditors} from '../editor/script-operands.js';
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
