// Decoded instruction references only. This model does not evaluate routes.
const ENTRY_FIELDS=['entry_x_encoded','entry_z_encoded','direction_encoded'];
const COVERAGE=['script_count','partial_script_count','unavailable_script_count'];
const NODE_KEYS=['id','name','imported','roles','in_scene_index'];
const EDGE_KEYS=['id','source','target','script_id','script_name','owner_id','partition','script_status','source_record','reference','reachability','entry_layers'];
const REFERENCE_KEYS=['pc','byte_offset','mnemonic','extended_target','target_scene_name','target_in_scene_index','status','name_byte_length','name_sha256',...ENTRY_FIELDS,'reachability'];
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&[Object.prototype,null].includes(Object.getPrototypeOf(value));
const exact=(value,keys)=>object(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const text=(value,max=8192)=>typeof value==='string'&&value.length>0&&value.length<=max;
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const scene=value=>typeof value==='string'&&/^scene:\/\/[A-Za-z0-9_-]{1,128}$/.test(value);
const compare=(a,b)=>a<b?-1:a>b?1:0;
const fail=message=>{throw new Error('Invalid transition graph: '+message);};

function detached(value,depth=0,budget={items:0,characters:0}){
  if(depth>16||++budget.items>4000000)fail('metadata exceeds its structural bound');
  if(value===null||typeof value==='boolean')return value;
  if(typeof value==='number'){if(!Number.isFinite(value))fail('nonfinite metadata');return value;}
  if(typeof value==='string'){budget.characters+=value.length;if(value.length>8192||budget.characters>64*1024*1024)fail('metadata text exceeds its bound');return value;}
  if(Array.isArray(value)){if(value.length>16448)fail('metadata list exceeds its bound');return value.map(child=>detached(child,depth+1,budget));}
  if(!object(value)||Object.keys(value).length>128)fail('metadata object is unsupported');
  return Object.fromEntries(Object.entries(value).map(([key,child])=>{if(!text(key,256)||['raw_hex','encoded_hex','raw_bytes','payload','tokens','rgba','stp','scene_name_bytes_hex'].includes(key))fail('private payload fields are unsupported');budget.characters+=key.length;return [key,detached(child,depth+1,budget)];}));
}
function coverage(value,max){
  if(!exact(value,COVERAGE)||COVERAGE.some(key=>!integer(value[key],0,max))||value.partial_script_count+value.unavailable_script_count>value.script_count)fail('source coverage');
}
function importedSet(value){
  if(!Array.isArray(value)||value.length<1||value.length>64||value.some(id=>!scene(id))||new Set(value).size!==value.length)fail('imported scene context');
  return new Set(value);
}
function sourceRecord(value,match,reference){
  const partition=match[2]==='actors/man-p1'?1:2;
  if(!object(value)||value.partition!==partition||value.record_index!==Number(match[3])||!integer(value.byte_offset,0,4*1024*1024)||!integer(value.byte_length,1,65536)||value.byte_offset+value.byte_length>4*1024*1024||!text(value.byte_coordinate_space,256)||!hash(value.sha256)||reference.byte_offset!==value.byte_offset+reference.pc||reference.pc+7+Number(reference.extended_target!==null)+reference.name_byte_length>value.byte_length)fail('source record identity, hash or instruction extent');
  for(const [key,min,max] of [['prot_entry_index',0,0xffffffff],['compressed_stream_offset',0,0xffffffff],['compressed_bytes_consumed',1,0xffffffff],['record_alias_count',1,8192],['containing_decoded_size',1,4*1024*1024]])if(Object.hasOwn(value,key)&&!integer(value[key],min,max))fail('source provenance bounds');
  if(Object.hasOwn(value,'prot_entry_name')&&value.prot_entry_name!==match[1]||Object.hasOwn(value,'iso_file')&&value.iso_file!=='PROT.DAT'||Object.hasOwn(value,'disc')&&(!exact(value.disc,['sha256','serial'])||!hash(value.disc.sha256)||value.disc.serial!=='SCUS-94254'))fail('source provenance differs from its scene');
  if(Object.hasOwn(value,'containing_decoded_size')&&value.byte_offset+value.byte_length>value.containing_decoded_size||Object.hasOwn(value,'compressed_stream_offset')&&Object.hasOwn(value,'compressed_bytes_consumed')&&value.compressed_stream_offset+value.compressed_bytes_consumed>0xffffffff)fail('source containing extent');
}
function edgeRecord(edge,nodes,sources){
  if(!exact(edge,EDGE_KEYS)||!text(edge.script_name,512)||!['decoded_supported_paths','partial'].includes(edge.script_status)||edge.reachability!=='not_evaluated')fail('edge metadata or runtime reachability claim');
  const match=typeof edge.script_id==='string'&&/^script:\/\/([A-Za-z0-9_-]{1,128})\/(actors\/man-p1|scripts\/man-p2)\/([0-9]{4})$/.exec(edge.script_id);
  if(!match||edge.source!=='scene://'+match[1]||edge.owner_id!==edge.script_id.replace(/^script:\/\//,'scene://')||edge.partition!==(match[2]==='actors/man-p1'?1:2)||!sources.has(edge.source)||!nodes.has(edge.source)||!nodes.has(edge.target))fail('source owner or dangling endpoint');
  const reference=edge.reference;
  if(!exact(reference,REFERENCE_KEYS)||!integer(reference.pc,0,65535)||!integer(reference.byte_offset,0,4*1024*1024)||reference.mnemonic!=='SCENE_CHANGE'||!(reference.extended_target===null||integer(reference.extended_target,0,255))||!integer(reference.name_byte_length,0,255)||!hash(reference.name_sha256)||reference.reachability!=='not_evaluated'||ENTRY_FIELDS.some(key=>!integer(reference[key],0,255)))fail('decoded reference');
  const pc=reference.pc.toString(16).padStart(4,'0'),id=edge.script_id.replace(/^script:\/\//,'transition://')+'/'+pc,target=nodes.get(edge.target);
  if(edge.id!==id)fail('edge identity differs from its source instruction');
  if(reference.target_scene_name===null){
    if(reference.target_in_scene_index!==null||reference.status!=='unsupported_name_encoding'||edge.target!==id+'/unresolved-target'||target.name!==null||target.imported!==false||target.in_scene_index!==null)fail('unresolved destination was invented');
  }else if(typeof reference.target_scene_name!=='string'||!/^[a-z0-9]{1,12}$/.test(reference.target_scene_name)||reference.name_byte_length!==reference.target_scene_name.length||typeof reference.target_in_scene_index!=='boolean'||reference.status!=='encoded_named_reference'||edge.target!=='scene://'+reference.target_scene_name||target.name!==reference.target_scene_name||!target.roles.includes('source')&&target.in_scene_index!==reference.target_in_scene_index)fail('named destination differs from its encoded reference');
  sourceRecord(edge.source_record,match,reference);
  const layers=edge.entry_layers;
  if(!exact(layers,['imported','authored','effective','validation','transition_id'])||!exact(layers.imported,ENTRY_FIELDS)||!exact(layers.effective,ENTRY_FIELDS)||!object(layers.authored)||Object.keys(layers.authored).some(key=>!ENTRY_FIELDS.includes(key))||ENTRY_FIELDS.some(key=>layers.imported[key]!==reference[key]||!integer(layers.effective[key],0,255)||Object.hasOwn(layers.authored,key)&&!integer(layers.authored[key],0,255)||layers.effective[key]!==((Object.hasOwn(layers.authored,key)?layers.authored:layers.imported)[key]))||layers.transition_id!==edge.script_id+'/transition/'+pc||layers.validation!==(Object.keys(layers.authored).length?'reverified_on_build':'imported_reference')||reference.target_scene_name===null&&Object.keys(layers.authored).length)fail('imported, authored or effective entry bytes');
}

export function decodeTransitionGraph(data,context){
  if(!object(context)||typeof context.projectWide!=='boolean'||!hash(context.sourceKey)||!text(context.projectPath,8192))fail('current project context');
  const imports=importedSet(context.sceneIds),projectWide=context.projectWide,graph=detached(data);
  const keys=projectWide?['schema_version','read_only','project_path','source_key','scene_ids','nodes','edges','scenes','coverage','limitations']:['schema_version','read_only','scene_id','nodes','edges','coverage','limitations','source_key','transition_state_key'];
  if(!exact(graph,keys)||graph.schema_version!==(projectWide?'legaia.project-transitions.v1':'legaia.scene-transitions.v1')||graph.read_only!==true||graph.source_key!==context.sourceKey||projectWide&&graph.project_path!==context.projectPath||!projectWide&&(!scene(context.sceneId)||!imports.has(context.sceneId)||graph.scene_id!==context.sceneId||!hash(graph.transition_state_key)||Object.hasOwn(context,'transitionStateKey')&&graph.transition_state_key!==context.transitionStateKey))fail('schema, read-only or stale source context');
  if(!Array.isArray(graph.nodes)||graph.nodes.length<1||graph.nodes.length>16448||!Array.isArray(graph.edges)||graph.edges.length>16384||!Array.isArray(graph.limitations)||graph.limitations.length>64||graph.limitations.some(note=>!text(note)))fail('graph bounds or limitations');
  coverage(graph.coverage,projectWide?65536:1024);
  const sources=new Map(),sceneReports=new Map();
  if(projectWide){
    const declared=importedSet(graph.scene_ids);if(declared.size!==imports.size||[...declared].some(id=>!imports.has(id)))fail('project imported scenes changed');
    if(!Array.isArray(graph.scenes)||graph.scenes.length!==imports.size)fail('project source coverage records');
    const sums=Object.fromEntries(COVERAGE.map(key=>[key,0]));
    for(const row of graph.scenes){
      if(!object(row)||!imports.has(row.scene_id)||row.scene_name!==row.scene_id.slice(8)||sceneReports.has(row.scene_id)||!['verified','unavailable'].includes(row.status))fail('source scene identity or duplicate coverage');
      if(row.status==='verified'){if(!exact(row,['scene_id','scene_name','status','reference_count','coverage'])||!integer(row.reference_count,0,16384))fail('verified source coverage');coverage(row.coverage,1024);sources.set(row.scene_id,row.coverage);for(const key of COVERAGE)sums[key]+=row.coverage[key];}
      else if(!exact(row,['scene_id','scene_name','status','reason'])||!text(row.reason))fail('unavailable source reason');
      sceneReports.set(row.scene_id,row);
    }
    if(COVERAGE.some(key=>graph.coverage[key]!==sums[key]))fail('project coverage totals');
  }else sources.set(graph.scene_id,graph.coverage);
  const nodes=new Map();
  for(const node of graph.nodes){
    if(!exact(node,NODE_KEYS)||!text(node.id,1024)||nodes.has(node.id)||typeof node.imported!=='boolean'||!Array.isArray(node.roles)||node.roles.length>2||new Set(node.roles).size!==node.roles.length||node.roles.some(role=>!['source','destination'].includes(role)))fail('node identity, roles or duplicates');
    if(scene(node.id)){if(node.name!==node.id.slice(8)||node.imported!==imports.has(node.id)||typeof node.in_scene_index!=='boolean')fail('scene node metadata');}
    else if(!/^transition:\/\/[A-Za-z0-9_-]{1,128}\/(?:actors\/man-p1|scripts\/man-p2)\/[0-9]{4}\/[0-9a-f]{4}\/unresolved-target$/.test(node.id)||node.name!==null||node.imported!==false||node.in_scene_index!==null)fail('unresolved node identity');
    if(node.roles.includes('source')!==sources.has(node.id))fail('source role differs from inspected scene coverage');
    nodes.set(node.id,node);
  }
  for(const id of projectWide?imports:[graph.scene_id])if(!nodes.has(id))fail('imported source node is missing');
  const ids=new Set(),incoming=new Set(),counts=new Map(),owners=new Map(),partialOwners=new Map(),scripts=new Map();
  for(const edge of graph.edges){
    edgeRecord(edge,nodes,sources);if(ids.has(edge.id))fail('duplicate instruction edge');ids.add(edge.id);incoming.add(edge.target);counts.set(edge.source,(counts.get(edge.source)??0)+1);
    const previous=scripts.get(edge.script_id);if(previous&&(previous.script_name!==edge.script_name||previous.script_status!==edge.script_status||['byte_offset','byte_length','sha256','byte_coordinate_space','partition','record_index'].some(key=>previous.source_record[key]!==edge.source_record[key])))fail('parallel references disagree about their source script');scripts.set(edge.script_id,edge);
    const rowOwners=owners.get(edge.source)??new Set();rowOwners.add(edge.owner_id);owners.set(edge.source,rowOwners);
    if(edge.script_status==='partial'){const partial=partialOwners.get(edge.source)??new Set();partial.add(edge.owner_id);partialOwners.set(edge.source,partial);}
  }
  for(const node of graph.nodes)if(node.roles.includes('destination')!==incoming.has(node.id)||!node.roles.length&&!imports.has(node.id))fail('destination role or orphan endpoint');
  for(const [id,value] of sources){if((owners.get(id)?.size??0)>value.script_count-value.unavailable_script_count||(partialOwners.get(id)?.size??0)>value.partial_script_count)fail('edge source scripts exceed their known coverage');if(projectWide&&sceneReports.get(id).reference_count!==(counts.get(id)??0))fail('scene reference count differs from decoded edges');}
  graph.nodes.sort((a,b)=>compare(a.id,b.id));graph.edges.sort((a,b)=>compare(a.id,b.id));
  if(projectWide){graph.scene_ids.sort(compare);graph.scenes.sort((a,b)=>compare(a.scene_id,b.scene_id));}
  return graph;
}

export function transitionGraphView(graph,{query='',focusId=null,importedOnly=false,maxNodes=80,maxLinks=160}={}){
  if(!object(graph)||!Array.isArray(graph.nodes)||!Array.isArray(graph.edges)||graph.nodes.length>16448||graph.edges.length>16384||typeof query!=='string'||query.length>512||!(focusId===null||text(focusId,1024))||typeof importedOnly!=='boolean'||!integer(maxNodes,0,256)||!integer(maxLinks,0,1024))fail('view options or unbounded graph');
  const allNodes=new Map(graph.nodes.map(node=>[node.id,node])),sourceScenes=new Map((graph.scenes??[]).map(row=>[row.scene_id,row])),needle=query.trim().toLowerCase(),eligibleNodes=graph.nodes.filter(node=>!importedOnly||node.imported),eligibleIds=new Set(eligibleNodes.map(node=>node.id));
  let baseEdges=graph.edges.filter(edge=>eligibleIds.has(edge.source)&&eligibleIds.has(edge.target)),baseNodes=eligibleNodes;
  if(focusId!==null){baseEdges=eligibleIds.has(focusId)?baseEdges.filter(edge=>edge.source===focusId||edge.target===focusId):[];const neighbors=new Set(eligibleIds.has(focusId)?[focusId]:[]);for(const edge of baseEdges){neighbors.add(edge.source);neighbors.add(edge.target);}baseNodes=baseNodes.filter(node=>neighbors.has(node.id));}
  const matches=value=>String(value??'').toLowerCase().includes(needle);
  const edges=baseEdges.filter(edge=>!needle||[edge.id,edge.source,edge.target,allNodes.get(edge.source)?.name,allNodes.get(edge.target)?.name,edge.script_id,edge.script_name,edge.owner_id,edge.script_status,edge.reference?.status,edge.reference?.target_scene_name,sourceScenes.get(edge.source)?.status,sourceScenes.get(edge.target)?.status].some(matches)).sort((a,b)=>compare(a.id,b.id));
  const candidateIds=new Set(baseNodes.filter(node=>!needle||[node.id,node.name,sourceScenes.get(node.id)?.status].some(matches)).map(node=>node.id));for(const edge of edges){candidateIds.add(edge.source);candidateIds.add(edge.target);}
  const candidates=baseNodes.filter(node=>candidateIds.has(node.id)).sort((a,b)=>compare(a.id,b.id));
  // Keep the focused source on canvas even when lexical truncation hides peers.
  const ranked=focusId!==null&&candidateIds.has(focusId)?[...candidates.filter(node=>node.id===focusId),...candidates.filter(node=>node.id!==focusId)]:candidates;
  const nodes=ranked.slice(0,maxNodes).sort((a,b)=>compare(a.id,b.id)),shown=new Set(nodes.map(node=>node.id)),grouped=new Map();
  for(const edge of edges){const key=JSON.stringify([edge.source,edge.target]);if(!grouped.has(key))grouped.set(key,{id:'link:'+key,source:edge.source,target:edge.target,edgeIds:[]});grouped.get(key).edgeIds.push(edge.id);}
  const pairs=[...grouped.values()].sort((a,b)=>compare(a.source,b.source)||compare(a.target,b.target)),links=pairs.filter(link=>shown.has(link.source)&&shown.has(link.target)).slice(0,maxLinks),drawnEdges=links.reduce((count,link)=>count+link.edgeIds.length,0);
  return {nodes:detached(nodes),links:detached(links),edges:detached(edges),totalNodes:graph.nodes.length,totalEdges:graph.edges.length,matchedNodes:candidates.length,matchedEdges:edges.length,omittedNodes:candidates.length-nodes.length,omittedLinks:pairs.length-links.length,omittedEdges:edges.length-drawnEdges,focusId};
}
