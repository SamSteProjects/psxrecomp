import fs from 'node:fs';
import assert from 'node:assert/strict';
const {modelResolutionPlacementIds}=await import('data:text/javascript;base64,'+Buffer.from(fs.readFileSync(new URL('../editor/model-resolution.js',import.meta.url))).toString('base64'));
const report=JSON.parse(fs.readFileSync(process.env.LEGAIA_MODEL_RESOLUTION_EVIDENCE));
const scene=report.scene_id,key=report.source_key,before=JSON.stringify(report);
const ids=modelResolutionPlacementIds(report,scene,key);
assert.deepEqual(ids,report.rows.map(row=>row.entity_id).sort());
ids.pop();assert.equal(modelResolutionPlacementIds(report,scene,key).length,6);
assert.equal(JSON.stringify(report),before);
assert.throws(()=>modelResolutionPlacementIds(report,'scene://foreign',key));
assert.throws(()=>modelResolutionPlacementIds(report,scene,'0'.repeat(64)));
const empty=structuredClone(report);empty.rows=[];empty.counts.retail_unresolved=empty.counts.current_unresolved=0;
assert.throws(()=>modelResolutionPlacementIds(empty,scene,key));
const mixed=structuredClone(report),npc=mixed.rows[0];npc.kind='npc';npc.entity_id='authored-actor://12345678-1234-1234-1234-123456789abc';npc.retail=null;mixed.counts.retail_unresolved--;mixed.counts.npc_drafts=1;
assert(modelResolutionPlacementIds(mixed,scene,key).includes(npc.entity_id));
for(const count of [128,129]){
 const large=structuredClone(report);large.rows=Array.from({length:count},(_,i)=>{const row=structuredClone(report.rows[0]);row.entity_id=scene+'/actors/man-p1/'+String(i+1).padStart(4,'0');row.retail.source_actor_id=row.current.source_actor_id=row.entity_id;row.retail.source_record.record_index=row.current.source_record.record_index=i+1;return row;});
 Object.assign(large.counts,{source_actors:count,npc_drafts:0,retail_unresolved:count,current_unresolved:count});
 if(count===128)assert.equal(modelResolutionPlacementIds(large,scene,key).length,128);
 else assert.throws(()=>modelResolutionPlacementIds(large,scene,key),/complete group/);
}
const duplicate=structuredClone(report);duplicate.rows[1]=duplicate.rows[0];assert.throws(()=>modelResolutionPlacementIds(duplicate,scene,key));
console.log('Complete affected placement groups: exact source, detached sorted identities, actor/NPC membership, empty/duplicate refusal and 128/129 boundary passed.');
