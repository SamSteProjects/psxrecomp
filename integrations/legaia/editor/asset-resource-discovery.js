// Catalog loading follows user category selection; the loader owns source validation.
export const resourceAssetCategories=new Set(['authored','audio','texture','animation','script','dialogue','flag','transition','collision','trigger','region','worldmap']);
export function createAssetResourceDiscovery({getContext,load,schedule=work=>setTimeout(work,0),onError=()=>{}}){
  let attempted=null,queued=null,disposed=false;
  function request(retry=false){
    if(disposed)return false;
    const context=getContext();
    if(!context?.eligible||context.busy||context.loaded||context.pending||typeof context.key!=='string'||!context.key)return false;
    if(retry)attempted=null;
    if(queued===context.key||attempted===context.key)return false;
    const key=context.key;queued=key;
    schedule(async()=>{
      if(queued===key)queued=null;
      if(disposed)return;
      const current=getContext();
      if(!current?.eligible||current.key!==key||current.busy||current.loaded||current.pending||attempted===key)return;
      attempted=key;
      try{await load();}catch(error){onError(error);}
    });
    return true;
  }
  return {request,dispose(){disposed=true;queued=null;}};
}
