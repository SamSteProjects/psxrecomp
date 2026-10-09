import assert from 'node:assert/strict';
import {draftGroupPositions} from '../editor/draft-group.js';
const ids=['authored-actor://00000000-0000-0000-0000-000000000001','authored-actor://00000000-0000-0000-0000-000000000002'],drafts=Object.fromEntries(ids.map((id,i)=>[id,{position:{x:i?512:192,z:i?704:320}}]));
const request={entity_ids:ids,layout:{kind:'snap',axes:['x','z'],spacing:256}},held=structuredClone(drafts);
assert.deepEqual([...draftGroupPositions(request,drafts).values()],[{x:256,z:256},{x:512,z:768}]);assert.deepEqual(drafts,held);
for(const change of [{spacing:65},{axes:['z','x']},{axes:['x','x']},{anchor_entity_id:ids[0]}])assert.throws(()=>draftGroupPositions({...request,layout:{...request.layout,...change}},drafts));
drafts[ids[0]].position.x=64;assert.throws(()=>draftGroupPositions(request,drafts));
console.log('NPC grid snap: exact selected-axis positions, retained inputs, invalid operation and native boundary refusal passed.');
