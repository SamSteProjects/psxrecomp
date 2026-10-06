import assert from 'node:assert/strict';
import {renderEnvironmentInspector} from '../editor/environment-inspector.js';
const ids=['EnvironmentPlacement','EnvironmentRetailTransform','EnvironmentPreviewTransform','EnvironmentMetadata'];
const definition=(label,path,state)=>({label,layout:'read-only-properties',properties:[{id:'value',label:'Value',path,type:'number',state}]});
const schema={schema_version:'legaia.inspector-schema.v1',live_writes:false,property_states:{'read-only-retail':{label:'Retail',note:'Recorded source'},effective:{label:'Effective',note:'Preview value'}},components:{
 EnvironmentPlacement:definition('Placement',['entity_id'],'read-only-retail'),
 EnvironmentRetailTransform:definition('Retail transform',['source_record','imported_transform','position','x'],'read-only-retail'),
 EnvironmentPreviewTransform:definition('Current preview transform',['effective_transform','position','x'],'effective'),
 EnvironmentMetadata:{...definition('Source and bindings',['source_record','source_record','map_sha256'],'read-only-retail'),details:[{label:'Source',path:['source_record']},{label:'Evidence',path:['evidence']}]}}};
const environment={kind:'environment',entity_id:'environment://fixture/decorations/00001',source_record:{imported_transform:{position:{x:100}},source_record:{map_sha256:'<source>'}},effective_transform:{position:{x:164}},evidence:{unknown:'<script>'}};
const before=structuredClone(environment),html=renderEnvironmentInspector(schema,environment,true);
for(const id of ids)assert(html.includes(`data-environment-component="${id}"`));
assert(html.includes('<code>100</code>'));assert(html.includes('<code>164</code>'));assert(html.includes('data-property-state="read-only-retail"'));assert(html.includes('data-property-state="effective"'));
assert(html.includes('&lt;script&gt;'));assert(!html.includes('<script>'));assert(html.includes('id="frame-environment"'));assert(!html.includes('<input'));assert(!html.includes('refresh pending'));assert.deepEqual(environment,before);
assert(renderEnvironmentInspector(schema,environment,false).includes('Previous preview snapshot'));
const missing=renderEnvironmentInspector(schema,{...environment,effective_transform:{}},true);assert(missing.includes('<code>—</code>'));assert.equal((missing.match(/<code>100<\/code>/g)??[]).length,1);
assert.throws(()=>renderEnvironmentInspector(schema,{kind:'actor'},true));assert.throws(()=>renderEnvironmentInspector(schema,environment,null));
assert.throws(()=>renderEnvironmentInspector({...schema,components:{...schema.components,EnvironmentPlacement:{...schema.components.EnvironmentPlacement,properties:[{id:'x',authoring:{}}]}}},environment,true));
console.log('SDK environment snapshot sections, separate retail/current values, escaping, unknowns and stale preview labels passed.');
