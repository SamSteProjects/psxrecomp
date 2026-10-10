const finite=value=>typeof value==='number'&&Number.isFinite(value);
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const fail=message=>{throw new Error(message);};
export function worldmapSceneView(report){
  const graph=report.scene_graph,scene=report.scene;
  if(!graph||graph.schema_version!=='legaia.worldmap-scene-graph.v1'||graph.coordinate_system!=='retail_field_y_down'||graph.matrix_convention!=='column-major-affine'||!Array.isArray(graph.assets)||!graph.assets.length||graph.assets.length>128||!Array.isArray(graph.entities)||!graph.entities.length||graph.entities.length>512)fail('World source scene graph is missing or exceeds its instance budget.');
  const assets=new Map(),entities=new Set();let triangles=0,textureBytes=0;
  for(const asset of graph.assets){
    if(typeof asset.asset_id!=='string'||!asset.asset_id.startsWith(`asset://${scene}/worldmap/`)||assets.has(asset.asset_id)||!asset.source_record||!asset.preview)fail('World source geometry belongs to another kingdom or duplicates an asset.');
    const p=asset.preview;
    if(!Array.isArray(p.vertices)||!p.vertices.length||p.vertices.length>100000||p.vertices.some(row=>!Array.isArray(row)||row.length!==3||row.some(v=>!finite(v)||Math.abs(v)>1000000))||!Array.isArray(p.triangles)||p.triangles.length>100000||!Array.isArray(p.triangle_materials)||p.triangle_materials.length!==p.triangles.length||!Array.isArray(p.materials)||p.materials.length>64||!Array.isArray(p.textures)||p.textures.length>64)fail('World source model geometry exceeds its verified bounds.');
    if(p.triangles.some((row,i)=>!Array.isArray(row)||row.length!==3||row.some(v=>!Number.isSafeInteger(v)||v<0||v>=p.vertices.length)||!Number.isSafeInteger(p.triangle_materials[i])||p.triangle_materials[i]<0||p.triangle_materials[i]>=p.materials.length))fail('World source model references an absent vertex or material.');
    if(asset.asset_id!==report.semantic_id&&!hash(asset.source_record.decoded_member_sha256))fail('World source model member hash is invalid.');
    for(const name of ['triangle_uvs','triangle_colors'])if(!Array.isArray(p[name])||p[name].length!==p.triangles.length)fail('World source model attributes differ from its geometry.');
    p.triangles.forEach((_,i)=>{const uv=p.triangle_uvs[i],colors=p.triangle_colors[i];if(uv!==null&&(!Array.isArray(uv)||uv.length!==3||uv.some(row=>!Array.isArray(row)||row.length!==2||row.some(v=>!finite(v)||v<0||v>256)))||!Array.isArray(colors)||colors.length!==3||colors.some(row=>!Array.isArray(row)||row.length!==3||row.some(v=>!finite(v)||v<0||v>255)))fail('World source model UV or color values are invalid.');});
    const materialSet=new Set();
    for(const texture of p.textures){if(!texture||!Number.isSafeInteger(texture.material_index)||texture.material_index<0||texture.material_index>=p.materials.length||materialSet.has(texture.material_index)||!['address_match','missing','ambiguous','unsupported','untextured'].includes(texture.status))fail('World source model texture ownership or status is invalid.');materialSet.add(texture.material_index);if(texture.status==='address_match'){const pixels=texture.width*texture.height;if(!Number.isSafeInteger(texture.width)||!Number.isSafeInteger(texture.height)||texture.width<1||texture.height<1||pixels>1048576||!Array.isArray(texture.uv_origin)||texture.uv_origin.length!==2||texture.uv_origin.some(v=>!Number.isSafeInteger(v)||v<0||v>255)||typeof texture.rgba_base64!=='string'||texture.rgba_base64.length>Math.ceil(pixels*4/3)*4||!/^[A-Za-z0-9+/]*={0,2}$/.test(texture.rgba_base64)||atob(texture.rgba_base64).length!==pixels*4)fail('World source model texture pixels are invalid.');textureBytes+=pixels*4;if(texture.stp_base64!==undefined){if(typeof texture.stp_base64!=='string'||texture.stp_base64.length>Math.ceil(pixels/3)*4||!/^[A-Za-z0-9+/]*={0,2}$/.test(texture.stp_base64)||atob(texture.stp_base64).length!==pixels)fail('World source model STP pixels are invalid.');textureBytes+=pixels;}}else if(texture.rgba_base64!==undefined||texture.stp_base64!==undefined)fail('Unsupported world source model cannot claim texture pixels.');}
    if(p.textures.length!==p.materials.length||textureBytes>16*1024*1024)fail('World source model texture coverage or byte budget is invalid.');
    triangles+=p.triangles.length;if(triangles>200000)fail('World source model triangle budget exceeded.');
    assets.set(asset.asset_id,{...asset,geometry_key:asset.asset_id});
  }
  if(!assets.has(report.semantic_id))fail('World source scene omits its qualified ground.');
  const inventory=graph.model_pack_coverage;
  if(inventory!==undefined){
    if(!inventory||Object.keys(inventory).sort().join(',')!=='slot_count,supported_count,unsupported'||!Number.isSafeInteger(inventory.slot_count)||inventory.slot_count<1||inventory.slot_count>128||inventory.supported_count!==assets.size-1||!Array.isArray(inventory.unsupported)||inventory.supported_count+inventory.unsupported.length!==inventory.slot_count)fail('World native model inventory coverage differs.');
    const slots=new Set();
    for(const asset of assets.values())if(asset.asset_id!==report.semantic_id){const slot=asset.source_record.pack_slot;if(!Number.isSafeInteger(slot)||slot<0||slot>=inventory.slot_count||slots.has(slot)||asset.asset_id!==`asset://${scene}/worldmap/models/${String(slot).padStart(4,'0')}`)fail('World native model inventory has duplicate or foreign slots.');slots.add(slot);}
    for(const row of inventory.unsupported){if(!row||Object.keys(row).sort().join(',')!=='decoded_member_offset,decoded_member_sha256,decoded_member_span_end,pack_slot,reason'||!Number.isSafeInteger(row.pack_slot)||row.pack_slot<0||row.pack_slot>=inventory.slot_count||slots.has(row.pack_slot)||!hash(row.decoded_member_sha256)||!Number.isSafeInteger(row.decoded_member_offset)||!Number.isSafeInteger(row.decoded_member_span_end)||row.decoded_member_offset<0||row.decoded_member_span_end<=row.decoded_member_offset||row.decoded_member_span_end>graph.source_record.decoded_byte_length||typeof row.reason!=='string'||!row.reason||row.reason.length>8192)fail('Unsupported World model inventory lacks native ownership.');slots.add(row.pack_slot);}
    if(slots.size!==inventory.slot_count)fail('World native model inventory omits a pack slot.');
    const spans=[...assets.values()].filter(a=>a.asset_id!==report.semantic_id).map(a=>a.source_record).concat(inventory.unsupported).sort((a,b)=>a.pack_slot-b.pack_slot);
    for(const [i,row] of spans.entries())if(!Number.isSafeInteger(row.decoded_member_offset)||row.decoded_member_offset<4+4*inventory.slot_count||row.decoded_member_offset%4||row.decoded_member_span_end!==(spans[i+1]?.decoded_member_offset??graph.source_record.decoded_byte_length)||row.decoded_member_span_end<=row.decoded_member_offset)fail('World native model inventory spans overlap or omit native bytes.');
  }
  const instances=graph.entities.map(entity=>{
    const ground=entity.placement_scope==='source_ground';
    if(typeof entity.entity_id!=='string'||entities.has(entity.entity_id)||!(ground?entity.entity_id===`scene://${scene}/worldmap/ground`&&entity.asset_id===report.semantic_id:entity.entity_id.startsWith(`scene://${scene}/worldmap/placements/`))||!assets.has(entity.asset_id)||!['source_ground','source_spawn_seed'].includes(entity.placement_scope)||entity.runtime_visibility!=='not_evaluated'||entity.runtime_resting_position!=='unknown')fail('World source placement ownership or runtime confidence is invalid.');
    entities.add(entity.entity_id);const m=entity.source_to_world,p=entity.source_position;
    if(!Array.isArray(m)||m.length!==16||m.some(v=>!finite(v)||Math.abs(v)>1000000)||m[3]!==0||m[7]!==0||m[11]!==0||m[15]!==1||!p||!['x','y','z'].every(axis=>finite(p[axis]))||m[12]!==p.x||m[13]!==p.y||m[14]!==p.z||!ground&&!hash(entity.source_record_sha256))fail('World source transform differs from its source seed.');
    const matrix=[];for(let row=0;row<4;row++)for(let col=0;col<4;col++)matrix.push(m[col*4+row]*(row===1?-1:1));
    return {...entity,geometry_key:entity.asset_id,renderable:true,model_to_scene:matrix};
  });
  const m=graph.metrics,c=graph.coverage,drawn=instances.reduce((sum,e)=>sum+assets.get(e.asset_id).preview.triangles.length,0);
  if(!m||m.asset_count!==assets.size||m.entity_count!==instances.length||m.stored_triangle_count!==triangles||m.drawn_triangle_count!==drawn||drawn>200000||m.texture_output_bytes!==textureBytes||!c||c.resolved_count!==instances.length-1||c.rendered_count!==instances.length-1||!Number.isSafeInteger(c.unresolved_count)||c.unresolved_count<0||c.candidate_count!==c.resolved_count+c.unresolved_count)fail('World source scene coverage differs from its geometry.');
  if(instances.filter(e=>e.placement_scope==='source_ground').length!==1)fail('World source scene requires exactly one ground entity.');
  return {assets:[...assets.values()],entities:instances};
}


export function worldmapHierarchyRows(sceneView,query='',selectedId=null){
  const entities=sceneView?.entities;
  if(!Array.isArray(entities)||entities.length>512||typeof query!=='string'||query.length>512||selectedId!==null&&typeof selectedId!=='string')fail('World hierarchy filters require bounded source entities and text.');
  const terms=query.trim().toLowerCase().split(/\s+/).filter(Boolean);if(terms.length>16)fail('World hierarchy search is limited to 16 terms.');
  const filters=terms.map(term=>{const match=/^(model|record|cell|id|asset|scope|x|y|z):(.*)$/.exec(term);if(!match)return {text:term};const [,field,value]=match;if(!value||['model','record','cell'].includes(field)&&(!/^[0-9]+$/.test(value)||Number(value)>65535))fail('World hierarchy field filters require an identity or bounded unsigned index.');if(['x','y','z'].includes(field)&&(!/^-?\d+$/.test(value)||Math.abs(Number(value))>131072))fail('World coordinate filters require bounded signed source integers.');return {field,value};});
  const seen=new Set();for(const entity of entities){if(typeof entity?.entity_id!=='string'||!entity.entity_id||entity.entity_id.length>1024||typeof entity.asset_id!=='string'||entity.asset_id.length>1024||seen.has(entity.entity_id))fail('World hierarchy has missing or duplicate source identities.');seen.add(entity.entity_id);}
  if(selectedId!==null&&!seen.has(selectedId))fail('Selected world entity is outside the qualified hierarchy.');
  let matching=0;const rows=[];
  for(const entity of entities){
    const ground=entity.placement_scope==='source_ground',label=ground?'Walk ground':`${entity.placement_scope==='authored_spawn_seed'?entity.entity_id.split('/').pop().slice(0,8):entity.entity_id.split('/').pop()} · model ${entity.model_pool_index} · record ${entity.object_record_index} · ${entity.placement_scope==='authored_spawn_seed'?'authored decoration':'source seed'}`;
    const position=entity.authored_source_position??entity.displayed_source_position??entity.source_position,text=[label,entity.entity_id,entity.asset_id,entity.placement_scope,Number.isSafeInteger(entity.object_record_index)?String(entity.object_record_index).padStart(4,'0'):'',JSON.stringify(entity.source_cell??null),position?`X ${position.x} Y ${position.y} Z ${position.z}`:''].join(' ').toLowerCase(),matches=filters.every(filter=>filter.text?text.includes(filter.text):['x','y','z'].includes(filter.field)?position?.[filter.field]===Number(filter.value):['model','record','cell'].includes(filter.field)?entity[{model:'model_pool_index',record:'object_record_index',cell:'source_cell'}[filter.field]]===Number(filter.value):String(entity[{id:'entity_id',asset:'asset_id',scope:'placement_scope'}[filter.field]]??'').toLowerCase().includes(filter.value));if(matches)matching++;
    if(matches||entity.entity_id===selectedId)rows.push({entityId:entity.entity_id,label:label+(matches?'':' · selected outside filter'),matches});
  }
  return {rows,total:entities.length,matching,selectedOutsideFilter:rows.some(row=>!row.matches)};
}


export function worldmapCurrentTextureView(retail,current){
 const receipt=current?.texture_authoring;
 if(current?.texture_layer!=='current'||current.project_source_key!==retail.project_source_key||!receipt||receipt.schema_version!=='legaia.worldmap-current-textures.v1'||receipt.scene!==retail.scene||receipt.disc_sha256!==retail.source_record.disc_sha256||receipt.scope!=='exact-layout-TIM-payloads-static-material-association'||receipt.gameplay_verified!==false||!Array.isArray(receipt.edits)||receipt.edits.length>128||new Set(receipt.edits.map(e=>e.texture_id)).size!==receipt.edits.length||receipt.edits.some(e=>typeof e.texture_id!=='string'||!e.texture_id.startsWith(`texture://${retail.scene}/kingdom/`)||!hash(e.source_tim_sha256)||!hash(e.effective_tim_sha256)||retail.preview.texture_catalog?.textures?.find(t=>t.semantic_id===e.texture_id)?.decoded_member_sha256!==e.source_tim_sha256||e.source_tim_sha256===e.effective_tim_sha256))fail('Current world texture receipt lost its native source identity.');
 const strip=value=>{const v=structuredClone(value);delete v.texture_layer;delete v.texture_authoring;const previews=[v.preview,...v.scene_graph.assets.map(a=>a.preview)];for(const p of previews)delete p.textures;for(const k of ['texture_output_bytes','matched_texture_count','unsupported_texture_count'])delete v.metrics[k];delete v.scene_graph.metrics.texture_output_bytes;return v;};
 if(JSON.stringify(strip(retail))!==JSON.stringify(strip(current)))fail('Current textures changed native world geometry, source metadata or membership.');
 return worldmapSceneView(current);
}
