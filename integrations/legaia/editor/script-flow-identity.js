const object=v=>v&&typeof v==='object'&&!Array.isArray(v);
export const canonicalScriptMetadata=v=>Array.isArray(v)?v.map(canonicalScriptMetadata):object(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonicalScriptMetadata(v[k])])):v;
export async function scriptFlowReportHash(report){
 const bytes=new TextEncoder().encode(JSON.stringify(canonicalScriptMetadata(report)));if(bytes.length>4*1024*1024)throw Error('Walkthrough flow report exceeds inspection bounds.');
 return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
}
