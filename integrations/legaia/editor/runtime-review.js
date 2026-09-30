// Detached decoded metadata. Saved observations never establish Live authority.
export const MAX_REVIEW_BYTES=1024*1024;
const keys=(value,allowed)=>{if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(key=>!allowed.includes(key)))throw new Error('Unknown runtime review fields');};
const string=(value,max=1024)=>{if(typeof value!=='string'||!value||value.length>max)throw new Error('Invalid runtime review text');return value;};
const scalar=value=>{if(value===null||typeof value==='boolean'||(typeof value==='number'&&Number.isFinite(value)))return value;if(typeof value==='string'&&value.length<=1024)return value;throw new Error('Invalid decoded scalar');};
function metadata(value,depth=0){
  if(value===null||typeof value!=='object')return scalar(value);
  if(depth>=3||Object.keys(value).length>16)throw new Error('Decoded metadata exceeds bounds');
  if(Array.isArray(value))return value.map(item=>metadata(item,depth+1));
  const result={};for(const [key,item] of Object.entries(value)){if(['__proto__','constructor','prototype'].includes(key))throw new Error('Invalid metadata key');result[string(key,128)]=metadata(item,depth+1);}return result;
}
const fieldKeys=['property','raw_numeric_value','interpreted_value','offset','width','signedness','representation','confidence','evidence','notes','applicability','unresolved','alternatives'];
const nodeKeys=['runtime_node_id','epoch_id','observed_position','position_capture_frames','candidate_entity_ids','decoded_fields','binding_confirmed','reason'];
const reviewKeys=['schema_version','historical','read_only','exported_at','scene_id','epoch_id','profile_id','nodes'];
export function validateRuntimeReview(value){
  keys(value,reviewKeys);
  if(value.schema_version!=='legaia.runtime-node-review.v1'||value.historical!==true||value.read_only!==true)throw new Error('Saved node reviews must be historical and read only');
  string(value.scene_id,256);string(value.epoch_id,256);string(value.exported_at,64);
  if(!Number.isFinite(Date.parse(value.exported_at)))throw new Error('Invalid export timestamp');
  if(value.profile_id!==null)string(value.profile_id,256);
  if(!Array.isArray(value.nodes)||value.nodes.length>128)throw new Error('Runtime review exceeds 128 nodes');
  const seen=new Set();
  for(const node of value.nodes){
    keys(node,nodeKeys);string(node.runtime_node_id,256);
    if(seen.has(node.runtime_node_id)||node.epoch_id!==value.epoch_id||node.binding_confirmed!==false)throw new Error('Ambiguous node identity or observation epoch');seen.add(node.runtime_node_id);
    keys(node.observed_position,['x','y','z']);for(const axis of ['x','y','z'])if(node.observed_position[axis]!==null&&!Number.isFinite(node.observed_position[axis]))throw new Error('Invalid captured position');
    if(node.position_capture_frames!==null){keys(node.position_capture_frames,['before','after']);const f=node.position_capture_frames;if(!Number.isSafeInteger(f.before)||f.before<0||!Number.isSafeInteger(f.after)||f.after<f.before)throw new Error('Invalid position capture frames');}
    if(!Array.isArray(node.candidate_entity_ids)||node.candidate_entity_ids.length>512||new Set(node.candidate_entity_ids).size!==node.candidate_entity_ids.length)throw new Error('Invalid candidate IDs');node.candidate_entity_ids.forEach(id=>string(id,256));
    if(node.reason!==null)string(node.reason);
    if(!Array.isArray(node.decoded_fields)||node.decoded_fields.length>64)throw new Error('Decoded fields exceed bounds');
    const fields=new Set();for(const field of node.decoded_fields){keys(field,fieldKeys);string(field.property,128);if(fields.has(field.property))throw new Error('Duplicate decoded field');fields.add(field.property);for(const item of Object.values(field))metadata(item);}
  }
  const encoded=JSON.stringify(value,null,2)+'\n';if(new TextEncoder().encode(encoded).length>MAX_REVIEW_BYTES)throw new Error('Runtime review exceeds 1 MiB');
  return JSON.parse(encoded);
}
export function captureRuntimeReview({scene_id,epoch_id,profile_id=null,nodes,exported_at=new Date().toISOString()}){
  if(!Array.isArray(nodes)||nodes.length>128)throw new Error('Runtime review exceeds 128 nodes');
  const selected=nodes.map(node=>({runtime_node_id:node.runtime_node_id,epoch_id:node.epoch_id,
    observed_position:node.observed_position,position_capture_frames:node.position_capture_frames??null,
    candidate_entity_ids:node.candidate_entity_ids??[],binding_confirmed:false,reason:node.reason??null,
    decoded_fields:(node.decoded_fields??[]).map(field=>Object.fromEntries(fieldKeys.filter(key=>Object.hasOwn(field,key)).map(key=>[key,field[key]])))}));
  return validateRuntimeReview({schema_version:'legaia.runtime-node-review.v1',historical:true,read_only:true,exported_at,scene_id,epoch_id,profile_id,nodes:selected});
}
export function parseRuntimeReview(text){
  if(typeof text!=='string'||new TextEncoder().encode(text).length>MAX_REVIEW_BYTES)throw new Error('Runtime review exceeds 1 MiB');
  return validateRuntimeReview(JSON.parse(text));
}
