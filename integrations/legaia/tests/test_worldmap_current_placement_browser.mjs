import fs from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyCurrentWorldPlacements} from '../editor/worldmap-current-placements.js';
import {worldmapHierarchyRows} from '../editor/worldmap-scene.js';

const rows = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
let refusals = 0;
for (const {retail, current, options} of rows) {
  const before = JSON.stringify({retail, current, options});
  const qualified = await qualifyCurrentWorldPlacements(retail, current, options);
  assert.equal(qualified.assets.length, current.scene_graph.assets.length);
  assert.equal(qualified.entities.length, current.scene_graph.entities.length);
  const authored = qualified.entities.filter(e => e.placement_scope === 'authored_spawn_seed');
  assert.equal(authored.length, current.placement_authoring.authored_entity_count);
  for (const entity of qualified.entities) {
    const matrix = [];
    for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) matrix.push(entity.source_to_world[c * 4 + r] * (r === 1 ? -1 : 1));
    assert.deepEqual(entity.model_to_scene, matrix);
  }
  for (const entity of authored) {
    assert.equal(entity.retail_source_position, null);
    const rows = worldmapHierarchyRows(qualified, `id:${entity.entity_id}`, entity.entity_id);
    assert.equal(rows.matching, 1); assert.equal(rows.rows[0].entityId, entity.entity_id);
  }
  assert.equal(JSON.stringify({retail, current, options}), before);
  const getAuthored = v => v.scene_graph.entities.find(e => e.placement_scope === 'authored_spawn_seed');
  const getOriginal = v => v.scene_graph.entities.find(e => e.placement_scope === 'source_spawn_seed');
  for (const mutate of [
    v => v.representation = 'proposed-source', v => v.allocation_proposal = {}, v => v.placement_authoring.extra = true,
    v => v.placement_authoring.source_record.source_disc_sha256 = '0'.repeat(64),
    v => v.placement_authoring.current_map_sha256 = '0'.repeat(64),
    v => v.placement_authoring.exported_map_base64 = v.placement_authoring.retail_map_base64,
    v => v.placement_authoring.floor_lut[0]++, v => v.placement_authoring.authored_records = {},
    v => v.placement_authoring.authored_allocations[0].preserved_terrain_hex = '00000000',
    v => v.placement_authoring.allocation_binding.operations[0].proposed_map_sha256 = '0'.repeat(64),
    v => getAuthored(v).entity_id = 'scene://foreign/entity', v => getAuthored(v).native_entity_id = 'foreign',
    v => getAuthored(v).asset_id = v.semantic_id, v => getAuthored(v).source_position.y++,
    v => getAuthored(v).source_to_world[13]++, v => getAuthored(v).retail_source_position = {x: 0, y: 0, z: 0},
    v => getAuthored(v).authored_placement.record_index++, v => getOriginal(v).source_to_world[12]++,
    v => getOriginal(v).retail_source_position.x++, v => getOriginal(v).authored_source_transform.record_id = 'foreign',
    v => v.scene_graph.entities.reverse(), v => v.scene_graph.metrics.drawn_triangle_count++,
    v => v.scene_graph.coverage.candidate_count++, v => v.scene_graph.limitations = [],
    v => v.scene_graph.assets[0].preview.vertices[0][0]++, v => v.authored_geometry = false]) {
    const bad = structuredClone(current); mutate(bad);
    await assert.rejects(qualifyCurrentWorldPlacements(retail, bad, options)); refusals++;
  }
}
assert.equal(rows.length, 3);
console.log(`Three complete native Current scene/renderer-matrix qualifications and ${refusals} altered-scene refusals passed.`);
