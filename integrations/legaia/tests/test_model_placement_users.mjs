import assert from 'node:assert/strict';
import {modelPlacementIdsForAsset} from '../editor/scene-placement-selection.js';
import {mountModelPlacementUsers} from '../editor/model-placement-users.js';
const asset='asset://fixture/model',rows=[{entity_id:'actor',asset_id:asset},{entity_id:'npc',asset_id:asset},{entity_id:'decor',asset_id:asset},{entity_id:'ground',asset_id:asset}],eligible=new Set(['actor','npc','decor']);
assert.deepEqual(modelPlacementIdsForAsset(rows,asset,eligible),['actor','decor','npc']);
assert.deepEqual(modelPlacementIdsForAsset(rows,'asset://unused/model',eligible),[]);
for(const id of ['',null,17,'x'.repeat(1025)])assert.throws(()=>modelPlacementIdsForAsset(rows,id,eligible));
assert.throws(()=>modelPlacementIdsForAsset([...rows,rows[0]],asset,eligible));assert.throws(()=>modelPlacementIdsForAsset(rows,asset,[]));
const context={projectPath:'project',sceneId:'scene',sourceKey:'preview',projectSourceKey:'document',rows,eligible};
let active=context,fresh=true,isBusy=false,calls=[],errors=[],release,held;
const host={children:[],ownerDocument:{createElement:()=>({dataset:{},disabled:false})},append(...items){this.children.push(...items);}};
const tool=mountModelPlacementUsers(host,{assetId:asset,getContext:()=>active,current:()=>fresh,busy:()=>isBusy,onError:error=>errors.push(error.message),onSelect:async(ids,current)=>{calls.push(ids);held=current;await new Promise(resolve=>release=resolve);}}),button=host.children[0];
assert.equal(button.disabled,false);assert.match(button.textContent,/3/);
const pending=button.onclick();assert.equal(button.disabled,true);await button.onclick();assert.equal(calls.length,1);assert.equal(held(),true);
active={...context,sourceKey:'changed'};assert.equal(held(),false);release();await pending;
assert.deepEqual(calls[0],['actor','decor','npc']);calls[0].pop();assert.equal(rows.length,4);
for(const blocked of [()=>{fresh=false;},()=>{isBusy=true;},()=>{active=null;},()=>{active={...context,rows:[]};},()=>{active={...context,projectPath:''};}]){
 active=context;fresh=true;isBusy=false;blocked();tool.synchronize();assert.equal(button.disabled,true);await button.onclick();assert.equal(calls.length,1);
}
active=context;fresh=true;isBusy=false;tool.synchronize();assert.equal(button.disabled,false);
const disposed=button.onclick();assert.equal(held(),true);tool.dispose();assert.equal(held(),false);release();await disposed;tool.synchronize();assert.equal(button.disabled,true);assert.deepEqual(errors,[]);
console.log('Asset model placement action: exact actor/NPC/scenery IDs, unused/invalid sources, busy/stale/source change, pending deduplication, disposal and detached dispatch passed.');
