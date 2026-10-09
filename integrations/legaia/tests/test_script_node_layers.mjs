import assert from 'node:assert/strict';
import {scriptNodeLayers,mountScriptNodeLayers,formatScriptOperand} from '../editor/script-node-layers.js';
assert.equal(formatScriptOperand('signed_words','[-32768,32767,0]'),'[0]: -32768\n[1]: 32767\n[2]: 0');
assert.equal(formatScriptOperand('Encoded successors','[{"pc":22,"condition":"encoded_continuation"}]'),'PC 0x0016 · encoded continuation');
assert.equal(formatScriptOperand('text','"Hi_There"'),'Hi_There');
assert.equal(formatScriptOperand('value','Not reviewed'),'Not reviewed');
const instruction=(raw,operands)=>({pc:15,length:7,mnemonic:'EFFECT_COLOR_INTENSITY',target_context:null,raw_hex:raw,operands,successors:[{pc:22,condition:'encoded_continuation'}]});
const report=row=>({status:'decoded_supported_paths',instructions:row?[row]:[],dialogues:[],stops:[],opaque_regions:[]});
const retail=report(instruction('3405ffffff4100',{rgb:[255,255,255],intensity:65}));
const current=report(instruction('3405feffff4200',{intensity:66,rgb:[254,255,255]}));
let value=scriptNodeLayers(retail,current,null,15);
assert.deepEqual(value.retail_to_current,[{pc:17,before:'ff',after:'fe'},{pc:20,before:'41',after:'42'}]);assert.equal(value.current_to_proposed,null);
assert.deepEqual(value.rows.find(r=>r.field==='rgb'),{field:'rgb',retail:'[255,255,255]',current:'[254,255,255]',proposed:'Not reviewed'});
assert.equal(value.rows.find(r=>r.field==='intensity').current,'66');value.layers.current.node.operands.rgb[0]=0;assert.equal(current.instructions[0].operands.rgb[0],254);
const proposed=report(instruction('3405feffff4300',{intensity:67,rgb:[254,255,255]}));value=scriptNodeLayers(retail,current,proposed,15);assert.deepEqual(value.current_to_proposed,[{pc:20,before:'42',after:'43'}]);
value=scriptNodeLayers(retail,report(null),null,15);assert.equal(value.layers.current.status,'boundary_not_decoded');assert.equal(value.retail_to_current,null);assert.equal(value.rows[0].current,'Boundary not decoded');
value=scriptNodeLayers(retail,null,null,15);assert.equal(value.rows[0].current,'Inspection unavailable');
for(const change of [r=>r.instructions[0].raw_hex='00',r=>r.instructions[0].length=8,r=>r.instructions[0].mnemonic='OTHER',r=>r.instructions[0].target_context=1,r=>r.instructions.push(structuredClone(r.instructions[0])),r=>r.instructions[0].successors[0].pc=true]){const broken=structuredClone(current);change(broken);assert.throws(()=>scriptNodeLayers(retail,broken,null,15));}
assert.throws(()=>scriptNodeLayers(retail,current,null,16));assert.throws(()=>scriptNodeLayers(retail,current,null,true));
const message=(text,raw)=>({status:'partial',instructions:[],dialogues:[{pc:30,length:4,text,raw_hex:raw}],stops:[],opaque_regions:[]});value=scriptNodeLayers(message('Hi','1f486900'),message('Ha','1f486100'),null,30);assert.equal(value.mnemonic,'MES_SEGMENT');assert.deepEqual(value.retail_to_current,[{pc:32,before:'69',after:'61'}]);assert.equal(value.rows.find(r=>r.field==='text').current,'"Ha"');
console.log('Selected script operand layers preserve source boundaries, exact byte differences, unknown path state and detached instruction/message data.');

class Element{
 constructor(){this.children=[];this.dataset={};this.style={};this.textContent='';}
 append(...children){this.children.push(...children);for(const child of children)child.parent=this;}
 replaceChildren(...children){this.children=[];this.append(...children);}
 setAttribute(){}
 remove(){if(this.parent)this.parent.children=this.parent.children.filter(row=>row!==this);}
}
const documentBefore=globalThis.document;globalThis.document={createElement:()=>new Element()};
try{
 const host=new Element(),view=mountScriptNodeLayers(host),all=node=>[node,...node.children.flatMap(all)];
 view.update(retail,report(null),null,15);assert(all(host).some(n=>n.textContent==='Boundary not decoded'));assert(all(host).some(n=>n.textContent==='Not reviewed'));
 const encoded=structuredClone(retail);encoded.instructions[0].operands.encoded_hex='05ffffff4100';view.update(encoded,current,proposed,15);assert(!all(host).some(n=>n.dataset.operandField==='encoded_hex'));assert(all(host).some(n=>n.textContent.includes('\"encoded_hex\": \"05ffffff4100\"')));
 view.update(retail,current,proposed,15);assert(all(host).some(n=>n.textContent==='67'));view.clear('Stale source');assert(!all(host).some(n=>n.textContent==='67'));assert(all(host).some(n=>n.textContent==='Stale source'));
 const malformed=structuredClone(current);malformed.instructions[0].raw_hex='ff';assert.equal(view.update(retail,malformed,null,15),false);assert(all(host).some(n=>n.textContent.includes('Selected operand layers unavailable')));view.dispose();assert.equal(host.children.length,0);
}finally{globalThis.document=documentBefore;}
console.log('Operand-layer renderer keeps unvisited/unreviewed states distinct, withdraws cleared/stale data and handles unavailable spans without disrupting the flow workspace.');
