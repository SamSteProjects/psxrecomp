import assert from 'node:assert/strict';
import {decodeTextureBindingCatalog,decodeTextureBindingSource} from '../editor/model-texture-binding.js';
const context={sceneId:'scene://town01',sourceKey:'a'.repeat(64)},asset='texture://town01/5/raw/0';
const catalog={schema_version:'legaia.material-texture-catalog.v1',scene_id:context.sceneId,project_source_key:context.sourceKey,textures:[{asset_id:asset,label:'Texture 0'}],project_changed:false};
assert.equal(decodeTextureBindingCatalog(catalog,context).length,1);assert.throws(()=>decodeTextureBindingCatalog({...catalog,textures:[...catalog.textures,...catalog.textures]},context));
const source={schema_version:'legaia.material-texture-source.v1',scene_id:context.sceneId,project_source_key:context.sourceKey,asset_id:asset,source_sha256:'b'.repeat(64),effective_sha256:'c'.repeat(64),image_layout:{bpp:4,x:64,y:255,width:268,height:2,width_words:67},palette_index:1,palette_count:2,palette_origin:{x:32,y:480},project_changed:false,pages:[]};
for(const [i,x,y,w] of [[0,64,255,64],[1,128,255,3],[2,64,256,64],[3,128,256,3]])source.pages.push({page_index:i,values:{texture_bpp:4,page_column:x/64,page_row:y===255?0:1,clut_column:2,clut_row:480},uv_rectangle:[0,y%256,w*4-1,y%256],image_rectangle:{x,y,width_words:w,height:1}});
assert.deepEqual(decodeTextureBindingSource(source,context,asset,1),source);
for(const mutate of [s=>s.project_changed=true,s=>s.palette_index=0,s=>s.pages.pop(),s=>s.palette_origin.x=33,s=>s.pages[0].values.page_column=2,s=>s.pages[0].uv_rectangle[2]=254,s=>s.pages[0].image_rectangle.width_words=63,s=>s.effective_sha256='stale']){const s=structuredClone(source);mutate(s);assert.throws(()=>decodeTextureBindingSource(s,context,asset,1));}
