import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {scriptFlowReportHash} from '../editor/script-flow-identity.js';
const rows=JSON.parse(readFileSync(process.argv[2],'utf8'));
assert.equal(rows.length,36);
for(const row of rows)assert.equal(await scriptFlowReportHash(row.report),row.expected);
console.log('36 controller Current/Proposed/reset report hashes match the editor');
