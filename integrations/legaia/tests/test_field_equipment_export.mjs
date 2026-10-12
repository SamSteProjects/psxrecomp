import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyFieldEquipment,qualifyFieldEquipmentExport} from '../editor/field-equipment.js';
const {cases,corners,pixels}=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refused=0;
for(const {context,held,value} of cases){const source=await qualifyFieldEquipment(held,context);await qualifyFieldEquipmentExport(value,source,context);for(const mutate of [v=>v.project_source_key='0'.repeat(64),v=>v.equipment_byte=255,v=>v.equipment_variant.source_descriptor_index=0,v=>v.audit.source_record.equipment_variant.projected_sha256='0'.repeat(64),v=>v.audit.sha256='0'.repeat(64),v=>v.filename='../wrong.glb',v=>v.audit.posed=!v.audit.posed]){const bad=structuredClone(value);mutate(bad);await assert.rejects(qualifyFieldEquipmentExport(bad,source,context));refused++;}}
console.log(`${cases.length} selected field exports, ${corners} native corners, ${pixels} embedded pixels and ${refused} altered export refusals pass`);
