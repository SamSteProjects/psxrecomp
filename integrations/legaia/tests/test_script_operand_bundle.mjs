import assert from 'node:assert/strict';
import {decodeOperandBundleReview} from '../editor/script-operand-bundle.js';
const scene='scene://fixture',hash='a'.repeat(64),ids=['scene://fixture/actors/man-p1/0001','scene://fixture/scripts/man-p2/0000'];
const owners=ids.map(owner_id=>({owner_id,components:{ScriptFlags:{entries:{['script://'+owner_id.slice(8)+'/flag-bit/0000']:{bit:3}}}}}));
const file={schema_version:'legaia.script-operand-bundle.v1',scene_id:scene,source_import_sha256:hash,owners:owners.slice().reverse()};
const reviews=owners.map(row=>({schema_version:'legaia.script-operand-review.v1',scene_id:scene,source_import_sha256:hash,owner_id:row.owner_id,review_key:'b'.repeat(64),change_count:1,entries:[{component:'ScriptFlags',operand_id:Object.keys(row.components.ScriptFlags.entries)[0],before:null,after:{bit:3},changed:true}]}));
const value={schema_version:'legaia.script-operand-bundle-review.v1',scene_id:scene,source_import_sha256:hash,review_key:'c'.repeat(64),owner_count:2,change_count:2,owners:reviews};const decoded=decodeOperandBundleReview(value,file,scene);decoded.owners[0].entries[0].after.bit=4;assert.equal(value.owners[0].entries[0].after.bit,3);
for(const mutate of [v=>v.owner_count=1,v=>v.change_count=1,v=>v.owners.reverse(),v=>v.scene_id='other',v=>v.owners[1].entries[0].after.bit=4]){const bad=structuredClone(value);mutate(bad);assert.throws(()=>decodeOperandBundleReview(bad,file,scene));}
const duplicate=structuredClone(file);duplicate.owners[1]=duplicate.owners[0];assert.throws(()=>decodeOperandBundleReview(value,duplicate,scene));
console.log('Canonical mixed-owner bundle identity, exact individual entry reviews, totals and detached response guards passed.');
