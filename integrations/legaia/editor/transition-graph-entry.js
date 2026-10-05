import {decodeTransitionResource} from './transition-resource.js';
const canonical=value=>JSON.stringify(value,(_key,item)=>item&&typeof item==='object'&&!Array.isArray(item)?Object.fromEntries(Object.keys(item).sort().map(key=>[key,item[key]])):item);
// Both inputs retain their independently qualified static source evidence.
// A scene navigation does not make an old graph authoritative for a fresh catalog.
export function qualifyTransitionGraphEntry(edge,record){
  const data=decodeTransitionResource(record?.data);
  if(record?.type!=='transition'||record.id!==edge?.id||record.sceneId!==edge.source||data.semantic_id!==edge.id)throw new Error('Transition graph entry differs from the fresh resource identity.');
  for(const key of ['id','source','target','script_id','script_name','owner_id','partition','script_status','source_record','reference','reachability','entry_layers']){
    if(canonical(edge[key])!==canonical(data[key]))throw new Error('Transition graph source or Current entry changed. Refresh the graph.');
  }
  return data;
}
