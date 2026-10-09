/** Compact empty controller families after their source snapshot is qualified. */
export function compactControllerAuthoring(section,snapshot,status){
 if(!snapshot||!Array.isArray(snapshot.targets)||typeof snapshot.supported!=='boolean')throw Error('Controller availability requires a qualified source snapshot.');
 const available=snapshot.targets.length>0;
 section.dataset.controllerAuthoringAvailability=available?'available':'unavailable';
 if(available)return;
 for(const child of section.children)if(child!==status&&child.tagName?.toLowerCase()!=='h3'&&child.getAttribute?.('role')!=='alert'){child.hidden=true;child.style.display='none';}
 status.textContent=typeof snapshot.reason==='string'&&snapshot.reason?snapshot.reason:'No source-qualified targets in this controller. Runtime execution remains unverified.';
}
