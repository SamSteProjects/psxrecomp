import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeSidebandResources, sidebandProjectRecords, qualifySidebandPreview} from '../editor/battle-sideband.js';
import {projectAssetRecords} from '../editor/project-assets.js';

const c = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const context = {projectPath:c.report.project_path, sourceKey:c.report.project_source_key};
const report = await decodeSidebandResources(c.report, context);
const records = sidebandProjectRecords(report);
assert.equal(records.length, 166);
assert(records.every(r => !r.sceneId && !r.projectMembership && r.projectSideband));
const combined = {scenes:[],assets:[],globalBattleSideband:report};
assert.equal(projectAssetRecords(combined,'global-battle-sideband').length,166);
assert.equal(projectAssetRecords(combined,'all').length,166);
assert.equal(projectAssetRecords(combined,'global-battle-character').length,0);
let checks = 0, refusals = 0;
for (const value of c.cases) {
  await qualifySidebandPreview(value, report, value.record);
  checks++;
  const edits = [v=>v.project_source_key='stale', v=>v.source_slot_base64=Buffer.from('changed').toString('base64'),
    v=>v.record.source_record.byte_offset++, v=>v.preview.vertices ? v.preview.vertices[0][0]++ : v.preview.words[0]^=1];
  if (value.record.asset_kind === 'tmd_model') edits.push(v=>v.preview.textures=[], v=>v.preview.frames=[],
    v=>v.preview.animation={}, v=>v.preview.reference_commit='foreign');
  for (const change of edits) {
    const altered = structuredClone(value); change(altered);
    await assert.rejects(() => qualifySidebandPreview(altered, report, value.record)); refusals++;
  }
}
for (const change of [v=>v.project_path+='foreign', v=>v.project_source_key='stale', v=>v.catalog.source_key='0'.repeat(64),
  v=>v.catalog.banks[0].byte_length++, v=>v.catalog.banks[1].sha256='0'.repeat(64), v=>v.catalog.slots.pop(),
  v=>v.catalog.slots[0].source_record.slot_offset++, v=>v.catalog.models[0].source_record.byte_offset++,
  v=>v.catalog.models[0].source_record.disc.sha256='0'.repeat(64), v=>v.catalog.models[0].references_beyond_texture_pool=true,
  v=>v.catalog.models[0].preview_summary.objects=257, v=>v.catalog.models[0].semantic_id='foreign',
  v=>v.catalog.textures[0].palette_count++, v=>v.catalog.textures[0].mode=3, v=>v.catalog.textures[0].image_offset++,
  v=>v.catalog.textures.push(v.catalog.textures[0]), v=>v.catalog.models.pop()]) {
  const altered = structuredClone(c.report); change(altered);
  await assert.rejects(() => decodeSidebandResources(altered, context)); refusals++;
}
console.log(`${records.length} distinct global sources, ${checks} literal model/page previews and ${refusals} source/pixel/catalog refusals pass`);
