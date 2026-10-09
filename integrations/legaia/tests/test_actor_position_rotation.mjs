import assert from 'node:assert/strict';
import {validateActorRotationReport} from '../editor/actor-placement-batch.js';
const r={layout:{kind:'rotate_angle',anchor_entity_id:'b',angle_degrees:45},changed_count:1,targets:[{entity_id:'a',effective:{x:640,y:-12,z:512},proposed:{x:576,y:-12,z:576}},{entity_id:'b',effective:{x:512,y:null,z:512},proposed:{x:512,y:null,z:512}}]};assert.equal(validateActorRotationReport(r),r);
for(const mutate of [v=>v.changed_count++,v=>v.layout.angle_degrees=45.5,v=>v.layout.anchor_entity_id='absent',v=>v.layout.extra=1,v=>v.targets[0].proposed.x=640,v=>v.targets[0].proposed.y=0,v=>v.targets[0].effective.x=641]){const v=structuredClone(r);mutate(v);assert.throws(()=>validateActorRotationReport(v));}
console.log('Actor position rotation: exact Q30 native rounding, fixed anchor, unchanged height and forged/invalid input refusal passed.');
