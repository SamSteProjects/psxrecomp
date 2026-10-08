import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeAssetReferences,assetReferenceRelationLabel} from '../editor/asset-references.js';
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),v=f.graph;
const decode=r=>decodeAssetReferences(r,r.asset_id,r.source_key,'project');
decode(v);
const edge=v.incoming.find(e=>e.kind==='retained_midi_sequence_input');assert(edge);
assert.match(assetReferenceRelationLabel(edge),/Historical MIDI capture target/);
assert.match(assetReferenceRelationLabel(edge),/Current input usage not asserted/);
for(const mutate of [e=>e.midi_input_evidence.input_usage='verified',e=>e.midi_input_evidence.relationship='current_assignment',e=>e.midi_input_evidence.native_asset_id='audio://legaia/prot/0000',e=>e.midi_input_evidence.midi_sha256='f'.repeat(64),e=>e.midi_input_evidence.source_scene_id='scene://other',e=>e.midi_input_evidence.sequence_sha256='bad',e=>e.layer='effective',e=>e.runtime_binding='verified',e=>e.kind='initial_model',e=>e.midi_input_evidence.extra=true]){const bad=structuredClone(v);mutate(bad.incoming.find(e=>e.id===edge.id));assert.throws(()=>decode(bad));}
console.log('Real MIDI reference graph decoding, historical labels, ownership, claims and strict field refusal passed');
