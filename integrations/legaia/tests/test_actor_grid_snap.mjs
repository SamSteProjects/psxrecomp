import assert from 'node:assert/strict';
import {actorGridSnapLayout,validateActorGridSnapReport} from '../editor/actor-placement-batch.js';
const layout={kind:'snap',axes:['x'],spacing:256},r={layout,changed_count:1,targets:[{effective:{x:192,y:null,z:320},proposed:{x:256,y:null,z:320}},{effective:{x:512,y:-12,z:256},proposed:{x:512,y:-12,z:256}}]};
assert.equal(validateActorGridSnapReport(r),r);const detached=actorGridSnapLayout(layout.axes,layout.spacing);detached.axes.pop();assert.equal(layout.axes.length,1);
for(const [axes,spacing] of [[['z','x'],256],[['x','x'],256],[[],256],[['x'],65],[['x'],4097],[['x'],true]])assert.throws(()=>actorGridSnapLayout(axes,spacing));
for(const mutate of [v=>v.changed_count++,v=>v.targets[0].proposed.x=192,v=>v.targets[0].proposed.y=0,v=>v.targets[0].proposed.z=256,v=>v.targets[0].effective.x=64,v=>v.layout.extra=1]){const v=structuredClone(r);mutate(v);assert.throws(()=>validateActorGridSnapReport(v));}
console.log('Actor grid snap: exact native rounding, selected axes, retained height, detached inputs and forged/boundary refusal passed.');
