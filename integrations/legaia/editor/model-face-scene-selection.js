import {faceSelectionView} from './model-face-selection-view.js';
const fail=m=>{throw new Error(m);};
function current(source,selection,key){if(source.project_source_key!==key||selection?.project_source_key!==key||selection.asset_id!==source.asset_id||selection.effective_sha256!==source.effective_sha256)fail('Scene face highlight differs from the qualified Current source.');}
export function highlightSceneFaceDocument(scene,source,selection){
  current(source,selection,scene.project_source_key);if(!Array.isArray(scene.assets)||scene.assets.length>128||!Array.isArray(scene.entities)||scene.entities.length>2048)fail('Scene face highlight exceeds its geometry or instance budget.');
  const keys=new Set(scene.entities.filter(e=>e.asset_id===source.asset_id&&e.renderable).map(e=>e.geometry_key)),result=structuredClone(scene);let count=0;
  for(const a of result.assets)if(keys.has(a.geometry_key)){if(a.asset_id!==source.asset_id)fail('Scene face highlight geometry has another asset owner.');a.preview=faceSelectionView(a.preview,source,selection).geometry;count++;}
  if(!count||count!==keys.size)fail('Qualified model has missing or duplicate Current scene geometry.');
  return result;
}
export function highlightSceneFaceProposal(report,source,selection){
  current(source,selection,report.project_source_key);if(report.asset_id!==source.asset_id||report.effective_sha256!==source.effective_sha256||report.instance_scope!=='all_model_instances'||!Array.isArray(report.proposal_assets)||!report.proposal_assets.length||report.proposal_assets.length>128)fail('Scene face highlight requires the exact reviewed shared-model proposal.');
  const result=structuredClone(report);result.preview=faceSelectionView(result.preview,source,selection).geometry;
  for(const a of result.proposal_assets){if(a.asset_id!==source.asset_id)fail('Scene face proposal geometry has another model owner.');a.preview=faceSelectionView(a.preview,source,selection).geometry;}
  return result;
}
