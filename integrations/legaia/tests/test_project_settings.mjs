import assert from 'node:assert/strict';
import {projectNameCommand} from '../editor/project-settings.js';
const schema={schema_version:'legaia.inspector-schema.v1',live_writes:false,components:{ProjectSettings:{properties:[{id:'name',type:'string',authoring:{minimum_length:1,maximum_length:120,set_command:'rename_project'}}]}}},settings={name:'Old',review_key:'a'.repeat(64)};
assert.deepEqual(projectNameCommand(schema,settings,'  New "Name"  '),{type:'rename_project',name:'New "Name"',review_key:settings.review_key});
for(const name of ['',true,'x'.repeat(121),'new\nname','\x7f','\ud800'])assert.throws(()=>projectNameCommand(schema,settings,name));
const bad=structuredClone(schema);bad.components.ProjectSettings.properties[0].authoring.set_command='write_ram';assert.throws(()=>projectNameCommand(bad,settings,'Valid'));assert.throws(()=>projectNameCommand(schema,{...settings,review_key:'wrong'},'Valid'));
assert.deepEqual(settings,{name:'Old',review_key:'a'.repeat(64)});console.log('Project name bounded command, Unicode text, quotes, control characters and metadata whitelist passed.');

assert.equal(projectNameCommand(schema,settings,'Unicode \u{1f680}').name,'Unicode \u{1f680}');
