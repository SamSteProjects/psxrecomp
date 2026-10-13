import {placementDigest} from './worldmap-placement-replay.js';
const ordered=v=>Array.isArray(v)?v.map(ordered):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,ordered(v[k])])):v,same=(a,b)=>JSON.stringify(ordered(a))===JSON.stringify(ordered(b));
const fail=()=>{throw Error('Current pack palette or texture pixels differ from immutable TIM bytes and native CLUT replay.');};
export function paletteBytes(value,max=2*1024*1024){if(typeof value!=='string'||value.length>4*Math.ceil(max/3))fail();try{const b=Uint8Array.from(atob(value),c=>c.charCodeAt(0));if(b.length>max)fail();return b;}catch{fail();}}
export function paletteRGBA(word){return [0,5,10].map(shift=>{const n=word>>shift&31;return n*8+Math.floor(n/4);}).concat(word===0?0:255);}
export async function qualifyPackPaletteContext(context,report,geometry){
 if(context?.schema_version!=='legaia.battle-pack-palette-context.v1'||!context.owners||Array.isArray(context.owners)||typeof context.owners!=='object'||Object.keys(context.owners).length>6)fail();
 const original=paletteBytes(context.retail_entry_base64),current=paletteBytes(context.palette_entry_base64),c=report.catalog;
 if(original.length!==c.source_entry_byte_length||current.length!==original.length||await placementDigest(original)!==c.source_entry_sha256)fail();const expected=original.slice(),d=new DataView(expected.buffer);
 for(const record of c.textures.filter(r=>r.preview_supported)){const s=record.source_record;if(await placementDigest(original.subarray(s.byte_offset,s.byte_offset+s.byte_length))!==s.sha256)fail();}
 for(const [id,owner]of Object.entries(context.owners)){
  const record=c.textures.find(r=>r.semantic_id===id&&r.preview_supported),s=record?.source_record;
  if(!s||owner.schema_version!=='legaia.battle-pack-palette-override.v1'||owner.asset_id!==id||!same(owner.source_record,s)||Object.keys(owner).sort().join(',')!=='asset_id,current_tim_sha256,edits,schema_version,source_record'||!Array.isArray(owner.edits)||!owner.edits.length||owner.edits.length>256)fail();let previous=-1;
  for(const row of owner.edits){const {palette_index:p,entry_index:e,word:w}=row,index=p*16+e,at=s.byte_offset+20+index*2;if(Object.keys(row).sort().join(',')!=='entry_index,palette_index,word'||![p,e,w].every(Number.isSafeInteger)||p<0||p>=16||e<0||e>=16||w<0||w>65535||index<=previous||d.getUint16(at,true)===w)fail();d.setUint16(at,w,true);previous=index;}
  if(await placementDigest(expected.subarray(s.byte_offset,s.byte_offset+s.byte_length))!==owner.current_tim_sha256)fail();
 }
 for(const [id,owner]of Object.entries(context.image_owners??{})){const record=c.textures.find(r=>r.semantic_id===id&&r.preview_supported),source=record?.source_record;if(!source||owner.schema_version!=='legaia.battle-pack-image-override.v1'||owner.asset_id!==id||!same(owner.source_record,source)||owner.index_byte_length!==32768||owner.input?.schema_version!=='legaia.battle-pack-png-input.v1')fail();const at=source.byte_offset+544,image=current.subarray(at,at+32768);if(await placementDigest(image)!==owner.index_sha256)fail();expected.set(image,at);}
 if(expected.some((n,i)=>n!==current[i]))fail();
 if(geometry)qualifyPackTexturePixels(current,c,geometry);
 return current;
}
export function qualifyPackTexturePixels(entry,catalog,geometry){
 const blocks=[],view=new DataView(entry.buffer,entry.byteOffset,entry.byteLength);
 for(const record of catalog.textures.filter(r=>r.preview_supported)){
  const at=record.source_record.byte_offset;if(view.getUint32(at,true)!==16||view.getUint32(at+4,true)!==8||view.getUint32(at+8,true)!==524||view.getUint16(at+16,true)!==256||view.getUint16(at+18,true)!==1||view.getUint32(at+532,true)!==32780||view.getUint16(at+540,true)!==64||view.getUint16(at+542,true)!==256)fail();
  blocks.push({id:record.semantic_id,x:view.getUint16(at+12,true),y:view.getUint16(at+14,true),width:256,height:1,at:at+20},{id:record.semantic_id,x:view.getUint16(at+536,true),y:view.getUint16(at+538,true),width:64,height:256,at:at+544});
 }
 for(const [i,texture]of geometry.textures.entries()){
  if(texture.status!=='address_match')continue;const m=geometry.materials[i],page=m.tpage,clut=m.clut,mode=page>>7&3;if(!m.textured||mode>2||page&~511)fail();const bpp=[4,8,16][mode],px=(page&15)*64,py=(page>>4&1)*256,cx=(clut&63)*16,cy=clut>>6&511,rgba=paletteBytes(texture.rgba_base64,256*256*4),stp=paletteBytes(texture.stp_base64,256*256),used=new Set(),cache=new Map();
  function word(x,y){const key=x+','+y;if(cache.has(key))return cache.get(key);const values=new Set();for(const b of blocks)if(x>=b.x&&x<b.x+b.width&&y>=b.y&&y<b.y+b.height){values.add(view.getUint16(b.at+((y-b.y)*b.width+x-b.x)*2,true));used.add(b.id);}if(values.size!==1)fail();const value=[...values][0];cache.set(key,value);return value;}
  let n=0;for(let v=texture.uv_origin[1];v<texture.uv_origin[1]+texture.height;v++)for(let u=texture.uv_origin[0];u<texture.uv_origin[0]+texture.width;u++){
   let raw=word(px+Math.floor(u*bpp/16),py+v);if(bpp<16){const index=raw>>(u%(16/bpp)*bpp)&((1<<bpp)-1);raw=word(cx+index,cy);}const expected=paletteRGBA(raw);if(expected.some((b,k)=>rgba[n*4+k]!==b)||stp[n]!==raw>>15)fail();n++;
  }
  if(rgba.length!==n*4||stp.length!==n||!same([...used].sort(),texture.source_ids))fail();
 }
}
