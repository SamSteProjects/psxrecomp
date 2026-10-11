import assert from 'node:assert/strict';
import fs from 'node:fs';
import {qualifyWorldDecorationSource,worldDecorationGroupSelection} from '../editor/worldmap-decoration-state.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let cases=0;
for(const row of rows){
  const source=await qualifyWorldDecorationSource(row.source,row.current,row.review.project_path),entities=row.current.scene_graph.entities.filter(e=>e.placement_scope==='authored_spawn_seed'),held=JSON.stringify([source,entities]);
  const a=entities[0],b=entities[1],first=worldDecorationGroupSelection(source,[],a),both=worldDecorationGroupSelection(source,first,b,'add');
  assert.deepEqual(first,[a.authored_placement.placement_id]);assert.deepEqual(both,row.review.placement_ids);
  assert.deepEqual(worldDecorationGroupSelection(source,both,b,'add'),both);assert.deepEqual(worldDecorationGroupSelection(source,both,a),[b.authored_placement.placement_id]);assert.deepEqual(worldDecorationGroupSelection(source,first,a),[]);
  for(const [ids,e,mode] of [[['foreign'],a,'toggle'],[[first[0],first[0]],a,'toggle'],[[],{...a,placement_scope:'source_spawn_seed'},'toggle'],[[],{...a,entity_id:'foreign'},'toggle'],[[],{...a,authored_placement:{...a.authored_placement,record_index:4}},'toggle'],[[],a,'replace']])assert.throws(()=>worldDecorationGroupSelection(source,ids,e,mode));
  assert.equal(JSON.stringify([source,entities]),held);cases++;
}
const rows32=Array.from({length:33},(_,i)=>({placement_id:`placement://authored/00000000-0000-4000-8000-${String(i).padStart(12,'0')}`,target_cell:i,record_index:i+4})),source={metadata:{scene:'map01',authored_allocations:rows32}},entity={placement_scope:'authored_spawn_seed',authored_placement:rows32[32],entity_id:'scene://map01/worldmap/authored-placements/'+rows32[32].placement_id.split('/').pop()},ids=rows32.slice(0,32).map(r=>r.placement_id);
assert.throws(()=>worldDecorationGroupSelection(source,ids,entity));assert.equal(ids.length,32);assert.equal(worldDecorationGroupSelection(source,[],entity,'add').length,1);
assert.equal(cases,3);console.log('Three actual source-bound selection workflows, foreign/duplicate ownership refusals and atomic 32-member limit passed.');
