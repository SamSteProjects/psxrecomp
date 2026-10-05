import {transitionGraphView} from './transition-graph.js';

let sequence=0;
const svgNamespace='http://www.w3.org/2000/svg';
const nameOf=node=>node.name??'Unresolved destination';
const statusOf=node=>node.imported?'Imported':node.in_scene_index?'Retail scene · not imported':'Unresolved destination';
const offset=value=>'0x'+value.toString(16).padStart(4,'0');
function element(tag,text,className){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(className)node.className=className;return node;}
function svgElement(tag,attributes,text){const node=document.createElementNS(svgNamespace,tag);for(const [key,value] of Object.entries(attributes??{}))node.setAttribute(key,String(value));if(text!==undefined)node.textContent=text;return node;}

// The layout organizes reference endpoints. It never computes a gameplay route.
function layout(nodes,links,focusId){
  const incoming=new Set(links.filter(link=>link.target===focusId).map(link=>link.source));
  const outgoing=new Set(links.filter(link=>link.source===focusId).map(link=>link.target));
  const columns=[[],[],[]],positions=new Map();
  for(const node of nodes){
    const column=focusId?(node.id===focusId?1:incoming.has(node.id)&&!outgoing.has(node.id)?0:2):node.roles.includes('source')?(node.roles.includes('destination')?1:0):2;
    columns[column].push(node);
  }
  // Split broad destination lists into short columns so Fit keeps labels legible.
  const packed=[];
  for(const column of columns){if(!column.length){packed.push([]);continue;}for(let start=0;start<column.length;start+=5)packed.push(column.slice(start,start+5));}
  const rows=Math.max(1,...packed.map(column=>column.length)),height=Math.max(360,rows*106+132);
  packed.forEach((column,index)=>column.forEach((node,row)=>positions.set(node.id,{x:160+280*index,y:100+(row+Math.floor((rows-column.length)/2))*106})));
  return {positions,width:Math.max(880,(packed.length-1)*280+320),height};
}

export function mountTransitionGraphWorkspace(host,graph,{activeSceneId=null,isCurrent=()=>true,onInspect=()=>{},onInspectEntry=null,onOpenScene=()=>{},onError=()=>{}}={}){
  let disposed=false,query='',importedOnly=false,focusId=null,selectedNode=null,selectedLink=null,page=0,view,geometry,box,gesture=null;
  const events=new AbortController(),markerId=`transition-graph-arrow-${++sequence}`;
  const nodeMap=new Map(graph.nodes.map(node=>[node.id,node]));
  host.classList.add('transition-workspace');
  host.innerHTML='<div class="transition-graph-controls"><label>Search scenes or instructions<input type="search" aria-label="Search transition graph" placeholder="Scene, script, owner or instruction"></label><label class="transition-imported-filter"><input type="checkbox" aria-label="Imported transition scenes only"> Imported scenes only</label><button data-focus disabled>Focus direct references</button><button data-all>Show all scenes</button></div><p class="transition-graph-counts" role="status"></p><div class="transition-graph-body"><aside class="transition-scene-list" aria-label="Graph scenes"></aside><section class="transition-map"><div class="transition-camera-controls"><button data-fit>Fit graph</button><button data-zoom-out aria-label="Zoom transition graph out">−</button><button data-zoom-in aria-label="Zoom transition graph in">+</button><span>Drag to pan · wheel to zoom · select a scene or arrow</span></div><svg class="transition-graph-svg" role="group" aria-label="Decoded scene-change references" tabindex="0"></svg><p class="transition-graph-legend">Green: imported scene · blue: retail destination · amber: unresolved destination. Arrows group decoded instructions; gameplay reachability is unknown.</p></section></div><section class="transition-node-detail" aria-label="Selected graph scene"></section><section class="transition-reference-list"><div class="transition-reference-heading"><h3>Reference instructions</h3><button data-prev>Previous</button><span data-page></span><button data-next>Next</button></div><div data-references></div></section><details class="transition-graph-coverage"><summary>Source coverage and limitations</summary><div data-coverage></div></details>';
  const find=selector=>host.querySelector(selector),svg=find('svg'),scenes=find('.transition-scene-list'),references=find('[data-references]'),detail=find('.transition-node-detail'),counts=find('.transition-graph-counts'),search=find('input[type=search]');
  const listen=(node,event,handler)=>node.addEventListener(event,handler,{signal:events.signal});
  // Dynamic frame nodes release their handlers when removed, without accumulating abort listeners.
  const wire=(node,event,handler)=>{node['on'+event]=handler;};
  const current=()=>!disposed&&isCurrent();
  const invoke=async action=>{if(!current())return;try{await action();}catch(error){if(current())onError(error);}};
  const setBox=()=>svg.setAttribute('viewBox',`${box.x} ${box.y} ${box.width} ${box.height}`);
  function fit(){if(!current()||!geometry)return;box={x:0,y:0,width:geometry.width,height:geometry.height};setBox();}
  function zoom(factor,anchor={x:.5,y:.5}){
    if(!current()||!box)return;
    const width=Math.min(geometry.width*3,Math.max(220,box.width*factor)),height=box.height*width/box.width;
    box={x:box.x+box.width*anchor.x-width*anchor.x,y:box.y+box.height*anchor.y-height*anchor.y,width,height};setBox();
  }
  function chooseNode(id){if(!current())return;selectedNode=id;selectedLink=null;page=0;render(false);[...svg.querySelectorAll('[data-graph-node]')].find(node=>node.dataset.graphNode===id)?.focus({preventScroll:true});}
  function chooseLink(id){if(!current())return;selectedLink=id;selectedNode=null;page=0;render(false);[...svg.querySelectorAll('[data-graph-link]')].find(node=>node.dataset.graphLink===id)?.focus({preventScroll:true});}
  function keyboardActivate(event,callback){if(event.key==='Enter'||event.key===' '){event.preventDefault();callback();}}
  function drawGraph(resetCamera){
    geometry=layout(view.nodes,view.links,focusId);svg.replaceChildren();
    const defs=svgElement('defs'),marker=svgElement('marker',{id:markerId,viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:7,markerHeight:7,orient:'auto-start-reverse'});
    marker.append(svgElement('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'#91aab5'}));defs.append(marker);svg.append(defs);
    const pairKeys=new Set(view.links.map(link=>JSON.stringify([link.source,link.target])));
    const badges=[];
    for(const link of view.links){
      const source=geometry.positions.get(link.source),target=geometry.positions.get(link.target),self=link.source===link.target,same=source.x===target.x;
      const direction=target.x>=source.x?1:-1,side=target.y>=source.y?1:-1,sx=source.x+(self?0:same?118*side:118*direction),tx=target.x+(self?76:same?118*side:-118*direction),sy=source.y,ty=target.y;
      const lane=!self&&pairKeys.has(JSON.stringify([link.target,link.source]))?(link.source<link.target?26:-26):0;
      const bend=30*side,far=Math.abs(source.x-target.x)>280,routeY=ty-53,startBus=sx+direction*20,endBus=tx-direction*20;
      const curve=self?`M ${sx} ${sy-32} C ${sx-54} ${sy-105}, ${tx+70} ${ty-105}, ${tx} ${ty-32}`:same?`M ${sx} ${sy} C ${sx+bend} ${sy}, ${tx+bend} ${ty}, ${tx} ${ty}`:far?`M ${sx} ${sy} L ${startBus} ${sy} L ${startBus} ${routeY} L ${endBus} ${routeY} L ${endBus} ${ty} L ${tx} ${ty}`:`M ${sx} ${sy} C ${(sx+tx)/2} ${sy+lane}, ${(sx+tx)/2} ${ty+lane}, ${tx} ${ty}`;
      const group=svgElement('g',{'data-graph-link':link.id,class:`transition-graph-link${selectedLink===link.id?' selected':''}`,role:'button',tabindex:0,'aria-label':`${link.edgeIds.length} encoded references from ${nameOf(nodeMap.get(link.source))} to ${nameOf(nodeMap.get(link.target))}`,'aria-pressed':String(selectedLink===link.id)});
      const strokes=svgElement('g',{class:`transition-graph-link${selectedLink===link.id?' selected':''}`,'aria-hidden':'true'});
      strokes.append(svgElement('path',{d:curve,class:'transition-link-hit'}),svgElement('path',{d:curve,class:'transition-link-line','marker-end':`url(#${markerId})`}));wire(strokes,'click',()=>chooseLink(link.id));svg.append(strokes);
      group.append(svgElement('title',{},`${link.edgeIds.length} independent instructions · select to inspect`));
      const labelX=self?sx+25:same?sx+bend*.75:far?endBus:(sx+tx)/2,labelY=self?sy-75:far?routeY:(sy+ty)/2+lane*.75;
      const badgeWidth=Math.max(28,String(link.edgeIds.length).length*9+16);
      group.append(svgElement('rect',{x:labelX-badgeWidth/2,y:labelY-11,width:badgeWidth,height:22,rx:5,class:'transition-link-count'}),svgElement('text',{x:labelX,y:labelY+4,'text-anchor':'middle'},link.edgeIds.length));
      wire(group,'click',()=>chooseLink(link.id));wire(group,'keydown',event=>keyboardActivate(event,()=>chooseLink(link.id)));badges.push(group);
    }
    for(const node of view.nodes){
      const position=geometry.positions.get(node.id),group=svgElement('g',{transform:`translate(${position.x},${position.y})`,'data-graph-node':node.id,class:`transition-graph-node ${node.imported?'imported':node.in_scene_index?'retail':'unresolved'}${node.id===activeSceneId?' active-scene':''}${node.id===selectedNode?' selected':''}`,role:'button',tabindex:0,'aria-label':`${nameOf(node)} · ${statusOf(node)}${node.id===activeSceneId?' · active scene':''}`,'aria-pressed':String(node.id===selectedNode)});
      const label=nameOf(node),shortLabel=label.length>22?label.slice(0,21)+'…':label;
      group.append(svgElement('title',{},`${label} · ${node.id} · ${statusOf(node)}`),svgElement('rect',{x:-118,y:-32,width:236,height:64,rx:8}),svgElement('text',{x:0,y:-3,'text-anchor':'middle',class:'transition-node-name'},shortLabel),svgElement('text',{x:0,y:18,'text-anchor':'middle',class:'transition-node-status'},node.id===activeSceneId?'Imported · active scene':statusOf(node)));
      wire(group,'click',()=>chooseNode(node.id));wire(group,'keydown',event=>keyboardActivate(event,()=>chooseNode(node.id)));svg.append(group);
    }
    // Badges remain clickable above crossing lines, without covering scene boxes.
    svg.append(...badges);
    if(!view.nodes.length)svg.append(svgElement('text',{x:500,y:170,'text-anchor':'middle'},'No scenes match these filters.'));
    if(resetCamera||!box)fit();else setBox();
  }
  function drawScenes(){
    scenes.replaceChildren();for(const node of view.nodes){const button=element('button',nameOf(node));button.dataset.graphScene=node.id;button.setAttribute('aria-pressed',String(selectedNode===node.id));button.append(element('small',statusOf(node)));wire(button,'click',()=>chooseNode(node.id));scenes.append(button);}
    if(view.omittedNodes)scenes.append(element('p',`${view.omittedNodes} further scenes match. Search by name to display them.`,'field-note'));
  }
  function drawDetail(){
    detail.replaceChildren();find('[data-focus]').disabled=!selectedNode;
    if(!selectedNode){detail.append(element('p',focusId?'Direct-reference view. Select an arrow to inspect its independent source instructions.':'Select a scene to inspect its direct references. Use Focus direct references to isolate its incoming and outgoing instructions.'));return;}
    const node=nodeMap.get(selectedNode),title=element('strong',nameOf(node));detail.append(title,element('span',` ${statusOf(node)} · ${node.id}`));
    const coverage=graph.scenes?.find(item=>item.scene_id===node.id);
    if(coverage)detail.append(element('p',coverage.status==='verified'?`${coverage.reference_count} decoded outgoing references. Supported source paths only.`:`Source catalog unavailable: ${coverage.reason}`,'field-note'));
    const button=element('button','Open imported scene');button.dataset.openGraphScene=node.id;button.disabled=!node.imported;wire(button,'click',()=>invoke(()=>onOpenScene(node)));detail.append(button);
  }
  function drawReferences(){
    let rows=view.edges;
    if(selectedNode)rows=rows.filter(edge=>edge.source===selectedNode||edge.target===selectedNode);
    if(selectedLink){const link=view.links.find(item=>item.id===selectedLink),ids=new Set(link?.edgeIds??[]);rows=rows.filter(edge=>ids.has(edge.id));}
    page=Math.max(0,Math.min(page,Math.ceil(rows.length/20)-1));find('[data-prev]').disabled=page===0;find('[data-next]').disabled=(page+1)*20>=rows.length;
    find('[data-page]').textContent=`${rows.length} instructions · page ${page+1} of ${Math.max(1,Math.ceil(rows.length/20))}`;references.replaceChildren();
    for(const edge of rows.slice(page*20,(page+1)*20)){
      const from=nodeMap.get(edge.source),to=nodeMap.get(edge.target),row=element('article',undefined,'transition-edge');row.dataset.transitionEdge=edge.id;
      row.append(element('h4',`${nameOf(from)} → ${nameOf(to)}`),element('p',`${edge.script_name} · ${offset(edge.reference.pc)} · partition ${edge.partition} · ${edge.script_status}`));
      const table=element('table',undefined,'transition-entry-layers'),caption=element('caption','Encoded entry operands · static reference, height unknown');table.append(caption);
      const header=element('tr');for(const text of ['Layer','X','Z','Direction'])header.append(element('th',text));const head=element('thead');head.append(header);table.append(head);const body=element('tbody');
      for(const [label,key] of [['Retail','imported'],['Authored','authored'],['Effective','effective']]){const values=edge.entry_layers[key],tr=element('tr');tr.append(element('th',label));for(const field of ['entry_x_encoded','entry_z_encoded','direction_encoded'])tr.append(element('td',values[field]??'Inherited'));body.append(tr);}table.append(body);row.append(table);
      const actions=element('div',undefined,'dialog-actions'),inspect=element('button','Inspect source script'),open=element('button','Open imported destination');
      inspect.dataset.inspectGraphEdge=edge.id;open.dataset.openGraphDestination=edge.id;open.disabled=!to.imported;
      const entry=element('button','Inspect transition entry');entry.dataset.inspectGraphEntry=edge.id;entry.disabled=typeof onInspectEntry!=='function';
      wire(entry,'click',()=>invoke(()=>onInspectEntry?.(edge)));
      wire(inspect,'click',()=>invoke(()=>onInspect(edge)));wire(open,'click',()=>invoke(()=>onOpenScene(to)));actions.append(inspect,entry,open);row.append(actions);
      const provenance=element('details');provenance.append(element('summary','Reference provenance'),element('pre',JSON.stringify(edge,null,2),'diagnostic-detail'));row.append(provenance);references.append(row);
    }
    if(!rows.length)references.append(element('p','No supported instructions match this view. This does not establish that a scene has no exits.','field-note'));
  }
  function render(resetCamera=true){
    if(!current())return;
    view=transitionGraphView(graph,{query,focusId,importedOnly});
    if(selectedNode&&!view.nodes.some(node=>node.id===selectedNode))selectedNode=null;
    if(selectedLink&&!view.links.some(link=>link.id===selectedLink))selectedLink=null;
    counts.textContent=`${view.nodes.length} of ${view.matchedNodes} matching scenes · ${view.links.length} reference pairs · ${view.matchedEdges} of ${view.totalEdges} matching instructions${focusId?' · direct references only':''}. ${view.omittedNodes||view.omittedLinks?`${view.omittedNodes} scenes, ${view.omittedLinks} pairs and ${view.omittedEdges} instructions are outside the bounded drawing; all matching instructions remain available below.`:'All matching instructions fit the drawing.'}`;
    drawGraph(resetCamera);drawScenes();drawDetail();drawReferences();
  }
  const coverage=find('[data-coverage]');coverage.append(element('p',`${graph.coverage.script_count} scripts inspected · ${graph.coverage.partial_script_count} partial · ${graph.coverage.unavailable_script_count} unavailable. Gameplay reachability has not been evaluated.`));
  for(const scene of graph.scenes??[])coverage.append(element('p',`${scene.scene_name}: ${scene.status==='verified'?`${scene.reference_count} decoded references`:scene.reason}`));
  for(const limitation of graph.limitations)coverage.append(element('p',limitation,'field-note'));
  listen(search,'input',()=>{if(!current())return;query=search.value;page=0;render();});
  listen(find('input[type=checkbox]'),'change',event=>{if(!current())return;importedOnly=event.target.checked;page=0;render();});
  listen(find('[data-focus]'),'click',()=>{if(!current()||!selectedNode)return;focusId=selectedNode;selectedLink=null;page=0;render();});
  listen(find('[data-all]'),'click',()=>{if(!current())return;focusId=null;selectedNode=null;selectedLink=null;page=0;render();});
  listen(find('[data-prev]'),'click',()=>{if(current()){page--;drawReferences();}});listen(find('[data-next]'),'click',()=>{if(current()){page++;drawReferences();}});
  listen(find('[data-fit]'),'click',fit);listen(find('[data-zoom-in]'),'click',()=>zoom(.8));listen(find('[data-zoom-out]'),'click',()=>zoom(1.25));
  listen(svg,'wheel',event=>{if(!current())return;event.preventDefault();const point=svg.createSVGPoint();point.x=event.clientX;point.y=event.clientY;const local=point.matrixTransform(svg.getScreenCTM().inverse());zoom(event.deltaY<0?.85:1/.85,{x:(local.x-box.x)/box.width,y:(local.y-box.y)/box.height});});
  listen(svg,'pointerdown',event=>{if(!current()||event.button!==0||event.target.closest('[data-graph-node],.transition-graph-link'))return;const bounds=svg.getBoundingClientRect();gesture={id:event.pointerId,x:event.clientX,y:event.clientY,box:{...box},scale:Math.max(box.width/bounds.width,box.height/bounds.height)};svg.setPointerCapture(event.pointerId);svg.classList.add('panning');});
  listen(svg,'pointermove',event=>{if(!current()||gesture?.id!==event.pointerId)return;box={...gesture.box,x:gesture.box.x-(event.clientX-gesture.x)*gesture.scale,y:gesture.box.y-(event.clientY-gesture.y)*gesture.scale};setBox();});
  const finishGesture=()=>{gesture=null;svg.classList.remove('panning');};listen(svg,'pointerup',finishGesture);listen(svg,'pointercancel',finishGesture);listen(svg,'lostpointercapture',finishGesture);
  listen(svg,'keydown',event=>{if(event.target!==svg||!current())return;if(event.key==='+'||event.key==='='){event.preventDefault();zoom(.8);}else if(event.key==='-'){event.preventDefault();zoom(1.25);}else if(event.key==='0'){event.preventDefault();fit();}});
  render();
  return {dispose(){disposed=true;events.abort();gesture=null;host.replaceChildren();host.classList.remove('transition-workspace');}};
}
