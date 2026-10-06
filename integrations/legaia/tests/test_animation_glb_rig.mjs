import assert from 'node:assert/strict';
import {validateRigBinding,validateRigReview} from '../editor/animation-glb-rig.js';
import {withObjectMapping} from '../editor/animation-glb-mapping.js';
const binding={object_count:2,external_object_nodes:[0,1],external_skin_index:0};
const report={external_skin_index:0,external_rig:{skin_index:0,joint_nodes:[0,1,5],mapped_joint_nodes:[0,1],common_root_node:3,skin_mesh_nodes:[4],inverse_bind_accessor:9,inverse_bind_count:3,mesh_skinning_applied:false,scope:'rigid-joint-motion-only',ignored_channels:[{node_index:5,path:'translation'}]}};
validateRigReview(report,binding);validateRigReview({},{});assert.deepEqual(withObjectMapping({object_count:2},'0,1','0'),binding);assert.equal(withObjectMapping(binding,'0,1','').external_skin_index,undefined);
for(const b of [{external_skin_index:0},{...binding,external_skin_index:true},{...binding,external_skin_index:64}])assert.throws(()=>validateRigBinding(b));
for(const text of ['-1','64','0.5','01','skin0'])assert.throws(()=>withObjectMapping(binding,'0,1',text));
for(const change of [r=>r.external_skin_index=1,r=>r.external_rig.skin_index=1,r=>r.external_rig.joint_nodes=[0,0,5],r=>r.external_rig.mapped_joint_nodes=[1,0],r=>r.external_rig.mesh_skinning_applied=true,r=>r.external_rig.inverse_bind_count=2,r=>r.external_rig.skin_mesh_nodes=[0],r=>r.external_rig.ignored_channels=[{node_index:0,path:'rotation'}],r=>r.external_rig.ignored_channels=[{node_index:4,path:'translation'}],r=>r.external_rig.extra=true]){const bad=structuredClone(report);change(bad);assert.throws(()=>validateRigReview(bad,binding));}
assert.throws(()=>validateRigReview(report,{}));console.log('Explicit skin/object binding and source joint/mesh/inverse-bind/ignored-channel Review contracts passed.');
