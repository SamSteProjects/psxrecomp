import assert from 'node:assert/strict';
import {texturePageUvTarget} from '../editor/uv-texture-region.js';
import {decodeTextureBindingSource} from '../editor/model-texture-binding.js';
const context={sceneId:'scene://town01',sourceKey:'a'.repeat(64)},asset='texture-new://00000000-0000-4000-8000-000000000000';
const source={schema_version:'legaia.material-texture-source.v1',scene_id:context.sceneId,project_source_key:context.sourceKey,asset_id:asset,source_sha256:'b'.repeat(64),effective_sha256:'c'.repeat(64),image_layout:{bpp:16,x:656,y:32,width:64,height:128,width_words:64},palette_index:0,palette_count:0,palette_origin:null,project_changed:false,pages:[{page_index:0,values:{texture_bpp:16,page_column:10,page_row:0},uv_rectangle:[16,32,79,159],image_rectangle:{x:656,y:32,width_words:64,height:128}}]};
const checked=decodeTextureBindingSource(source,context,asset,0),before=structuredClone(checked),target=texturePageUvTarget(checked,0);assert.deepEqual(target,[16,32,79,159]);target[0]=99;assert.deepEqual(checked,before);
for(const index of [-1,1,0.5,true,null])assert.throws(()=>texturePageUvTarget(checked,index));
for(const rectangle of [[0,0,0,255],[0,2,255,2],[2,0,1,255],[0,0,256,255],[false,0,255,255]])assert.throws(()=>texturePageUvTarget({...checked,pages:[{page_index:0,uv_rectangle:rectangle}]},0));
assert.throws(()=>decodeTextureBindingSource({...source,pages:[{...source.pages[0],uv_rectangle:[0,0,63,127]}]},context,asset,0));assert.deepEqual(checked,before);console.log('Qualified native texture-page offset, detached UV target controls, degenerate regions and wrong source rectangles rejected.');

// An indexed image crosses both page axes; rectangles are inclusive native bytes.
const indexed={...structuredClone(source),image_layout:{bpp:8,x:72,y:252,width:400,height:8,width_words:200},palette_index:1,palette_count:2,palette_origin:{x:32,y:480},pages:[]};
for(const [i,x,y,w,h,r] of [[0,72,252,120,4,[16,252,255,255]],[1,192,252,80,4,[0,252,159,255]],[2,72,256,120,4,[16,0,255,3]],[3,192,256,80,4,[0,0,159,3]]])indexed.pages.push({page_index:i,values:{texture_bpp:8,page_column:i%2?3:1,page_row:i<2?0:1,clut_column:2,clut_row:480},uv_rectangle:r,image_rectangle:{x,y,width_words:w,height:h}});
const checkedIndexed=decodeTextureBindingSource(indexed,context,asset,1);assert.deepEqual(texturePageUvTarget(checkedIndexed,3),[0,0,159,3]);assert.equal(checkedIndexed.pages[3].values.clut_row,480);console.log('Indexed multi-page UV byte regions and explicit palette qualification passed.');
