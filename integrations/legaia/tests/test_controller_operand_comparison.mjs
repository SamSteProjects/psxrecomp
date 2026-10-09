import assert from 'node:assert/strict';
import fs from 'node:fs';
import {controllerOperandComparison,filterControllerComparison} from '../editor/controller-operand-comparison.js';
const rows=[{family:'A',label:'Party Selectors',id:'script://fixture/party-selector/0005',pc:5,mnemonic:'PARTY_LEADER_REQUEST',retail:{party_selector:2},authored:{party_selector:7},current:{party_selector:7},changed:true},{family:'B',label:'Branches',id:'script://fixture/branch/0065',pc:101,mnemonic:'JMP_REL',retail:{target_pc:5},authored:null,current:{target_pc:5},changed:false}];
assert.equal(filterControllerComparison(rows).length,2);
assert.deepEqual(filterControllerComparison(rows,{layer:'changed'}),[rows[0]]);
assert.deepEqual(filterControllerComparison(rows,{layer:'authored'}),[rows[0]]);
assert.deepEqual(filterControllerComparison(rows,{family:'B',query:'0x0065 jmp_rel'}),[rows[1]]);
assert.deepEqual(filterControllerComparison(rows,{query:'party 7'}),[rows[0]]);
assert.deepEqual(filterControllerComparison(rows,{family:'B',layer:'changed'}),[]);
assert.throws(()=>filterControllerComparison(rows,{layer:'live'}));
assert.throws(()=>filterControllerComparison(rows,{query:'x'.repeat(257)}));
if(process.argv[2]){
 const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),before=structuredClone(fixture);
 const value=controllerOperandComparison(fixture.families,fixture.owner,fixture.context);
 assert.equal(value.rows.length,fixture.count);assert.equal(value.rows.filter(r=>r.changed).length,fixture.changed);assert.equal(value.rows.filter(r=>r.authored!==null).length,fixture.changed);
 assert.deepEqual(fixture,before);value.rows[0].retail.mutated=true;assert.deepEqual(fixture,before);
 for(const mutate of [f=>delete f.families.ControllerFades,f=>f.families.ControllerPartySelectors.current_record_sha256='f'.repeat(64),f=>f.families.ControllerPartySelectors.targets[0].current_values.party_selector=8,f=>f.families.ControllerBranches.targets[0].current_target_pc=32767,f=>f.families.ControllerSystemFlags.targets[0].current_index=4096,f=>f.families.ControllerTileRects.targets[0].semantic_id='foreign']){const f=structuredClone(fixture);mutate(f);assert.throws(()=>controllerOperandComparison(f.families,f.owner,f.context));}
 console.log(`Qualified ${value.rows.length} supported operands and ${fixture.changed} authored changes; source binding, native decoders, detachment and malformed layer refusal passed.`);
}
console.log('Comparison family, authored/change and token filters passed.');
