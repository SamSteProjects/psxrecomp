import assert from 'node:assert/strict';
import {assetReferenceInstructionSite,qualifyAssetReferenceInstructionSite,openAssetReferences} from '../editor/asset-references.js';
const hash='a'.repeat(64),catalogKey='b'.repeat(64),scene='scene://fixture',script='script://fixture/actors/man-p1/0001',target='dialogue://fixture/0001/000a';
const source={id:script,kind:'script',scene_id:scene,available:true,label:'Source script'},dialogue={id:target,kind:'dialogue',scene_id:scene,available:true,label:'Dialogue'};
const nodes=new Map([[script,source],[target,dialogue]]),edge={id:'c'.repeat(64),source_id:script,target_id:target,kind:'script_dialogue_segment',scene_id:scene,layer:'decoded',pc:10,runtime_binding:'not_asserted',source_import_sha256:hash,source_catalog_key:catalogKey};
const site=assetReferenceInstructionSite(edge,nodes);
assert.deepEqual(site,{script_id:script,owner_id:'scene://fixture/actors/man-p1/0001',scene_id:scene,partition:1,record_index:1,pc:10,source_catalog_key:catalogKey,source_import_sha256:hash,source_record_sha256:null});
const record={semantic_id:script,script_id:script,asset_kind:'script',owner_semantic_id:site.owner_id,partition:1,source_record:{partition:1,record_index:1,byte_length:30,sha256:'d'.repeat(64)}};
const qualified=qualifyAssetReferenceInstructionSite(site,record,catalogKey);qualified.pc=0;assert.equal(site.pc,10);
for(const mutate of [e=>e.pc=true,e=>e.pc=65536,e=>e.kind='initial_model',e=>e.layer='imported',e=>e.scene_id='scene://other',e=>e.source_catalog_key='bad',e=>e.runtime_binding='confirmed']){const value=structuredClone(edge);mutate(value);assert.equal(assetReferenceInstructionSite(value,nodes),null);}
assert.equal(assetReferenceInstructionSite(edge,new Map([[script,{...source,available:false}],[target,dialogue]])),null);
assert.equal(assetReferenceInstructionSite(edge,new Map([[script,source],[target,{...dialogue,kind:'model'}]])),null);
for(const mutate of [s=>s.owner_id+='x',s=>s.pc=30,s=>s.partition=2,s=>s.record_index=2,s=>s.scene_id='scene://other',s=>s.source_record_sha256='e'.repeat(64)]){const value=structuredClone(site);mutate(value);assert.throws(()=>qualifyAssetReferenceInstructionSite(value,record,catalogKey));}
assert.throws(()=>qualifyAssetReferenceInstructionSite(site,record,hash));assert.throws(()=>qualifyAssetReferenceInstructionSite(site,{...record,source_record:{...record.source_record,byte_length:10}},catalogKey));
const p2='script://fixture/scripts/man-p2/0004',p2Source={...source,id:p2,scene_ids:[scene],navigable_scene_ids:[scene]},p2Edge={...edge,source_id:p2};
const p2Site=assetReferenceInstructionSite(p2Edge,new Map([[p2,p2Source],[target,dialogue]]),'project');assert.equal(p2Site.partition,2);assert.equal(p2Site.record_index,4);
assert.equal(assetReferenceInstructionSite(p2Edge,new Map([[p2,{...p2Source,navigable_scene_ids:[],available:false}],[target,dialogue]]),'project'),null);
for(const [kind,targetKind] of [['encoded_scene_change','scene'],['script_flag_reference','flag'],['script_transition_reference','transition']]){
 const eligible=assetReferenceInstructionSite({...edge,kind},new Map([[script,source],[target,{...dialogue,kind:targetKind,available:false}]]));assert.equal(eligible.pc,10);
}
const hashed=assetReferenceInstructionSite({...edge,kind:'script_transition_reference',transition_reference_evidence:{source_record_sha256:record.source_record.sha256}},new Map([[script,source],[target,{...dialogue,kind:'transition'}]]));assert.equal(qualifyAssetReferenceInstructionSite(hashed,record,catalogKey).source_record_sha256,record.source_record.sha256);
class Element{
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.events={};this.textContent='';this.open=false;this.value='';}
 append(...items){for(const item of items){if(this.tagName==='select'&&!this.children.length&&item.tagName==='option')this.value=item.value;item.parent=this;this.children.push(item);}}
 replaceChildren(...items){this.children=[];this.append(...items);}
 get isConnected(){return this===globalThis.document.body||!!this.parent?.isConnected&&this.parent.children.includes(this);}
 contains(item){return item===this||this.children.some(child=>child.contains(item));}
 setAttribute(name,value){this[name]=value;}
 addEventListener(name,callback){this.events[name]=callback;}
 showModal(){this.open=true;}
 close(){this.open=false;this.events.close?.();}
 remove(){if(this.parent)this.parent.children=this.parent.children.filter(item=>item!==this);}
}
const tree=node=>[node,...node.children.flatMap(tree)],body=new Element('body');globalThis.document={body,createElement:tag=>new Element(tag)};
const report={schema_version:'legaia.asset-references.v1',asset_id:script,source_key:hash,read_only:true,nodes:[source,dialogue],incoming:[],outgoing:[edge],coverage:{verified_scene_ids:[scene],resource_scene_id:scene,unresolved_reference_count:1},limitations:['Source only']};
let state={asset_reference_source_key:hash,capabilities:{asset_references:true}},busy=false,selected=[],neighbors=[],errors=[];
globalThis.fetch=async()=>({ok:true,json:async()=>structuredClone(report)});
const mount=()=>openAssetReferences({record:{id:script,label:'Source'},getState:()=>state,busy:()=>busy,onNavigate:node=>neighbors.push(node),onInspectInstruction:value=>selected.push(value),onError:error=>errors.push(error.message)});
const flush=()=>new Promise(resolve=>setTimeout(resolve,0));
let view=mount();await flush();let inspect=tree(view).find(item=>item.dataset.referenceInstruction);assert.ok(inspect);await inspect.onclick();assert.deepEqual(selected,[site]);assert.deepEqual(neighbors,[]);assert.equal(view.open,false);await inspect.onclick();assert.equal(selected.length,1);
view=mount();await flush();inspect=tree(view).find(item=>item.dataset.referenceInstruction);busy=true;await inspect.onclick();assert.equal(view.open,true);assert.equal(selected.length,1);busy=false;state={...state,asset_reference_source_key:'f'.repeat(64)};await inspect.onclick();assert.equal(view.open,true);assert.equal(selected.length,1);view.close();state.asset_reference_source_key=hash;
view=mount();await flush();
const oldInstruction=tree(view).find(item=>item.dataset.referenceInstruction),oldTarget=tree(view).find(item=>item.dataset.referenceTarget),oldExplore=tree(view).find(item=>item.dataset.exploreReferenceTarget),search=tree(view).find(item=>item['aria-label']==='Search recorded references');
search.value='No matching identity';search.oninput();
for(const button of [oldInstruction,oldTarget,oldExplore])await button.onclick();
assert.equal(view.open,true);assert.equal(selected.length,1);assert.equal(neighbors.length,0);
search.value='';search.oninput();assert.ok(tree(view).find(item=>item.dataset.referenceInstruction));
// Even an un-dispatched control value change invalidates a retained row.
inspect=tree(view).find(item=>item.dataset.referenceInstruction);search.value='Changed before event';await inspect.onclick();assert.equal(selected.length,1);view.close();
view=mount();await flush();inspect=tree(view).find(item=>item.dataset.referenceInstruction);view.remove();await inspect.onclick();assert.equal(selected.length,1);view.close();
let resolve;globalThis.fetch=()=>new Promise(done=>resolve=done);view=mount();view.close();resolve({ok:true,json:async()=>structuredClone(report)});await flush();assert.equal(tree(view).some(item=>item.dataset.referenceInstruction),false);assert.deepEqual(errors,[]);
console.log('Asset reference instruction sites: qualified P1/P2 identity, source refresh, targets, stale/busy/close/late-response and exactly-once navigation pass');
