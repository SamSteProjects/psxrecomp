import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeAssetReferences,assetReferenceRelationLabel} from '../editor/asset-references.js';
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),g=f.graph;
decodeAssetReferences(g,g.asset_id,g.source_key,'project');
const edge=g.incoming.find(e=>e.kind==='current_native_sequence_midi_binding');assert(edge);assert.match(assetReferenceRelationLabel(edge),/Current authored native sequence/);
for(const mutate of [e=>e.layer='authored',e=>e.current_midi_binding_evidence.midi_asset_id='audio-input://legaia/midi/'+'f'.repeat(64),e=>e.current_midi_binding_evidence.current_sequence_sha256='f'.repeat(64),e=>e.current_midi_binding_evidence.runtime_binding='verified',e=>e.current_midi_binding_evidence.input_usage='not_asserted',e=>e.current_midi_binding_evidence.binding_scene_id='scene://other']){const bad=structuredClone(g),e=bad.incoming.find(e=>e.kind==='current_native_sequence_midi_binding');mutate(e);assert.throws(()=>decodeAssetReferences(bad,g.asset_id,g.source_key,'project'));}
console.log('Current MIDI reference graph endpoint, scene, output hash, layer and runtime-claim refusal passed');
