import {parseHierarchyQuery} from './hierarchy-query.js';
import {HIERARCHY_GROUP_IDS} from './hierarchy-groups.js';
export function decodeSceneViewHierarchy(value){
 if(!value||Object.keys(value).sort().join(',')!=='collapsed_groups,query')throw Error('Saved hierarchy requires search and collapsed groups only.');
 parseHierarchyQuery(value.query);
 const groups=value.collapsed_groups;
 if(!Array.isArray(groups)||groups.length>HIERARCHY_GROUP_IDS.length||groups.some((id,i)=>!HIERARCHY_GROUP_IDS.includes(id)||i&&id<=groups[i-1]))throw Error('Saved hierarchy requires canonical supported collapsed groups.');
 return structuredClone(value);
}
export function captureSceneViewHierarchy(query,state,scope){
 if(state?.scope!==scope||!(state.collapsed instanceof Set))throw Error('Wait for the current hierarchy before saving its view.');
 return decodeSceneViewHierarchy({query,collapsed_groups:[...state.collapsed].sort()});
}
