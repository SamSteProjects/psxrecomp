// Whole-record encoded graph diagnostics. No VM, flag evaluation or byte recovery.
const integer=(value,max=65535)=>Number.isSafeInteger(value)&&value>=0&&value<=max;
const text=(value,max)=>typeof value==='string'&&value.length<=max;
const offset=value=>'0x'+value.toString(16).toUpperCase().padStart(4,'0');
const fail=()=>{throw new Error('Source flow overview requires bounded, distinct decoded boundaries.');};

export function analyzeScriptFlow(report){
  if(!report||!['partial','decoded_supported_paths'].includes(report.status)||
    !Array.isArray(report.instructions)||!Array.isArray(report.dialogues)||
    report.instructions.length+report.dialogues.length>8192||!Array.isArray(report.stops)||report.stops.length>8192)fail();
  const unvisitedInstructions=report.unvisited_instructions??[],unvisitedDialogues=report.unvisited_dialogues??[];
  if(!Array.isArray(unvisitedInstructions)||!Array.isArray(unvisitedDialogues)||
    report.instructions.length+report.dialogues.length+unvisitedInstructions.length+unvisitedDialogues.length>8192)fail();
  const nodes=new Map(),stops=new Map();
  const add=(row,mnemonic,successors)=>{
    if(!row||!integer(row.pc)||!Number.isSafeInteger(row.length)||row.length<1||row.length>65536-row.pc||nodes.has(row.pc)||
      !text(mnemonic,128)||!mnemonic||!Array.isArray(successors)||successors.length>64)fail();
    const edges=successors.map(edge=>{
      if(!edge||!integer(edge.pc,65536)||!(edge.condition===null||text(edge.condition,256)))fail();
      return {source:row.pc,target:edge.pc,condition:edge.condition};
    });
    nodes.set(row.pc,{pc:row.pc,mnemonic,edges});
  };
  for(const row of report.instructions)add(row,row?.mnemonic,row?.successors);
  for(const row of report.dialogues)add(row,'DIALOGUE_SEGMENT',[{pc:row.pc+row.length,condition:'encoded_continuation'}]);
  for(const row of unvisitedInstructions)add(row,row?.mnemonic,row?.successors);
  for(const row of unvisitedDialogues)add(row,'DIALOGUE_SEGMENT',[{pc:row.pc+row.length,condition:'encoded_continuation'}]);
  for(const row of report.stops){
    if(!row||!integer(row.pc,65536)||!text(row.reason,8192)||!row.reason)fail();
    if(!stops.has(row.pc))stops.set(row.pc,[]);
    if(!stops.get(row.pc).includes(row.reason))stops.get(row.pc).push(row.reason);
  }
  const entry=report.entry_pc??report.record?.script_offset??null;
  if(entry!==null&&!integer(entry))fail();
  const pcs=[...nodes.keys()].sort((a,b)=>a-b),adj=new Map(),reverse=new Map(pcs.map(pc=>[pc,[]])),boundaries=new Map();
  for(const pc of pcs){
    const targets=[];
    for(const edge of nodes.get(pc).edges){
      if(nodes.has(edge.target)){targets.push(edge.target);reverse.get(edge.target).push(pc);}
      else{
        if(!boundaries.has(edge.target))boundaries.set(edge.target,[]);
        boundaries.get(edge.target).push({...edge});
      }
    }
    adj.set(pc,targets);
  }
  let reachable=null;
  if(entry!==null&&nodes.has(entry)){
    reachable=new Set([entry]);const queue=[entry];
    for(let index=0;index<queue.length;index++)for(const target of adj.get(queue[index]))if(!reachable.has(target)){reachable.add(target);queue.push(target);}
  }
  const retainedUnvisited=[...unvisitedInstructions,...unvisitedDialogues].map(row=>row.pc).sort((a,b)=>a-b);
  if(reachable!==null&&retainedUnvisited.some(pc=>reachable.has(pc)))fail();
  if(report.unreachable_source_pcs!==undefined&&
    (!Array.isArray(report.unreachable_source_pcs)||report.unreachable_source_pcs.length!==retainedUnvisited.length||
    report.unreachable_source_pcs.some((pc,index)=>pc!==retainedUnvisited[index])))fail();
  // Iterative Kosaraju traversal avoids the JS call-stack limit on long records.
  const visited=new Set(),order=[];
  for(const start of pcs){
    if(visited.has(start))continue;
    visited.add(start);const stack=[{pc:start,index:0}];
    while(stack.length){
      const frame=stack.at(-1),next=adj.get(frame.pc);
      if(frame.index===next.length){order.push(frame.pc);stack.pop();continue;}
      const target=next[frame.index++];
      if(!visited.has(target)){visited.add(target);stack.push({pc:target,index:0});}
    }
  }
  const assigned=new Set(),cycles=[];
  for(let index=order.length-1;index>=0;index--){
    const start=order[index];if(assigned.has(start))continue;
    const members=[],stack=[start];assigned.add(start);
    while(stack.length){const pc=stack.pop();members.push(pc);for(const source of reverse.get(pc))if(!assigned.has(source)){assigned.add(source);stack.push(source);}}
    if(members.length===1&&!adj.get(start).includes(start))continue;
    members.sort((a,b)=>a-b);const own=new Set(members);let internal=0,exits=0;
    for(const pc of members)for(const edge of nodes.get(pc).edges){if(own.has(edge.target))internal++;else exits++;}
    cycles.push({pcs:members,internal_edge_count:internal,outgoing_edge_count:exits,
      closed_encoded_component:exits===0,entry_reachable:reachable===null?null:reachable.has(start)});
  }
  cycles.sort((a,b)=>a.pcs[0]-b.pcs[0]);
  return {entry_pc:entry,entry_decoded:entry!==null&&nodes.has(entry),node_count:nodes.size,
    edge_count:pcs.reduce((count,pc)=>count+nodes.get(pc).edges.length,0),
    reachable_pcs:reachable===null?null:pcs.filter(pc=>reachable.has(pc)),
    unvisited_pcs:reachable===null?null:pcs.filter(pc=>!reachable.has(pc)),
    terminals:pcs.filter(pc=>nodes.get(pc).edges.length===0),cycles,
    boundaries:[...boundaries].sort(([a],[b])=>a-b).map(([pc,edges])=>({pc,edges,reasons:[...(stops.get(pc)??[])],entry_reachable:reachable===null?null:edges.some(edge=>reachable.has(edge.source))})),
    stops:[...stops].sort(([a],[b])=>a-b).map(([pc,reasons])=>({pc,reasons})),
    nodes:pcs.map(pc=>({pc,mnemonic:nodes.get(pc).mnemonic}))};
}

export function mountScriptFlowOverview(host,{selectInstruction=()=>{},label='Retail encoded flow',title='Whole-record source flow overview'}={}){
  const create=(tag,value)=>{const node=document.createElement(tag);if(value!==undefined)node.textContent=value;return node;};
  const section=create('details');section.className='script-flow-overview';section.dataset.scriptFlowOverview='';
  section.append(create('summary',title));
  const summary=create('p'),note=create('p','Encoded edges only. Conditions, story activation and external resumption are not evaluated. A closed cycle does not prove an infinite loop; unvisited decoded nodes do not prove gameplay unreachability.');
  summary.dataset.flowSummary='';summary.setAttribute('role','status');note.className='field-note';
  const content=create('div');section.append(summary,note,content);host.append(section);
  let disposed=false,current=null,lastReport=null,lastLabel=null;
  const link=(pc,mnemonic)=>{const node=create('button',`Inspect ${offset(pc)}${mnemonic?' · '+mnemonic:''}`);node.type='button';node.dataset.flowPc=pc;node.onclick=()=>{if(!disposed)selectInstruction(pc);};return node;};
  function paged(parent,items,render){
    const body=create('div'),tools=create('div'),previous=create('button','Previous flow page'),next=create('button','Next flow page'),status=create('span');
    tools.className='script-flow-pages';previous.type=next.type='button';previous.setAttribute('aria-label','Previous flow page');next.setAttribute('aria-label','Next flow page');tools.append(previous,status,next);parent.append(body,tools);let page=0;
    const draw=()=>{body.replaceChildren();const start=page*32;for(const item of items.slice(start,start+32))body.append(render(item));status.textContent=items.length?`${start+1}–${Math.min(start+32,items.length)} of ${items.length}`:'No entries';previous.disabled=page===0;next.disabled=start+32>=items.length;tools.hidden=items.length<=32;};
    previous.onclick=()=>{if(disposed||previous.disabled)return;page--;draw();};next.onclick=()=>{if(disposed||next.disabled)return;page++;draw();};draw();
  }
  function update(report,{label:nextLabel=label}={}){
    if(disposed)return false;
    if(report===lastReport&&nextLabel===lastLabel&&current!==null)return true;
    lastReport=report;lastLabel=nextLabel;current=null;content.replaceChildren();
    try{
      const result=analyzeScriptFlow(report),names=new Map(result.nodes.map(row=>[row.pc,row.mnemonic]));current=result;
      summary.textContent=`${nextLabel} · ${result.node_count} decoded boundaries · ${result.edge_count} encoded edges · ${result.cycles.length} cyclic components · ${result.boundaries.length} undecoded targets. `+
        (result.reachable_pcs===null?`Entry ${result.entry_pc===null?'unavailable':offset(result.entry_pc)+' is not decoded'}; reachability unknown.`:`Entry ${offset(result.entry_pc)} · ${result.reachable_pcs.length} reachable · ${result.unvisited_pcs.length} unvisited from this entry.`);
      const list=(title,items,render)=>{const details=create('details');details.append(create('summary',`${title} (${items.length})`));paged(details,items,render);content.append(details);};
      if(result.entry_decoded)content.append(link(result.entry_pc,names.get(result.entry_pc)));
      list('Cyclic components',result.cycles,cycle=>{
        const item=create('details');item.append(create('summary',`${offset(cycle.pcs[0])} · ${cycle.pcs.length} boundaries · ${cycle.outgoing_edge_count} outgoing edges · ${cycle.closed_encoded_component?'closed encoded component':'has encoded exits'} · ${cycle.entry_reachable===null?'entry reachability unknown':cycle.entry_reachable?'reachable from entry':'unvisited from entry'}`));
        paged(item,cycle.pcs,pc=>link(pc,names.get(pc)));return item;
      });
      if(result.unvisited_pcs!==null)list('Unvisited decoded boundaries',result.unvisited_pcs,pc=>link(pc,names.get(pc)));
      list('No decoded successors',result.terminals,pc=>link(pc,names.get(pc)));
      list('Undecoded targets',result.boundaries,boundary=>{
        const item=create('details');item.append(create('summary',`${offset(boundary.pc)} · ${boundary.edges.length} incoming encoded edges · ${boundary.entry_reachable===null?'entry reachability unknown':boundary.entry_reachable?'referenced from entry path':'unvisited from entry'}`));
        item.append(create('p',boundary.reasons.join(' · ')||'No decoded boundary at this target. Bytes remain unresolved.'));
        paged(item,boundary.edges,edge=>{const row=create('p');row.append(link(edge.source,names.get(edge.source)));if(edge.condition!==null)row.append(create('span',' · '+edge.condition));return row;});return item;
      });
      list('Decoder stops',result.stops,stop=>create('p',`${offset(stop.pc)} · ${stop.reasons.join(' · ')}`));return true;
    }catch(error){summary.textContent=error.message;return false;}
  }
  return {update,get result(){return current;},dispose(){if(disposed)return;disposed=true;current=null;section.remove();}};
}
