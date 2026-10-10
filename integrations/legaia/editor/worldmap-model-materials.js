import {worldmapCurrentTextureView} from './worldmap-scene.js';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function worldModelPacketAttributes(source,bytes=source.retail){
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),triangle_colors=[],triangle_uvs=[],triangle_materials=[],materials=[],ids=new Map();let total=0;
 for(let i=0;i<source.shape.objects.length;i++){
  const at=12+i*28,vc=v.getUint32(at+4,true),nc=v.getUint32(at+12,true),end=Math.min(...[vc?12+v.getUint32(at,true):bytes.length,nc?12+v.getUint32(at+8,true):bytes.length]);let pos=12+v.getUint32(at+16,true);
  while(pos+4<=end){const count=v.getUint16(pos,true),flags=v.getUint16(pos+2,true);if(!count&&!flags)break;if(pos+8>end||flags<16||flags>39)throw Error('Unsupported native material packet.');const stride=v.getUint8(pos+5)*4,next=pos+8+(count+1)*stride,row=Math.floor((flags-16)/4),corners=flags&2?4:3,textured=[0,1,4,5].includes(row),gouraud=[1,3,5].includes(row),baked=row>=2,uvOffset=row<2?0:gouraud?corners*4:4,colorsCount=gouraud?corners:1;
   if(!count||!stride||next>end||(total+=count)>100000||baked&&colorsCount*4>stride||textured&&uvOffset+(corners===4?12:10)>stride)throw Error('Native material fields exceed their packet.');
   for(let n=0;n<count;n++){const start=pos+8+n*stride,colors=Array.from({length:corners},(_,k)=>baked?[0,1,2].map(a=>v.getUint8(start+(gouraud?k:0)*4+a)):[128,128,128]),uvs=textured?[0,4,8,10].slice(0,corners).map(k=>[v.getUint8(start+uvOffset+k),v.getUint8(start+uvOffset+k+1)]):null,material={textured,clut:textured?v.getUint16(start+uvOffset+2,true):null,tpage:textured?v.getUint16(start+uvOffset+6,true):null,semi_transparent:!!(v.getUint8(pos+7)&2)},key=JSON.stringify(material);
    if(!ids.has(key)){ids.set(key,materials.length);materials.push(material);}for(const used of corners===4?[[0,1,2],[1,3,2]]:[[0,1,2]]){triangle_colors.push(used.map(k=>colors[k]));triangle_uvs.push(uvs?used.map(k=>uvs[k]):null);triangle_materials.push(ids.get(key));}
   }pos=next;
  }
 }
 if(materials.length>64||triangle_materials.length>100000)throw Error('Model materials exceed comparison limits.');return {triangle_colors,triangle_uvs,triangle_materials,materials};
}
export function qualifyWorldModelMaterials(retail,current,{source,receipt,request=receipt?.request,currentGeometry,proposedGeometry,currentView=null}){
 if(retail?.project_source_key!==request.source_key||retail.scene!==request.asset_id.split('/')[2]||retail.project_changed!==false||retail.gameplay_verified!==false||current?.project_changed!==false||current.gameplay_verified!==false)throw Error('Model materials lost their reviewed kingdom source.');
 const view=currentView??worldmapCurrentTextureView(retail,current),asset=view.assets.find(a=>a.asset_id===request.asset_id),original=retail.scene_graph.assets.find(a=>a.asset_id===request.asset_id);
 if(!asset||!original||!same(asset.source_record,source.metadata.source_record)||!same((currentView?asset:original).preview.triangles,currentGeometry.triangles)||!same(currentGeometry.triangles,proposedGeometry.triangles))throw Error('Model material asset differs from its native source.');
 const retailAttrs=worldModelPacketAttributes(source),attrs=worldModelPacketAttributes(source,currentView?source.tmd:source.retail);for(const key of Object.keys(attrs))if(!same(original.preview[key],retailAttrs[key])||currentView&&!same(asset.preview[key],attrs[key]))throw Error('Model material fields differ from literal native packets.');
 return {current:{...structuredClone(currentGeometry),...structuredClone(attrs),textures:structuredClone(asset.preview.textures)},proposed:{...structuredClone(proposedGeometry),...structuredClone(attrs),textures:structuredClone(asset.preview.textures)},texture_authoring:structuredClone(current.texture_authoring)};
}
