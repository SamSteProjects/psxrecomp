import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {decodeTextureUploadMap,uploadMapHits} from '../editor/texture-upload-map.js';
const sorted=v=>v===null||typeof v!=='object'?v:Array.isArray(v)?v.map(sorted):Object.fromEntries(Object.keys(v).sort().map(k=>[k,sorted(v[k])]));
const rectangles=[{asset_id:null,kind:'boot-upload',rectangle:{x:0,y:456,width_words:192,height:1}},{asset_id:'texture://vell/1/raw/0',kind:'image',rectangle:{x:4,y:450,width_words:4,height:8}}];
const digest=rows=>createHash('sha256').update(JSON.stringify(sorted(rows),null,2)+'\n').digest('hex');
const value={schema_version:'legaia.texture-upload-map.v1',read_only:true,project_changed:false,project_source_key:'a'.repeat(64),scene_id:'scene://vell',asset_id:'texture://vell/1/raw/0',excluded_asset_id:null,coverage:'known-static-scene-authored-and-boot-uploads',runtime_residency_verified:false,vram_width_words:1024,vram_height:512,known_rectangle_count:2,occupancy_sha256:digest(rectangles),rectangles};
const placement={...value};delete placement.rectangles;
const qualified=await decodeTextureUploadMap(value,placement);qualified.rectangles[0].rectangle.x=2;assert.equal(value.rectangles[0].rectangle.x,0);
for(const change of [{asset_id:'other'},{project_source_key:'b'.repeat(64)},{scene_id:'other'},{excluded_asset_id:'other'},{coverage:'live'},{read_only:false},{project_changed:true},{runtime_residency_verified:true},{vram_width_words:512},{known_rectangle_count:3},{extra:true},{occupancy_sha256:'b'.repeat(64)}])await assert.rejects(decodeTextureUploadMap({...value,...change},placement));
for(const row of [{...rectangles[0],asset_id:'texture://other'},{...rectangles[0],kind:'guessed'},{...rectangles[1],asset_id:'script://other'},{...rectangles[0],rectangle:{x:1000,y:456,width_words:192,height:1}},{...rectangles[0],rectangle:{x:0,y:511,width_words:192,height:2}},{...rectangles[0],rectangle:{...rectangles[0].rectangle,x:true}}]){
 const rows=[row,rectangles[1]],v={...value,rectangles:rows,occupancy_sha256:digest(rows)};await assert.rejects(decodeTextureUploadMap(v,{...placement,occupancy_sha256:v.occupancy_sha256}));
}
await assert.rejects(decodeTextureUploadMap({...value,rectangles:[{...rectangles[0],rectangle:{...rectangles[0].rectangle,x:1}},rectangles[1]]},placement));
assert.equal(uploadMapHits(value,4,456).length,2);assert.equal(uploadMapHits(value,192,456).length,0);assert.equal(uploadMapHits(value,4,457).length,1);assert.equal(uploadMapHits(value,-1,456).length,0);
const hits=uploadMapHits(value,4,456);hits[0].rectangle.x=9;assert.equal(value.rectangles[0].rectangle.x,0);
console.log('Static upload map source/occupancy hash, bounded native rectangles, wrapped-tail picking and detached rows passed.');
