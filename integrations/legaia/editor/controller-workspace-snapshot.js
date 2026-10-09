// Combined read-only preload; every control still validates its own native DTO.
export const CONTROLLER_SNAPSHOT_SCHEMAS={ControllerSystemFlags:'legaia.controller-system-flags.v1',ControllerBranches:'legaia.controller-branches.v1',ControllerTileRects:'legaia.controller-tile-rects.v1',ControllerFades:'legaia.controller-fades.v1',ControllerTableCopies:'legaia.controller-table-copies.v1',ControllerWordTriplets:'legaia.controller-word-triplets.v1',ControllerThreeWords:'legaia.controller-three-words.v1',ControllerSceneBytes:'legaia.controller-scene-bytes.v1',ControllerFiveWords:'legaia.controller-five-words.v1',ControllerGlobalBytes:'legaia.controller-global-bytes.v1'};
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
export function decodeControllerWorkspaceSnapshot(raw,owner,key){
 if(!/^scene:\/\/[A-Za-z0-9_-]+\/controllers\/man-p1\/0000$/.test(owner)||!hash(key)||raw?.schema_version!=='legaia.controller-workspace-snapshot.v1'||raw.owner_id!==owner||raw.state_key!==key||!hash(raw.source_record_sha256)||!hash(raw.current_record_sha256)||raw.read_only!==true||raw.project_changed!==false||raw.gameplay_verified!==false||!raw.families||Array.isArray(raw.families)||Object.keys(raw.families).length!==Object.keys(CONTROLLER_SNAPSHOT_SCHEMAS).length)throw Error('Controller workspace snapshot source changed.');
 for(const [family,schema] of Object.entries(CONTROLLER_SNAPSHOT_SCHEMAS)){const value=raw.families[family];if(value?.schema_version!==schema||value.owner_id!==owner||value.state_key!==key||value.source_record_sha256!==raw.source_record_sha256||value.current_record_sha256!==raw.current_record_sha256||value.gameplay_verified!==false)throw Error('Controller workspace family source changed.');}
 return structuredClone(raw.families);
}
export async function controllerSnapshotRequest(route,options,initialSnapshot,snapshotRoute){
 if(initialSnapshot!==null&&route===snapshotRoute){
  if(options.signal?.aborted)throw new DOMException('Snapshot preload was aborted','AbortError');
  const body=JSON.parse(options.body);
  if(options.method!=='POST'||!body||Object.keys(body).length!==1||body.entity!==initialSnapshot.owner_id)throw Error('Controller snapshot preload owner changed.');
  return {ok:true,json:async()=>structuredClone(initialSnapshot)};
 }
 return fetch(route,options);
}
