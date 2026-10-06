import assert from 'node:assert/strict';
import {assetInspectorDefinition,assetInspectorRegistry} from '../editor/asset-inspector.js';
import {registeredActions,bindComponentActions} from '../editor/component-inspector.js';
const schema={schema_version:'legaia.inspector-schema.v1',live_writes:false,asset_inspectors:{model:'AssetModel'},components:{AssetModel:{layout:'read-only-properties',properties:[],actions:[{id:'inspect-asset-model',label:'Inspect model',capability:'model_preview'},{id:'inspect-asset-texture',label:'Wrong type',capability:'texture_preview'},{id:'write-ram',label:'Unknown',capability:'model_preview'}]}}};
const record={id:'asset://scene/models/1',type:'model'};let calls=0,current=true,busy=false;
assert.equal(assetInspectorDefinition(schema,record),'AssetModel');
assert.equal(assetInspectorDefinition(schema,{type:'unknown'}),null);
assert.throws(()=>assetInspectorDefinition({...schema,asset_inspectors:{model:'Transform'}},record));
const registry=assetInspectorRegistry(record,item=>{assert.equal(item,record);calls++;});
const actions=registeredActions(schema,'AssetModel',record,{model_preview:true,texture_preview:true},registry,false);
assert.deepEqual(actions.map(row=>row.id),['inspect-asset-model']);assert.equal(actions[0].disabled,false);
assert.equal(registeredActions(schema,'AssetModel',record,{model_preview:false},registry,false).length,0);
const button={dataset:{inspectorAction:'inspect-asset-model'}};
bindComponentActions({querySelectorAll:()=>[button]},registry,{current:()=>current,editable:()=>false,busy:()=>busy,onError:e=>{throw e;}});
await button.onclick();assert.equal(calls,1);current=false;await button.onclick();assert.equal(calls,1);current=true;busy=true;await button.onclick();assert.equal(calls,1);
for(const type of ['texture','animation','script','dialogue','flag','transition','collision'])assert.equal(Object.keys(assetInspectorRegistry({type},()=>{})).length,1);
assert.deepEqual(Object.keys(assetInspectorRegistry({type:'region'},()=>{})),['inspect-asset-field','inspect-asset-region-bounds']);
assert.deepEqual(Object.keys(assetInspectorRegistry({type:'trigger'},()=>{})),['inspect-asset-field','inspect-asset-trigger-cells']);
assert.deepEqual(Object.keys(assetInspectorRegistry({type:'trigger',id:'trigger://fixture/field-map/primary/kind-1/0000',data:{table_source:'primary',table_kind:1,encoded:{gate:1}}},()=>{})),['inspect-asset-field','inspect-asset-trigger-cells','inspect-asset-trigger-scripts','inspect-asset-trigger-group']);
for(const type of ['actor','scene','template'])assert.equal(Object.keys(assetInspectorRegistry({type},()=>{})).length,1);
const landmark={id:'worldmap://fixture/1',type:'worldmap',data:{destination_source_label:'town01'}};
const wmDefinition={layout:'read-only-properties',properties:[],actions:[{id:'open-asset-worldmap',capability:'worldmap_source_navigation'},{id:'inspect-landmark-destination',capability:'worldmap_source_navigation',when:['data','destination_source_label']}]};
const wmSchema={schema_version:'legaia.inspector-schema.v1',live_writes:false,components:{AssetWorldmap:wmDefinition}},wmRegistry=assetInspectorRegistry(landmark,(record,id)=>{assert.equal(record,landmark);return id;});
assert.deepEqual(registeredActions(wmSchema,'AssetWorldmap',landmark,{worldmap_source_navigation:true},wmRegistry,false).map(a=>a.id),['open-asset-worldmap','inspect-landmark-destination']);
assert.equal(registeredActions(wmSchema,'AssetWorldmap',{...landmark,data:{}},{worldmap_source_navigation:true},wmRegistry,false).length,1);
assert.equal(registeredActions(wmSchema,'AssetWorldmap',landmark,{worldmap_source_navigation:false},wmRegistry,false).length,0);
assert.equal(await wmRegistry['inspect-landmark-destination'].run(),'inspect-landmark-destination');
assert.equal(Object.keys(assetInspectorRegistry({type:'unknown'},()=>{})).length,0);
console.log('Asset inspector descriptor/type registry, capability filtering and stale/busy read-only dispatch passed.');

const npcId='authored-actor://00000000-0000-4000-8000-000000000001',npc={id:npcId,type:'actor',sceneId:'scene://town01',authoredRecord:{id:npcId,kind:'actor',draft:true,name:'Resident',scene_id:'scene://town01',donor_entity_id:'scene://town01/actors/man-p1/0011',authored:{name:'Resident',scene_id:'scene://town01',donor_entity_id:'scene://town01/actors/man-p1/0011',position:{x:128,z:256}}}},npcSchema={...schema,authored_asset_inspectors:{npc_draft:'AssetNpcDraft'}};
assert.equal(assetInspectorDefinition(npcSchema,npc),'AssetNpcDraft');assert.deepEqual(Object.keys(assetInspectorRegistry(npc,()=>{})),['select-asset-actor']);
for(const edit of [r=>r.id='scene://retail/actor',r=>r.sceneId='scene://other',r=>r.authoredRecord.draft='true',r=>r.authoredRecord.authored.name='Other',r=>r.authoredRecord.authored.donor_entity_id='other',r=>r.authoredRecord.authored.position.x=32]){const bad=structuredClone(npc);edit(bad);assert.throws(()=>assetInspectorDefinition(npcSchema,bad));}
assert.throws(()=>assetInspectorDefinition(schema,npc));
console.log('NPC authored asset classification, source/placement coherence and selection-only action registry passed.');

const donorModel='asset://legaia/models/0011',linkedNpc=structuredClone(npc);
linkedNpc.authoredRecord.model_reference={source_id:npcId,source_name:'Resident',target_id:donorModel,scene_id:npc.sceneId,kind:'draft_initial_model_assignment',imported:false,effective:true,effective_donor_id:npc.authoredRecord.donor_entity_id,runtime_binding:'not_asserted'};
assert.equal(assetInspectorDefinition(npcSchema,linkedNpc),'AssetNpcDraft');
assert(Object.hasOwn(assetInspectorRegistry(linkedNpc,()=>{}),'inspect-npc-donor-model'));
for(const edit of [r=>r.target_id='guest://pointer',r=>r.effective_donor_id='other',r=>r.imported=true,r=>r.runtime_binding='observed',r=>r.source_id='other',r=>r.source_name='other']){const bad=structuredClone(linkedNpc);edit(bad.authoredRecord.model_reference);assert.throws(()=>assetInspectorDefinition(npcSchema,bad));}
console.log('NPC donor-model navigation requires a coherent recorded SDK assignment; unresolved assignments expose no model action.');

const linkedSchema={...npcSchema,components:{...npcSchema.components,AssetNpcDraft:{layout:'read-only-properties',properties:[],actions:[{id:'select-asset-actor',capability:'project_navigation'},{id:'inspect-npc-donor-model',capability:'model_preview',when:['authoredRecord','model_reference','target_id']}]}}},linkedRegistry=assetInspectorRegistry(linkedNpc,()=>{});
assert.deepEqual(registeredActions(linkedSchema,'AssetNpcDraft',linkedNpc,{project_navigation:true,model_preview:false},linkedRegistry,false).map(a=>a.id),['select-asset-actor']);
assert.equal(registeredActions(linkedSchema,'AssetNpcDraft',linkedNpc,{project_navigation:true,model_preview:true},linkedRegistry,false).length,2);
