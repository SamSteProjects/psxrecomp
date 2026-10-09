import assert from 'node:assert/strict';
import {assetInspectorDefinition,assetInspectorRegistry,renderAssetInspector} from '../editor/asset-inspector.js';
import {registeredActions,bindComponentActions} from '../editor/component-inspector.js';
const schema={schema_version:'legaia.inspector-schema.v1',live_writes:false,asset_inspectors:{model:'AssetModel'},components:{AssetModel:{layout:'read-only-properties',properties:[],actions:[{id:'inspect-asset-model',label:'Inspect model',capability:'model_preview'},{id:'inspect-asset-texture',label:'Wrong type',capability:'texture_preview'},{id:'write-ram',label:'Unknown',capability:'model_preview'}]}}};
const record={id:'asset://scene/models/1',type:'model'};let calls=0,current=true,busy=false;
assert.equal(assetInspectorDefinition(schema,record),'AssetModel');
const renderedSchema=structuredClone(schema);renderedSchema.components.AssetModel.label='Model <source>';renderedSchema.components.AssetModel.units='Native "units"';renderedSchema.components.AssetModel.details=[{label:'Source evidence',path:['data']}];const renderedRecord={...record,data:{evidence:'<script>unknown</script>'}};
const rendered=renderAssetInspector(renderedSchema,renderedRecord,{model_preview:true,texture_preview:true});assert(rendered.includes('data-inspector-component-section="AssetModel"'));assert(rendered.includes('data-asset-inspector="AssetModel"'));assert(rendered.includes('<h3>Model &lt;source&gt; <small>Native &quot;units&quot;</small></h3>'));assert(rendered.includes('Source evidence'));assert(rendered.includes('&lt;script&gt;'));assert(!rendered.includes('<script>'));assert(rendered.includes('data-inspector-action="inspect-asset-model"'));assert(!rendered.includes('Wrong type'));assert(!rendered.includes('Unknown'));assert(!rendered.includes('<input'));assert.equal(renderAssetInspector(schema,{type:'unknown'},{}),false);
for(const [type,id] of Object.entries({audio:'AssetAudio',actor:'AssetActor',scene:'AssetScene',template:'AssetTemplate',worldmap:'AssetWorldmap',model:'AssetModel',texture:'AssetTexture',animation:'AssetAnimation',controller:'AssetController',script:'AssetScript',dialogue:'AssetDialogue',flag:'AssetFlag',transition:'AssetTransition',collision:'AssetCollision',trigger:'AssetTrigger',region:'AssetRegion'})){const sample={schema_version:'legaia.inspector-schema.v1',live_writes:false,asset_inspectors:{[type]:id},components:{[id]:{label:type,layout:'read-only-properties',properties:[]}}};assert(renderAssetInspector(sample,{id:'asset://fixture/'+type,type},{}).includes(`data-asset-inspector="${id}"`));}
assert.equal(assetInspectorDefinition(schema,{type:'unknown'}),null);
const navigationSchema=structuredClone(schema);navigationSchema.components.AssetModel.properties=[{id:'id',path:['id'],label:'Identity',type:'asset-reference'},{id:'source',path:['source'],label:'Source scene',type:'asset-reference'}];const navigationRecord={...record,source:'scene://town01'};
const navigation=renderAssetInspector(navigationSchema,navigationRecord,{},()=>{},{referenceNavigation:true});assert(navigation.includes('data-component-reference="scene://town01"'));assert(!navigation.includes(`data-component-reference="${record.id}"`));assert(navigation.includes(`<code>${record.id}</code>`));assert(!renderAssetInspector(navigationSchema,navigationRecord,{}).includes('data-component-reference'));
assert.throws(()=>assetInspectorDefinition({...schema,asset_inspectors:{model:'Transform'}},record));
const registry=assetInspectorRegistry(record,item=>{assert.equal(item,record);calls++;});
const actions=registeredActions(schema,'AssetModel',record,{model_preview:true,texture_preview:true},registry,false);
assert.deepEqual(actions.map(row=>row.id),['inspect-asset-model']);assert.equal(actions[0].disabled,false);
assert.equal(registeredActions(schema,'AssetModel',record,{model_preview:false},registry,false).length,0);
const button={dataset:{inspectorAction:'inspect-asset-model'}};
bindComponentActions({querySelectorAll:()=>[button]},registry,{current:()=>current,editable:()=>false,busy:()=>busy,onError:e=>{throw e;}});
await button.onclick();assert.equal(calls,1);current=false;await button.onclick();assert.equal(calls,1);current=true;busy=true;await button.onclick();assert.equal(calls,1);
for(const type of ['texture','script','dialogue','flag','transition','collision'])assert.equal(Object.keys(assetInspectorRegistry({type},()=>{})).length,1);
for(const type of ['model','animation'])assert.deepEqual(Object.keys(assetInspectorRegistry({type},()=>{})).slice(0,2),['find-retail-asset-actors','find-current-asset-actors']);
const bindingSchema=structuredClone(schema);bindingSchema.components.AssetModel.actions=[{id:'find-retail-asset-actors',capability:'project_navigation'},{id:'find-current-asset-actors',capability:'project_navigation'}];
assert.equal(registeredActions(bindingSchema,'AssetModel',record,{project_navigation:true},registry,false).length,2);assert.equal(registeredActions(bindingSchema,'AssetModel',record,{project_navigation:false},registry,false).length,0);
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
assert.equal(assetInspectorDefinition(npcSchema,npc),'AssetNpcDraft');assert.deepEqual(Object.keys(assetInspectorRegistry(npc,()=>{})),['select-asset-actor','inspect-npc-donor-script','inspect-npc-build-script','inspect-npc-current-script','edit-npc-transitions','edit-npc-system-flags','edit-npc-branches','edit-npc-model-selectors','edit-npc-flags','reset-npc-script','edit-npc-effect-colors','edit-npc-dialogue','edit-npc-waits','edit-npc-facing','edit-npc-movement','edit-npc-appearance']);
for(const edit of [r=>r.id='scene://retail/actor',r=>r.sceneId='scene://other',r=>r.authoredRecord.draft='true',r=>r.authoredRecord.authored.name='Other',r=>r.authoredRecord.authored.donor_entity_id='other',r=>r.authoredRecord.authored.position.x=32]){const bad=structuredClone(npc);edit(bad);assert.throws(()=>assetInspectorDefinition(npcSchema,bad));}
assert.throws(()=>assetInspectorDefinition(schema,npc));
console.log('NPC authored asset classification, source/placement coherence and qualified donor-script action registry passed.');

const donorModel='asset://legaia/models/0011',linkedNpc=structuredClone(npc);
linkedNpc.authoredRecord.model_reference={source_id:npcId,source_name:'Resident',target_id:donorModel,scene_id:npc.sceneId,kind:'draft_initial_model_assignment',imported:false,effective:true,effective_donor_id:npc.authoredRecord.donor_entity_id,runtime_binding:'not_asserted'};
assert.equal(assetInspectorDefinition(npcSchema,linkedNpc),'AssetNpcDraft');
assert(Object.hasOwn(assetInspectorRegistry(linkedNpc,()=>{}),'inspect-npc-donor-model'));
for(const edit of [r=>r.target_id='guest://pointer',r=>r.effective_donor_id='other',r=>r.imported=true,r=>r.runtime_binding='observed',r=>r.source_id='other',r=>r.source_name='other']){const bad=structuredClone(linkedNpc);edit(bad.authoredRecord.model_reference);assert.throws(()=>assetInspectorDefinition(npcSchema,bad));}
console.log('NPC donor-model navigation requires a coherent recorded SDK assignment; unresolved assignments expose no model action.');

const linkedSchema={...npcSchema,components:{...npcSchema.components,AssetNpcDraft:{layout:'read-only-properties',properties:[],actions:[{id:'select-asset-actor',capability:'project_navigation'},{id:'inspect-npc-donor-model',capability:'model_preview',when:['authoredRecord','model_reference','target_id']}]}}},linkedRegistry=assetInspectorRegistry(linkedNpc,()=>{});
assert.deepEqual(registeredActions(linkedSchema,'AssetNpcDraft',linkedNpc,{project_navigation:true,model_preview:false},linkedRegistry,false).map(a=>a.id),['select-asset-actor']);
assert.equal(registeredActions(linkedSchema,'AssetNpcDraft',linkedNpc,{project_navigation:true,model_preview:true},linkedRegistry,false).length,2);

// Exercise the actual server descriptor, including every currently shipped NPC action.
if(process.argv[2]){
 const {readFileSync}=await import('node:fs');const serverSchema=JSON.parse(readFileSync(process.argv[2],'utf8'));
 const declared=serverSchema.components.AssetNpcDraft.actions;
 const capabilities=Object.fromEntries(declared.map(a=>[a.capability,true]));
 const actual=registeredActions(serverSchema,'AssetNpcDraft',linkedNpc,capabilities,linkedRegistry,false);
 assert.deepEqual(actual.map(a=>a.id),declared.map(a=>a.id));
 for(const id of ['inspect-npc-current-script','edit-npc-transitions','edit-npc-system-flags']){
  assert(Object.hasOwn(linkedRegistry,id));assert(!Object.hasOwn(assetInspectorRegistry({type:'actor'},()=>{}),id));
  assert.equal(registeredActions(serverSchema,'AssetNpcDraft',linkedNpc,{...capabilities,[declared.find(a=>a.id===id).capability]:false},linkedRegistry,false).some(a=>a.id===id),false);
 }
 const malformed=structuredClone(serverSchema);malformed.components.AssetNpcDraft.actions.push({...declared[0]});
 assert.throws(()=>registeredActions(malformed,'AssetNpcDraft',linkedNpc,capabilities,linkedRegistry,false));
 malformed.components.AssetNpcDraft.actions=Array.from({length:33},(_,i)=>({id:'unknown-'+i,capability:'none'}));
 assert.throws(()=>registeredActions(malformed,'AssetNpcDraft',linkedNpc,capabilities,linkedRegistry,false));
 console.log('Actual NPC Asset Details schema actions, donor gating, capability filtering and bounded/duplicate refusal passed.');
}

const editSchema=structuredClone(schema);editSchema.components.AssetModel.actions=[{id:'edit-asset-materials',label:'Edit material bindings',capability:'model_material_authoring',requires_edit:true}];
assert.equal(registeredActions(editSchema,'AssetModel',record,{model_material_authoring:true},registry,false)[0].disabled,true);
assert.equal(registeredActions(editSchema,'AssetModel',record,{model_material_authoring:true},registry,true)[0].disabled,false);
assert.equal(registeredActions(editSchema,'AssetModel',record,{model_material_authoring:false},registry,true).length,0);
assert.equal(assetInspectorRegistry({type:'texture'},()=>{})['edit-asset-materials'],undefined);
const editButton={dataset:{inspectorAction:'edit-asset-materials',inspectorComponent:'AssetModel',inspectorEdit:'true'},disabled:false};let editMode=false,edited=0;
bindComponentActions({querySelectorAll:()=>[editButton]},assetInspectorRegistry(record,()=>edited++),{current:()=>true,editable:()=>editMode,busy:()=>false,onError:e=>{throw e;}});
await editButton.onclick();assert.equal(edited,0);editMode=true;await editButton.onclick();assert.equal(edited,1);editMode=false;await editButton.onclick();assert.equal(edited,1);
console.log('Model material action requires explicit Edit eligibility and capability; texture assets and mode changes cannot dispatch it.');
