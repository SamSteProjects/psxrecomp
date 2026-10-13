import {qualifyPlayerArtInspection} from './player-art-authoring.js';
import {createPlayerArtSampler} from './player-art-animation.js';
import {placementDigest} from './worldmap-placement-replay.js';
import {sourcePngPixels} from './battle-sideband.js';
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b)),fail=()=>{throw Error('PLAYER art export differs from the qualified source assembly and channels.');};
const absent=(v,keys)=>keys.every(k=>!Object.hasOwn(v,k));

export async function qualifyPlayerArtExport(value,arts,models,record,selection,held){
  const {mode,frame_index:frame,fps}=selection;
  if(!['pose','clip'].includes(mode)||mode==='pose'&&(!Number.isSafeInteger(frame)||fps!==null)||mode==='clip'&&(frame!==null||!Number.isFinite(fps)||fps<1||fps>120)||value?.schema_version!=='legaia.player-art-export.v1'||value.mode!==mode||value.frame_index!==frame||value.fps!==fps||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||!same(value.playback,held))fail();
  const sampler=await createPlayerArtSampler(value.playback,arts,models,record,selection);
  return qualifyGeometryExport(value,value.playback,sampler,selection);
}

export async function qualifyPlayerArtCurrentExport(value,arts,models,record,selection,held){
  if(value?.schema_version!=='legaia.player-art-current-export.v1'||value.motion_layer!=='current'||!same(value.inspection,held)||!same(value.playback,held.base_playback)||value.mode!==selection.mode||value.frame_index!==selection.frame_index||value.fps!==selection.fps||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false)fail();
  const q=await qualifyPlayerArtInspection(held,arts,models,record,selection,held.frame_index,held.part_index),motion={layer:'current',current_slot_sha256:held.current_slot_sha256,current_body_sha256:held.current_body_sha256,decoded_sha256:await placementDigest(Uint8Array.from(atob(held.current_decoded_base64),c=>c.charCodeAt(0))),owners:held.owners};
  if(!['pose','clip'].includes(selection.mode)||selection.mode==='pose'&&(!Number.isSafeInteger(selection.frame_index)||selection.fps!==null)||selection.mode==='clip'&&(selection.frame_index!==null||!Number.isFinite(selection.fps)||selection.fps<1||selection.fps>120))fail();
  return qualifyGeometryExport(value,held.base_playback,q.sampler,selection,motion);
}

async function qualifyGeometryExport(value,receipt,sampler,selection,motion=null){
  const {mode,frame_index:frame,fps}=selection,base=receipt.base_inspection,g=base.geometry,a=value.audit;
  const posed=mode==='pose'?sampler.sample(frame):null,geometry=posed?.geometry??g;
  const source={model:base.record.source_record,current_sha256:receipt.effective_file_sha256,player_assembly:base.assembly,stream:receipt.stream.source_record,art_record:receipt.art_record,layer:receipt.layer,...(motion?{motion}:{})};
  const animation={semantic_id:receipt.stream.semantic_id,label:receipt.stream.name,source_record:receipt.stream.source_record,timing:'not_observed',archive_selection:receipt.archive_selection,...(motion?{motion_layer:'current'}:{}),...(posed?{source_frame_index:frame}:{})};
  const suffix=posed?`frame-${frame}`:'clip',filename=`player-art-${motion?'current-motion-':''}${receipt.stream.player_index}-${receipt.stream.archive_role}-${receipt.stream.stream_index}-${receipt.layer}-${suffix}.glb`;
  if(value.filename!==filename||a?.schema_version!=='legaia.model-export.v1'||a.asset_semantic_id!==g.semantic_id||!same(a.source_record,source)||a.reference_commit!==g.reference_commit||a.representation!==(motion?'player-art-current-motion-selected-equipment-assembly':'player-art-selected-equipment-assembly')||a.posed!==!!posed||a.frame_index!==(posed?0:null)||!same(a.animation,animation)||!same(a.object_transforms,posed?.object_transforms??null)||a.object_count!==g.objects.length||a.triangle_count!==g.triangles.length||a.source_coordinate_system!==geometry.coordinate_system||a.coordinate_conversion!=='[x,-y,z]; reverse triangle winding'||typeof value.glb_base64!=='string'||value.glb_base64.length>44*1024*1024)fail();
  if(!posed&&(a.full_clip!==true||a.frame_count!==sampler.frameCount||a.export_fps!==fps||a.interpolation!=='STEP'||a.duration_seconds!==sampler.frameCount/fps||a.timing_evidence!=='caller_selected_rate_not_verified_retail_timing'))fail();
  const data=Uint8Array.from(atob(value.glb_base64),c=>c.charCodeAt(0)),v=new DataView(data.buffer);
  if(data.length<28||data.length>32*1024*1024||a.byte_length!==data.length||await placementDigest(data)!==a.sha256||v.getUint32(0,true)!==0x46546c67||v.getUint32(4,true)!==2||v.getUint32(8,true)!==data.length||v.getUint32(16,true)!==0x4e4f534a)fail();
  const binAt=20+v.getUint32(12,true);if(binAt+8>data.length||v.getUint32(binAt+4,true)!==0x004e4942||binAt+8+v.getUint32(binAt,true)!==data.length)fail();
  const doc=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(data.subarray(20,binAt))),binary=data.subarray(binAt+8),embedded=Object.fromEntries(Object.entries(a).filter(([k])=>!['sha256','byte_length'].includes(k)));
  if(doc.asset?.version!=='2.0'||!same(doc.extras,embedded)||doc.skins||doc.extensions||doc.buffers?.length!==1||doc.buffers[0].uri||doc.buffers[0].byteLength!==binary.length||doc.nodes?.length!==g.objects.length||doc.meshes?.length>g.objects.length||doc.accessors?.length>4096||doc.bufferViews?.length>4096||doc.scenes?.length!==1||doc.scene!==0||!same(doc.scenes[0].nodes,g.objects.map((_,i)=>i)))fail();
  const read=(index,n,count)=>{const ac=doc.accessors?.[index],b=doc.bufferViews?.[ac?.bufferView];if(!ac||!b||ac.componentType!==5126||ac.type!==['','SCALAR','VEC2','VEC3','VEC4'][n]||ac.count!==count||ac.sparse||ac.normalized||(ac.byteOffset??0)!==0||b.buffer!==0||b.byteStride||!Number.isSafeInteger(b.byteOffset)||b.byteOffset<0||b.byteLength!==count*n*4||b.byteOffset+b.byteLength>binary.length)fail();const view=new DataView(binary.buffer,binary.byteOffset+b.byteOffset,b.byteLength);return Array.from({length:count},(_,i)=>Array.from({length:n},(_,j)=>view.getFloat32((i*n+j)*4,true)));};
  const exact=(actual,expected)=>{if(!same(actual,expected.map(row=>row.map(Math.fround))))fail();};
  const textures=g.textures.filter(t=>t.status==='address_match').sort((a,b)=>a.material_index-b.material_index);
  if(doc.materials?.length!==g.materials.length||!same(doc.extensionsUsed,['KHR_materials_unlit'])||(doc.textures?.length??0)!==textures.length)fail();
  for(const [i,m]of doc.materials.entries()){const t=textures.find(t=>t.material_index===i),image=t?textures.indexOf(t):null;if(!same(m.extras?.retail_material,g.materials[i])||m.doubleSided!==true||!same(m.extensions,{KHR_materials_unlit:{}})||m.pbrMetallicRoughness?.metallicFactor!==0||m.pbrMetallicRoughness?.roughnessFactor!==1)fail();if(t){if(!same(m.pbrMetallicRoughness.baseColorTexture,{index:image})||m.alphaMode!=='MASK'||m.alphaCutoff!==.5||!same(doc.textures[image],{source:image,sampler:0})||!same(m.extras.texture_source_ids,t.source_ids??[]))fail();}else if(m.pbrMetallicRoughness.baseColorTexture)fail();}
  if(textures.length&&!same(doc.samplers,[{magFilter:9728,minFilter:9728,wrapS:33071,wrapT:33071}]))fail();
  const frames=posed?null:Array.from({length:sampler.frameCount},(_,i)=>sampler.sample(i).object_transforms);
  for(const [i,node]of doc.nodes.entries()){
    const object=g.objects[i];if(!same(node.extras?.source_object,object)||!absent(node,['matrix','scale','children','skin','weights','extensions']))fail();
    if(posed&&!absent(node,['translation','rotation']))fail();
    if(!object.triangle_count){if(Object.hasOwn(node,'mesh'))fail();}else{
      const mesh=doc.meshes[node.mesh];if(!mesh||!absent(mesh,['weights','extensions']))fail();const materials=new Set();
      for(const p of mesh.primitives){if(p.mode!==4||!absent(p,['indices','targets','extensions'])||materials.has(p.material))fail();materials.add(p.material);const positions=[],colors=[],uvs=[],texture=textures.find(t=>t.material_index===p.material);if(!same(Object.keys(p.attributes??{}).sort(),(texture?['POSITION','COLOR_0','TEXCOORD_0']:['POSITION','COLOR_0']).sort()))fail();
        for(let t=object.triangle_start;t<object.triangle_start+object.triangle_count;t++)if(g.triangle_materials[t]===p.material)for(const corner of [0,2,1]){const [x,y,z]=geometry.vertices[g.triangles[t][corner]];positions.push([x,-y,z]);colors.push(g.triangle_colors[t][corner].map(n=>texture?Math.min(1,n/128):n/255<=.04045?n/255/12.92:((n/255+.055)/1.055)**2.4));if(texture){const [u,v]=g.triangle_uvs[t][corner];uvs.push([(u-texture.uv_origin[0]+.5)/texture.width,(v-texture.uv_origin[1]+.5)/texture.height]);}}
        exact(read(p.attributes?.POSITION,3,positions.length),positions);exact(read(p.attributes.COLOR_0,3,colors.length),colors);if(texture)exact(read(p.attributes.TEXCOORD_0,2,uvs.length),uvs);
      }
      if(!same([...materials].sort((a,b)=>a-b),[...new Set(g.triangle_materials.slice(object.triangle_start,object.triangle_start+object.triangle_count))].sort((a,b)=>a-b)))fail();
    }
    if(!posed){const clip=doc.animations?.[0];if(doc.animations.length!==1||clip.channels?.length!==g.objects.length*2||clip.samplers?.length!==g.objects.length*2)fail();
      for(const path of ['translation','rotation']){const channels=clip.channels.filter(c=>c.target?.node===i&&c.target.path===path);if(channels.length!==1)fail();const channel=clip.samplers[channels[0].sampler];if(channel?.interpolation!=='STEP')fail();exact(read(channel.input,1,sampler.frameCount+1),Array.from({length:sampler.frameCount+1},(_,f)=>[f/fps]));
        const expected=frames.map(ts=>{const t=ts[i];if(path==='translation')return [t.translation[0],-t.translation[1],t.translation[2]];const [rx,ry,rz]=t.rotation_psx.map(n=>n*Math.PI/4096),sx=Math.sin(rx),cx=Math.cos(rx),sy=Math.sin(ry),cy=Math.cos(ry),sz=Math.sin(rz),cz=Math.cos(rz),q=[-(sx*cy*cz-cx*sy*sz),cx*sy*cz+sx*cy*sz,-(cx*cy*sz-sx*sy*cz),cx*cy*cz+sx*sy*sz],norm=Math.hypot(...q);return q.map(n=>n/norm);});expected.push(expected.at(-1));const actual=read(channel.output,path==='translation'?3:4,expected.length);
        for(let f=0;f<actual.length;f++)for(let k=0;k<actual[f].length;k++)if(!Number.isFinite(actual[f][k])||Math.abs(actual[f][k]-expected[f][k])>1e-6)fail();
        if(!Array.isArray(node[path])||node[path].length!==expected[0].length||node[path].some((n,k)=>!Number.isFinite(n)||Math.abs(n-expected[0][k])>1e-10))fail();
      }
    }
  }
  if(posed&&doc.animations)fail();
  if(a.texture_count!==textures.length||(doc.images?.length??0)!==textures.length)fail();
  for(const [i,image]of (doc.images??[]).entries()){const b=doc.bufferViews[image.bufferView],t=textures[i];if(image.uri||image.mimeType!=='image/png'||!b||b.buffer!==0||!Number.isSafeInteger(b.byteOffset)||b.byteOffset<0||!Number.isSafeInteger(b.byteLength)||b.byteLength<1||b.byteOffset+b.byteLength>binary.length)fail();const rgba=await sourcePngPixels(binary.subarray(b.byteOffset,b.byteOffset+b.byteLength),t.width,t.height),expected=Uint8Array.from(atob(t.rgba_base64),c=>c.charCodeAt(0));if(!same([...rgba],[...expected]))fail();}
  return data;
}
