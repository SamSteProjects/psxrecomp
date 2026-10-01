import assert from 'node:assert/strict';
import {renderComponentProperties,propertyCommand,renderUnregisteredComponents,renderComponentDetails} from '../editor/component-inspector.js';
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
