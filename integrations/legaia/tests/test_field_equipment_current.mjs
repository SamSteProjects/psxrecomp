import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyFieldEquipment,qualifyFieldEquipmentExport} from '../editor/field-equipment.js';
const {cases}=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refused=0,full=0;
for(const {context,held,value,full:clip} of cases){const source=await qualifyFieldEquipment(held,context);await qualifyFieldEquipmentExport(value,source,context);if(clip){await qualifyFieldEquipmentExport(clip,source,{...context,exportFps:17.5});full++;}for(const change of [v=>v.layer='retail_selected_variant',v=>v.model_binding.asset_sha256='0'.repeat(64),v=>v.model_binding.source_sha256='0'.repeat(64),v=>v.retail_model_sha256='0'.repeat(64),v=>v.base_geometry.vertices[0][0]++]){const v=structuredClone(held);change(v);await assert.rejects(qualifyFieldEquipment(v,context));refused++;}}
console.log(`${cases.length} Current field variants/static exports, ${full} full clips and ${refused} altered Current receipts refuse`);
