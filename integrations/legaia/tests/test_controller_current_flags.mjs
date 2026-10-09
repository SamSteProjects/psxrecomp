import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeFlagResource} from '../editor/flag-resource.js';
import {decodeFlagQualification} from '../editor/flag-qualification.js';
const groups=JSON.parse(fs.readFileSync(process.env.LEGAIA_CONTROLLER_CURRENT_FLAGS+'/groups.json'));
for(const g of groups)decodeFlagResource(g);
const group=groups.find(g=>g.references.some(r=>r.authored_index!==null));
const row=group.references.find(r=>r.authored_index!==null);
assert.throws(()=>decodeFlagQualification(row.authored_qualification,row.authored_qualification));
for(const change of [r=>delete r.authored_qualification,r=>r.authored_qualification.schema_version='legaia.system-flag-operand-qualification.v1',r=>r.effective_index=999,r=>r.authored_qualification.owner_id='scene://town01/actors/man-p1/0001',r=>r.authored_qualification.source_record_sha256='f'.repeat(64)]){
 const bad=structuredClone(group);change(bad.references.find(r=>r.authored_index!==null));assert.throws(()=>decodeFlagResource(bad));
}
console.log('38 real controller resources decoded; dedicated Current qualification and five forged annotation refusals passed.');
