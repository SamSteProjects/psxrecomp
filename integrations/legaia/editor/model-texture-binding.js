// Qualified native page regions, independent of model/scene runtime residency.
const fail=m=>{throw new Error(m);},int=(v,a,b)=>Number.isSafeInteger(v)&&v>=a&&v<=b;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const asset=v=>typeof v==='string'&&(v.startsWith('texture://')||/^texture-new:\/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(v))&&v.length<=512;
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
export function decodeTextureBindingCatalog(v,context){
  if(!exact(v,['schema_version','scene_id','project_source_key','textures','project_changed'])||v.schema_version!=='legaia.material-texture-catalog.v1'||v.scene_id!==context.sceneId||v.project_source_key!==context.sourceKey||v.project_changed!==false||!Array.isArray(v.textures)||v.textures.length>4096)fail('Texture catalog differs from the current scene.');
  const seen=new Set();for(const row of v.textures){if(!exact(row,['asset_id','label'])||!asset(row.asset_id)||seen.has(row.asset_id)||typeof row.label!=='string'||!row.label.length||row.label.length>512)fail('Texture catalog has an invalid or duplicate source.');seen.add(row.asset_id);}return structuredClone(v.textures);
}
export function decodeTextureBindingSource(v,context,assetId,paletteIndex){
  if(!exact(v,['schema_version','scene_id','project_source_key','asset_id','source_sha256','effective_sha256','image_layout','palette_index','palette_count','palette_origin','pages','project_changed'])||v.schema_version!=='legaia.material-texture-source.v1'||v.scene_id!==context.sceneId||v.project_source_key!==context.sourceKey||v.asset_id!==assetId||!asset(v.asset_id)||!hash(v.source_sha256)||!hash(v.effective_sha256)||v.palette_index!==paletteIndex||!int(v.palette_index,0,32767)||!int(v.palette_count,0,32768)||v.project_changed!==false)fail('Texture page source differs from the selected source or palette.');
  const l=v.image_layout;if(!exact(l,['bpp','x','y','width','height','width_words'])||![4,8,16].includes(l.bpp)||!int(l.x,0,1023)||!int(l.y,0,511)||!int(l.width,1,4096)||!int(l.height,1,512-l.y)||!int(l.width_words,1,1024-l.x)||l.width*l.bpp!==l.width_words*16)fail('Texture binding has invalid native image bounds.');
  const indexed=l.bpp!==16,p=v.palette_origin;
  if(indexed?(!int(v.palette_count,1,32768)||paletteIndex>=v.palette_count||!exact(p,['x','y'])||!int(p.x,0,1024-(1<<l.bpp))||p.x%16||!int(p.y,0,511)):(v.palette_count!==0||paletteIndex!==0||p!==null))fail('Texture binding has invalid native palette bounds.');
  const firstX=Math.floor(l.x/64)*64,firstY=Math.floor(l.y/256)*256,words=256*l.bpp/16,columns=Math.ceil((l.x+l.width_words-firstX)/words),rows=Math.ceil((l.y+l.height-firstY)/256);
  if(!Array.isArray(v.pages)||v.pages.length!==columns*rows||v.pages.length>32)fail('Texture page regions do not cover the image.');
  for(const [i,row] of v.pages.entries()){
    const px=firstX+i%columns*words,py=firstY+Math.floor(i/columns)*256,left=Math.max(px,l.x),top=Math.max(py,l.y),right=Math.min(px+words,l.x+l.width_words),bottom=Math.min(py+256,l.y+l.height),values=row.values;
    if(!exact(row,['page_index','values','uv_rectangle','image_rectangle'])||row.page_index!==i||!exact(values,['texture_bpp','page_column','page_row',...(indexed?['clut_column','clut_row']:[])])||values.texture_bpp!==l.bpp||values.page_column!==px/64||values.page_row!==py/256||indexed&&(values.clut_column!==p.x/16||values.clut_row!==p.y)||JSON.stringify(row.uv_rectangle)!==JSON.stringify([(left-px)*16/l.bpp,top-py,(right-px)*16/l.bpp-1,bottom-py-1])||!exact(row.image_rectangle,['x','y','width_words','height'])||row.image_rectangle.x!==left||row.image_rectangle.y!==top||row.image_rectangle.width_words!==right-left||row.image_rectangle.height!==bottom-top)fail('Texture page binding contradicts its native source rectangles.');
  }return structuredClone(v);
}
