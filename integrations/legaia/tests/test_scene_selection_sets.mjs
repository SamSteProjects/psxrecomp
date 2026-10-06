import assert from 'node:assert/strict';
import {decodeSavedSceneSelection,unavailableSelectionNpcs} from '../editor/scene-selection-sets.js';
const state={scene:{id:'scene',entities:[{id:'actor-1'},{id:'actor-2'}]},actor_selection_source_key:'import',scene_selection_map_sha256:'map',scene_selection_eligible_ids:['actor-1','actor-2','decor-1']};
const value={scene_id:'scene',import_sha256:'import',map_sha256:'map',entity_ids:['actor-1','decor-1']},before=structuredClone(value);
const ids=decodeSavedSceneSelection(value,state);ids.push('actor-2');assert.deepEqual(value,before);
for(const entity_ids of [['actor-1'],['decor-1'],['actor-1','actor-2'],['actor-1','actor-2','decor-1']])assert.deepEqual(decodeSavedSceneSelection({...value,entity_ids},state),entity_ids);
for(const change of [v=>v.scene_id='other',v=>v.import_sha256='stale',v=>v.map_sha256='stale',v=>v.entity_ids=['actor-1','actor-1'],v=>v.entity_ids=[],v=>v.entity_ids=['actor-1','unknown'],v=>v.entity_ids=['decor-1','actor-1'],v=>v.entity_ids=null,v=>v.entity_ids=Array.from({length:129},(_,i)=>String(i)),v=>v.entity_ids=[null]]){const bad=structuredClone(value);change(bad);assert.throws(()=>decodeSavedSceneSelection(bad,state));}
assert.deepEqual(decodeSavedSceneSelection({...value,map_sha256:'old',entity_ids:['actor-1']},state),['actor-1']);
assert.throws(()=>decodeSavedSceneSelection(value,{...state,scene_selection_eligible_ids:[]}));
console.log('Saved scene selection canonical detached IDs, 1–128 bounds, actor/decor/mixed membership, import binding and decoration MAP binding passed.');

const npc='authored-actor://11111111-2222-4333-8444-555555555555',npcState={...state,actor_drafts:{[npc]:{scene_id:'scene'}},scene_selection_eligible_ids:[...state.scene_selection_eligible_ids,npc]};
for(const entity_ids of [[npc],['actor-1',npc],[npc,'decor-1'].sort(),['actor-1',npc,'decor-1'].sort()])assert.deepEqual(decodeSavedSceneSelection({...value,entity_ids,map_sha256:entity_ids.includes('decor-1')?'map':null},npcState),entity_ids);
assert.throws(()=>decodeSavedSceneSelection({...value,entity_ids:[npc],map_sha256:'map'},{...npcState,actor_drafts:{}}));
assert.throws(()=>decodeSavedSceneSelection({...value,entity_ids:[npc],map_sha256:'map'},{...npcState,actor_drafts:{[npc]:{scene_id:'other'}}}));
console.log('NPC-only and mixed saved selections retain owning scene and reject missing/wrong-scene NPCs.');

const repairValue={...value,entity_ids:[npc,'actor-1']};assert.deepEqual(unavailableSelectionNpcs(repairValue,npcState),[]);assert.deepEqual(unavailableSelectionNpcs(repairValue,{...npcState,actor_drafts:{}}),[npc]);assert.deepEqual(unavailableSelectionNpcs(repairValue,{...npcState,actor_drafts:{[npc]:{scene_id:'other'}}}),[npc]);const missing=unavailableSelectionNpcs(repairValue,{...npcState,actor_drafts:{}});missing.push('new');assert.equal(repairValue.entity_ids.length,2);assert.deepEqual(unavailableSelectionNpcs(null,npcState),[]);
console.log('Unavailable NPC selection diagnostics preserve identities and distinguish owning scenes.');
