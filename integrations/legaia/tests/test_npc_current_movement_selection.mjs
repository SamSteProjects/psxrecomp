import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeNpcCurrentScript,npcCurrentMovementSelection,npcCurrentSystemSelection,npcCurrentOperandSelection,npcCurrentBranchSelection,npcCurrentDialogueSelection,npcCurrentEffectSelection} from '../editor/npc-current-script.js';
assert(process.argv[2],'Fresh Retail Current and movement qualification required');
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),before=structuredClone(f),current=await decodeNpcCurrentScript(f.report,f.entity_id,f.state);
const selected=npcCurrentMovementSelection(current,f.movement,35,f.state);assert.equal(selected.entity_id,f.entity_id);assert.equal(selected.movement_id,'script://town01/actors/man-p1/0011/movement/0023');assert.deepEqual(selected.values,{x:64,z:16384,move_id:13});
selected.values.x=128;assert.deepEqual(f,before);
for(const pc of [null,19,999999])assert.throws(()=>npcCurrentMovementSelection(current,f.movement,pc,f.state));
for(const change of [s=>s.project.mode='live',s=>s.capabilities.actor_movement_authoring=false,s=>s.project_copy_source_key='f'.repeat(64),s=>s.actor_drafts[f.entity_id].donor_entity_id='scene://town01/actors/man-p1/0040']){const state=structuredClone(f.state);change(state);assert.throws(()=>npcCurrentMovementSelection(current,f.movement,35,state));}
for(const change of [s=>s.options.targets.find(n=>n.pc===35).source_record_sha256='b'.repeat(64),s=>s.options.targets.find(n=>n.pc===35).effective_values.x=128,s=>s.entity_id='authored-actor://other']){const source=structuredClone(f.movement);change(source);assert.throws(()=>npcCurrentMovementSelection(current,source,35,f.state));}
console.log('Current destination editing independently binds source owner, native record, effective coordinates, exact PC, Edit/capability and stale-context gates.');

const system=npcCurrentSystemSelection(current,f.system_flags,22,f.state);assert.equal(system.system_flag_id,'script://town01/actors/man-p1/0011/system-flag/0016');assert.deepEqual(system.values,{index:326});system.values.index=4095;assert.deepEqual(f,before);
for(const pc of [null,35,99999])assert.throws(()=>npcCurrentSystemSelection(current,f.system_flags,pc,f.state));
for(const change of [s=>s.project.mode='live',s=>s.capabilities.npc_system_selector_authoring=false,s=>s.project_copy_source_key='f'.repeat(64)]){const state=structuredClone(f.state);change(state);assert.throws(()=>npcCurrentSystemSelection(current,f.system_flags,22,state));}
for(const change of [s=>s.options.targets.find(n=>n.pc===22).source_record_sha256='b'.repeat(64),s=>s.options.targets.find(n=>n.pc===22).effective_values.index=2048,s=>s.entity_id='authored-actor://other']){const source=structuredClone(f.system_flags);change(source);assert.throws(()=>npcCurrentSystemSelection(current,source,22,f.state));}
console.log('Current system selector editing binds exact PC, source record, effective index, ownership and Edit/capability gates.');

for(const [family,pc,values,capability] of [['facing',35,{sector:7},'actor_facing_authoring'],['flags',20,{bit:2},'actor_flag_authoring']]){
 const selected=npcCurrentOperandSelection(current,f[family],pc,f.state,family);assert.deepEqual(selected.values,values);selected.values[Object.keys(values)[0]]=0;assert.deepEqual(f,before);
 for(const badPc of [null,22,99999])assert.throws(()=>npcCurrentOperandSelection(current,f[family],badPc,f.state,family));
 for(const change of [s=>s.project.mode='live',s=>s.capabilities[capability]=false,s=>s.project_copy_source_key='f'.repeat(64)]){const state=structuredClone(f.state);change(state);assert.throws(()=>npcCurrentOperandSelection(current,f[family],pc,state,family));}
 const forged=structuredClone(current);forged.inspection.instructions.find(r=>r.pc===pc).raw_hex='00'.repeat(forged.inspection.instructions.find(r=>r.pc===pc).length);assert.throws(()=>npcCurrentOperandSelection(forged,f[family],pc,f.state,family));
 const source=structuredClone(f[family]);source.options.targets.find(r=>r.pc===pc).source_record_sha256='a'.repeat(64);assert.throws(()=>npcCurrentOperandSelection(current,source,pc,f.state,family));
}
assert.throws(()=>npcCurrentOperandSelection(current,f.waits,35,f.state,'waits'));assert.throws(()=>npcCurrentOperandSelection(current,f.facing,35,f.state,'other'));
if(process.argv[3]){const w=JSON.parse(fs.readFileSync(process.argv[3],'utf8')),report=await decodeNpcCurrentScript(w.report,w.entity_id,w.state),row=w.waits.options.targets[0];assert.deepEqual(npcCurrentOperandSelection(report,w.waits,row.pc,w.state,'waits').values,row.effective_values);const changed=structuredClone(w.waits);changed.options.targets[0].effective_values.duration_ticks++;assert.throws(()=>npcCurrentOperandSelection(report,changed,row.pc,w.state,'waits'));}
console.log('Current facing/wait/flag-bit navigation qualifies source bytes and effective operands with independent family, owner, Edit and stale gates.');

assert.deepEqual(npcCurrentBranchSelection(current,f.branches,22,f.state).values,{target_pc:55});const text=npcCurrentDialogueSelection(current,f.dialogue,84,f.state);assert.equal(text.run_ids.length,2);assert.deepEqual(f,before);
for(const [source,pc,capability,select] of [[f.branches,22,'actor_branch_authoring',npcCurrentBranchSelection],[f.dialogue,84,'actor_dialogue_authoring',npcCurrentDialogueSelection]]){
 for(const badPc of [null,35,99999])assert.throws(()=>select(current,source,badPc,f.state));
 for(const change of [s=>s.project.mode='live',s=>s.capabilities[capability]=false,s=>s.project_copy_source_key='a'.repeat(64)]){const state=structuredClone(f.state);change(state);assert.throws(()=>select(current,source,pc,state));}
}
const wrongBranch=structuredClone(f.branches);wrongBranch.options.targets[0].operand_pc++;assert.throws(()=>npcCurrentBranchSelection(current,wrongBranch,22,f.state));const wrongText=structuredClone(f.dialogue);wrongText.options.runs[0].pc++;assert.throws(()=>npcCurrentDialogueSelection(current,wrongText,84,f.state));
if(process.argv[4]){const m=JSON.parse(fs.readFileSync(process.argv[4],'utf8')),report=await decodeNpcCurrentScript(m.report,m.entity_id,m.state),row=m.model_selectors.options.targets[0];assert.deepEqual(npcCurrentOperandSelection(report,m.model_selectors,row.pc,m.state,'model_selectors').values,row.effective_values);const forged=structuredClone(report);forged.inspection.instructions.find(r=>r.pc===row.pc).raw_hex='00'.repeat(forged.inspection.instructions.find(r=>r.pc===row.pc).length);assert.throws(()=>npcCurrentOperandSelection(forged,m.model_selectors,row.pc,m.state,'model_selectors'));}
console.log('Current branch words, source glyph spans and signed model selectors qualify exact ownership, bytes and selection.');

if(process.argv[5]){const menu=JSON.parse(fs.readFileSync(process.argv[5],'utf8')),report=await decodeNpcCurrentScript(menu.report,menu.entity_id,menu.state),row=menu.dialogue.options.runs.find(r=>r.kind==='menu_label');assert(npcCurrentDialogueSelection(report,menu.dialogue,row.menu_pc,menu.state).run_ids.includes(row.semantic_id));}

assert.throws(()=>npcCurrentEffectSelection(current,f.effect_colors,35,f.state));
if(process.argv[6]){const color=JSON.parse(fs.readFileSync(process.argv[6],'utf8')),report=await decodeNpcCurrentScript(color.report,color.entity_id,color.state),row=color.effect_colors.options.targets[0];assert.deepEqual(npcCurrentEffectSelection(report,color.effect_colors,row.pc,color.state).values,row.effective_values);
 for(const change of [s=>s.project.mode='live',s=>s.capabilities.actor_effect_color_authoring=false,s=>s.project_copy_source_key='a'.repeat(64)]){const state=structuredClone(color.state);change(state);assert.throws(()=>npcCurrentEffectSelection(report,color.effect_colors,row.pc,state));}
 for(const change of [s=>s.options.targets[0].source_record_sha256='a'.repeat(64),s=>s.options.targets[0].decoded_byte_offset++,s=>s.options.targets[0].effective_values.red=(s.options.targets[0].effective_values.red+1)%256]){const source=structuredClone(color.effect_colors);change(source);assert.throws(()=>npcCurrentEffectSelection(report,source,row.pc,color.state));}
 const forged=structuredClone(report);forged.inspection.instructions.find(r=>r.pc===row.pc).raw_hex='00'.repeat(forged.inspection.instructions.find(r=>r.pc===row.pc).length);assert.throws(()=>npcCurrentEffectSelection(forged,color.effect_colors,row.pc,color.state));}
console.log('Current RGB/intensity editing binds native opcode/selector/dispatch, exact span, source owner and effective signed operands.');
