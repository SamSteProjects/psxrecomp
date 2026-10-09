import assert from 'node:assert/strict';
import {CONTROLLER_BUILD_TARGETS,controllerBuildTarget} from '../editor/controller-build-navigation.js';
import {CONTROLLER_SNAPSHOT_SCHEMAS} from '../editor/controller-workspace-snapshot.js';
const sceneId='scene://fixture',owner=sceneId+'/controllers/man-p1/0000',asset=owner.replace('scene://','script://'),scenes=[{id:sceneId,name:'fixture'}];
assert.deepEqual(new Set(Object.values(CONTROLLER_BUILD_TARGETS).map(row=>row[0])),new Set(Object.keys(CONTROLLER_SNAPSHOT_SCHEMAS)));
for(const [scope,[component,kind,field]] of Object.entries(CONTROLLER_BUILD_TARGETS)){
 const operand=asset+'/'+kind+'/ffff',after=component==='ControllerSystemFlags'||component==='ControllerBranches'?7:{signed_words:[1,2,3]},value=component==='ControllerSystemFlags'?{index:after}:component==='ControllerBranches'?{target_pc:after}:after;
 const change={scene:'fixture',owner_id:owner,asset_id:operand,scope,field,after},records=[{kind:'controller',id:asset,scene_id:sceneId,authored:{[component]:{source_record_sha256:'a'.repeat(64),entries:{[operand]:value}}}}];
 const before=JSON.stringify([change,records]);assert.deepEqual(controllerBuildTarget(change,scenes,records),{sceneId,assetId:asset,ownerId:owner,component,pc:65535});assert.equal(JSON.stringify([change,records]),before);
 for(const altered of [{scene:'foreign'},{owner_id:'scene://fixture/controllers/man-p1/0001'},{scope:'unsupported'},{field:'foreign'},{asset_id:asset+'/foreign/ffff'},{asset_id:asset+'/'+kind+'/10000'},{asset_id:operand+'extra'},{after:null},{after:{value:9}}])assert.throws(()=>controllerBuildTarget({...change,...altered},scenes,records));
 assert.throws(()=>controllerBuildTarget(change,[],records));assert.throws(()=>controllerBuildTarget(change,scenes,[]));
 const changed=structuredClone(records);changed[0].authored[component].entries[operand]={other:1};assert.throws(()=>controllerBuildTarget(change,scenes,changed));
}
assert.equal(controllerBuildTarget({owner_id:'scene://fixture/actors/man-p1/0001'},scenes,[]),null);
console.log('All eleven controller Build scopes bind source owner, field, operand PC, scene and unchanged authored values without mutation.');
