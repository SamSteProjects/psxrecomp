import assert from 'node:assert/strict';
import {renderComponentProperties,propertyCommand,renderUnregisteredComponents,renderComponentDetails,registeredActions,renderComponentActions,bindComponentActions} from '../editor/component-inspector.js';
const schema={schema_version:'legaia.inspector-schema.v1',live_writes:false,components:{Transform:{layout:'layered-number',layers:['imported','authored','effective'],notes:['Unknown <height>'],properties:['x','y','z'].map(id=>({id,label:id.toUpperCase(),path:['position',id],type:'number',retail_status:id==='y'?'unresolved':'imported',build:{note:'Build constraint'},authoring:{minimum:-32767,maximum:32767,step:'any',set_command:'set_transform',clear_command:'clear_transform'}}))}}};
const component={imported:{position:{x:64,y:null,z:128}},authored:{position:{x:192}},effective:{position:{x:192,y:null,z:128}}};
const html=renderComponentProperties(schema,'Transform',component,true);
assert(html.includes('value="192"'));assert(html.includes('Retail value unresolved'));assert(html.includes('Unknown &lt;height&gt;'));assert(!html.includes('disabled'));
assert(renderComponentProperties(schema,'Transform',component,false).includes('disabled'));
assert.deepEqual(propertyCommand(schema,'Transform','x','actor','256'),{type:'set_transform',entity_id:'actor',position:{x:256}});
assert.deepEqual(propertyCommand(schema,'Transform','y','actor',''),{type:'clear_transform',entity_id:'actor',axes:['y']});
for(const text of ['NaN','Infinity','32768',' ','-32768'])assert.throws(()=>propertyCommand(schema,'Transform','x','actor',text));
assert.throws(()=>propertyCommand(schema,'Transform','w','actor','1'));
const bad=structuredClone(schema);bad.components.Transform.properties[0].authoring.set_command='write_ram';assert.throws(()=>propertyCommand(bad,'Transform','x','actor','1'));
assert.throws(()=>renderComponentProperties({...schema,live_writes:true},'Transform',component));
console.log('Metadata inspector layers, unknown values, read-only mode, escaped text and bounded command adapter passed.');

const fallback=renderUnregisteredComponents({...schema,unknown_component_policy:'read-only-details'},{Unknown:{value:'<script>alert(1)</script>'},Transform:component},['Transform']);
assert(fallback.includes('Read only'));assert(fallback.includes('&lt;script&gt;'));assert(!fallback.includes('<input'));assert(!fallback.includes('<button'));assert(!fallback.includes('<script>'));

const layered=structuredClone(schema);layered.components.Appearance={layout:'layered-properties',layers:[{id:'imported',label:'Retail'},{id:'authored',label:'Authored'},{id:'effective',label:'Effective'}],properties:[{id:'asset',label:'Asset',path:['asset'],layers:['imported','effective']},{id:'donor',label:'Donor',path:['donor'],layers:['authored'],empty_label:'Inherit'}]};
const appearance=renderComponentProperties(layered,'Appearance',{imported:{asset:'retail'},authored:{},effective:{asset:'replacement'}});
assert(appearance.includes('retail'));assert(appearance.includes('replacement'));assert(appearance.includes('Inherit'));assert(!appearance.includes('<input'));
layered.components.Runtime={layout:'read-only-properties',properties:[{id:'status',label:'Status',path:['status'],fallback_paths:[['state']],empty_label:'Unknown'},{id:'confirmed',label:'Confirmed',path:['confirmed']}],details:[{label:'Evidence',path:[]}]};
assert(renderComponentProperties(layered,'Runtime',{state:'candidate',confirmed:false}).includes('false'));
assert(renderComponentProperties(layered,'Runtime',{}).includes('Unknown'));
assert(renderComponentDetails(layered,'Runtime',{evidence:'<b>retail</b>'}).includes('&lt;b&gt;'));
assert.throws(()=>propertyCommand(layered,'Appearance','donor','actor','evil'));
console.log('Layered donor references, runtime unknown/false states and escaped SDK details passed.');

const actionsSchema=structuredClone(layered);actionsSchema.components.Appearance.actions=[{id:'choose',label:'Choose <donor>','capability':'donors',requires_edit:false},{id:'preview',label:'Preview','capability':'donors',when:['authored','donor']},{id:'unknown',label:'Unsafe','capability':'donors'}];
let calls=0,current=true,editing=true,isBusy=false,allowed=true,errors=[];
const registry={choose:{requiresEdit:true,canRun:()=>allowed,run:()=>{calls++;}},preview:{run:()=>{calls++;}}};
assert.equal(registeredActions(actionsSchema,'Appearance',{authored:{}},{donors:true},registry,true).length,1);
const actionHTML=renderComponentActions(actionsSchema,'Appearance',{authored:{donor:'source'}},{donors:true},registry,false);
assert(actionHTML.includes('disabled'));assert(actionHTML.includes('Choose &lt;donor&gt;'));assert(!actionHTML.includes('Unsafe'));
assert.equal(registeredActions(actionsSchema,'Appearance',{}, {donors:false},registry,true).length,0);
const button={dataset:{inspectorAction:'choose'}},root={querySelectorAll:()=>[button]};bindComponentActions(root,registry,{current:()=>current,editable:()=>editing,busy:()=>isBusy,onError:e=>errors.push(e.message)});
await button.onclick();assert.equal(calls,1);
for(const field of ['current','editing','isBusy','allowed']){current=true;editing=true;isBusy=false;allowed=true;if(field==='current')current=false;if(field==='editing')editing=false;if(field==='isBusy')isBusy=true;if(field==='allowed')allowed=false;await button.onclick();assert.equal(calls,1);}
console.log('Registered actions filter capabilities/conditions/unknown handlers and guard Edit/busy/stale dispatch.');

const animationSchema=structuredClone(actionsSchema);animationSchema.components.Animation={layout:'read-only-properties',properties:[],actions:[{id:'author',label:'Author animation channels',capability:'authoring',requires_edit:true,when:['preview_support','supported']},{id:'scene',label:'Preview imported scene animation',capability:'preview',when:['preview_support','supported']}]};
const animationRegistry={author:{requiresEdit:true,run:()=>{}},scene:{run:()=>{}}};
assert.equal(registeredActions(animationSchema,'Animation',{preview_support:{supported:false}},{authoring:true,preview:true},animationRegistry,true).length,0);
const animationActions=registeredActions(animationSchema,'Animation',{preview_support:{supported:true}},{authoring:true,preview:true},animationRegistry,false);
assert(animationActions.find(action=>action.id==='author').disabled);assert(!animationActions.find(action=>action.id==='scene').disabled);
console.log('Animation action eligibility separates imported-source support, preview availability and Edit-only authoring.');
const retainedSchema=structuredClone(animationSchema);retainedSchema.components.Retained={layout:'read-only-properties',properties:[{id:'record',label:'Retained clip',path:['authored','record_id'],empty_label:'Inherited/imported'},{id:'model',label:'Captured model',path:['authored','model_asset_id'],type:'asset-reference'},{id:'verified',label:'Gameplay verified',path:['gameplay_verified']}],actions:[{id:'manage',label:'Manage allocated clips',capability:'assignment',requires_edit:true},{id:'preview',label:'Preview allocated initial animation',capability:'assignment',when:['authored','record_id']}]};
const retainedRegistry={manage:{requiresEdit:true,run:()=>{}},preview:{run:()=>{}}},retained={authored:{record_id:'uuid',model_asset_id:'asset://town01/models/scene-tmd/0105'},gameplay_verified:false};
assert(renderComponentProperties(retainedSchema,'Retained',{authored:null,gameplay_verified:false},false,true).includes('Inherited/imported'));const retainedHTML=renderComponentProperties(retainedSchema,'Retained',retained,false,true);assert(retainedHTML.includes('data-component-reference="asset://town01/models/scene-tmd/0105"'));assert(retainedHTML.includes('false'));assert(!retainedHTML.includes('<input'));
assert.equal(registeredActions(retainedSchema,'Retained',{authored:null},{assignment:true},retainedRegistry,true).length,1);const retainedActions=registeredActions(retainedSchema,'Retained',retained,{assignment:true},retainedRegistry,false);assert(retainedActions.find(a=>a.id==='manage').disabled);assert(!retainedActions.find(a=>a.id==='preview').disabled);assert.equal(registeredActions(retainedSchema,'Retained',retained,{assignment:false},retainedRegistry,true).length,0);
console.log('Retained assignment metadata preserves inherited/false values, model navigation and capability/Edit separation.');
let contextReceived;const contextualButton={dataset:{inspectorAction:'inspect',inspectorComponent:'ScriptWaits'}};bindComponentActions({querySelectorAll:()=>[contextualButton]},{inspect:{run:context=>contextReceived=context}},{current:()=>true,editable:()=>false,busy:()=>false,onError:error=>{throw error;}});await contextualButton.onclick();assert.deepEqual(contextReceived,{componentId:'ScriptWaits',actionId:'inspect'});assert(renderComponentActions(retainedSchema,'Retained',retained,{assignment:true},retainedRegistry,true).includes('data-inspector-component="Retained"'));
console.log('Registered action dispatch carries escaped component identity without changing mutation eligibility.');
