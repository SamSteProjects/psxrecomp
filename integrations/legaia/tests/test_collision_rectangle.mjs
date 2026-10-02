import assert from 'node:assert/strict';
import {wallRectangle,decodeWallRectangle} from '../editor/collision-rectangle.js';
const rectangle={row_start:1,row_end:1,column_start:0,column_end:0,quadrant:0,blocked:true},key='a'.repeat(64),scene='scene://fixture';
assert.deepEqual(wallRectangle(rectangle),rectangle);
for(const changes of [{row_start:0},{row_end:0},{quadrant:true},{blocked:1},{column_start:2},{row_end:127,column_end:127,quadrant:'all'},{extra:1}])assert.throws(()=>wallRectangle({...rectangle,...changes}));
const review={schema_version:'legaia.collision-rectangle-review.v1',project_source_key:key,review_key:key,source_sha256:key,scene_id:scene,scope:'source-MAP-wall-bits-only',gameplay_verified:false,project_change:true,rectangle:Object.fromEntries(Object.entries(rectangle).reverse()),rows:[{row:1,column:0,quadrant:0,retail:false,effective:false,proposed:true}],wall_bit_count:1,effective_change_count:1,authored_bit_count:1};
assert.deepEqual(decodeWallRectangle(review,key,scene,rectangle).rectangle,rectangle);
for(const changes of [{project_source_key:'f'.repeat(64)},{gameplay_verified:true},{effective_change_count:0},{rows:[...review.rows,...review.rows]},{rows:[{...review.rows[0],quadrant:2}]}])assert.throws(()=>decodeWallRectangle({...review,...changes},key,scene,rectangle));
console.log('Wall rectangle bounds, canonical request, source context and reviewed-bit guards passed.');
