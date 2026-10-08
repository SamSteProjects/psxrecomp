import assert from 'node:assert/strict';
import fs from 'node:fs';
import {currentAnimationSelection} from '../editor/script-animation-operands.js';
const fixtures=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const fixture of fixtures){
 const {snapshot,source,pc,state}=fixture;
 const result=currentAnimationSelection(snapshot,source,pc,state),target=source.targets.find(t=>t.pc===pc);
 assert.deepEqual(result.values,target.effective_values);assert.equal(result.animation_operand_id,target.semantic_id);
 const before=structuredClone(target.effective_values);result.values[Object.keys(result.values)[0]]=0;assert.deepEqual(source.targets.find(t=>t.pc===pc).effective_values,before);
 for(const mutate of [v=>v.snapshot.state_key='0'.repeat(64),v=>v.state.project.mode='live',v=>v.state.capabilities.script_animation_operand_authoring=false,v=>v.state.scene.id='scene://foreign',v=>v.snapshot.source_record_sha256='0'.repeat(64),v=>v.snapshot.current_report.instructions=v.snapshot.current_report.instructions.filter(r=>r.pc!==pc),v=>v.snapshot.current_report.instructions.find(r=>r.pc===pc).length++,v=>v.snapshot.current_report.instructions.find(r=>r.pc===pc).target_context=255,v=>v.snapshot.current_report.instructions.find(r=>r.pc===pc).raw_hex='ff'+v.snapshot.current_report.instructions.find(r=>r.pc===pc).raw_hex.slice(2),v=>v.snapshot.current_report.instructions.find(r=>r.pc===pc).operands[Object.keys(target.values)[0]]^=1,v=>v.snapshot.source_report.instructions.find(r=>r.pc===pc).raw_hex='00',v=>v.pc=65535]){
  const bad=structuredClone(fixture);mutate(bad);assert.throws(()=>currentAnimationSelection(bad.snapshot,bad.source,bad.pc,bad.state));refusals++;
 }
}
assert.equal(fixtures.length,3);console.log(`Current animation P1/P2/extended-context qualification and ${refusals} forged/stale/Live refusals passed.`);
