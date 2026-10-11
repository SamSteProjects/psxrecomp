import fs from 'node:fs';import assert from 'node:assert/strict';
import {worldAnimationBuildSource,worldAnimationBuildTarget,qualifyWorldAnimationBuildPose} from '../editor/worldmap-animation-build-navigation.js';
import {mergeWorldAnimationAuthoredAssets} from '../editor/worldmap-animation-assets.js';
import {worldmapBehaviorProjectRecords} from '../editor/worldmap-behavior-resources.js';
import {qualifyWorldAnimationCurrent} from '../editor/worldmap-animation-current.js';
const {current,poses,proof,assets}=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),records=mergeWorldAnimationAuthoredAssets(worldmapBehaviorProjectRecords(assets.resources,'test-key'),assets.authored,assets.bindings),changes=proof.build.report.changes.filter(r=>r.scope==='world-animation-channel-content-only');
let checked=0;
for(const change of changes){const target=worldAnimationBuildTarget(change,records,assets.bindings);assert.equal(target.entityId,'scene://map02/worldmap/placements/183d');assert.equal(target.frame,change.frame_index);assert.equal(target.object,change.object_index);
 const pose=poses.find(p=>p.frame_index===change.frame_index);if(pose){await qualifyWorldAnimationCurrent(pose,current,pose.entity_id,pose.project_path,pose.frame_index,pose.binding);assert.deepEqual(qualifyWorldAnimationBuildPose(pose,target.record,change),{retail:change.before,current:change.after});checked++;}
}
const change=changes.find(c=>c.frame_index===4&&c.field==='rotation_psx.z'),target=worldAnimationBuildTarget(change,records,assets.bindings),pose=poses.find(p=>p.frame_index===4);
for(const mutate of [c=>c.owner_id='foreign',c=>c.asset_id='foreign',c=>c.scene='map03',c=>c.record_index++,c=>c.shared_record=false,c=>c.contributor_scope='axis',c=>c.authored_owners=[],c=>c.frame_index=512,c=>c.object_index=64,c=>c.field='rotation_psx.w',c=>c.after=17,c=>c.bank_byte_offset++,c=>c.source_record_sha256='0'.repeat(64)]){const bad=structuredClone(change);mutate(bad);assert.throws(()=>worldAnimationBuildTarget(bad,records,assets.bindings));}
for(const mutate of [c=>c.proposed_record_sha256='0'.repeat(64),c=>c.before+=16,c=>c.after+=16,c=>c.frame_index--,c=>c.object_index--]){const bad=structuredClone(change);mutate(bad);assert.throws(()=>qualifyWorldAnimationBuildPose(pose,target.record,bad));}
assert.equal(worldAnimationBuildSource({scope:'unrelated'},assets.authored),null);assert.throws(()=>worldAnimationBuildSource(change,[]));assert.throws(()=>worldAnimationBuildTarget(change,records,{}));assert.equal(changes.length,12);assert.equal(checked,6);
console.log('12 native Build links, 6 fresh Current axis comparisons and 20 ownership/span/value/hash refusals passed.');
