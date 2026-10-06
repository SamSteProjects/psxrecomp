import assert from 'node:assert/strict';
import {floorRectangle,decodeFloorRectangle} from '../editor/floor-rectangle.js';
const rectangle={row_start:0,row_end:0,column_start:0,column_end:0,tier:1},key='a'.repeat(64),scene='scene://fixture';
const value={schema_version:'legaia.floor-rectangle-review.v1',project_source_key:key,scene_id:scene,source_sha256:key,review_key:'b'.repeat(64),rectangle,scope:'source-MAP-floor-selectors-only',gameplay_verified:false,project_change:true,selector_count:1,rows:[{row:0,column:0,retail:0,effective:0,proposed:1}],floor_height_lut:Array.from({length:16},(_,i)=>i*16),floor_source_record:{map_sha256:key,disc_sha256:key,man_sha256:key},limitations:[],effective_change_count:1,authored_selector_count:1,audited_selector_count:1,value:{source_sha256:key,edits:[{row:0,column:0,tier:1}]}};
const decoded=decodeFloorRectangle(value,key,scene,rectangle);decoded.rows[0].proposed=2;assert.equal(value.rows[0].proposed,1);
for(const change of [v=>v.project_source_key='c'.repeat(64),v=>v.rows[0].row=1,v=>v.rows[0].proposed=2,v=>v.rows[0].retail=true,v=>v.floor_height_lut[0]=32768,v=>v.floor_source_record.map_sha256='c'.repeat(64),v=>v.effective_change_count=0,v=>v.value.edits[0].tier=true]){const v=structuredClone(value);change(v);assert.throws(()=>decodeFloorRectangle(v,key,scene,rectangle));}
for(const v of [{...rectangle,tier:true},{...rectangle,row_start:-1},{...rectangle,row_end:127,column_end:127},{...rectangle,extra:1}])assert.throws(()=>floorRectangle(v));
console.log('Floor bounds, exact selector qualification, typed MAN LUT, source hashes and detached Review guards passed.');

const current={...rectangle,tier:'current'},cells=[{row:0,column:0,tier:1}],mixed={...structuredClone(value),schema_version:'legaia.floor-rectangle-review.v2',rectangle:current,cell_edits:cells};
assert.deepEqual(decodeFloorRectangle(mixed,key,scene,current,cells),mixed);
assert.throws(()=>decodeFloorRectangle(mixed,key,scene,current,[{row:0,column:0,tier:2}]));
assert.throws(()=>decodeFloorRectangle({...mixed,cell_edits:[...cells,...cells]},key,scene,current,cells));
const keep={...mixed,cell_edits:[],rows:[{row:0,column:0,retail:0,effective:1,proposed:1}],effective_change_count:0};assert.deepEqual(decodeFloorRectangle(keep,key,scene,current),keep);
const restore={...mixed,cell_edits:[{row:0,column:0,tier:'retail'}],rows:[{row:0,column:0,retail:0,effective:1,proposed:0}],authored_selector_count:0,audited_selector_count:0,value:{source_sha256:key,edits:[]}};assert.deepEqual(decodeFloorRectangle(restore,key,scene,current,restore.cell_edits),restore);
console.log('Mixed floor paint Review identity, duplicate rejection, Current preservation and retail restoration passed.');
