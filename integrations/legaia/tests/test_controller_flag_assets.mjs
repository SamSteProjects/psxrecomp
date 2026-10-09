import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeFlagResource} from '../editor/flag-resource.js';
import {decodeAssetReferences,assetReferenceInstructionSite} from '../editor/asset-references.js';
const base=process.env.LEGAIA_CONTROLLER_FLAG_ASSET_EVIDENCE;
const groups=JSON.parse(fs.readFileSync(base+'/groups.json'));
assert.equal(groups.length,38);
assert.equal(groups.reduce((n,g)=>n+decodeFlagResource(g).reference_count,0),122);
assert(groups.every(g=>g.references.every(r=>r.flag_operand_id===null&&r.authored_index===null)));
const report=JSON.parse(fs.readFileSync(base+'/report.json'));
const project=JSON.parse(fs.readFileSync(base+'/project-report.json'));
const active=decodeAssetReferences(report,report.asset_id,report.source_key);
decodeAssetReferences(project,project.asset_id,project.source_key,'project');
assert.equal(active.outgoing.length,122);
const nodes=new Map(active.nodes.map(n=>[n.id,n]));
assert(active.outgoing.every(e=>assetReferenceInstructionSite(e,nodes).script_id===report.asset_id));
let refusals=0;
for(const change of [g=>g.owner_id='scene://town01/actors/man-p1/0001',g=>g.references[0].authored_index=1,g=>g.references[0].flag_operand_id='script://actor/flag-bit/0000',g=>g.controller_source_evidence.execution='confirmed',g=>g.controller_source_evidence.source_record.sha256='a'.repeat(64)]){const bad=structuredClone(groups[0]);change(bad);assert.throws(()=>decodeFlagResource(bad));refusals++;}
for(const change of [r=>r.outgoing[0].source_id='scene://town01',r=>r.outgoing[0].kind='script_flag_reference',r=>r.outgoing[0].layer='effective',r=>r.outgoing[0].controller_source_evidence.execution='confirmed',r=>r.outgoing[0].pc=0,r=>r.outgoing[0].flag_reference_evidence.scope='live',r=>r.outgoing.push({...structuredClone(r.outgoing[0]),id:'0'.repeat(64)})]){const bad=structuredClone(report);change(bad);assert.throws(()=>decodeAssetReferences(bad,bad.asset_id,bad.source_key));refusals++;}
console.log(`38 controller groups / 122 operands qualified in shared Inspector and active/project graphs; ${refusals} forged records refused.`);
