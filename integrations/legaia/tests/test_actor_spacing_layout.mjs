import assert from 'node:assert/strict';
import {validateActorSpacingReport} from '../editor/actor-placement-batch.js';
const base={entity_id:'b',effective:{x:512,y:null,z:512},proposed:{x:512,y:null,z:512}};
const cases=[
  [{kind:'scale',anchor_entity_id:'b',percent:50},{x:576,y:-12,z:576}],
  [{kind:'scale',anchor_entity_id:'b',percent:200},{x:768,y:-12,z:640}],
  [{kind:'scale',anchor_entity_id:'b',percent:1},{x:512,y:-12,z:512}],
  [{kind:'mirror',anchor_entity_id:'b',axis:'x'},{x:384,y:-12,z:576}],
  [{kind:'mirror',anchor_entity_id:'b',axis:'z'},{x:640,y:-12,z:448}]
];let refusals=0;
for(const [layout,proposed] of cases){
  const report={layout,changed_count:1,targets:[{entity_id:'a',effective:{x:640,y:-12,z:576},proposed},structuredClone(base)]};
  assert.equal(validateActorSpacingReport(report),report);
  for(const mutate of [r=>r.layout.anchor_entity_id='foreign',r=>r.layout.extra=1,r=>r.changed_count++,r=>r.targets[0].proposed.x++,r=>r.targets[0].proposed.y=0,r=>r.targets[1].proposed.z++,r=>r.targets[0].effective.x=641,r=>r.targets[1].entity_id='a']){
    const bad=structuredClone(report);mutate(bad);assert.throws(()=>validateActorSpacingReport(bad));refusals++;
  }
}
for(const percent of [true,0,1001,50.5])assert.throws(()=>validateActorSpacingReport({layout:{kind:'scale',anchor_entity_id:'b',percent},targets:[base,base],changed_count:0}));
console.log(`Five native actor spacing/reflection cases and ${refusals+4} altered/domain refusals passed.`);
