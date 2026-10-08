import assert from 'node:assert/strict';
import {createScriptWalkthrough,scriptWalkthroughEvidence,mountScriptWalkthrough} from '../editor/script-walkthrough.js';
const node=(pc,successors=[])=>({pc,length:1,mnemonic:'SOURCE_'+pc,successors});
const report={status:'partial',entry_pc:0,instructions:[node(0,[{pc:1,condition:null}]),node(1,[{pc:0,condition:'repeat_unknown'},{pc:4,condition:'external_unknown'}]),node(3)],dialogues:[{pc:4,length:2,text:'Source dialogue'}],stops:[{pc:6,reason:'unsupported opcode'}]};
const frozen=JSON.stringify(report),walk=createScriptWalkthrough(report);
assert.equal(walk.snapshot().state,'not_started');assert.throws(()=>walk.step(0));assert.throws(()=>walk.start(2));
assert.equal(walk.start(0).trace.length,1);assert.equal(walk.step(0).pc,1);assert.throws(()=>walk.step());assert.throws(()=>walk.step(-1));assert.throws(()=>walk.step(true));assert.throws(()=>walk.step(2));
let s=walk.step(1);assert.equal(s.pc,4);assert.equal(s.trace.at(-1).via.condition,'external_unknown');assert.equal(s.trace.at(-1).mnemonic,'DIALOGUE_SEGMENT');
s=walk.step(0);assert.equal(s.state,'undecoded_target');assert.equal(s.pc,6);assert.deepEqual(s.stop_reasons,['unsupported opcode']);assert.throws(()=>walk.step(0));
assert.equal(walk.back().pc,4);assert.equal(walk.back().pc,1);assert.equal(walk.step(0).pc,0);assert.equal(walk.snapshot().trace.length,3);
s=walk.snapshot();s.trace[0].pc=999;s.successors.length=0;assert.equal(walk.snapshot().trace[0].pc,0);assert.equal(walk.snapshot().successors.length,1);assert.equal(JSON.stringify(report),frozen);
assert.equal(walk.start(3).state,'no_encoded_successor');assert.throws(()=>walk.step(0));assert.equal(walk.back().pc,3);
walk.start(0);for(let i=1;i<1024;i++)walk.step(0);assert.equal(walk.snapshot().state,'visit_limit');assert.equal(walk.snapshot().trace.length,1024);assert.throws(()=>walk.step(0));assert.equal(walk.back().state,'choose_successor');walk.reset();assert.equal(walk.snapshot().pc,null);
const context={project_path:'C:/private/project',scene_id:'scene://fixture',script_id:'script://fixture/actors/man-p1/0000',project_source_key:'a'.repeat(64),record_sha256:'b'.repeat(64),representation:'retail_source'};
assert.throws(()=>scriptWalkthroughEvidence(walk.snapshot(),context));walk.start(0);walk.step(0);let evidence=scriptWalkthroughEvidence(walk.snapshot(),context);assert.equal(evidence.conditions_evaluated,false);assert.equal(evidence.runtime_execution,'not_asserted');assert.equal(evidence.project_changed,false);evidence.source.record_sha256='f'.repeat(64);assert.equal(context.record_sha256,'b'.repeat(64));
for(const mutate of [c=>c.record_sha256='unknown',c=>c.project_source_key=null,c=>c.scene_id='scene://other',c=>c.representation='current',c=>c.project_path='',c=>c.script_id='script://outside/owner']){const bad=structuredClone(context);mutate(bad);assert.throws(()=>scriptWalkthroughEvidence(walk.snapshot(),bad));}
assert.throws(()=>createScriptWalkthrough({...report,instructions:[...report.instructions,node(0)]}));assert.throws(()=>createScriptWalkthrough({...report,instructions:[node(0,[{pc:65537,condition:null}])]}));
console.log('Source walkthrough: explicit branches, cycles, dialogue, undecoded/terminal stops, Back/Reset, bounded detached traces and source export ownership passed');

class Element{
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.textContent='';this.isConnected=true;}
 append(...nodes){for(const child of nodes){child.parent=this;this.children.push(child);}}
 replaceChildren(...nodes){this.children=[];this.append(...nodes);}
 setAttribute(){}
 closest(){return null;}
 querySelectorAll(selector){return tree(this).filter(n=>n!==this&&n.tagName===selector);}
 remove(){this.isConnected=false;if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);}
}
const tree=n=>[n,...n.children.flatMap(tree)],timers=new Map();let timerId=0;
globalThis.document={createElement:tag=>new Element(tag)};
globalThis.setInterval=fn=>{timers.set(++timerId,fn);return timerId;};globalThis.clearInterval=id=>timers.delete(id);
const host=new Element('div'),ctx=structuredClone(context),selected=[];let blocked=false,selectedPC=1;
const view=mountScriptWalkthrough(host,{report,getContext:()=>ctx,selection:()=>selectedPC,selectInstruction:(pc,reveal)=>selected.push([pc,reveal]),busy:()=>blocked});
const button=text=>tree(host).find(n=>n.tagName==='button'&&n.textContent===text);
button('Start at source entry').onclick();assert.equal(view.snapshot.pc,0);assert.deepEqual(selected,[[0,false]]);
let follow=tree(host).find(n=>n.dataset.walkthroughSuccessor===0);follow.onclick();assert.equal(view.snapshot.pc,1);
blocked=true;for(const fn of timers.values())fn();assert.equal(button('Back one walkthrough step').disabled,true);follow=tree(host).find(n=>n.dataset.walkthroughSuccessor===1);follow.onclick();assert.equal(view.snapshot.pc,1);
assert.equal(tree(host).find(n=>n.dataset.walkthroughPc===0).disabled,true);blocked=false;for(const fn of timers.values())fn();assert.equal(tree(host).find(n=>n.dataset.walkthroughPc===0).disabled,false);button('Back one walkthrough step').onclick();assert.equal(view.snapshot.pc,0);button('Reset walkthrough').onclick();assert.equal(view.snapshot.state,'not_started');button('Start at selected instruction').onclick();assert.equal(view.snapshot.pc,1);
ctx.project_source_key='f'.repeat(64);for(const fn of timers.values())fn();assert.equal(view.snapshot.state,'not_started');assert.equal(button('Download source walkthrough').disabled,true);assert.match(tree(host).find(n=>n.dataset.walkthroughStatus==='').textContent,/Source context changed/);button('Start at source entry').onclick();assert.equal(view.snapshot.state,'not_started');
view.dispose();assert.equal(timers.size,0);assert.equal(host.children.length,0);
console.log('Source walkthrough UI: explicit steps, shared instruction handoff, busy guard, stale trace withdrawal and timer disposal passed');

const host2=new Element('div'),errors=[];let release;
const pending=new Promise(resolve=>release=resolve),view2=mountScriptWalkthrough(host2,{report,getContext:()=>context,requalify:()=>pending,onError:e=>errors.push(e.message)}),button2=text=>tree(host2).find(n=>n.tagName==='button'&&n.textContent===text);
button2('Start at source entry').onclick();const exportTask=button2('Download source walkthrough').onclick();assert.equal(button2('Start at source entry').disabled,true);tree(host2).find(n=>n.dataset.walkthroughSuccessor===0).onclick();assert.equal(view2.snapshot.trace.length,1);release(false);await exportTask;assert.equal(view2.snapshot.state,'not_started');assert.equal(button2('Download source walkthrough').disabled,true);assert.equal(errors.length,1);assert.match(tree(host2).find(n=>n.dataset.walkthroughStatus==='').textContent,/requalification failed/);view2.dispose();assert.equal(timers.size,0);
console.log('Source walkthrough export: pending ownership locks traversal and failed authoritative requalification withdraws trace/download');
