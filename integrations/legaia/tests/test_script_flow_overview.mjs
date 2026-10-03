import assert from 'node:assert/strict';
import {analyzeScriptFlow,mountScriptFlowOverview} from '../editor/script-flow-overview.js';
const node=(pc,targets=[],length=1)=>({pc,length,mnemonic:'FIXTURE',successors:targets.map(target=>typeof target==='number'?{pc:target,condition:null}:target)});
const report=(instructions,entry_pc=0)=>({status:'partial',entry_pc,instructions,dialogues:[],stops:[],opaque_regions:[]});
const fixture=report([node(0,[1]),node(1,[2,{pc:9,condition:'encoded_test'}]),node(2,[1]),node(4,[4]),node(5),node(6,[7]),node(7,[65536])]);
fixture.stops=[{pc:9,reason:'unsupported opcode'},{pc:8,reason:'overlap'}];
let result=analyzeScriptFlow(fixture);
assert.deepEqual(result.reachable_pcs,[0,1,2]);assert.deepEqual(result.unvisited_pcs,[4,5,6,7]);
assert.deepEqual(result.cycles,[{pcs:[1,2],internal_edge_count:2,outgoing_edge_count:1,closed_encoded_component:false,entry_reachable:true},{pcs:[4],internal_edge_count:1,outgoing_edge_count:0,closed_encoded_component:true,entry_reachable:false}]);
assert.deepEqual(result.terminals,[5]);assert.equal(result.edge_count,7);
assert.deepEqual(result.boundaries,[{pc:9,edges:[{source:1,target:9,condition:'encoded_test'}],reasons:['unsupported opcode'],entry_reachable:true},{pc:65536,edges:[{source:7,target:65536,condition:null}],reasons:[],entry_reachable:false}]);
const snapshot=JSON.stringify(fixture);result.cycles[0].pcs[0]=100;result.boundaries[0].edges[0].condition='changed';assert.equal(JSON.stringify(fixture),snapshot);
const unknown=structuredClone(fixture);delete unknown.entry_pc;
assert.equal(analyzeScriptFlow(unknown).reachable_pcs,null);assert.equal(analyzeScriptFlow(unknown).cycles[0].entry_reachable,null);
unknown.record={script_offset:4};assert.deepEqual(analyzeScriptFlow(unknown).reachable_pcs,[4]);
assert.equal(analyzeScriptFlow({...fixture,entry_pc:3}).reachable_pcs,null);
const anchored=report([node(0,[4]),node(4,[0])]);anchored.unvisited_instructions=[node(3,[4])];anchored.unvisited_dialogues=[{pc:10,length:2,text:'unvisited'}];
assert.deepEqual(analyzeScriptFlow(anchored).unvisited_pcs,[3,10]);assert.deepEqual(analyzeScriptFlow(anchored).cycles[0].pcs,[0,4]);
assert.throws(()=>analyzeScriptFlow({...anchored,unvisited_instructions:[node(0)]}));
assert.throws(()=>analyzeScriptFlow({...anchored,unreachable_source_pcs:[3]}));
assert.throws(()=>analyzeScriptFlow({...anchored,instructions:[node(0,[3]),node(4,[0])]}));
const dialogue=report([node(0,[1]),node(4,[1])]);dialogue.dialogues=[{pc:1,length:3,text:'fixture'}];
assert.deepEqual(analyzeScriptFlow(dialogue).cycles[0].pcs,[1,4]);assert.equal(analyzeScriptFlow(dialogue).nodes[1].mnemonic,'DIALOGUE_SEGMENT');
const duplicateEdges=report([node(0,[0,0])]);assert.equal(analyzeScriptFlow(duplicateEdges).cycles[0].internal_edge_count,2);
for(const mutate of [r=>r.entry_pc=true,r=>r.entry_pc=-1,r=>r.instructions.push(r.instructions[0]),r=>r.instructions[0].pc=65536,r=>r.instructions[0].length=0,r=>r.instructions[0].successors[0].pc=65537,r=>r.instructions[0].successors[0].condition={},r=>r.instructions[0].successors=Array(65).fill({pc:1,condition:null}),r=>r.dialogues.push({pc:0,length:2}),r=>r.stops[0].reason=true]){const value=structuredClone(fixture);mutate(value);assert.throws(()=>analyzeScriptFlow(value));}
// Full decoder-sized chain and cycle: an implementation using recursive DFS overflows here.
const long=report(Array.from({length:8192},(_,pc)=>node(pc,[pc===8191?0:pc+1])));
assert.equal(analyzeScriptFlow(long).cycles[0].pcs.length,8192);assert.equal(analyzeScriptFlow(long).reachable_pcs.length,8192);
assert.throws(()=>analyzeScriptFlow(report([...long.instructions,node(8192)])));
assert.deepEqual(analyzeScriptFlow(report([],null)).cycles,[]);
class Element{
  constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.attributes={};this.textContent='';}
  append(...nodes){for(const child of nodes){child.parent=this;this.children.push(child);}}
  replaceChildren(...nodes){this.children=[];this.append(...nodes);}
  setAttribute(key,value){this.attributes[key]=String(value);}
  remove(){if(this.parent)this.parent.children=this.parent.children.filter(child=>child!==this);}
}
globalThis.document={createElement:tag=>new Element(tag)};
const tree=node=>[node,...node.children.flatMap(tree)],host=new Element('div'),selected=[];
const view=mountScriptFlowOverview(host,{selectInstruction:pc=>selected.push(pc)});
assert.equal(view.update(fixture),true);assert.match(tree(host).find(node=>node.dataset.flowSummary==='').textContent,/3 reachable.*4 unvisited/);
const inspect=tree(host).find(node=>node.dataset.flowPc===1);inspect.onclick();assert.deepEqual(selected,[1]);
assert.equal(view.update(fixture),true);assert.equal(tree(host).find(node=>node.dataset.flowPc===1),inspect);
assert.equal(view.update(unknown,{label:'Current encoded flow'}),true);assert.match(tree(host).find(node=>node.dataset.flowSummary==='').textContent,/Current encoded flow.*Entry 0x0004/);
const many=report(Array.from({length:70},(_,pc)=>node(pc)),0);view.update(many);
const next=tree(host).find(node=>node.textContent==='Next flow page'&&!node.disabled);assert.ok(next);next.onclick();assert.ok(tree(host).some(node=>node.dataset.flowPc===33));
assert.equal(view.update({}),false);assert.equal(view.result,null);assert.match(tree(host).find(node=>node.dataset.flowSummary==='').textContent,/bounded/);
view.dispose();inspect.onclick();assert.deepEqual(selected,[1]);assert.equal(host.children.length,0);assert.equal(view.update(fixture),false);
console.log('Script source overview: graph, entry, cycles, boundaries, bounds, pagination and disposal pass');
