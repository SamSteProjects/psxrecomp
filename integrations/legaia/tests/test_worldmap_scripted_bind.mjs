import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyScriptedWorldBind,scriptedWorldScriptTarget,mountScriptedBindNavigation} from '../editor/worldmap-scripted-bind.js';
const scenes=JSON.parse(readFileSync(process.argv[2],'utf8')),cases=JSON.parse(readFileSync(process.argv[3],'utf8')),held=JSON.stringify([scenes,cases]);let refusals=0;
for(const c of cases){const row=scenes.find(r=>r.name===c.scene),entity=row.current.scene_graph.entities.find(e=>e.entity_id===c.entity_id);assert.deepEqual(await qualifyScriptedWorldBind(c.result,row.current,entity,row.options.path),c.result);
 const target=await scriptedWorldScriptTarget(c.result,row.current,entity,row.options.path);assert.deepEqual(target,{scriptId:c.result.script.id,sourceKey:c.result.source_key,projectPath:row.options.path,recordSha256:c.result.script.retail_sha256,entryPc:c.result.script.entry_pc});
 for(const change of [v=>v.entity_id='foreign',v=>v.source_key='0'.repeat(64),v=>v.native_entity_id='foreign',v=>v.anchor.col++,v=>v.trigger.byte_offset+=4,v=>v.trigger.encoded.record_index++,v=>v.script.id='foreign',v=>v.script.entry_pc++,v=>v.script.encoded_animation_selector++,v=>v.script.current_sha256='0'.repeat(64),v=>v.script.retail_sha256='0'.repeat(64),v=>v.shared_script=false,v=>v.runtime_activation='active',v=>v.animation_clip='resolved',v=>v.extra=true]){const altered=structuredClone(c.result);change(altered);await assert.rejects(()=>qualifyScriptedWorldBind(altered,row.current,entity,row.options.path));refusals++;}
 const forged=structuredClone(entity),forgedResult=structuredClone(c.result);forged.entity_id=forgedResult.entity_id='foreign';await assert.rejects(()=>qualifyScriptedWorldBind(forgedResult,row.current,forged,row.options.path));refusals++;
 console.log(c.scene,c.entity_id,'shared Current bind ownership qualifies');
}
assert.equal(JSON.stringify([scenes,cases]),held);
// Selection can change between a state refresh and a queued click, or while
// registered-resource discovery is awaiting its catalog.
const previousDocument=globalThis.document;
const element=()=>({dataset:{},children:[],append(...rows){this.children.push(...rows);},remove(){this.removed=true;}});
globalThis.document={createElement:element};
try{
 const host=element(),target={scriptId:'qualified-script'},errors=[];let fresh=true,isBusy=false,calls=0,finish,validDuringDiscovery;
 const tool=mountScriptedBindNavigation({host,target,current:()=>fresh,busy:()=>isBusy,onError:e=>errors.push(e),onOpenScript:async(received,valid)=>{calls++;assert.notEqual(received,target);assert.deepEqual(received,target);validDuringDiscovery=valid;await new Promise(resolve=>finish=resolve);}});
 const button=host.children[0].children[1];
 fresh=false;await button.onclick();assert.equal(calls,0);
 fresh=true;isBusy=true;await button.onclick();assert.equal(calls,0);
 isBusy=false;const pendingClick=button.onclick();assert.equal(calls,1);assert.equal(button.disabled,true);await button.onclick();assert.equal(calls,1);
 assert.equal(validDuringDiscovery(),true);tool.dispose();assert.equal(validDuringDiscovery(),false);finish();await pendingClick;assert.equal(button.disabled,true);assert.equal(host.children[0].removed,true);assert.deepEqual(errors,[]);
}finally{if(previousDocument===undefined)delete globalThis.document;else globalThis.document=previousDocument;}
const proof={cases:cases.length,refusals,navigation_lifecycle_passed:true,inputs_unchanged:true,gameplay_verified:false};if(process.argv[4])writeFileSync(process.argv[4],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
