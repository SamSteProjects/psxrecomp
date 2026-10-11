import fs from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyWorldDecorationSource, qualifyWorldDecorationRemovalReview, removeWorldDecoration} from '../editor/worldmap-decoration-state.js';

const rows = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
let refusals = 0;
for (const row of rows) {
  const held = JSON.stringify(row);
  const source = await qualifyWorldDecorationSource(row.source, row.current, row.source.project_path);
  const ids = row.review.placement_ids;
  assert.equal(ids.length, 2);
  const review = await qualifyWorldDecorationRemovalReview(row.review, source, ids);
  const replay = await removeWorldDecoration(source, ids);
  assert.equal(review.binding, null);
  assert.deepEqual(Buffer.from(replay.bytes), Buffer.from(row.after.placement_authoring.current_map_base64, 'base64'));
  assert.deepEqual(review.audit.removed, ids.map(id => row.source.authored_allocations.find(a => a.placement_id === id)));
  for (const mutate of [
    v => v.placement_ids.reverse(), v => v.placement_ids.push(v.placement_ids[0]),
    v => v.placement_ids[0] = 'foreign', v => v.schema_version = 'legaia.worldmap-decoration-removal-review.v1',
    v => v.audit.removed[0].target_cell++, v => v.audit.removed.reverse(),
    v => v.audit.rebased_donors.push({placement_id: 'foreign'}),
    v => v.audit.remaining_allocations.push(v.audit.removed[0]),
    v => v.audit.changed_bytes.pop(), v => v.audit.scope = 'authored-decoration-removal-only',
    v => v.before_binding.operations.pop(), v => v.binding = v.before_binding,
    v => v.proposed_map_sha256 = '0'.repeat(64), v => v.build_ready = true,
  ]) {
    const bad = structuredClone(row.review); mutate(bad);
    await assert.rejects(qualifyWorldDecorationRemovalReview(bad, source, ids)); refusals++;
  }
  for (const bad of [[], ids.slice().reverse(), [ids[0], ids[0]], ['foreign'], [true]]) {
    await assert.rejects(removeWorldDecoration(source, bad)); refusals++;
  }
  assert.equal(JSON.stringify(row), held);
}
assert.equal(rows.length, 3);
console.log(`Three complete native group-removal replays and ${refusals} altered/domain refusals passed.`);
if (process.argv[3]) {
  const chains = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
  for (const row of chains) {
    const source = {metadata: row.metadata, retailBytes: new Uint8Array(Buffer.from(row.retail, 'base64')),
      bytes: new Uint8Array(Buffer.from(row.current, 'base64')), authoredRecords: {}};
    const held = JSON.stringify(source.metadata);
    await qualifyWorldDecorationRemovalReview(row.review, source, row.review.placement_ids);
    const replay = await removeWorldDecoration(source, row.review.placement_ids);
    assert.deepEqual(Buffer.from(replay.bytes), Buffer.from(row.review.proposed_map_base64, 'base64'));
    if (row.review.placement_ids.length === 2) {
      assert.equal(replay.audit.remaining_allocations.length, 1);
      assert.equal(replay.audit.remaining_allocations[0].model_pool_index, row.model);
      assert.equal(replay.audit.remaining_allocations[0].donor_cell, row.metadata.authored_allocations[0].donor_cell);
    } else assert.equal(replay.binding, null);
    assert.equal(JSON.stringify(source.metadata), held);
  }
  assert.equal(chains.length, 4);
  console.log('Four v1/v2 ancestor-chain and last-owner replays preserve exact native bytes and surviving models.');
}
