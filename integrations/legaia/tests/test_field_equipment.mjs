import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyFieldEquipment} from '../editor/field-equipment.js';
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let vertices=0,refused=0;
for(const {context,value} of cases){await qualifyFieldEquipment(value,context);vertices+=value.geometry.vertices.length;for(const mutate of [v=>v.project_source_key='0'.repeat(64),v=>v.equipment_byte=255,v=>v.geometry.equipment_variant.target_descriptor_index++,v=>v.projected_tmd_base64=v.source_tmd_base64,v=>v.geometry.vertices[0][0]++,v=>v.geometry.equipment_variant.runtime_equipment='observed',v=>v.layer='current']){const bad=structuredClone(value);mutate(bad);await assert.rejects(qualifyFieldEquipment(bad,context));refused++;}}
console.log(`${cases.length} field variants, ${vertices} vertices and ${refused} altered source/descriptor/pose refusals pass`);
