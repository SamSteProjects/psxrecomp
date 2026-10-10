import fs from 'node:fs';import assert from 'node:assert/strict';
import {worldmapCurrentTextureView} from '../editor/worldmap-scene.js';
const root=process.argv[2];
for(const scene of ['map01','map02','map03']){
 const retail=JSON.parse(fs.readFileSync(root+'/'+scene+'-retail.json')),current=JSON.parse(fs.readFileSync(root+'/'+scene+'-current.json')),held=structuredClone(current),view=worldmapCurrentTextureView(retail,current);assert.equal(view.entities.length,retail.scene_graph.entities.length);assert.deepEqual(current,held);
 for(const mutate of [v=>v.source_record.disc_sha256='0'.repeat(64),v=>v.scene_graph.entities[0].x++,v=>v.scene_graph.assets[0].preview.vertices[0][0]++,v=>v.preview.texture_catalog.textures[0].decoded_member_sha256='0'.repeat(64),v=>v.texture_layer='retail',v=>v.texture_authoring.edits[0].source_tim_sha256='0'.repeat(64),v=>v.texture_authoring.scope='runtime-texture-residency',v=>v.scene_graph.metrics.texture_output_bytes++,v=>v.project_source_key='0'.repeat(64)]){const bad=structuredClone(current);mutate(bad);assert.throws(()=>worldmapCurrentTextureView(retail,bad));}
}
console.log('Three native Current texture views: unchanged source geometry/membership and nine forged-response refusals each passed.');
