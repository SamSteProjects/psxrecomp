// GLB display dependencies are evidence for image selection, never native ownership.
import {decodeTextureGlbImages} from './texture-png.js';
const fail=m=>{throw new Error(m);};
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const integer=(v,min,max)=>Number.isInteger(v)&&v>=min&&v<=max;
const roles=['base_color','metallic_roughness','normal','occlusion','emissive'];
const features=['baseColorFactor','metallicFactor','roughnessFactor','emissiveFactor','alphaMode','alphaCutoff','doubleSided','extensions'];
const index=(v,size,nullable=false)=>nullable&&v===null||integer(v,0,size-1);
export function decodeGlbDependencies(v,glbHash){
  if(new TextEncoder().encode(JSON.stringify(v)).length>2*1024*1024||!exact(v,['schema_version','catalog','texture_links','materials','primitive_uses','mesh_count','sampler_count','primitive_count','read_only','project_changed','native_binding_inferred','limitations'])||v.schema_version!=='legaia.texture-glb-dependencies.v1'||v.read_only!==true||v.project_changed!==false||v.native_binding_inferred!==false||!integer(v.mesh_count,0,1024)||!integer(v.sampler_count,0,256)||!integer(v.primitive_count,0,4096)||!Array.isArray(v.texture_links)||v.texture_links.length>256||!Array.isArray(v.materials)||v.materials.length>256||!Array.isArray(v.primitive_uses)||v.primitive_uses.length!==v.primitive_count||!Array.isArray(v.limitations)||v.limitations.length>16||v.limitations.some(t=>typeof t!=='string'||t.length>2048))fail('GLB dependency graph differs from its readonly source or budget.');
  decodeTextureGlbImages(v.catalog,glbHash);
  for(const [i,t] of v.texture_links.entries())if(!exact(t,['texture_index','image_index','sampler_index','has_extensions'])||t.texture_index!==i||!index(t.image_index,v.catalog.image_count,true)||!index(t.sampler_index,v.sampler_count,true)||typeof t.has_extensions!=='boolean')fail('GLB texture dependency has an invalid image or sampler identity.');
  for(const [i,m] of v.materials.entries()){
    if(!exact(m,['material_index','name','links','shader_features'])||m.material_index!==i||!(m.name===null||typeof m.name==='string'&&m.name.length<=256&&!/[\x00-\x1f]/.test(m.name))||!Array.isArray(m.links)||m.links.length>5||!Array.isArray(m.shader_features)||m.shader_features.length>8||m.shader_features.some((f,i)=>!features.includes(f)||i&&features.indexOf(f)<=features.indexOf(m.shader_features[i-1])))fail('GLB material dependency is malformed.');
    for(const [j,l] of m.links.entries())if(!exact(l,['role','texture_index','texcoord','has_extensions'])||!roles.includes(l.role)||j&&roles.indexOf(l.role)<=roles.indexOf(m.links[j-1].role)||!index(l.texture_index,v.texture_links.length)||!integer(l.texcoord,0,7)||typeof l.has_extensions!=='boolean')fail('GLB material texture link is malformed.');
  }
  let lastMesh=-1,lastPrimitive=-1;
  for(const p of v.primitive_uses){if(!exact(p,['mesh_index','primitive_index','material_index'])||!index(p.mesh_index,v.mesh_count)||!integer(p.primitive_index,0,4095)||!index(p.material_index,v.materials.length,true)||p.mesh_index<lastMesh||p.mesh_index===lastMesh&&p.primitive_index!==lastPrimitive+1||p.mesh_index!==lastMesh&&p.primitive_index!==0)fail('GLB mesh primitive dependency is malformed or duplicated.');lastMesh=p.mesh_index;lastPrimitive=p.primitive_index;}
  return structuredClone(v);
}
export async function loadGlbImageDependencies(post,contentBase64,glbHash){
  try{const graph=decodeGlbDependencies(await post('/api/texture-glb-dependencies',{content_base64:contentBase64},2*1024*1024),glbHash);return {graph,catalog:graph.catalog,issue:null};}
  catch(error){if(error?.name==='AbortError')throw error;const catalog=decodeTextureGlbImages(await post('/api/texture-glb-images',{content_base64:contentBase64},262144),glbHash);return {graph:null,catalog,issue:String(error?.message??'Unsupported GLB dependency graph').slice(0,512)};}
}
export function glbImageUses(graph,imageIndex){
  if(!integer(imageIndex,0,graph.catalog.image_count-1))fail('Choose an image from the qualified GLB.');
  const links=[];
  for(const material of graph.materials)for(const link of material.links){const texture=graph.texture_links[link.texture_index];if(texture.image_index!==imageIndex)continue;links.push({materialIndex:material.material_index,name:material.name,role:link.role,texcoord:link.texcoord,textureIndex:texture.texture_index,samplerIndex:texture.sampler_index,hasExtensions:texture.has_extensions||link.has_extensions||material.shader_features.includes('extensions'),shaderFeatures:material.shader_features,primitives:graph.primitive_uses.filter(p=>p.material_index===material.material_index)});}
  return structuredClone(links);
}
export function renderGlbDependencies(host,graph,imageIndex,issue=null){
  host.replaceChildren();if(!graph){if(issue){const note=document.createElement('p');note.className='field-note';note.textContent='GLB dependency inspection unavailable: '+issue+'. Embedded PNG selection remains separately verified.';host.append(note);}return;}
  const make=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
  const rows=glbImageUses(graph,imageIndex),details=make('details'),summary=make('summary',`GLB image ${imageIndex} dependencies - ${rows.length} material texture links`);details.append(summary);
  const note=make('p','These are GLB display references. Native texture pages, palettes and model faces require explicit reviewed bindings.');details.append(note);
  if(!rows.length)details.append(make('p','No standard material texture link references this image. It may be unused or referenced through an unsupported extension.'));
  if(rows.length>64)details.append(make('p',`Showing 64 of ${rows.length} material links. The complete dependency evidence contains every qualified link.`));
  for(const row of rows.slice(0,64)){const article=make('section');article.append(make('h4',`Material ${row.materialIndex} - ${row.name??'unnamed'} - ${row.role.replaceAll('_',' ')}`),make('p',`Texture ${row.textureIndex}; UV set ${row.texcoord}; sampler ${row.samplerIndex??'default'}. ${row.hasExtensions?'Extension semantics remain unresolved.':''}`));const uses=row.primitives.map(p=>`Mesh ${p.mesh_index}, primitive ${p.primitive_index}`);article.append(make('p',uses.length?uses.slice(0,32).join('; ')+(uses.length>32?`; ${uses.length-32} more GLB primitive uses`:''):'This material is unused by GLB mesh primitives.'));if(row.shaderFeatures.length)article.append(make('p',`Shader fields retained as display context: ${row.shaderFeatures.join(', ')}.`));details.append(article);}
  const evidence=make('details'),pre=make('pre',JSON.stringify(graph,null,2));pre.style.overflowWrap='anywhere';evidence.append(make('summary','Complete source dependency evidence'),pre);details.append(evidence);host.append(details);
}
