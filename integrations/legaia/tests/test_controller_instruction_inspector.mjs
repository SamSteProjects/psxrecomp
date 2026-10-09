import assert from 'node:assert/strict';
import {renderControllerInstruction} from '../editor/scene-controller.js';
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.style={};this.textContent='';}
 append(...nodes){this.children.push(...nodes);}
}
globalThis.document={createElement:tag=>new Element(tag)};
const row={pc:5,length:3,byte_offset:105,mnemonic:'TEXT_ACTOR_PAYLOAD_REQUEST',raw_hex:'4ce100',target_context:null,operands:{sub_op:225,embedded_payload:{pc:7,length:1,terminator:0},nonzero_first_byte:false,payload_ownership:'runtime_text_actor_not_parent_dialogue',actor_binding:'runtime_allocation_unresolved',runtime_effect:'not_evaluated',encoded_hex:'e100'},successors:[{pc:8,condition:'encoded_continuation'},{pc:9,condition:null}]};
const report={entry_pc:5,source_record:{byte_offset:100,byte_length:9},record:{raw_hex:'00000000004ce10021'},instructions:[row,{pc:8}],dialogues:[]},before=JSON.stringify({row,report}),selected=[];
const detail=renderControllerInstruction(row,report,pc=>selected.push(pc));
const nodes=node=>[node,...node.children.flatMap(nodes)],all=nodes(detail),fields=all.find(node=>Object.hasOwn(node.dataset,'controllerInstructionFields'));
assert.equal(detail.dataset.controllerInstructionPc,5);assert.equal(detail.children[0].textContent,'PC 0x0005 · TEXT_ACTOR_PAYLOAD_REQUEST');
assert(fields.children.some(n=>n.textContent==='Embedded Payload / Terminator'));
assert(fields.children.some(n=>n.textContent==='runtime text actor not parent dialogue'));
assert(fields.children.some(n=>n.textContent==='No'));
assert(!fields.children.some(n=>n.textContent==='Encoded Hex'));
const buttons=all.filter(n=>n.tag==='button');assert.equal(buttons[0].disabled,false);assert.equal(buttons[1].disabled,true);
buttons[0].onclick();buttons[1].onclick();assert.deepEqual(selected,[8]);
const raw=all.find(n=>Object.hasOwn(n.dataset,'controllerInstructionEvidence'));assert.equal(raw.children[1].textContent,JSON.stringify(row,null,2));assert.equal(raw.open,undefined);
assert.equal(JSON.stringify({row,report}),before);
for(const change of [r=>r.pc=4,r=>r.pc=10,r=>r.length=0,r=>r.length=5,r=>r.byte_offset=0,r=>r.raw_hex='4ce101']){const bad=structuredClone(row);change(bad);assert.throws(()=>renderControllerInstruction(bad,report,()=>{}));}
const terminal=structuredClone(row);terminal.successors=[];terminal.target_context=7;terminal.operands={text:'<img src=x onerror=alert(1)>',values:[-32768,32767],unknown:null};
const terminalNodes=nodes(renderControllerInstruction(terminal,report,()=>{}));assert(terminalNodes.some(n=>n.textContent==='<img src=x onerror=alert(1)>'));assert(terminalNodes.some(n=>n.textContent==='-32768, 32767'));assert(terminalNodes.some(n=>n.textContent==='Unresolved'));assert(terminalNodes.some(n=>n.textContent.includes('Extended target 7')));assert(terminalNodes.some(n=>n.textContent.startsWith('No encoded successors')));
console.log('Controller instruction fields, detached source data, exact byte refusals, literal text and decoded successor navigation passed.');
