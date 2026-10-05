import assert from 'node:assert/strict';
import {decodeSavedSceneView} from '../editor/scene-views.js';
const state={scene:{id:'scene'},scene_view_source_key:'source'},value={scene_id:'scene',import_sha256:'source',display:{camera:{projection:'orthographic',yaw:0,pitch:Math.PI/2,distance:1000,target:{x:2880,y:-64,z:5440}},representation:'retail',layers:{actors:true,scenery:true,ground:false}}};
const before=structuredClone(value),view=decodeSavedSceneView(value,state);view.camera.target.x=0;assert.deepEqual(value,before);
for(const change of [v=>v.scene_id='other',v=>v.import_sha256='stale',v=>v.display.camera.pitch=-.001,v=>v.display.camera.distance=Infinity,v=>v.display.camera.target.y=null,v=>v.display.layers.actors=1,v=>v.display.runtime={},v=>v.display.camera.projection='invalid']){const bad=structuredClone(value);change(bad);assert.throws(()=>decodeSavedSceneView(bad,state));}
console.log('Saved scene view source/display guards and detached recall passed.');

const front=structuredClone(value);front.display.camera.pitch=0;assert.equal(decodeSavedSceneView(front,state).camera.pitch,0);front.display.camera.projection='perspective';assert.throws(()=>decodeSavedSceneView(front,state));
