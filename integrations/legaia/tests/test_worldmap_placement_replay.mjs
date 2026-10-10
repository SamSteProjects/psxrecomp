import fs from 'node:fs';
import assert from 'node:assert/strict';
import {allocateWorldPlacements, decodeWorldPlacementSeeds, worldPlacementInventory,
  replayWorldPlacementAllocations, composeWorldPlacementTransforms, placementDigest} from '../editor/worldmap-placement-replay.js';

const decode = value => new Uint8Array(Buffer.from(value, 'base64'));
function equivalent(actual, expected) {
  // Native trigonometric libraries may differ in the final bit. All ownership,
  // integer positions, bytes and hashes remain exact; matrices use 1e-12.
  if (typeof actual === 'number' && typeof expected === 'number' && !Number.isInteger(expected))
    assert.ok(Math.abs(actual - expected) <= 1e-12, `${actual} != ${expected}`);
  else if (Array.isArray(expected)) {
    assert.ok(Array.isArray(actual)); assert.equal(actual.length, expected.length);
    expected.forEach((value, i) => equivalent(actual[i], value));
  } else if (expected && typeof expected === 'object') {
    assert.deepEqual(Object.keys(actual).sort(), Object.keys(expected).sort());
    for (const key of Object.keys(expected)) equivalent(actual[key], expected[key]);
  } else assert.equal(actual, expected);
}
let cases = 0, refusals = 0;
for (const row of JSON.parse(fs.readFileSync(process.argv[2], 'utf8'))) {
  const raw = decode(row.retail), before = raw.slice(), floor = row.floor, scene = row.scene;
  equivalent(await decodeWorldPlacementSeeds(raw, floor, scene), row.decoded);
  const inventory = await worldPlacementInventory(raw, floor, scene);
  for (const key of ['donors', 'free_record_indices', 'target_cells', 'current_placements']) equivalent(inventory[key], row.inventory[key]);
  let bytes = raw;
  for (const operation of row.operations) {
    const result = await allocateWorldPlacements(bytes, floor, scene, operation.requests);
    assert.deepEqual(result.bytes, decode(operation.candidate)); equivalent(result.audit, operation.audit);
    bytes = result.bytes;
  }
  const replay = await replayWorldPlacementAllocations(raw, floor, scene, row.binding, row.provenance);
  assert.deepEqual(replay.bytes, bytes);
  equivalent(replay.allocations, row.operations.flatMap(operation => operation.audit.allocations));
  assert.deepEqual(await composeWorldPlacementTransforms(raw, bytes, floor, scene, row.entries), decode(row.composed));
  assert.deepEqual(raw, before); assert.equal(await placementDigest(raw), row.provenance.source_map_sha256);
  const changes = [b => b.extra = true, b => b.scene = 'foreign', b => b.source_disc_sha256 = '0'.repeat(64),
    b => b.source_map_sha256 = '0'.repeat(64), b => b.source_floor_lut_sha256 = '0'.repeat(64),
    b => b.schema_version = 'foreign', b => b.operations[0].extra = true,
    b => b.operations[0].proposed_map_sha256 = '0'.repeat(64), b => b.operations = [],
    b => b.operations[0].requests[0].placement_id = 'foreign', b => b.operations[0].requests[0].extra = true,
    b => b.operations[0].requests[0].donor_cell = true, b => b.operations[0].requests[0].target_cell = -1,
    b => b.operations[0].requests[0].record_index = 1, b => b.operations[0].requests[0].values.offset.x = 32768,
    b => b.operations[0].requests[0].values.yaw_units = 4096,
    b => b.operations[0].requests.push(structuredClone(b.operations[0].requests[0]))];
  for (const change of changes) {
    const binding = structuredClone(row.binding); change(binding);
    await assert.rejects(replayWorldPlacementAllocations(raw, floor, scene, binding, row.provenance)); refusals++;
  }
  const badFloor = [...floor]; badFloor[0] = badFloor[0] === 32767 ? 32766 : badFloor[0] + 1;
  await assert.rejects(replayWorldPlacementAllocations(raw, badFloor, scene, row.binding, row.provenance)); refusals++;
  for (const change of [e => e.extra = true, e => e.source_record_sha256 = '0'.repeat(64),
    e => e.values.offset.z = false, e => e.values.yaw_units = -1, e => e.shared_record = 'yes']) {
    const entries = structuredClone(row.entries), key = Object.keys(entries)[0]; change(entries[key]);
    await assert.rejects(composeWorldPlacementTransforms(raw, bytes, floor, scene, entries)); refusals++;
  }
  const donor = row.operations[0].requests[0], badRequests = [
    [{...donor, target_cell: donor.donor_cell}], [{...donor, record_index: row.inventory.donors[0].object_record_index}],
    [donor, donor], [], Array(33).fill(donor)];
  for (const requests of badRequests) { await assert.rejects(allocateWorldPlacements(raw, floor, scene, requests)); refusals++; }
  const nonzero = raw.slice(); nonzero[donor.record_index * 32 + 31] = 1;
  await assert.rejects(allocateWorldPlacements(nonzero, floor, scene, [donor])); refusals++;
  if (row.inventory.donors.length === 2) {
    // Both resolved and unresolved placed anchors own a target even when its
    // own grid record has no model. Never overwrite that bind context.
    for (const tilt of [0, 1]) {
      const anchored = raw.slice(), view = new DataView(anchored.buffer);
      view.setUint16(11 * 32 + 16, 1, true); view.setUint16(11 * 32 + 18, 4, true);
      view.setInt8(11 * 32 + 6, 1); view.setUint16(11 * 32 + 8, tilt, true);
      view.setUint16(0x8000 + 199 * 2, 11, true);
      assert.ok(!(await worldPlacementInventory(anchored, floor, scene)).target_cells.includes(200));
      await assert.rejects(allocateWorldPlacements(anchored, floor, scene, [donor])); refusals++;
    }
  }
  for (const bad of [raw.subarray(1), new Uint8Array(0x12001)]) {
    await assert.rejects(decodeWorldPlacementSeeds(bad, floor, scene)); refusals++;
  }
  cases++;
}
assert.ok(cases >= 3);
console.log(`${cases} complete native placement decode/allocation/transform chains and ${refusals} altered-input refusals passed.`);
