import assert from 'node:assert/strict';
import {decodeSavedActorSelection} from '../editor/actor-selection-sets.js';
const state={scene:{id:'scene',entities:[{id:'a'},{id:'b'},{id:'c'}]},actor_selection_source_key:'source'},value={scene_id:'scene',import_sha256:'source',actor_ids:['a','b']},before=structuredClone(value);
const ids=decodeSavedActorSelection(value,state);ids.push('c');assert.deepEqual(value,before);
for(const change of [v=>v.scene_id='other',v=>v.import_sha256='stale',v=>v.actor_ids=['a','a'],v=>v.actor_ids=['a'],v=>v.actor_ids=['a','other'],v=>v.actor_ids=['b','a'],v=>v.actor_ids=null]){const bad=structuredClone(value);change(bad);assert.throws(()=>decodeSavedActorSelection(bad,state));}
console.log('Saved actor selection scene/source/membership bindings, canonical order, atomic rejection and detached recall IDs passed.');
