import assert from 'node:assert/strict';
import {decodeDraftRepeatScene,draftRepeatPosition} from '../editor/draft-repeat.js';
const original={entity_id:'original',position:{x:128,y:null,z:256}},base={scene_id:'scene',source_key:'source',position_to_display:[1],assets:[{geometry_key:'g',asset_id:'a'}],entities:[original]},draft={scene_id:'scene',name:'Copy 001',donor_entity_id:'donor',position:{x:192,z:256}},report={scene_id:'scene',review_key:'review',copies:[{entity_id:'new',draft}]};
const scene={...structuredClone(base),schema:'legaia.scene-preview.v1',representation:'authored',entities:[structuredClone(original),{entity_id:'new',kind:'actor_draft',name:draft.name,donor_entity_id:'donor',source_actor_id:'donor',position:{x:192,z:256,y:null},preview_position:{x:192,z:256,y:12},display_position:{x:192,z:256,y:-12},renderable:true,geometry_key:'g',asset_id:'a'}]};
const response={schema_version:'legaia.draft-repeat-scene.v1',project_source_key:'source',review_key:'review',scene_id:'scene',scene},before=structuredClone(response);const decoded=decodeDraftRepeatScene(response,report,base);decoded.entities[0].position.x=0;assert.deepEqual(response,before);
for(const change of [r=>r.review_key='stale',r=>r.project_source_key='stale',r=>r.scene.entities[0].position.x=0,r=>r.scene.entities[1].position.x=0,r=>r.scene.entities[1].donor_entity_id='wrong',r=>r.scene.entities[1].display_position.y=12,r=>r.scene.assets=[],r=>r.scene.entities[1].entity_id='original']){const bad=structuredClone(response);change(bad);assert.throws(()=>decodeDraftRepeatScene(bad,report,base));}
console.log('Repeated draft review/source identity, existing content, exact copy binding/coordinates and detached scene passed.');

const grid={count:5,columns:3,step:{x:64,z:-128}};
assert.deepEqual(Array.from({length:5},(_,i)=>draftRepeatPosition(original,grid,i+1)),[{x:192,z:256},{x:256,z:256},{x:128,z:128},{x:192,z:128},{x:256,z:128}]);
assert.deepEqual(draftRepeatPosition(original,{count:3,step:{x:64,z:128}},3),{x:320,z:640});
for(const bad of [{...grid,columns:1},{...grid,columns:7},{...grid,columns:2.5},{...grid,step:{x:0,z:64}},{...grid,step:{x:64,z:0}}])assert.throws(()=>draftRepeatPosition(original,bad,1));
assert.throws(()=>draftRepeatPosition(original,grid,6));
console.log('Line compatibility, row-major grid, negative spacing and invalid grid qualification passed.');
