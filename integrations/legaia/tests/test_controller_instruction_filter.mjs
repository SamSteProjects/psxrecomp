import assert from 'node:assert/strict';
import {controllerInstructionMatches,mountControllerInstructionFilter} from '../editor/scene-controller.js';
class Element{
 constructor(tag){this.tag=tag;this.value='';this.children=[];this.dataset={};this.style={};}
 append(...children){this.children.push(...children);}
 setAttribute(name,value){this[name]=value;}
}
globalThis.document={createElement:tag=>new Element(tag)};
const rows=[{pc:145,mnemonic:'TEXT_ACTOR_PAYLOAD_REQUEST',operands:{actor_binding:'runtime_allocation_unresolved',sub_op:225,encoded_hex:'feed'}},{pc:165,mnemonic:'JMP_REL',operands:{target_pc:11}},{pc:182,mnemonic:'TEXT_ACTOR_PAYLOAD_REQUEST',operands:{sub_op:225}}],before=JSON.stringify(rows);
for(const query of ['text actor','TEXT_ACTOR_PAYLOAD_REQUEST','pc:0x0091','pc:145','payload unresolved','225 pc:0x91'])assert(controllerInstructionMatches(rows[0],query),query);
for(const query of ['pc:14','pc:0x92','pc:broken','feed','JMP','payload 999','pc:145 pc:182'])assert(!controllerInstructionMatches(rows[0],query),query);
assert(rows.every(row=>controllerInstructionMatches(row,'   ')));
const host=new Element('section'),elements=new Map(rows.map(row=>[row.pc,new Element('details')])),hidden=[];let fresh=true,busy=false;
const filter=mountControllerInstructionFilter(host,{rows,rowElements:elements,current:()=>fresh,busy:()=>busy,onHidden:pc=>hidden.push(pc)}),input=host.children.find(n=>n.tag==='input'),clear=host.children.find(n=>n.tag==='button'),count=host.children.find(n=>n.dataset.controllerInstructionCount!==undefined);
assert.equal(count.textContent,'Showing 3 of 3 decoded instructions');assert(clear.disabled);
input.value='text payload';input.oninput();assert.equal(count.textContent,'Showing 2 of 3 decoded instructions');assert(elements.get(165).hidden);assert(!elements.get(145).hidden);assert(hidden.includes(165));
input.value='pc:0x91';input.oninput();assert.equal(count.textContent,'Showing 1 of 3 decoded instructions');
assert(filter.reset());assert.equal(input.value,'');assert([...elements.values()].every(n=>!n.hidden));
input.value='missing';input.oninput();assert.equal(count.textContent,'Showing 0 of 3 decoded instructions');clear.onclick();assert.equal(count.textContent,'Showing 3 of 3 decoded instructions');
busy=true;filter.updateState();assert(input.disabled);input.value='pc:145';input.oninput();assert.equal(count.textContent,'Showing 3 of 3 decoded instructions');assert(!filter.reset());
busy=false;fresh=false;filter.updateState();assert(input.disabled);assert(clear.disabled);input.oninput();assert.equal(count.textContent,'Showing 3 of 3 decoded instructions');assert(!filter.reset());
assert.equal(JSON.stringify(rows),before);
console.log('Controller instruction search: exact decimal/hex PC, compound operands, source-only coverage, empty results, reveal reset and stale/busy refusal passed.');
