// Move existing tool nodes intact; callbacks and draft state remain owned by their tools.
export function mountSceneToolDrawer({toolbar,viewport,keep=[],onToggle=()=>{}}){
  const doc=viewport.ownerDocument,retained=new Set(keep),tools=[];
  for(let node=toolbar.nextElementSibling;node&&node!==viewport;node=node.nextElementSibling)if(!retained.has(node))tools.push(node);
  if(!tools.length)return null;
  const drawer=doc.createElement('details'),summary=doc.createElement('summary'),content=doc.createElement('div');drawer.id='scene-tool-drawer';summary.textContent='Scene tools';content.className='scene-tool-content';
  Object.assign(drawer.style,{flexShrink:'0',borderBottom:'1px solid #2b3539',minHeight:'0'});Object.assign(summary.style,{cursor:'pointer',padding:'8px 12px',color:'#c6d8ce',fontWeight:'600'});Object.assign(content.style,{maxHeight:'38vh',overflowY:'auto',overflowX:'hidden'});
  viewport.parentElement.style.minHeight='0';
  drawer.append(summary,content);for(const node of tools)content.append(node);viewport.before(drawer);
  const fit=()=>{const parent=viewport.parentElement;const reserved=Array.from(parent.children).filter(node=>node!==viewport&&node!==drawer).reduce((sum,node)=>sum+node.getBoundingClientRect().height,0);content.style.maxHeight=Math.max(80,Math.min(doc.defaultView.innerHeight*.38,parent.clientHeight-reserved-summary.getBoundingClientRect().height-180))+'px';};
  if(typeof ResizeObserver!=='undefined'){const observer=new ResizeObserver(fit);observer.observe(viewport.parentElement);observer.observe(toolbar);for(const node of keep)observer.observe(node);}
  fit();
  drawer.addEventListener('toggle',()=>{fit();if(!drawer.open&&content.contains(doc.activeElement))summary.focus();onToggle(drawer.open);});
  return {drawer,summary,content};
}
