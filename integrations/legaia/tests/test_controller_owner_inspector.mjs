import assert from 'node:assert/strict';
import {controllerOwnerComponents,controllerAssetSourceHash} from '../editor/controller-owner-inspector.js';
const scene='scene://fixture',id='script://fixture/controllers/man-p1/0000',hash='a'.repeat(64);
const kinds={ControllerSystemFlags:'system-flag',ControllerBranches:'branch',ControllerTileRects:'tile-rect',ControllerFades:'fade',ControllerTableCopies:'table-copy',ControllerWordTriplets:'word-triplet',ControllerThreeWords:'three-word',ControllerSceneBytes:'scene-byte',ControllerBgm:'bgm',ControllerFlagBits:'flag-bit',ControllerFiveWords:'five-word',ControllerGlobalBytes:'global-byte',ControllerPartySelectors:'party-selector'};
for(const [family,kind] of Object.entries(kinds)){
 const record={id,kind:'controller',scene_id:scene,authored:{[family]:{source_record_sha256:hash,entries:{[id+'/'+kind+'/0010']:{value:1},[id+'/'+kind+'/0005']:{value:2}}}}};
 const components=controllerOwnerComponents(record,scene);assert.equal(components[family].authored_instruction_count,2);assert.equal(components[family].first_pc,5);components[family].entries[id+'/'+kind+'/0005'].value=9;assert.equal(record.authored[family].entries[id+'/'+kind+'/0005'].value,2);
 const asset={id,type:'controller',sceneId:scene,authoredRecord:record};assert.equal(controllerAssetSourceHash(asset),hash);assert.equal(controllerAssetSourceHash({...asset,data:{source_record:{sha256:hash}}}),hash);
 assert.throws(()=>controllerAssetSourceHash({...asset,data:{source_record:{sha256:'b'.repeat(64)}}}));
 for(const mutate of [r=>r.id='scene://fixture/actors/man-p1/0001',r=>r.scene_id='scene://other',r=>r.kind='script',r=>r.authored[family].entries=[],r=>r.authored[family].source_record_sha256='bad',r=>r.authored[family].entries={'foreign':{}},r=>r.authored[family].entries={[id+'/'+kind+'/0005']:null},r=>r.authored.Transform={entries:{}}]){const copy=structuredClone(record);mutate(copy);assert.throws(()=>controllerOwnerComponents(copy,scene));}
 const empty=structuredClone(record);empty.authored[family].entries={};assert.deepEqual(controllerOwnerComponents(empty,scene),{});
}
assert.equal(controllerAssetSourceHash({data:{source_record:{sha256:hash}}}),hash);assert.throws(()=>controllerAssetSourceHash({}));
console.log('All thirteen controller Inspector projections retain stable ownership, detached entries, bounded PCs and matching Retail source hashes.');
