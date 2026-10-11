import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {scriptedGroupSelection} from '../editor/worldmap-scripted-group-selection.js';
const row=JSON.parse(readFileSync(process.argv[2],'utf8'))[0],source=row.source,entities=row.proposed.scene_graph.entities.filter(e=>e.placement_scope==='authored_scripted_seed');
// Proposed transforms are deliberately different: use immutable Current allocations
// and their UUID/native identity to construct the selection witnesses.
const current=entities.map(e=>({...e,authored_placement:source.authored_scripted_placements.find(a=>a.placement_id===e.authored_placement.placement_id)})),ids=current.map(e=>e.authored_placement.placement_id).sort(),held=JSON.stringify({source,current});
assert.deepEqual(scriptedGroupSelection(source,[],current,'replace'),ids);
assert.deepEqual(scriptedGroupSelection(source,[ids[0]],[current.find(e=>e.authored_placement.placement_id===ids[1])],'add'),ids);
assert.deepEqual(scriptedGroupSelection(source,ids,[current.find(e=>e.authored_placement.placement_id===ids[0])],'toggle'),[ids[1]]);
assert.deepEqual(scriptedGroupSelection(source,ids,[],'replace'),[]);
assert.deepEqual(scriptedGroupSelection(source,ids,[],'add'),ids);
assert.deepEqual(scriptedGroupSelection(source,[],[current[0],current[0]],'replace'),[current[0].authored_placement.placement_id]);
for(const mutate of [e=>e.placement_scope='source_spawn_seed',e=>e.authored_placement_kind='decoration',e=>e.native_entity_id='foreign',e=>e.entity_id='foreign',e=>e.authored_placement.script_id='foreign',e=>e.authored_placement.native_seed.source_position.y++]){const e=structuredClone(current[0]);mutate(e);assert.throws(()=>scriptedGroupSelection(source,[],[e],'replace'));}
for(const old of [['foreign'],[ids[0],ids[0]],Array(33).fill(ids[0])])assert.throws(()=>scriptedGroupSelection(source,old,current,'add'));
assert.throws(()=>scriptedGroupSelection(source,ids,current,'unknown'));
assert.throws(()=>scriptedGroupSelection({...source,binding:null},ids,current,'add'));
assert.throws(()=>scriptedGroupSelection(source,[],entities,'replace'));
assert.throws(()=>scriptedGroupSelection(source,[],Array(513).fill(current[0]),'replace'));
assert.throws(()=>scriptedGroupSelection({...source,authored_scripted_placements:Array(33).fill(source.authored_scripted_placements[0])},[],current,'replace'));
assert.equal(JSON.stringify({source,current}),held);console.log('Scripted group viewport selection: six selection cases and fourteen owner/scope/budget refusals pass; inputs unchanged.');
