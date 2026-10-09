import {navigableComponentReference} from './component-inspector.js';

// Each lookup retains its original active/project source membership.
export function createAssetDetailsTrail(){
  let entries=[];
  const key=value=>typeof value==='string'&&value.length>0&&value.length<=262144;
  return {
    remember(record,sourceKey,lookup){
      if(!navigableComponentReference(record?.id,'asset-reference')||!key(sourceKey)||typeof lookup!=='function')throw Error('Asset navigation source is unavailable. Reopen Asset Details.');
      const snapshot=JSON.stringify(record);if(snapshot.length>2097152)throw Error('Asset metadata exceeds the navigation history limit.');
      const label=typeof record.label==='string'?record.label:record.id;
      entries=[...entries,{id:record.id,label,snapshot,sourceKey,lookup}].slice(-16);
    },
    peek(){const entry=entries.at(-1);return entry?{id:entry.id,label:entry.label}:null;},
    back(sourceKey){
      const entry=entries.at(-1);if(!entry)return null;
      if(!key(sourceKey)||sourceKey!==entry.sourceKey)throw Error('Asset navigation sources changed. Reopen Asset Details.');
      const records=entry.lookup();if(!Array.isArray(records))throw Error('Asset navigation catalog is unavailable.');
      const matches=records.filter(record=>record?.id===entry.id);
      if(matches.length!==1||JSON.stringify(matches[0])!==entry.snapshot)throw Error('Previous asset is missing, ambiguous or changed in its source catalog. Reopen Asset Details.');
      entries=entries.slice(0,-1);return {record:matches[0],lookup:entry.lookup};
    },
    clear(){entries=[];},
    size(){return entries.length;}
  };
}
