// Operates only on SDK-decoded instruction boundaries. No VM or byte recovery.
export function findDecodedPath(instructions,start,target){
  if(!Array.isArray(instructions)||instructions.length>8192)throw new Error('Decoded path graph exceeds inspection bounds');
  const nodes=new Map();
  for(const node of instructions){
    if(!node||!Number.isInteger(node.pc)||node.pc<0||node.pc>65536||nodes.has(node.pc)||!Array.isArray(node.successors)||node.successors.length>64||node.successors.some(edge=>!edge||!Number.isSafeInteger(edge.pc)))throw new Error('Decoded path graph contains invalid boundaries');
    nodes.set(node.pc,node);
  }
  if(!nodes.has(start)||!nodes.has(target))throw new Error('Choose decoded start and destination instructions');
  const queue=[start],previous=new Map([[start,null]]),boundaries=new Set();
  for(let cursor=0;cursor<queue.length;cursor++){
    const pc=queue[cursor];
    if(pc===target){
      const path=[];let current=target;
      while(current!==null){const entry=previous.get(current);path.push({pc:current,condition:entry?.condition??null});current=entry?.pc??null;}
      return {status:'decoded_path',path:path.reverse(),visited_count:cursor+1};
    }
    for(const edge of nodes.get(pc).successors){
      if(!nodes.has(edge.pc)){boundaries.add(edge.pc);continue;}
      if(previous.has(edge.pc))continue;
      previous.set(edge.pc,{pc,condition:edge.condition??null});queue.push(edge.pc);
    }
  }
  return {status:'no_decoded_path',path:[],visited_count:queue.length,
    undecoded_targets:[...boundaries].sort((a,b)=>a-b).slice(0,256),undecoded_target_count:boundaries.size};
}
