import assert from 'node:assert/strict';
import {decodeTexturePlacement} from '../editor/texture-image-conversion.js';
const request={asset_id:'texture://fixture/1/raw/0',source_key:'a'.repeat(64),bpp:4};
const input={sceneId:'scene://fixture',pngSha256:'b'.repeat(64),pngSize:100};
const report={schema_version:'legaia.texture-placement.v1',read_only:true,project_changed:false,project_source_key:request.source_key,scene_id:input.sceneId,asset_id:request.asset_id,excluded_asset_id:null,png_sha256:input.pngSha256,png_byte_length:100,width:8,height:8,bpp:4,width_words:2,palette_words:16,coverage:'known-static-scene-authored-and-boot-uploads',runtime_residency_verified:false,known_rectangle_count:10,occupancy_sha256:'c'.repeat(64),status:'found',placement:{image_x:0,image_y:0,clut_x:0,clut_y:511},pair_checks:1,search_complete:true,limitations:['Static coverage only.']};
const decoded=decodeTexturePlacement(report,request,input);decoded.placement.image_x=8;assert.equal(report.placement.image_x,0);
for(const change of [{project_source_key:'d'.repeat(64)},{png_sha256:'d'.repeat(64)},{png_byte_length:99},{scene_id:'other'},{asset_id:'other'},{excluded_asset_id:request.asset_id},{bpp:8},{width_words:3},{runtime_residency_verified:true},{project_changed:true},{read_only:false},{known_rectangle_count:8193},{occupancy_sha256:'bad'},{pair_checks:1000001},{search_complete:false},{extra:true},{placement:{...report.placement,image_x:1023}},{placement:{...report.placement,clut_x:1}},{placement:{...report.placement,clut_y:0}}])assert.throws(()=>decodeTexturePlacement({...report,...change},request,input));
for(const status of ['no_fit','search_budget_exhausted']){
 const value={...report,status,placement:null,search_complete:status==='no_fit'};
 assert.equal(decodeTexturePlacement(value,request,input).status,status);
 assert.throws(()=>decodeTexturePlacement({...value,placement:report.placement},request,input));
 assert.throws(()=>decodeTexturePlacement({...value,search_complete:!value.search_complete},request,input));
}
const authored='texture-new://fixture/new';assert.equal(decodeTexturePlacement({...report,asset_id:authored,excluded_asset_id:authored},{...request,asset_id:authored},input).excluded_asset_id,authored);
const direct={...report,bpp:16,width_words:8,palette_words:0,placement:{image_x:0,image_y:0,clut_x:0,clut_y:0}};
assert.equal(decodeTexturePlacement(direct,{...request,bpp:16},input).bpp,16);
assert.throws(()=>decodeTexturePlacement({...direct,placement:{...direct.placement,clut_y:1}},{...request,bpp:16},input));
console.log('Static placement identity, native bounds, palette exclusion, detached replies and search outcomes passed.');
