import {decodeSceneCatalog} from '/scene-catalog.js';
import {openCatalogScenePreview} from '/catalog-scene-preview.js';
import {openModelResolution} from '/model-resolution.js';
import {openSequenceReplacement} from '/sequence-replacement-authoring.js';
import {animationChannelAuthoringTarget,validateImportedChannelHandoff,validateRetainedChannelHandoff} from '/animation-channel-authoring.js';
import {createAnimationChannelGraph} from '/animation-channel-graph.js';
import {openProjectChanges} from '/project-changes.js';
import {openCommandHistory} from '/command-history.js';
import {mountSceneRuler} from '/scene-ruler.js';
import {mountMeshSourceLibrary,navigateMeshSource} from '/mesh-source-library.js';
import {mountNpcPresets,NPC_PRESET_SCOPE} from '/npc-presets.js';
import {qualifyTransitionGraphEntry} from '/transition-graph-entry.js';
import {mountPlacementGizmo} from '/worldmap-placement-gizmo.js';
import {highlightSceneFaceDocument,highlightSceneFaceProposal} from '/model-face-scene-selection.js';
import {openTextureSlotEditor} from '/texture-slots.js';
import {openTextureResizeEditor} from '/texture-resize.js';
import {decodeRetailComparison,retailComparisonLabel} from '/texture-comparison.js';
import {openTextureSourceRetention} from '/texture-source-retention.js';
import {environmentYawMatrix,yawFromDrag,environmentRotationCommand} from '/environment-rotation.js';
import {mountBuildReview,validResourceRelocation} from '/build-review.js';
import {mountDraftOutputReview} from '/draft-review.js';
import {mountBuildHistory} from '/build-history.js';
import {openAssetBuildHistory} from '/asset-build-history.js';
import {openAssetReferences,qualifyAssetReferenceInstructionSite} from '/asset-references.js';
import {openActorAnimationAssignment} from '/actor-animation.js';
import {mountProjectSettings} from '/project-settings.js';
import {mountProjectCopy} from '/project-copy.js';
import {mountModelSourceLibrary,navigateModelSource} from '/model-source-library.js';
import {mountAnimationSourceLibrary,navigateAnimationSource} from '/animation-source-library.js';
import {mountEnvironmentGroup} from '/environment-group.js';
import {mountEnvironmentLayout} from '/environment-layout.js';
import {mountEnvironmentRotationGroup} from '/environment-rotation-group.js';
import {mountSceneSelectionSets,decodeSavedSceneSelection} from '/scene-selection-sets.js';
import {mountScenePlacementGroup} from '/scene-placement-group.js';
import {mergeScenePlacementSelection,invertScenePlacementSelection,scenePlacementSelectionKind,matchingModelPlacementIds,modelPlacementIdsForAsset} from '/scene-placement-selection.js';
import {mountWallRectangle,wallRectangleGeometry} from '/collision-rectangle.js';
import {mountFloorRectangle,decodeFloorRectangle} from '/floor-rectangle.js';
import {mountFloorHeights,decodeFloorHeights} from '/floor-heights.js';
import {nativeFloorSelectorAtTriangle} from '/floor-picking.js';
import {qualifyNormalRebuild} from '/model-normal-rebuild.js';
import {rescaleStoredNormal} from '/model-normal-length.js';
import {normalAngleUnits,rotateStoredNormals,qualifyNormalRotation} from '/model-normal-rotation.js';
import {rotateObjectWords,qualifyObjectAngle} from '/model-object-angle.js';
import {scaleObjectWords,qualifyObjectAxisScale} from '/model-object-axis-scale.js';
import {mirrorObjectWords,qualifyObjectMirror} from '/model-object-mirror.js';
import {mountNormalUsers,decodeNormalUsers} from '/model-normal-users.js';
import {validateNormalRetarget} from '/normal-retarget.js';
import {mountVertexUsers,decodeVertexUsers} from '/model-vertex-users.js';
import {validateVertexRetarget} from '/vertex-retarget.js';
import {qualifySourceNormals,rigidFrameNormals} from '/source-normal-view.js';
import {mountAssetNavigation} from '/asset-navigation.js';
import {wallCellAt,wallDragRectangle,wallSelectionGeometry} from '/wall-viewport.js';
import {interpolateAnimationRange} from '/animation-range.js';
import {mountScriptOperandBundle} from '/script-operand-bundle.js';
import {appendCaptureSummary} from '/script-capture.js';
import {mountScriptOperandFiles,operandOwnerContext} from '/script-operand-files.js';
import {npcDonorModel,npcDonorScript,mountAssetInspector,assetInspectorDefinition,mountTriggerBindingInspector} from '/asset-inspector.js';
import {mountAssetRecordDownload} from '/asset-record-export.js';
import {createAssetMetadataPin,mountAssetMetadataComparison} from '/asset-metadata-comparison.js';
import {renderEnvironmentInspector} from '/environment-inspector.js';
import {bindComponentReferences} from '/component-references.js';
import {decodeFlagResource,openFlagResource} from '/flag-resource.js';
import {decodeTransitionResource,openTransitionResource} from '/transition-resource.js';
import {decodeTransitionArrivalPreview,transitionArrivalCurrent,transitionArrivalMarkers,drawTransitionArrival,decodeTransitionArrivalReview,arrivalDraftPoint,arrivalFromGizmo} from '/transition-arrival-preview.js';
import {mountNpcArrivalAuthoring} from '/npc-arrival-authoring.js';
import {decodeNpcArrivalPreview,npcArrivalPreviewCurrent,npcArrivalPreviewMarkers,drawNpcArrivalPreview} from '/npc-arrival-preview.js';
import {decodeFieldSpatial,drawFieldSpatial,hitFieldSpatial,fieldSpatialFrame} from '/field-spatial.js';
import {openRegionBounds,decodeRegionBoundsAnnotations,regionBoundsGeometry} from '/region-bounds.js';
import {openTriggerCells,decodeTriggerCellsAnnotations,triggerCellsGeometry} from '/trigger-cells.js';
import {openTriggerScripts} from '/trigger-scripts.js';
import {openTriggerGroup,triggerGroupGeometry,triggerGroupFrame} from '/trigger-group.js';
import {decodeTransitionGraph} from '/transition-graph.js';
import {mountTransitionGraphWorkspace} from '/transition-graph-workspace.js';
import {openModelPrimitiveEditor,decodeModelPrimitives} from '/model-primitives.js';
import {nativeSceneFaceAtTriangle} from '/model-face-picking.js';
import {openAnimationGlbEditor} from '/animation-glb.js';
import {resolveActorAnimationGlbTarget} from '/actor-animation-glb-target.js';
import {openAnimationAllocationEditor} from '/animation-allocation.js';
import {openRetainedAnimationAsset,decodeRetainedAnimationAsset} from './retained-animation-assets.js';
import {openAnimationRecordLibrary,allocatedAnimationExportRequest} from '/animation-record-library.js';
import {openRetainedAnimationEditor} from '/animation-record-edit.js';
import {openRetainedAnimationGlbEditor} from '/animation-record-glb.js';
import {openModelGlbEditor} from '/model-glb.js';
import {openModelMaterialsEditor} from '/model-materials.js';
import {openTexturePngEditor} from '/texture-png.js';
import {createSceneAnimationController} from '/scene-animation.js';
import {mountPresetBatch} from '/preset-batch.js';
import {parseAssetQuery,assetMatchesQuery} from '/asset-search.js';
import {parseHierarchyQuery,hierarchyMatches,matchingActorIds} from '/hierarchy-query.js';
import {mountHierarchyNavigation} from '/hierarchy-navigation.js';
import {mountModelPlacementUsers} from '/model-placement-users.js';
import {mountAnimationPlacementUsers,currentAnimationPlacementIds} from '/animation-placement-users.js';
import {mountAnimationContributions} from '/animation-contributions.js';
import {openStabilitySourceAudit} from '/sdk-stability-sources.js';
import {openStabilityChecks} from '/sdk-stability-checks.js';
import {mountHierarchyGroups,revealHierarchyEntities,matchingHierarchyPlacementIds} from '/hierarchy-groups.js';
import {captureSceneViewHierarchy} from '/hierarchy-views.js';
import {mountSceneToolDrawer} from '/scene-tool-drawer.js';
import {mountSceneViews,decodeSavedSceneView,captureSceneViewVisibility,sceneViewIsolationIds,unavailableSceneViewNpcs} from '/scene-views.js';
import {sceneCameraBasis,sceneCameraPlanePoint,sceneAxisCamera,sceneFrameCamera} from '/scene-camera.js';
import {mountSceneCameraInspector} from '/scene-camera-inspector.js';
import {appendPresetImport,presetExportButton} from '/preset-files.js';
import {openActorPresetReview} from '/actor-preset-review.js';
import {ANIMATION_PRESET_SCOPE,presetScopeLabel} from '/preset-animation.js';
import {mountSceneGroundPosition,decodeGroundPositionPreview,nativePositionEntry} from '/scene-ground-position.js';
import {mountNpcCreationPreview} from '/npc-creation-preview.js';
import {mountNpcCreationBuildReview} from '/npc-creation-build-review.js';
import {mountNpcGroundPlacement} from '/npc-ground-placement.js';
import {captureNpcCreation,createdNpcSelection,captureNpcPresetCreation,createdNpcPresetSelection,captureNpcDuplication,duplicatedNpcSelection} from '/npc-creation-selection.js';
import {modelUsageContext,effectiveModelUsers,validateModelUserSelection,retailModelDonors} from '/model-user-selection.js';
import {renderComponentProperties,propertyCommand,renderUnregisteredComponents,renderComponentDetails,renderComponentActions,bindComponentActions} from '/component-inspector.js';
import {mountInspectorComponentFilter} from '/inspector-component-filter.js';
import {mountInspectorSections,inspectorSectionSnapshot} from '/inspector-sections.js';
import {focusScriptInspectorFamily,mountScriptFamilyNavigation} from '/script-inspector-navigation.js';
import {mountScriptBookmarks,qualifyScriptBookmark} from '/script-bookmarks.js';
import {mountProjectScriptBookmarks} from '/project-script-bookmarks.js';
import {openScriptComponentReset} from '/script-component-reset.js';
import {mountScriptOwnerInspector} from '/script-owner-inspector.js';
import {openNpcBuildScript} from './npc-build-script.js';
import {openNpcDialogue} from './npc-dialogue.js';
import {openNpcWaits} from './npc-waits.js';
import {openNpcAnimationOperands} from './npc-animation-operands.js';
import {openNpcEffectColors} from './npc-effect-colors.js';
import {openNpcTransitions} from './npc-transitions.js';
import {renderEffectColorAuthoring} from './script-effect-colors.js';
import {mountAnimationOperands,currentAnimationSelection} from './script-animation-operands.js';
import {openNpcFacing} from './npc-facing.js';
import {openNpcModelSelectors} from './npc-model-selectors.js';
import {openNpcFlags} from './npc-flags.js';
import {openNpcSystemFlags} from './npc-system-flags.js';
import {openNpcBranches} from './npc-branches.js';
import {openNpcMovement} from './npc-movement.js';
function openNpcAppearanceInspector(entityId,modelAssetId=null){
  return openNpcAppearance({entityId,modelAssetId,isSelected:()=>modelAssetId===null||npcDraftSelection===entityId,getState:()=>state,isBusy:()=>busy,canEdit,api,
    canInspectScene:()=>sceneModelsReady()&&scenePreviewCurrent()&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft&&!actorGroupInspection,
    getScenePreview:()=>scenePreview,
    inspectScene:(proposed,report,returnToReview,isCurrent)=>{
      cancelViewportGesture();const failures=sceneRenderer.load(structuredClone(proposed));if(failures.length){sceneRenderer.load(structuredClone(scenePreview));throw new Error(failures.join('; '));}
      scenePose={key:sceneKey,name:'Proposed NPC appearance - not applied',returnToFile:returnToReview,isCurrent};scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent='Proposed NPC appearance - script donor and placement retained';
      configureSceneInspectionComparison(proposed);for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('[aria-label="Scene preview rate"]').parentElement])control.hidden=true;
      const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to NPC appearance';frameShapeProposal({instance_scope:'all_model_instances',proposal_instances:[{entity_id:report.entity_id,proposed:report.proposed.position}]},null);draw();
    }
  });
}
import {openNpcAppearance} from './npc-appearance.js';
import {openNpcDonorScript} from './npc-donor-script.js';
import {openNpcCurrentScript} from './npc-current-script.js';
import {openDraftRepeat} from '/draft-repeat.js';
import {openDraftGroup} from '/draft-group.js';
import {openDonorGroup} from '/draft-donor-group.js';
import {npcAnimationSceneTarget,npcDonorAnimationBinding,renderNpcDraftInspector,mountNpcDraftScriptActions,npcScriptBindingSnapshot} from '/npc-draft-inspector.js';
import {openNpcScriptReset} from '/npc-script-reset.js';
import {mountActorSelectionSets,decodeSavedActorSelection} from '/actor-selection-sets.js';
import {mountGroupAppearance} from '/group-appearance.js';
import {textureSceneUsage,textureMatchedPlacementIds} from '/texture-usage.js';
import {findDecodedPath} from '/script-paths.js';
import {mountScriptFlowOverview} from '/script-flow-overview.js';
import {mountScriptWalkthrough} from '/script-walkthrough.js';
import {decodeTextFont,layoutGlyphRun} from '/text-font.js';
import {instructionOperandEditors,menuLabelEditors} from '/script-operands.js';
import {mountScriptFacing} from '/script-facing.js';
import {mountScriptBranches} from '/script-branches.js';
import {mountSystemSelectors} from '/system-flag-selectors.js';
import {mountSourceBuildScript} from '/source-build-script.js';
import {mountWorldmapAuthoring} from '/worldmap-authoring.js';
import {mountWorldmapGeometry} from '/worldmap-geometry.js';
import {mountWorldPlacements} from '/worldmap-placement-editor.js';
import {openAudioSequence} from '/audio-sequence.js';
import {openAudioInput} from '/audio-input-assets.js';
import {openMidiInput} from '/midi-input-assets.js';
import {openAudioBank} from '/audio-bank.js';
import {mountProjectAssets,projectAssetVariant,qualifyProjectCatalogVariant} from '/project-assets.js';
import {captureRuntimeReview,parseRuntimeReview,compareRuntimeReviews,historicalRuntimePositions,historicalRuntimeComparisonPositions,historicalSampleHits,MAX_REVIEW_BYTES} from '/runtime-review.js';
import {createHistoricalActorComparisonDialog} from '/historical-actor-comparison.js';
import {mountActorPlacementBatch,toggleActorGroupSelection,mergeActorGroupSelection,actorGroupRange} from '/actor-placement-batch.js';
const $ = (id) => document.getElementById(id);
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const numeric = (value) => typeof value === 'number' && Number.isFinite(value);
const format = (value) => numeric(value) ? String(Math.round(value * 1000) / 1000) : 'Unknown';
let assetPlacementSelection=null,animationContributions=null;
let state = {project:{}, scene:null, assets:[], selection:{}, history:{}, capabilities:{}};
let busy = false, toastTimer, lastSceneId, grid = true;
let sceneAnimationController=null;
let sceneCameraInspector=null;
let sceneAnimationWriteGuard=false;
let worldmapControls=null,worldmapGeometryControls=null,worldPlacementControls=null,worldmapDraftPending=false;
let projectAssetControls=null;
let sceneResourceSelection=null;
let scenePlacementMode=false,scenePlacementBoxMode=false,scenePlacementSelection=[],scenePlacementKey=null,scenePlacementInspection=null,scenePlacementTool=null;
let actorGroupInspection=null,actorGroupSelection=[],actorGroupSelectionKey=null,actorGroupRangeAnchor=null,actorBoxMode=false;
const canvas = $('viewport'), ctx = canvas.getContext('2d');
const transformTools=document.createElement('div');transformTools.className='transform-tools';
transformTools.innerHTML='<label><input id="transform-snap" type="checkbox"> Snap moves</label><label>Step <select id="transform-snap-step" aria-label="Transform snap step"><option value="16">16 units</option><option value="64" selected>64 units</option><option value="256">256 units</option><option value="1024">1024 units</option></select></label><span id="transform-drag-status" role="status">X/Z moves · snap aligns to scene origin</span>';
const sceneryTool=document.createElement('select');sceneryTool.id='scenery-transform-tool';sceneryTool.setAttribute('aria-label','Scenery transform tool');for(const [value,text] of [['move','Move'],['yaw','Rotate scenery Y']]){const option=document.createElement('option');option.value=value;option.textContent=text;sceneryTool.append(option);}const yawSnap=document.createElement('input');yawSnap.type='checkbox';yawSnap.checked=true;yawSnap.id='scenery-yaw-snap';const yawLabel=document.createElement('label');yawLabel.textContent='Snap yaw ';yawLabel.append(yawSnap);const yawStep=document.createElement('select');yawStep.id='scenery-yaw-step';yawStep.setAttribute('aria-label','Scenery yaw snap step');for(const [value,text] of [[16,'16 units'],[64,'64 units'],[256,'256 units (22.5°)'],[1024,'1024 units (90°)']]){const option=document.createElement('option');option.value=String(value);option.textContent=text;yawStep.append(option);}yawStep.value='256';transformTools.prepend(sceneryTool,yawLabel,yawStep);for(const control of [sceneryTool,yawSnap,yawStep])control.onchange=()=>{cancelViewportGesture();draw();};
$('viewport-wrap').before(transformTools);
function snappedTransformCoordinate(value,step){return Math.round(value/(step||1))*(step||1);}
const camera = {projection:'perspective',yaw:-0.65,pitch:0.66,distance:2000,target:{x:0,y:0,z:0}};
let width=1, height=1, projected=[], handles=[], drag=null, draft=null, pendingEntityFrame=null;
let sceneRepresentation="authored";
let sceneRenderer=null,scenePreview=null,sceneProjectPath=null,sceneLoadedId=null,sceneKey=null,scenePendingKey=null,sceneFailedKey=null,sceneAbort=null,sceneError=null,modelsEnabled=true,cameraRevision=0,sceneNormalDiagnostic=false,assetNavigation=null;
const sceneLayers={actors:true,scenery:true,ground:true};
let showObservedNodes=false,runtimeNodeHits=[],pickRuntimeNodes=false;
const observedLayerButton=document.createElement('button');observedLayerButton.textContent='Runtime positions';observedLayerButton.setAttribute('aria-pressed','false');observedLayerButton.title='Alt-click a sampled marker to inspect it, including occluded nodes; not confirmed NPC identities';observedLayerButton.onclick=()=>{showObservedNodes=!showObservedNodes;observedLayerButton.setAttribute('aria-pressed',String(showObservedNodes));draw();};$('frame-selected').after(observedLayerButton);
const pickRuntimeButton=document.createElement('button');pickRuntimeButton.textContent='Pick runtime node';pickRuntimeButton.setAttribute('aria-pressed','false');pickRuntimeButton.onclick=()=>{pickRuntimeNodes=!pickRuntimeNodes;pickRuntimeButton.setAttribute('aria-pressed',String(pickRuntimeNodes));if(pickRuntimeNodes){showObservedNodes=true;observedLayerButton.setAttribute('aria-pressed','true');}draw();};$('frame-selected').after(pickRuntimeButton);
const nodesButton=document.createElement('button');nodesButton.textContent='Observed nodes';$('frame-selected').after(nodesButton);
const nodesDialog=document.createElement('dialog');nodesDialog.className='project-dialog observed-nodes-dialog';document.body.append(nodesDialog);
let nodeReviewRevision=0;
let historicalPositions=null,historicalHits=[],pickHistoricalSamples=false;
const historicalTools=document.createElement('div');historicalTools.className='scene-tools';historicalTools.id='historical-runtime-tools';historicalTools.hidden=true;
const historicalStatus=document.createElement('span');historicalStatus.setAttribute('role','status');historicalStatus.style.display='block';historicalStatus.style.marginBottom='4px';historicalTools.style.padding='6px 12px';historicalTools.append(historicalStatus);
const historicalLayerLabel=document.createElement('label');historicalLayerLabel.textContent='Historical samples ';historicalLayerLabel.style.marginRight='8px';const historicalLayer=document.createElement('select');historicalLayer.id='historical-sample-layer';historicalLayer.setAttribute('aria-label','Historical sample layer');for(const [value,text] of [['both','Both files'],['baseline','Baseline (blue)'],['comparison','Comparison (amber)']]){const option=document.createElement('option');option.value=value;option.textContent=text;historicalLayer.append(option);}historicalLayerLabel.append(historicalLayer);historicalTools.append(historicalLayerLabel);historicalLayerLabel.hidden=true;
historicalLayer.onchange=()=>{const overlay=currentHistoricalPositions();if(busy||!overlay?.comparison)return;try{const value=historicalRuntimeComparisonPositions(overlay.comparison.before,overlay.comparison.after,{scene_id:state.scene?.id,mode:state.project?.mode},historicalLayer.value);cancelViewportGesture();Object.assign(overlay,value);draw();}catch(error){notify(error.message,true);}};

for(const [id,label,action] of [['historical-frame','Frame historical positions',()=>{const overlay=currentHistoricalPositions();if(!overlay||busy)return;try{cancelViewportGesture();const points=overlay.nodes.map(node=>displayPosition(node.observed_position));Object.assign(camera,sceneFrameCamera(camera,{width,height},points));pendingEntityFrame=null;cameraRevision++;draw();}catch(error){notify(error.message,true);}}],['historical-review','Return to historical review',()=>{const overlay=currentHistoricalPositions();if(overlay&&!busy){if(overlay.comparison)renderRuntimeComparison(overlay.comparison);else renderSavedNodeReview(overlay.review);}} ],['historical-clear','Clear historical positions',()=>{historicalPositions=null;draw();}]]){const button=document.createElement('button');button.id=id;button.textContent=label;button.onclick=action;historicalTools.append(button);}
$('viewport-wrap').before(historicalTools);
const historicalSample=document.createElement('select');historicalSample.id='historical-sample';historicalSample.setAttribute('aria-label','Historical node sample');historicalSample.style.maxWidth='100%';historicalTools.append(historicalSample);
const inspectHistorical=document.createElement('button');inspectHistorical.id='historical-inspect';inspectHistorical.textContent='Inspect historical sample';inspectHistorical.onclick=()=>openHistoricalSample(historicalSample.value);historicalTools.append(inspectHistorical);
const historicalActorCoordinates=createHistoricalActorComparisonDialog({getContext:()=>{const overlay=currentHistoricalPositions(),actor=selected();return {key:historicalPositionKey(),scene_id:state.scene?.id,mode:state.project?.mode,representation:sceneRepresentation,source_key:state.project_copy_source_key,actor,preview:activeScenePreview()?.entities?.find(row=>row.entity_id===actor?.id),node_id:historicalSample.value,overlay};},notify,download:downloadRuntimeReview});
const compareHistoricalActor=document.createElement('button');compareHistoricalActor.id='historical-compare-actor';compareHistoricalActor.textContent='Compare selected actor coordinates';compareHistoricalActor.onclick=()=>{if(!busy&&!drag&&!draft&&currentHistoricalPositions())historicalActorCoordinates.open();};historicalTools.append(compareHistoricalActor);
const pickHistorical=document.createElement('button');pickHistorical.id='historical-pick';pickHistorical.textContent='Pick historical sample';pickHistorical.setAttribute('aria-pressed','false');pickHistorical.onclick=()=>{if(busy||!currentHistoricalPositions())return;cancelViewportGesture();pickHistoricalSamples=!pickHistoricalSamples;draw();};historicalTools.append(pickHistorical);
function openHistoricalSample(id){const overlay=currentHistoricalPositions();if(busy||!overlay||!overlay.nodes.some(node=>node.runtime_node_id===id))return;cancelViewportGesture();pickHistoricalSamples=false;if(overlay.comparison)renderRuntimeComparison(overlay.comparison);else renderSavedNodeReview(overlay.review);const search=nodesDialog.querySelector('input[type="search"]');search.value=id;search.dispatchEvent(new Event('input'));for(const detail of nodesDialog.querySelectorAll('details'))if(!detail.hidden&&detail.querySelector('summary')?.textContent.includes(id))detail.open=true;draw();}

function historicalPositionKey(){return JSON.stringify([state.project?.path,state.project?.mode,state.scene?.id,state.project_copy_source_key,sceneRequestKey()]);}
function currentHistoricalPositions(){if(historicalPositions&&(historicalPositions.key!==historicalPositionKey()||state.project?.mode!=='edit'||!scenePreviewCurrent()))historicalPositions=null;return historicalPositions;}
function appendHistoricalPositionAction(review,comparison=null){
 const key=historicalPositionKey(),button=document.createElement('button');button.id=comparison?'show-historical-comparison':'show-historical-positions';button.textContent=comparison?'Show historical comparison positions':'Show historical positions';const note=document.createElement('p');note.className='field-note';
 let decoded=null;try{decoded=(comparison?historicalRuntimeComparisonPositions(comparison.before,comparison.after,{scene_id:state.scene?.id,mode:state.project?.mode}):historicalRuntimePositions(review,{scene_id:state.scene?.id,mode:state.project?.mode}));if(!scenePreviewCurrent())throw new Error('Load the matching scene preview first.');if(!decoded.nodes.length)throw new Error('No complete supported XYZ samples in this file.');note.textContent=`${decoded.nodes.length} complete samples; ${decoded.skipped} incomplete or out-of-range samples skipped. File-declared coordinates only; source and actor identities are unconfirmed. Markers include occluded positions.${comparison?' Lines join matching declared keys, not motion paths or confirmed lifetimes. File order is not capture chronology.':''}`;}catch(error){note.textContent=error.message;}
 button.disabled=busy||!decoded?.nodes.length||!scenePreviewCurrent();button.onclick=()=>{if(busy||key!==historicalPositionKey()||!scenePreviewCurrent())return;try{const value=(comparison?historicalRuntimeComparisonPositions(comparison.before,comparison.after,{scene_id:state.scene?.id,mode:state.project?.mode}):historicalRuntimePositions(review,{scene_id:state.scene?.id,mode:state.project?.mode}));if(!value.nodes.length)return;cancelViewportGesture();historicalPositions={...value,key};historicalLayer.value='both';nodesDialog.close();draw();}catch(error){notify(error.message,true);}};nodesDialog.append(button,note);
}
function synchronizeHistoricalPositions(){
 const overlay=currentHistoricalPositions();historicalActorCoordinates.refresh();historicalTools.hidden=!overlay;if(!overlay){pickHistoricalSamples=false;return;}if(!overlay.nodes.length)pickHistoricalSamples=false;const selectedSample=historicalSample.value;historicalSample.replaceChildren();for(const id of new Set(overlay.nodes.map(node=>node.runtime_node_id))){const option=document.createElement("option");option.value=id;option.textContent=id;historicalSample.append(option);}if([...historicalSample.options].some(option=>option.value===selectedSample))historicalSample.value=selectedSample;historicalSample.disabled=busy||!overlay.nodes.length;pickHistorical.setAttribute("aria-pressed",String(pickHistoricalSamples));pickHistorical.classList.toggle("active",pickHistoricalSamples);
 historicalStatus.textContent=`Historical ${overlay.comparison?'comparison ('+overlay.layer+')':'file samples'} · ${overlay.nodes.length} positions · ${overlay.skipped} skipped · ${overlay.review.scene_id} · epoch ${overlay.review.epoch_id} · identity unconfirmed`;
 historicalLayerLabel.hidden=!overlay.comparison;historicalLayer.disabled=busy;for(const button of historicalTools.querySelectorAll('button'))button.disabled=busy||['historical-frame','historical-inspect','historical-pick'].includes(button.id)&&!overlay.nodes.length;
 compareHistoricalActor.disabled=busy||Boolean(drag||draft)||!overlay.nodes.length||!selected()?.id?.startsWith(state.scene.id+'/actors/man-p1/');
 return overlay;
}
function drawHistoricalPositions(){
 historicalHits=[];const overlay=synchronizeHistoricalPositions();if(!overlay)return;
 ctx.save();ctx.strokeStyle='#f4ce83';ctx.fillStyle='#f4ce83';ctx.lineWidth=1.5;ctx.setLineDash([3,2]);ctx.font='11px "Segoe UI",sans-serif';let labels=0;
 for(const pair of overlay.pairs??[])line(displayPosition(pair.before),displayPosition(pair.after),'#c9cbd3',1);for(const node of overlay.nodes){ctx.strokeStyle=ctx.fillStyle=node.sample_layer==='baseline'?'#79d5e8':'#f4ce83';const point=project(displayPosition(node.observed_position));if(!point||!Number.isFinite(point.x)||!Number.isFinite(point.y))continue;historicalHits.push({x:point.x,y:point.y,id:node.runtime_node_id});ctx.beginPath();ctx.arc(point.x,point.y,6,0,Math.PI*2);ctx.stroke();if(labels++<16){const text=(node.sample_layer==='baseline'?'Baseline ':node.sample_layer==='comparison'?'Comparison ':'Historical ')+node.runtime_node_id,textWidth=Math.min(ctx.measureText(text).width,Math.max(1,width-16));ctx.fillText(text,Math.max(8,Math.min(point.x+9,width-textWidth-8)),Math.max(12,Math.min(height-8,point.y+(node.sample_layer==='comparison'?16:-9))),Math.max(1,width-16));}}
 ctx.setLineDash([]);ctx.fillStyle='#f4ce83';ctx.fillText((overlay.comparison?'Baseline blue / comparison amber; lines join declared keys only':'Historical file positions')+' · unconfirmed · includes occluded samples',12,94);ctx.restore();
}

function downloadRuntimeReview(review,filename='runtime-nodes-historical.json'){
  const url=URL.createObjectURL(new Blob([JSON.stringify(review,null,2)+'\n'],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function appendSavedNodeReviewPicker(){
  const revision=nodeReviewRevision,label=document.createElement('label'),input=document.createElement('input');label.textContent='Open saved runtime node review';input.type='file';input.accept='.json';input.setAttribute('aria-label','Saved runtime node review');label.append(input);nodesDialog.append(label);
  const error=document.createElement('p');error.className='dialog-error';error.setAttribute('role','alert');nodesDialog.append(error);
  input.onchange=async()=>{const file=input.files?.[0];if(!file)return;try{if(file.size>MAX_REVIEW_BYTES)throw new Error('Saved review exceeds 1 MiB');const review=parseRuntimeReview(await file.text());if(revision!==nodeReviewRevision||!nodesDialog.open||input.files?.[0]!==file)return;renderSavedNodeReview(review);}catch(e){if(revision===nodeReviewRevision&&nodesDialog.open)error.textContent=e.message;}};
}
function renderSavedNodeReview(review){
  nodeReviewRevision++;nodesDialog.replaceChildren();const heading=document.createElement('h2');heading.textContent='Saved runtime node review · historical';nodesDialog.append(heading);
  const note=document.createElement('p');note.textContent=`Read only · ${review.nodes.length} nodes · ${review.scene_id} · epoch ${review.epoch_id} · exported ${review.exported_at}. Export time is not capture time. This file does not establish current Live state or confirm actor identities.`;nodesDialog.append(note);
  const search=document.createElement('input');search.type='search';search.setAttribute('aria-label','Filter saved nodes');search.placeholder='Filter node or candidate ID';nodesDialog.append(search);
  const list=document.createElement('div');nodesDialog.append(list);const rows=[];
  for(const node of review.nodes){const row=document.createElement('details'),summary=document.createElement('summary'),detail=document.createElement('div');summary.textContent=`${node.runtime_node_id} · XYZ ${node.observed_position.x??'?'} / ${node.observed_position.y??'?'} / ${node.observed_position.z??'?'} · ${node.candidate_entity_ids.length} unconfirmed candidates`;const frames=document.createElement('p');frames.textContent=`Position capture frames: ${node.position_capture_frames?.before??'unknown'}–${node.position_capture_frames?.after??'unknown'} · ${node.reason??'No binding reason recorded'}`;detail.append(frames);const candidates=document.createElement('p');candidates.textContent='Unconfirmed candidate IDs: '+(node.candidate_entity_ids.join(', ')||'none');detail.append(candidates);for(const field of node.decoded_fields){const entry=document.createElement('p'),evidence=document.createElement('small'),value=field.interpreted_value;entry.textContent=`${field.property}: ${value==null?'Unknown':typeof value==='object'?JSON.stringify(value):String(value)} · raw ${field.raw_numeric_value??'unknown'} · ${field.confidence??'unknown'} · applicability ${field.applicability??'unknown'}${field.unresolved?' · unresolved':''}`;evidence.textContent=` ${field.notes??''} ${(field.evidence??[]).join(', ')}`;entry.append(evidence);detail.append(entry);}row.append(summary,detail);list.append(row);rows.push({row,text:JSON.stringify(node).toLowerCase()});}
  search.oninput=()=>{for(const item of rows)item.row.hidden=!item.text.includes(search.value.trim().toLowerCase());};
  const download=document.createElement('button');download.textContent='Download historical metadata';download.onclick=()=>downloadRuntimeReview(review);nodesDialog.append(download);appendRuntimeComparisonPicker(review);appendSavedNodeReviewPicker();appendHistoricalPositionAction(review);
  const back=document.createElement('button');back.textContent='Back to observed nodes';back.onclick=()=>renderObservedNodes();nodesDialog.append(back);const close=document.createElement('button');close.textContent='Close saved review';close.onclick=()=>nodesDialog.close();nodesDialog.append(close);if(!nodesDialog.open)nodesDialog.showModal();
}
function appendRuntimeComparisonPicker(baseline){
  const revision=nodeReviewRevision,label=document.createElement('label'),input=document.createElement('input');
  label.textContent='Compare another saved review with this baseline';input.type='file';input.accept='.json';input.setAttribute('aria-label','Compare saved runtime review');label.append(input);nodesDialog.append(label);
  const error=document.createElement('p');error.className='dialog-error';error.setAttribute('role','alert');nodesDialog.append(error);
  input.onchange=async()=>{const file=input.files?.[0];if(!file)return;try{
    if(file.size>MAX_REVIEW_BYTES)throw new Error('Saved review exceeds 1 MiB');
    const comparison=compareRuntimeReviews(baseline,parseRuntimeReview(await file.text()));
    if(revision!==nodeReviewRevision||!nodesDialog.open||input.files?.[0]!==file)return;
    renderRuntimeComparison(comparison);
  }catch(e){if(revision===nodeReviewRevision&&nodesDialog.open&&input.files?.[0]===file)error.textContent=e.message;}};
}
function renderRuntimeComparison(comparison){
  nodeReviewRevision++;nodesDialog.replaceChildren();
  const heading=document.createElement('h2');heading.textContent='Saved runtime comparison · historical';nodesDialog.append(heading);
  for(const text of comparison.limitations){const note=document.createElement('p');note.textContent=text;nodesDialog.append(note);}
  const context=document.createElement('p');context.textContent=`${comparison.before.scene_id} · epoch ${comparison.before.epoch_id} · profile ${comparison.before.profile_id??'unknown'} · baseline exported ${comparison.before.exported_at} · comparison exported ${comparison.after.exported_at}`;nodesDialog.append(context);
  const search=document.createElement('input');search.type='search';search.placeholder='Filter node, candidate or field';search.setAttribute('aria-label','Filter runtime comparison');nodesDialog.append(search);
  const filter=document.createElement('select');filter.setAttribute('aria-label','Runtime comparison status');
  for(const [value,label] of [['all','All keys'],['paired_changed','Changed samples'],['paired_unchanged','Unchanged samples'],['before_only','Baseline file only'],['after_only','Comparison file only']]){const option=document.createElement('option');option.value=value;option.textContent=label;filter.append(option);}nodesDialog.append(filter);
  const count=document.createElement('p');count.setAttribute('role','status');nodesDialog.append(count);const rows=[];
  for(const item of comparison.rows){const row=document.createElement('details'),summary=document.createElement('summary');
    summary.textContent=`${item.runtime_node_id} · ${item.status.replaceAll('_',' ')} · identity unconfirmed`;row.append(summary);
    if(item.position_delta){const delta=document.createElement('p');delta.textContent=`Coordinate sample difference (comparison minus baseline): X ${item.position_delta.x??'unknown'} / Y ${item.position_delta.y??'unknown'} / Z ${item.position_delta.z??'unknown'}`;row.append(delta);}
    const table=document.createElement('table'),header=document.createElement('tr');table.className='runtime-comparison-table';
    for(const text of ['Captured value','Baseline','Comparison']){const cell=document.createElement('th');cell.textContent=text;header.append(cell);}table.append(header);
    const values=[...['x','y','z'].map(axis=>[axis.toUpperCase(),node=>node.observed_position[axis]??'unknown']),['Position frames',node=>node.position_capture_frames?`${node.position_capture_frames.before}–${node.position_capture_frames.after}`:'unknown'],['Unconfirmed candidates',node=>node.candidate_entity_ids.join(', ')||'none'],['Binding reason',node=>node.reason??'unknown']];
    for(const [label,get] of values){const tr=document.createElement('tr');for(const text of [label,item.before?get(item.before):'Key absent',item.after?get(item.after):'Key absent']){const td=document.createElement('td');td.textContent=String(text);tr.append(td);}table.append(tr);}row.append(table);
    const fields=document.createElement('p');fields.textContent='Changed decoded field metadata: '+(item.changed_fields.map(field=>field.property).join(', ')||'none');row.append(fields);
    for(const field of item.changed_fields){const detail=document.createElement('details'),title=document.createElement('summary');title.textContent=field.property+' · changed metadata';detail.append(title);for(const [label,value] of [['Baseline',field.before],['Comparison',field.after]]){const text=document.createElement('pre');text.textContent=label+': '+(value?JSON.stringify(value,null,2):'Field absent');detail.append(text);}row.append(detail);}
    // Preserve all original evidence without overwhelming the comparison table.
    const full=document.createElement('details'),title=document.createElement('summary');title.textContent='Full captured metadata';full.append(title);
    for(const [label,node] of [['Baseline',item.before],['Comparison',item.after]]){const detail=document.createElement('pre');detail.textContent=label+': '+(node?JSON.stringify(node,null,2):'Key absent from this file');full.append(detail);}row.append(full);
    nodesDialog.append(row);rows.push({row,item,text:JSON.stringify(item).toLowerCase()});
  }
  const update=()=>{let visible=0;for(const {row,item,text} of rows){row.hidden=(filter.value!=='all'&&filter.value!==item.status)||!text.includes(search.value.trim().toLowerCase());if(!row.hidden)visible++;}count.textContent=`${visible} of ${rows.length} declared node keys`;};search.oninput=filter.onchange=update;update();
  const download=document.createElement('button');download.textContent='Download historical comparison';download.onclick=()=>downloadRuntimeReview(comparison,'runtime-node-comparison-historical.json');nodesDialog.append(download);appendHistoricalPositionAction(comparison.before,comparison);
  for(const [label,review] of [['Return to baseline review',comparison.before],['Open comparison review',comparison.after]]){const button=document.createElement('button');button.textContent=label;button.onclick=()=>renderSavedNodeReview(review);nodesDialog.append(button);}
  const close=document.createElement('button');close.textContent='Close comparison';close.onclick=()=>nodesDialog.close();nodesDialog.append(close);if(!nodesDialog.open)nodesDialog.showModal();
}
nodesButton.onclick=()=>renderObservedNodes();
function renderObservedNodes(query='',nodeIds=null){
  nodeReviewRevision++;
  nodesDialog.replaceChildren();const heading=document.createElement('h2');heading.textContent='Observed runtime nodes';nodesDialog.append(heading);
  const note=document.createElement('p');note.textContent='Captured positions, independent of imported actor matching. Framing changes only the editor camera.';nodesDialog.append(note);
  const epoch=acceptedEpoch(state.runtime),correlation=state.runtime_correlation,context=JSON.stringify([state.project?.path,state.scene?.id]);
  const nodes=state.project?.mode==='live'&&epoch&&correlation?.available===true&&correlation.epoch_id===epoch?(correlation.runtime_nodes??[]).filter(node=>!nodeIds||nodeIds.includes(node.runtime_node_id)):[];
  const search=document.createElement('input');search.type='search';search.value=query;search.placeholder='Filter by node, coordinates, or candidate';search.setAttribute('aria-label','Filter observed nodes');nodesDialog.append(search);
  const list=document.createElement('div');list.className='observed-nodes-list';nodesDialog.append(list);
  const count=document.createElement('p');count.setAttribute('role','status');nodesDialog.append(count);
  const current=()=>state.project?.mode==='live'&&acceptedEpoch(state.runtime)===epoch&&JSON.stringify([state.project?.path,state.scene?.id])===context&&state.runtime_correlation?.available===true&&state.runtime_correlation.epoch_id===epoch;
  const rows=[];
  for(const node of nodes){
    const row=document.createElement('div'),label=document.createElement('p');const p=node.observed_position;label.textContent=`${node.runtime_node_id} | position frames ${node.position_capture_frames?.before??'unknown'}–${node.position_capture_frames?.after??'unknown'} | XYZ ${p?.x??'?'} / ${p?.y??'?'} / ${p?.z??'?'} | ${node.candidate_entity_ids?.length??0} candidate entities`;row.append(label);
    const button=document.createElement('button');button.textContent='Frame node';button.disabled=node.epoch_id!==epoch||!p||!['x','y','z'].every(a=>numeric(p[a]));
    button.onclick=()=>{if(state.project?.mode!=='live'||acceptedEpoch(state.runtime)!==epoch||JSON.stringify([state.project?.path,state.scene?.id])!==context||state.runtime_correlation?.available!==true||state.runtime_correlation.epoch_id!==epoch)return;coordinateProbe={point:{...p},epoch,context};cancelViewportGesture();camera.target=displayPosition(p);camera.distance=800;cameraRevision++;nodesDialog.close();draw();};row.append(button);list.append(row);rows.push({row,text:[node.runtime_node_id,p?.x,p?.y,p?.z,...(node.candidate_entity_ids??[])].join(' ').toLowerCase()});
    const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Captured fields and evidence';details.append(summary);
    for(const field of node.decoded_fields??[]){
      const entry=document.createElement('p');const interpreted=field.interpreted_value;
      const value=interpreted===null||interpreted===undefined?'Unknown':typeof interpreted==='object'?JSON.stringify(interpreted):String(interpreted);
      entry.textContent=`${field.property}: ${value} | raw ${field.raw_numeric_value??'unknown'} | ${field.confidence??'unknown'} | applicability ${field.applicability??'unknown'}${field.unresolved?' | unresolved':''}`;
      const evidence=document.createElement('small');evidence.textContent=` ${field.notes??''} ${(field.evidence??[]).join(', ')}`;entry.append(evidence);details.append(entry);
    }
    row.append(details);
    for(const id of node.candidate_entity_ids??[]){
      const entity=entities().find(item=>item.id===id);if(!entity)continue;
      const inspect=document.createElement('button');inspect.textContent=`Inspect candidate ${entity.name??entity.label??id}`;inspect.title='Unconfirmed identity match; opens imported and observed values separately';
      inspect.onclick=async()=>{if(busy||!current())return;nodesDialog.close();await api('/api/selection',{entity_id:id});};row.append(inspect);
    }
  }
  const filter=()=>{const query=search.value.trim().toLowerCase();let shown=0;for(const item of rows){item.row.hidden=!item.text.includes(query);if(!item.row.hidden)shown++;}count.textContent=`${shown} of ${nodes.length} captured nodes`;};search.oninput=filter;filter();
  if(!nodes.length){const empty=document.createElement('p');empty.textContent='No accepted actor sample. Enter Live mode and Observe actors first.';nodesDialog.append(empty);}
  const save=document.createElement('button');save.textContent='Download captured node metadata';save.disabled=!nodes.length;save.onclick=()=>{if(busy||!current()){notify('The observation context changed. Refresh the captured list before downloading.',true);return;}try{downloadRuntimeReview(captureRuntimeReview({scene_id:state.scene.id,epoch_id:epoch,profile_id:state.runtime.observation?.profile?.profile_id??null,nodes}));}catch(error){notify(error.message,true);}};nodesDialog.append(save);appendSavedNodeReviewPicker();
  const refresh=document.createElement('button');refresh.textContent='Refresh captured list';refresh.onclick=()=>renderObservedNodes(search.value,nodeIds);nodesDialog.append(refresh);
  const close=document.createElement('button');close.textContent='Close';close.onclick=()=>nodesDialog.close();nodesDialog.append(close);if(!nodesDialog.open)nodesDialog.showModal();
};

let scenePose=null,savedActorSelections=null,savedSceneSelections=null,savedSceneViews=null,groupPresetTool=null;
let scriptTargetOverlay=null,scriptTargetHits=[],pickScriptTargets=false;
const scriptTargetTools=document.createElement('div');scriptTargetTools.id='script-target-tools';scriptTargetTools.hidden=true;
scriptTargetTools.innerHTML='<span role="status"></span><select aria-label="Script target instruction"></select><button type="button" data-inspect>Inspect target</button><button type="button" data-pick aria-pressed="false">Pick script target</button><button type="button" data-frame>Frame script targets</button><button type="button" data-clear>Clear script targets</button>';
$('viewport-wrap').before(scriptTargetTools);
scriptTargetTools.querySelector('[data-clear]').onclick=()=>{scriptTargetOverlay?.onClear?.();scriptTargetOverlay=null;draw();};
scriptTargetTools.querySelector('[data-frame]').onclick=()=>frameScriptTargets();
scriptTargetTools.querySelector('[data-inspect]').onclick=()=>inspectScriptTarget(Number(scriptTargetTools.querySelector('select').value));
scriptTargetTools.querySelector('[data-pick]').onclick=()=>{cancelViewportGesture();pickScriptTargets=!pickScriptTargets;draw();};
async function inspectScriptTarget(pc){
  const overlay=currentScriptTargets();if(busy||!overlay||!overlay.targets.some(target=>target.pc===pc))return;
  if(overlay.inspect){cancelViewportGesture();overlay.inspect(pc);return;}
  const id=overlay.identity.replace(/^script:\/\//,'scene://');
  const owner=id.includes('/scripts/man-p2/')?{id,name:overlay.identity,partitionTwo:true}:entities().find(entity=>entity.id===id);
  if(!owner){notify('The source script owner is unavailable. Reopen its script report.',true);return;}
  cancelViewportGesture();await openActorScript(owner,false,null,null,pc);
}
function showNpcMovementTargets(overlay,returnToEditor,isCurrent,onClear){
  if(busy||!scenePreviewCurrent()||overlay.project_source_key!==state.project_copy_source_key||!isCurrent()||!overlay.targets.length||overlay.targets.some(r=>!Number.isFinite(r.position.x)||!Number.isFinite(r.position.z)))throw new Error('Scene or NPC movement source changed. Reopen the movement editor.');
  scriptTargetOverlay?.onClear?.();cancelViewportGesture();
  scriptTargetOverlay={...overlay,key:resourceStateKey(),identity:overlay.entity_id+' - NPC script dispatch unresolved',partial:overlay.partial??false,inspect:returnToEditor,isCurrent,onClear};
  const select=scriptTargetTools.querySelector('select');select.replaceChildren();for(const target of overlay.targets){const option=document.createElement('option');option.value=target.pc;option.textContent=scriptOffset(target.pc)+' '+target.mnemonic+' - X '+target.position.x+', Z '+target.position.z+(target.path_status==='source_unvisited'?' - unvisited source anchor':'');select.append(option);}
  frameScriptTargets();
}
function currentScriptTargets(){
  if(scriptTargetOverlay&&(scriptTargetOverlay.key!==resourceStateKey()||scriptTargetOverlay.isCurrent&&!scriptTargetOverlay.isCurrent())){scriptTargetOverlay.onClear?.();scriptTargetOverlay=null;}
  return scriptTargetOverlay;
}
function frameScriptTargets(){
  const overlay=currentScriptTargets();if(!overlay||busy)return;
  cancelViewportGesture();
  const points=overlay.targets.map(target=>displayPosition({...target.position,y:overlay.height}));
  const min={},max={};for(const axis of ['x','y','z']){min[axis]=Math.min(...points.map(p=>p[axis]));max[axis]=Math.max(...points.map(p=>p[axis]));camera.target[axis]=(min[axis]+max[axis])/2;}
  camera.distance=Math.max(800,Math.hypot(max.x-min.x,max.y-min.y,max.z-min.z)*1.5);cameraRevision++;draw();
}
function drawScriptTargets(){
  scriptTargetHits=[];
  const overlay=currentScriptTargets();scriptTargetTools.hidden=!overlay;
  if(!overlay)pickScriptTargets=false;
  scriptTargetTools.querySelector('[data-pick]').setAttribute('aria-pressed',String(pickScriptTargets));
  if(!overlay)return;
  scriptTargetTools.querySelector('[role="status"]').textContent=`${overlay.identity} · ${overlay.representation??'retail'} targets · ${overlay.targets.length} decoded targets · reference Y ${overlay.height} · ${overlay.partial?'partial paths':'inspected paths'} · execution unknown`;
  const labels=[],markerPoints=overlay.targets.map(target=>project(displayPosition({...target.position,y:overlay.height}))).filter(Boolean);let hiddenLabels=0;
  ctx.save();ctx.strokeStyle='#e9abff';ctx.fillStyle='#e9abff';ctx.lineWidth=2;ctx.font='11px "Segoe UI",sans-serif';
  for(const target of overlay.targets){
    const p=project(displayPosition({...target.position,y:overlay.height}));if(!p)continue;
    const hit={pc:target.pc,x:p.x,y:p.y};scriptTargetHits.push(hit);
    ctx.strokeRect(p.x-6,p.y-6,12,12);
    const context=target.context===null||target.context===undefined?'':` · context ${target.context} unresolved`;
    const title=`${scriptOffset(target.pc)} ${target.mnemonic}${target.parked?' · parked':''}${target.path_status==='source_unvisited'?' · unvisited source anchor':''}${context}`,coordinates=`X ${target.position.x} · Z ${target.position.z}`;
    const box={x:Math.max(4,Math.min(p.x+10,width-ctx.measureText(title).width-12)),y:p.y-21,w:Math.max(ctx.measureText(title).width,ctx.measureText(coordinates).width)+8,h:32};
    let fits=false;
    for(let attempt=0;attempt<32;attempt++){
      box.y=p.y-21+(attempt===0?0:(attempt%2?1:-1)*Math.ceil(attempt/2)*36);
      if(box.y>=0&&box.y+box.h<=height&&!markerPoints.some(marker=>marker.x+8>box.x&&marker.x-8<box.x+box.w&&marker.y+8>box.y&&marker.y-8<box.y+box.h)&&!labels.some(other=>box.x<other.x+other.w&&box.x+box.w>other.x&&box.y<other.y+other.h&&box.y+box.h>other.y)){fits=true;break;}
    }
    if(!fits){hiddenLabels++;continue;}
    hit.label={...box};
    labels.push(box);ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(box.x,box.y+box.h/2);ctx.stroke();ctx.lineWidth=2;
    ctx.fillStyle='#101b20ed';ctx.fillRect(box.x,box.y,box.w,box.h);ctx.fillStyle='#e9abff';
    ctx.fillText(title,box.x+4,box.y+12);ctx.fillText(coordinates,box.x+4,box.y+27);
  }
  ctx.restore();
  if(hiddenLabels)scriptTargetTools.querySelector('[role="status"]').textContent+=` · ${hiddenLabels} labels hidden at this zoom`;
}
let npcArrivalOverlay=null,npcArrivalHeight=0,npcArrivalGizmo=null,npcArrivalGesture=null;
const npcArrivalTools=document.createElement('div');npcArrivalTools.id='npc-arrival-preview-tools';npcArrivalTools.hidden=true;
npcArrivalTools.innerHTML='<span role="status"></span><label>NPC arrival reference Y <input type="number" step="any" value="0" min="-10000000" max="10000000"></label><button type="button" data-frame>Frame NPC arrival comparison</button><button type="button" data-return>Return to NPC arrival editor</button><button type="button" data-clear>Clear NPC arrival comparison</button>';
npcArrivalTools.style.overflowY='auto';npcArrivalTools.style.overflowX='hidden';npcArrivalTools.style.padding='8px 12px';npcArrivalTools.style.overflowWrap='anywhere';npcArrivalTools.querySelector('[role="status"]').style.display='block';npcArrivalTools.querySelector('input').style.width='110px';
$('viewport-wrap').before(npcArrivalTools);
const npcArrivalAuthoring=mountNpcArrivalAuthoring(npcArrivalTools,{getState:()=>state,getPreview:()=>currentNpcArrivalPreview(),current:()=>canEdit()&&!!currentNpcArrivalPreview(),busy:()=>busy,setBusy,api,onApplied:preview=>{npcArrivalOverlay=preview;draw();},onDraftChange:()=>draw(),onCancelGesture:()=>npcArrivalGizmo?.cancel('NPC arrival input changed'),onError:error=>notify(error.message,true)});
function currentNpcArrivalPreview(){if(npcArrivalOverlay&&!npcArrivalPreviewCurrent(npcArrivalOverlay,state))npcArrivalOverlay=null;return npcArrivalOverlay;}
function frameNpcArrivalPreview(){const report=currentNpcArrivalPreview();if(!report||busy)return;cancelViewportGesture();const points=npcArrivalPreviewMarkers(report,npcArrivalHeight,npcArrivalAuthoring.getPreview()).map(displayPosition);for(const axis of ['x','y','z'])camera.target[axis]=(Math.min(...points.map(p=>p[axis]))+Math.max(...points.map(p=>p[axis])))/2;camera.distance=Math.max(1000,Math.hypot(points[0].x-points[1].x,points[0].z-points[1].z)*1.5);cameraRevision++;draw();}
async function openNpcArrivalDestination(source,row){
 if(busy||!canEdit()||source.project_source_key!==state.project_copy_source_key)throw Error('NPC arrival source changed. Reopen the editor.');
 const request={entity_id:source.entity_id,transition_id:row.semantic_id,project_source_key:source.project_source_key};setBusy(true);
 try{const response=await fetch('/api/npc-arrival-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request)}),text=await response.text();if(new TextEncoder().encode(text).length>4194304)throw Error('NPC arrival preview exceeds its metadata budget.');const value=JSON.parse(text);if(!response.ok)throw Error(value.error||'NPC arrival preview failed');const report=decodeNpcArrivalPreview(value,request,state);
 setBusy(false);if(report.destination_scene_id!==state.scene.id&&!await api('/api/scene',{scene_id:report.destination_scene_id}))return false;
 if(!npcArrivalPreviewCurrent(report,state))throw Error('NPC arrival destination changed. Reopen the editor.');npcArrivalOverlay=report;npcArrivalHeight=0;npcArrivalTools.querySelector('input').value='0';npcArrivalTools.querySelector('input').removeAttribute('aria-invalid');document.querySelector('.workspace-tabs [data-panel="viewport"]').click();frameNpcArrivalPreview();return true;
 }finally{setBusy(false);draw();}
}
npcArrivalTools.querySelector('[data-frame]').onclick=frameNpcArrivalPreview;
npcArrivalTools.querySelector('[data-clear]').onclick=()=>{npcArrivalGizmo?.cancel('NPC arrival preview cleared');npcArrivalOverlay=null;draw();};
npcArrivalTools.querySelector('[data-return]').onclick=async()=>{const report=currentNpcArrivalPreview();if(!report||busy)return;if(report.source_scene_id!==state.scene.id&&!await api('/api/scene',{scene_id:report.source_scene_id}))return;if(state.npc_arrival_preview_state_key!==report.project_inputs_key)return;const draft=state.actor_drafts?.[report.entity_id];if(!draft||draft.scene_id!==state.scene.id)return;npcArrivalOverlay=null;selectNpcDraft(report.entity_id);openNpcTransitions({entityId:report.entity_id,getState:()=>state,isBusy:()=>busy,canEdit,api,focusPc:report.source.options.transitions.find(r=>r.semantic_id===report.transition_id).pc,onPreview:openNpcArrivalDestination});draw();};
npcArrivalTools.querySelector('input').oninput=event=>{const input=event.target,height=Number(input.value),valid=input.value.trim()!==''&&Number.isFinite(height)&&Math.abs(height)<=1e7;input.setAttribute('aria-invalid',String(!valid));if(valid){npcArrivalHeight=height;draw();}};
function drawNpcArrivalComparison(){const report=currentNpcArrivalPreview();npcArrivalTools.hidden=!report;npcArrivalAuthoring.refresh();npcArrivalGizmo?.update();if(!report)return;const points=npcArrivalPreviewMarkers(report,npcArrivalHeight);npcArrivalTools.querySelector('[role="status"]').textContent=`NPC ${report.source.draft.name} / destination ${report.destination_scene_id} / Retail X ${points[0].x}, Z ${points[0].z} / NPC Current X ${points[1].x}, Z ${points[1].z} / reference Y ${npcArrivalHeight} (height unknown); Retail/Current separate; draft requires Review, route activation unknown`;for(const control of npcArrivalTools.querySelectorAll('button,input'))control.disabled=busy;npcArrivalAuthoring.refresh();drawNpcArrivalPreview(ctx,report,npcArrivalHeight,project,displayPosition,{width,height},npcArrivalAuthoring.getPreview());}
let transitionArrivalOverlay=null,transitionArrivalHeight=0,transitionArrivalProposal=null,transitionArrivalReviewGeneration=0,arrivalDraft=null,arrivalGizmo=null,arrivalGesture=null;
const transitionArrivalTools=document.createElement('div');transitionArrivalTools.id='transition-arrival-tools';transitionArrivalTools.hidden=true;
transitionArrivalTools.innerHTML='<span role="status"></span><label>Arrival reference Y <input type="number" step="any" value="0" min="-10000000" max="10000000"></label><button type="button" data-frame>Frame arrival comparison</button><button type="button" data-return>Return to source scene</button><button type="button" data-clear>Clear arrival comparison</button>';
$('viewport-wrap').before(transitionArrivalTools);
const arrivalForm=document.createElement('form');arrivalForm.innerHTML='<label>Arrival X <input name="x" type="number" min="64" max="16384" step="64" required></label><label>Arrival Z <input name="z" type="number" min="64" max="16384" step="64" required></label><label>Arrival facing sector <input name="facing_sector" type="number" min="0" max="7" step="1" required></label><button type="submit" data-review>Review proposed arrival</button><button type="button" data-apply disabled>Apply reviewed arrival</button><button type="button" data-discard>Discard arrival draft</button><p role="status"></p><details><summary>Reviewed source byte audit</summary><pre></pre></details>';transitionArrivalTools.append(arrivalForm);
const arrivalMove=document.createElement('input');arrivalMove.type='checkbox';arrivalMove.setAttribute('aria-label','Move arrival draft');const arrivalMoveLabel=document.createElement('label');arrivalMoveLabel.append(arrivalMove,document.createTextNode('Move arrival draft (X/Z, snap 64)'));arrivalForm.before(arrivalMoveLabel);
arrivalMove.onchange=()=>{arrivalGizmo?.cancel('Arrival move mode changed');draw();};
function arrivalValues(){return Object.fromEntries(['x','z','facing_sector'].map(key=>[key,Number(arrivalForm.elements[key].value)]));}
function arrivalLocalPreview(){try{return {draft:true,proposed_arrival:arrivalDraftPoint(arrivalValues())};}catch{return null;}}
function arrivalChanged(){transitionArrivalReviewGeneration++;transitionArrivalProposal=null;arrivalDraft=arrivalLocalPreview();arrivalStatus.textContent='Draft changed. Review again before Apply.';arrivalForm.querySelector('pre').textContent='';draw();}
const arrivalStatus=arrivalForm.querySelector('[role="status"]');
function discardArrivalDraft(){arrivalGizmo?.cancel('Arrival draft discarded');transitionArrivalReviewGeneration++;transitionArrivalProposal=null;arrivalDraft=null;const report=currentTransitionArrival();if(report){const point=report.resource.arrival_layers.effective;for(const [key,value] of Object.entries({x:point.x,z:point.z,facing_sector:point.facing_angle_12bit/512}))arrivalForm.elements[key].value=value;}arrivalStatus.textContent='Review saved Current coordinates or enter a proposed arrival. Apply changes only the source transition entry.';arrivalForm.querySelector('pre').textContent='';draw();}
arrivalForm.oninput=()=>{const values=Object.fromEntries(['x','z','facing_sector'].map(key=>[key,arrivalForm.elements[key].value]));arrivalGizmo?.cancel('Arrival fields changed');for(const [key,value] of Object.entries(values))arrivalForm.elements[key].value=value;arrivalChanged();};
arrivalForm.querySelector('[data-discard]').onclick=discardArrivalDraft;
arrivalForm.onsubmit=async event=>{event.preventDefault();arrivalGizmo?.cancel('Arrival Review requested');const report=currentTransitionArrival();if(!report||busy||!arrivalForm.checkValidity())return;const generation=++transitionArrivalReviewGeneration,request={asset_id:report.asset_id,project_state_key:state.project_transition_state_key,destination_source_key:state.scene_preview_source_key,arrival:Object.fromEntries(['x','z','facing_sector'].map(key=>[key,Number(arrivalForm.elements[key].value)]))};transitionArrivalProposal=null;setBusy(true);
try{const response=await fetch('/api/transition-arrival-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request)}),value=await response.json();if(generation!==transitionArrivalReviewGeneration||currentTransitionArrival()!==report)return;if(!response.ok)throw new Error(value.error||'Arrival Review failed');const review=decodeTransitionArrivalReview(value,request);if(review.preview.resource.source_record.sha256!==report.resource.source_record.sha256)throw new Error('Arrival source record changed');transitionArrivalProposal={...review,request};arrivalDraft=null;arrivalStatus.textContent=`Reviewed ${review.current_change_count} changed Current operand bytes; ${review.source_byte_audit.length} source byte changes. ${review.authored_change?'Apply publishes one source entry edit.':'Already saved; no authored change.'}`;arrivalForm.querySelector('pre').textContent=JSON.stringify(review.source_byte_audit,null,2);setBusy(false);frameTransitionArrival();}catch(error){arrivalStatus.textContent=error.message;}finally{setBusy(false);draw();}};
arrivalForm.querySelector('[data-apply]').onclick=async()=>{const proposal=transitionArrivalProposal,report=currentTransitionArrival();if(!proposal||!report||busy||!proposal.authored_change)return;const root=state.project?.path,request=proposal.request;if(!await api('/api/transition-arrival-apply',{...request,review_key:proposal.review_key}))return;if(root!==state.project?.path||state.scene?.id!==report.destination_scene_id)return;const freshRequest={...request,project_state_key:state.project_transition_state_key,destination_source_key:state.scene_preview_source_key};setBusy(true);try{const response=await fetch('/api/transition-arrival-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(freshRequest)}),value=await response.json();if(!response.ok)throw new Error(value.error||'Saved arrival refresh failed');const fresh=decodeTransitionArrivalReview(value,freshRequest);if(root!==state.project?.path||!transitionArrivalCurrent(fresh.preview,state))return;transitionArrivalOverlay=fresh.preview;setBusy(false);discardArrivalDraft();arrivalStatus.textContent='Arrival saved to its source entry. Undo/Redo and Build use the normal project workflow.';}catch(error){notify(error.message,true);}finally{setBusy(false);draw();}};

function currentTransitionArrival(){if(transitionArrivalOverlay&&!transitionArrivalCurrent(transitionArrivalOverlay,state)){transitionArrivalOverlay=null;transitionArrivalProposal=null;arrivalDraft=null;transitionArrivalReviewGeneration++;}return transitionArrivalOverlay;}
function frameTransitionArrival(){const report=currentTransitionArrival();if(!report||busy)return;cancelViewportGesture();const points=transitionArrivalMarkers(report,transitionArrivalHeight,transitionArrivalProposal??arrivalDraft).map(point=>displayPosition(point));for(const axis of ['x','y','z'])camera.target[axis]=(Math.min(...points.map(p=>p[axis]))+Math.max(...points.map(p=>p[axis])))/2;camera.distance=Math.max(1000,Math.hypot(Math.max(...points.map(p=>p.x))-Math.min(...points.map(p=>p.x)),Math.max(...points.map(p=>p.z))-Math.min(...points.map(p=>p.z)))*1.5);cameraRevision++;draw();}
transitionArrivalTools.querySelector('[data-frame]').onclick=frameTransitionArrival;
transitionArrivalTools.querySelector('[data-clear]').onclick=()=>{arrivalGizmo?.cancel('Arrival comparison cleared');transitionArrivalOverlay=null;transitionArrivalProposal=null;arrivalDraft=null;arrivalMove.checked=false;transitionArrivalReviewGeneration++;draw();};
transitionArrivalTools.querySelector('[data-return]').onclick=async()=>{const report=currentTransitionArrival();if(!report||busy)return;await api('/api/scene',{scene_id:report.source_scene_id});};
transitionArrivalTools.querySelector('input').oninput=event=>{const input=event.target,height=Number(input.value),valid=input.value.trim()!==''&&Number.isFinite(height)&&Math.abs(height)<=1e7;input.setAttribute('aria-invalid',String(!valid));if(valid){transitionArrivalHeight=height;draw();}};
function drawArrivalComparison(){const report=currentTransitionArrival();transitionArrivalTools.hidden=!report;arrivalGizmo?.update();arrivalMove.disabled=busy;if(!report)return;const markers=transitionArrivalMarkers(report,transitionArrivalHeight);transitionArrivalTools.querySelector('[role="status"]').textContent=`Destination ${report.destination_scene_id} · ${report.asset_id} · Retail X ${markers[0].x} Z ${markers[0].z} · Current X ${markers[1].x} Z ${markers[1].z} · reference Y ${transitionArrivalHeight} (height unknown) · arrival only; execution unknown`;for(const button of transitionArrivalTools.querySelectorAll('button'))button.disabled=busy;transitionArrivalTools.querySelector('input').disabled=busy;for(const input of arrivalForm.querySelectorAll('input'))input.disabled=busy;arrivalForm.querySelector('[data-apply]').disabled=busy||!transitionArrivalProposal?.authored_change;drawTransitionArrival(ctx,report,transitionArrivalHeight,project,displayPosition,{width,height},transitionArrivalProposal??arrivalDraft);}
let coordinateProbe=null,locateSample=null,locateGeneration=0;
const locateButton=document.createElement('button');locateButton.textContent='Locate coordinates';$('frame-selected').after(locateButton);
const locateDialog=document.createElement('dialog');locateDialog.className='project-dialog';locateDialog.innerHTML='<form><h2>Locate guest coordinates</h2><p>Place a reference marker using game coordinates. This changes only the editor camera.</p><label>X <input name="x" type="number" step="any" required></label><label>Y <input name="y" type="number" step="any" required value="0"></label><label>Z <input name="z" type="number" step="any" required></label><button type="button" data-surface>Use source surface height</button><p data-surface-status role="status"></p><button type="submit">Locate</button><button type="button" data-clear>Clear marker</button><button type="button" data-close>Cancel</button></form>';document.body.append(locateDialog);
locateButton.onclick=()=>locateDialog.showModal();
locateDialog.addEventListener('close',()=>{locateGeneration++;locateSample=null;locateDialog.querySelector('[data-surface-status]').textContent='';});
locateDialog.querySelectorAll('input').forEach(input=>input.addEventListener('input',()=>{locateGeneration++;locateSample=null;locateDialog.querySelector('[data-surface-status]').textContent='';}));
locateDialog.querySelector('[data-surface]').onclick=async()=>{
  if(busy)return;
  const button=locateDialog.querySelector('[data-surface]'),status=locateDialog.querySelector('[data-surface-status]');
  const x=Number(locateDialog.querySelector('[name="x"]').value),z=Number(locateDialog.querySelector('[name="z"]').value);
  if(['x','z'].some(axis=>!locateDialog.querySelector(`[name="${axis}"]`).value.trim())||![x,z].every(v=>Number.isFinite(v)&&v>=0&&v<=16384)){status.textContent='Enter X/Z from 0 through 16384 to sample the source surface.';return;}
  const generation=++locateGeneration,key=state.scene_preview_source_key,context=JSON.stringify([state.project?.path,state.scene?.id]);
  locateSample=null;setBusy(true);button.disabled=true;status.textContent='Sampling source terrain…';
  try{
    const response=await fetch('/api/terrain-point',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({x,z,source_key:key})}),result=await response.json();
    if(generation!==locateGeneration||!locateDialog.open||context!==JSON.stringify([state.project?.path,state.scene?.id])||key!==state.scene_preview_source_key)return;
    if(!response.ok)throw new Error(result.error||'Terrain sampling failed');
    if(result.source_key!==key||result.scene_id!==state.scene?.id||result.position?.x!==x||result.position?.z!==z)throw new Error('Terrain sample context differs from the requested point');
    if(result.position.y===null){status.textContent='No source surface covers this point. Enter a reference Y manually.';return;}
    if(!Number.isFinite(result.position.y))throw new Error('Invalid source height');
    locateDialog.querySelector('[name="y"]').value=result.position.y;locateSample={x,z,y:result.position.y};
    status.textContent=`Source surface Y ${result.position.y}; runtime elevation is unverified.`;
  }catch(error){if(generation===locateGeneration)status.textContent=error.message;}finally{button.disabled=false;setBusy(false);}
};

locateDialog.querySelector('[data-close]').onclick=()=>locateDialog.close();
locateDialog.querySelector('[data-clear]').onclick=()=>{coordinateProbe=null;locateDialog.close();draw();};
locateDialog.querySelector('form').onsubmit=event=>{
  event.preventDefault();const point={};for(const axis of ['x','y','z']){const input=locateDialog.querySelector(`[name="${axis}"]`);point[axis]=Number(input.value);if(!input.value.trim()||!Number.isFinite(point[axis]))return;}
  coordinateProbe={point,sampleEvidence:!!locateSample&&["x","y","z"].every(axis=>locateSample[axis]===point[axis]),context:JSON.stringify([state.project?.path,state.scene?.id])};cancelViewportGesture();camera.target=displayPosition(point);camera.distance=1000;cameraRevision++;locateDialog.close();draw();
};
function drawCoordinateProbe(){
  if(!coordinateProbe||coordinateProbe.context!==JSON.stringify([state.project?.path,state.scene?.id]))return;
  if(coordinateProbe.epoch&&(state.project?.mode!=='live'||acceptedEpoch(state.runtime)!==coordinateProbe.epoch||state.runtime_correlation?.available!==true||state.runtime_correlation.epoch_id!==coordinateProbe.epoch))return;
  const world=displayPosition(coordinateProbe.point),p=project(world);if(!p)return;
  ctx.save();ctx.strokeStyle='#ffda78';ctx.fillStyle='#ffda78';ctx.lineWidth=2;ctx.beginPath();ctx.arc(p.x,p.y,9,0,Math.PI*2);ctx.moveTo(p.x-15,p.y);ctx.lineTo(p.x+15,p.y);ctx.moveTo(p.x,p.y-15);ctx.lineTo(p.x,p.y+15);ctx.stroke();ctx.font='12px "Segoe UI",sans-serif';const v=coordinateProbe.point;ctx.fillText(`${coordinateProbe.epoch?'Captured node':coordinateProbe.sampleEvidence?'Source surface':'Reference'} X ${v.x} Y ${v.y} Z ${v.z}`,p.x+18,p.y-12);ctx.restore();
}

const frameSamplesButton=document.createElement('button');frameSamplesButton.textContent='Frame live samples';frameSamplesButton.disabled=true;frameSamplesButton.title='Frame all accepted-epoch candidates for the selected actor without changing authored placement';$('frame-selected').after(frameSamplesButton);
frameSamplesButton.onclick=()=>{
  const points=observedCandidatePoints();if(!points.length)return;
  cancelViewportGesture();
  const min={},max={};for(const axis of ['x','y','z']){min[axis]=Math.min(...points.map(p=>p[axis]));max[axis]=Math.max(...points.map(p=>p[axis]));camera.target[axis]=(min[axis]+max[axis])/2;}
  camera.distance=Math.max(800,Math.hypot(max.x-min.x,max.y-min.y,max.z-min.z)*1.5);cameraRevision++;draw();
};

let sceneHidden=new Set(),sceneHiddenScope=null,sceneIsolated=null;
function hiddenSceneEntities(){
  const scope=JSON.stringify([state.project?.path,state.scene?.id]);
  if(scope!==sceneHiddenScope){sceneHidden.clear();sceneIsolated=null;sceneHiddenScope=scope;}
  const preview=activeScenePreview();if(sceneIsolated&&(state.project?.mode!=='edit'||scenePose||actorGroupInspection||environmentGroupInspection||scenePlacementInspection||!scenePreviewCurrent()||sceneIsolated.key!==sceneRequestKey()||!sceneIsolated.ids.every(id=>preview?.entities.some(e=>e.entity_id===id&&e.renderable))))sceneIsolated=null;
  const isolatedHidden=sceneIsolated?(preview?.entities??[]).filter(e=>!sceneIsolated.ids.includes(e.entity_id)).map(e=>e.entity_id):[];
  const inspectionHidden=scenePose?.inspectionIsolated?new Set((activeScenePreview()?.entities??[]).filter(e=>!scenePose.inspectionEntityIds?.includes(e.entity_id)).map(e=>e.entity_id)):new Set();
  return new Set([...isolatedHidden,...inspectionHidden,...sceneHidden,...(activeScenePreview()?.entities??[]).filter(e=>!sceneLayers[e.kind!=='environment'?'actors':e.entity_id.endsWith('/ground')?'ground':'scenery']).map(e=>e.entity_id)]);
}
function visibilitySelection(){return environmentSelection??npcDraftSelection??state.selection?.entity_id;}
for(const [id,label,sameModel] of [['hide-selected','Hide selected',false],['hide-model','Hide model instances',true],['show-hidden','Show hidden',null]]){
  const button=document.createElement('button');button.id=id;button.textContent=label;
  button.title='Temporary viewport visibility only; does not edit or export the scene';
  button.onclick=()=>{
    hiddenSceneEntities();
    if(sameModel===null)sceneHidden.clear();
    else{
      const identifier=visibilitySelection();if(!identifier)return;
      const item=activeScenePreview()?.entities.find(e=>e.entity_id===identifier);
      if(sameModel){if(!item?.asset_id)return;for(const e of activeScenePreview().entities)if(e.asset_id===item.asset_id)sceneHidden.add(e.entity_id);}
      else if(sceneHidden.has(identifier))sceneHidden.delete(identifier);else sceneHidden.add(identifier);
    }
    cancelViewportGesture();renderHierarchy();draw();
  };
  $('frame-all').before(button);
}
const selectModelInstancesButton=document.createElement('button');selectModelInstancesButton.id='select-model-instances';selectModelInstancesButton.textContent='Select model instances';selectModelInstancesButton.disabled=true;$('hide-model').after(selectModelInstancesButton);
function updateAssetPlacementActions(){document.querySelectorAll('[data-asset-placement-action]').forEach(button=>button.refreshPlacementAction?.());}
function updateModelInstanceSelection(){
  updateAssetPlacementActions();
  const button=selectModelInstancesButton;button.disabled=true;button.title='Choose a placement in the current authored scene; selects shared SDK model identities, including hidden placements';
  if(!canSelectHierarchyMatches()||!scenePreviewCurrent()||sceneRepresentation!=='authored'||wallSelectMode)return;
  try{const ids=matchingModelPlacementIds(activeScenePreview().entities,visibilitySelection(),scenePlacementEligible());button.disabled=false;button.title=ids.length+' placements share the selected current SDK model identity; hidden placements are included';}catch(error){button.title=error.message;}
}
async function selectCurrentPlacementGroup(ids,focus,current){
  if(!current()||!canSelectHierarchyMatches()||!scenePreviewCurrent()||sceneRepresentation!=='authored'||wallSelectMode)return false;
  ids=mergeScenePlacementSelection([],ids,scenePlacementEligible());
  const key=resourceStateKey(),source=state.scene_preview_source_key;
  if(!ids.includes(focus))throw new Error('The active placement must belong to the current group.');
  if(entities().some(entity=>entity.id===focus)&&!await api('/api/selection',{entity_id:focus}))return false;
  if(!current()||key!==resourceStateKey()||source!==state.scene_preview_source_key||!canSelectHierarchyMatches()||!scenePreviewCurrent()||sceneRepresentation!=='authored'||wallSelectMode)throw new Error('Scene sources or selection changed. Select again.');
  setSourcePlacementGroup(ids,focus);$('entity-search').value='';renderHierarchy();revealHierarchyEntities($('hierarchy'),ids,focus);renderInspector();draw();notify(ids.length+' placements selected, including qualified hidden members. Project content unchanged.');return true;
}
async function selectCurrentModelPlacementGroup(assetId,focus,current){
  if(!scenePreviewCurrent())return false;
  const ids=modelPlacementIdsForAsset(activeScenePreview().entities,assetId,scenePlacementEligible());
  return selectCurrentPlacementGroup(ids,focus,()=>current()&&scenePreviewCurrent()&&JSON.stringify(ids)===JSON.stringify(modelPlacementIdsForAsset(activeScenePreview().entities,assetId,scenePlacementEligible())));
}
selectModelInstancesButton.onclick=async()=>{
  if(selectModelInstancesButton.disabled||!scenePreviewCurrent())return;
  try{const focus=visibilitySelection(),assetId=activeScenePreview().entities.find(row=>row.entity_id===focus)?.asset_id;await selectCurrentModelPlacementGroup(assetId,focus,()=>focus===visibilitySelection());}catch(error){notify(error.message,true);}
};
const sceneIsolateButton=document.createElement('button');sceneIsolateButton.id='scene-isolate-selected';sceneIsolateButton.textContent='Isolate selected';sceneIsolateButton.setAttribute('aria-pressed','false');sceneIsolateButton.title='Temporarily show the selected instances; Restore preserves manual visibility and scene layers';$('frame-all').before(sceneIsolateButton);
const sceneFrameIsolatedButton=document.createElement('button');sceneFrameIsolatedButton.id='scene-frame-isolated';sceneFrameIsolatedButton.textContent='Frame isolated';sceneFrameIsolatedButton.title='Fit the visible isolated mesh bounds; preserve camera angles and scene visibility';sceneFrameIsolatedButton.disabled=true;sceneIsolateButton.after(sceneFrameIsolatedButton);
sceneFrameIsolatedButton.onclick=()=>{if(busy||!sceneModelsReady())return;hiddenSceneEntities();if(!sceneIsolated||!scenePreviewCurrent())return;cancelViewportGesture();const view=sceneView();const points=sceneIsolated.ids.flatMap(id=>sceneRenderer.bounds(view.positions,id,view.hiddenEntities,view.transforms));if(!points.length)return;try{const framed=sceneFrameCamera(camera,{width,height},points);pendingEntityFrame=null;Object.assign(camera,framed);cameraRevision++;draw();}catch(error){notify(error.message,true);}};
function isolationSelection(){if(scenePlacementSelection.length||actorGroupSelection.length||environmentGroupSelection.length)return currentPlacementSelection();return visibilitySelection()?[visibilitySelection()]:[];}
function isolationSelectionReady(ids,hidden){return ids.length>=1&&ids.length<=128&&new Set(ids).size===ids.length&&ids.every(id=>!hidden.has(id)&&activeScenePreview()?.entities.some(e=>e.entity_id===id&&e.renderable));}
function updateSceneIsolation(){const hidden=hiddenSceneEntities(),ids=isolationSelection();sceneIsolateButton.disabled=busy||state.project?.mode!=='edit'||!scenePreviewCurrent()||!!scenePose||!!actorGroupInspection||!!environmentGroupInspection||!!scenePlacementInspection||!sceneIsolated&&!isolationSelectionReady(ids,hidden);sceneIsolateButton.textContent=sceneIsolated?'Restore scene':ids.length>1?`Isolate selection (${ids.length})`:'Isolate selected';sceneIsolateButton.classList.toggle('active',!!sceneIsolated);sceneIsolateButton.setAttribute('aria-pressed',String(!!sceneIsolated));sceneFrameIsolatedButton.disabled=busy||!sceneIsolated||!sceneModelsReady()||!sceneIsolated.ids.some(id=>!hidden.has(id));}
sceneIsolateButton.onclick=()=>{if(busy)return;const hidden=hiddenSceneEntities();if(sceneIsolated)sceneIsolated=null;else{const ids=isolationSelection();if(state.project?.mode!=='edit'||!scenePreviewCurrent()||scenePose||actorGroupInspection||environmentGroupInspection||scenePlacementInspection||!isolationSelectionReady(ids,hidden))return;sceneIsolated={ids:[...ids].sort(),key:sceneRequestKey()};}cancelViewportGesture();renderHierarchy();draw();};
for(const [layer,label] of Object.entries({actors:'Actors',scenery:'Scenery',ground:'Ground'})){
  const button=document.createElement('button');button.id='scene-layer-'+layer;button.textContent=label;button.className='active';button.setAttribute('aria-pressed','true');button.title=`Show ${label.toLowerCase()} in the scene view`;
  button.onclick=()=>{sceneLayers[layer]=!sceneLayers[layer];button.classList.toggle('active',sceneLayers[layer]);button.setAttribute('aria-pressed',String(sceneLayers[layer]));cancelViewportGesture();renderHierarchy();draw();};
  $('frame-all').before(button);
}
const sceneExportButton=document.createElement('button');sceneExportButton.id='scene-export-glb';sceneExportButton.textContent='Export scene GLB';sceneExportButton.title='Export the complete source scene, including temporarily hidden instances; static reference poses';$('frame-all').after(sceneExportButton);
const selectedExportButton=document.createElement('button');selectedExportButton.id='scene-export-selected';selectedExportButton.textContent='Export selected GLB';selectedExportButton.title='Export one selected instance at its scene position';sceneExportButton.after(selectedExportButton);
sceneExportButton.onclick=()=>exportSceneGlb();
selectedExportButton.onclick=()=>{const id=visibilitySelection();if(!id){notify('Select an actor or scenery instance first.',true);return;}exportSceneGlb(id);};
async function exportSceneGlb(entityId=null){
  if(busy)return;
  if(!scenePreviewCurrent()||!state.scene_preview_source_key){notify('Wait for a current scene preview before exporting.',true);return;}
  if(currentNpcCreationInspection()||currentGroundPositionInspection()||scenePose||shapeDraft||actorGroupInspection||environmentGroupInspection||scenePlacementInspection){notify('Restore the scene inspection and finish or discard model edits before exporting.',true);return;}
  cancelViewportGesture();const key=sceneRequestKey();setBusy(true);sceneExportButton.disabled=true;selectedExportButton.disabled=true;
  try{
    const response=await fetch('/api/export/scene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({representation:sceneRepresentation,source_key:state.scene_preview_source_key,...(entityId?{entity_id:entityId}:{})})}),result=await response.json();
    if(!response.ok||result.error)throw new Error(result.error??'Scene export failed');
    if(key!==sceneRequestKey()){notify('Scene export completed for the previous scene; reopen its project Exports folder.');return;}
    exportDialog.innerHTML=`<div class="dialog-heading"><h2>Scene exported</h2><button type="button">Close</button></div><p>${result.audit.entity_count} instances · ${result.audit.geometry_count} shared geometries · ${result.audit.unavailable_entities.length} metadata-only instances</p><p>${result.audit.export_scope==='selected-instance'?'Selected instance at its scene placement.':`Complete ${escapeHTML(result.audit.representation)} scene, including temporarily hidden instances.`} Static reference poses and source units; runtime visibility, lighting and physical scale are unverified.</p><label>Private GLB file<input readonly value="${escapeHTML(result.path)}"></label><details><summary>Source provenance and limitations</summary><pre>${escapeHTML(JSON.stringify(result.audit,null,2))}</pre></details>`;
    exportDialog.querySelector('button').onclick=()=>exportDialog.close();exportDialog.showModal();
  }catch(error){notify(error.message,true);}finally{sceneExportButton.disabled=false;selectedExportButton.disabled=false;setBusy(false);}
};
const projectionSelect=document.createElement('select');projectionSelect.id='scene-projection';projectionSelect.setAttribute('aria-label','Scene projection');projectionSelect.innerHTML='<option value="perspective">Perspective</option><option value="orthographic">Orthographic</option>';$('frame-all').before(projectionSelect);
projectionSelect.onchange=()=>{cancelViewportGesture();pendingEntityFrame=null;camera.projection=projectionSelect.value;if(camera.projection==='perspective')camera.pitch=Math.max(.12,camera.pitch);document.querySelector('.viewport-type').textContent=projectionSelect.selectedOptions[0].textContent;cameraRevision++;draw();};
const topViewButton=document.createElement('button');topViewButton.id='scene-top-view';topViewButton.textContent='Top (X/Z)';topViewButton.title='Orthographic top view: +X right, +Z down; camera only';$('frame-all').before(topViewButton);
function applySceneAxis(axis){cancelViewportGesture();pendingEntityFrame=null;Object.assign(camera,sceneAxisCamera(camera,axis));projectionSelect.value='orthographic';document.querySelector('.viewport-type').textContent=axis[0].toUpperCase()+axis.slice(1)+' / Orthographic';cameraRevision++;draw();}
topViewButton.onclick=()=>applySceneAxis('top');
sceneCameraInspector=mountSceneCameraInspector({after:projectionSelect,getCamera:()=>camera,
 getContext:()=>JSON.stringify([state.project?.path,state.scene?.id,sceneRequestKey(),cameraRevision]),isBusy:()=>busy,available:()=>!!state.scene?.id,
 apply:next=>{cancelViewportGesture();pendingEntityFrame=null;Object.assign(camera,next);projectionSelect.value=camera.projection;document.querySelector('.viewport-type').textContent=camera.projection==='orthographic'?'Orthographic':'Perspective';cameraRevision++;draw();}
});
for(const [axis,label,title] of [['front','Front (X/Y)','Orthographic front: +X right, +Y up; camera only'],['side','Side (Z/Y)','Orthographic right side: +Z left, +Y up; camera only']]){const button=document.createElement('button');button.id='scene-'+axis+'-view';button.textContent=label;button.title=title;topViewButton.before(button);button.onclick=()=>applySceneAxis(axis);}
const modelToggle=document.createElement('button');modelToggle.id='scene-model-toggle';modelToggle.textContent='Models';modelToggle.className='active';modelToggle.setAttribute('aria-pressed','true');modelToggle.hidden=true;$('frame-all').before(modelToggle);
modelToggle.onclick=()=>{if(sceneError){sceneFailedKey=null;sceneKey=null;scenePreview=null;sceneError=null;modelsEnabled=true;}else modelsEnabled=!modelsEnabled;modelToggle.classList.toggle('active',modelsEnabled);modelToggle.setAttribute('aria-pressed',modelsEnabled);refreshScenePreview();draw();};
const representationSelect=document.createElement('select');representationSelect.id='scene-representation';representationSelect.setAttribute('aria-label','Scene representation');representationSelect.innerHTML='<option value="authored">Authored scene</option><option value="retail">Retail scene · comparison</option>';$('frame-all').before(representationSelect);
representationSelect.onchange=()=>{sceneRepresentation=representationSelect.value;if(sceneRepresentation==='retail'){collisionLayer.value='imported';clearFieldMap();updateFieldToggle();}cancelViewportGesture();pendingEntityFrame=null;npcDraftSelection=null;environmentSelection=null;sceneAbort?.abort();scenePreview=null;sceneKey=null;scenePendingKey=null;sceneFailedKey=null;sceneError=null;sceneRenderer?.clear();renderHierarchy();renderInspector();refreshScenePreview();draw();notify(sceneRepresentation==='retail'?'Retail scene comparison. Viewport movement is disabled; the Inspector retains authored project values.':'Authored scene restored.');};
function sceneRequestKey(){return state.scene_preview_source_key?`${state.scene_preview_source_key}|${sceneRepresentation}`:null;}
const sceneSelect=document.createElement('select');sceneSelect.className='scene-selector';sceneSelect.setAttribute('aria-label','Active scene');$('viewport-title').after(sceneSelect);
sceneSelect.onchange=()=>api('/api/scene',{scene_id:sceneSelect.value});
const comparisonNotice=document.createElement('p');comparisonNotice.id='scene-comparison-note';comparisonNotice.className='field-note';comparisonNotice.textContent='Viewport: retail comparison. Inspector fields remain authored project values; edits appear in Authored scene.';comparisonNotice.hidden=true;$('inspector').before(comparisonNotice);
const runtimeBox=document.createElement('div');runtimeBox.className='runtime-status';$('inspector').before(runtimeBox);
const liveFollow={active:false,timer:null,pending:null,controller:null,generation:0,context:null,epoch:null,count:0,reason:'Not following',runPid:null};
const liveContext=()=>JSON.stringify([state.project?.path,state.scene?.id]);
const acceptedEpoch=runtime=>{const value=runtime?.available&&runtime.observation?.epoch?.epoch_id;return typeof value==='string'&&value?value:null;};
runtimeBox.innerHTML='<span id="runtime-message"></span><div class="runtime-actions"><button id="runtime-check">Check runtime</button><button id="runtime-observe">Observe actors</button><button id="runtime-follow" aria-pressed="false">Follow live</button></div><p id="runtime-follow-status" role="status"></p>';
$('runtime-check').onclick=()=>api('/api/runtime/discover',{});$('runtime-observe').onclick=()=>api('/api/runtime/observe',{include_actors:true});
$('runtime-follow').onclick=()=>liveFollow.active?stopLiveFollow('Stopped by you'):startLiveFollow();
function renderRuntimeControls(){
  runtimeBox.hidden=!state.capabilities?.runtime_discovery;
  $('runtime-message').textContent=state.runtime?.available?'Runtime connected · read-only observation':state.runtime?.reason?.message ?? 'Runtime has not been checked';
  $('runtime-check').disabled=busy||liveFollow.active;$('runtime-observe').hidden=!state.runtime?.available;$('runtime-observe').disabled=busy||liveFollow.active;
  const live=state.project?.mode==='live',button=$('runtime-follow');button.textContent=liveFollow.active?'Stop following':'Follow live';button.setAttribute('aria-pressed',liveFollow.active);button.classList.toggle('active',liveFollow.active);
  button.disabled=!liveFollow.active&&(busy||!!liveFollow.pending||!live||!state.runtime?.available||document.hidden);button.title=live?'Capture actors every 2 seconds after the previous response; stop on guard failure':'Enter Live mode after a guarded runtime observation';
  $('runtime-follow-status').textContent=liveFollow.active?`Following · ${liveFollow.pending?'Capturing…':busy?'Waiting for the current action':`${liveFollow.count} actor samples · next capture in 2 seconds`}`:`Stopped · ${liveFollow.reason}`;
}
function cancelFollowTimer(){clearTimeout(liveFollow.timer);liveFollow.timer=null;}
function stopLiveFollow(reason){
  liveFollow.active=false;liveFollow.generation++;cancelFollowTimer();liveFollow.controller?.abort();liveFollow.epoch=null;liveFollow.context=null;liveFollow.runPid=null;liveFollow.reason=reason;renderRuntimeControls();
}
function reconcileLiveFollow(){
  if(!liveFollow.active)return;
  if(document.hidden)stopLiveFollow('Page hidden; start again when ready');
  else if(state.project?.mode!=='live')stopLiveFollow('Edit mode');
  else if(liveFollow.context!==liveContext())stopLiveFollow('Project or scene changed');
  else if(!state.runtime?.available)stopLiveFollow(state.runtime?.reason?.message ?? 'Runtime observation unavailable');
}
function scheduleLiveFollow(){
  cancelFollowTimer();if(!liveFollow.active||busy||liveFollow.pending||document.hidden)return;
  liveFollow.timer=setTimeout(()=>{liveFollow.timer=null;captureLiveFollow();},2000);
}
function startLiveFollow(){
  if(busy||liveFollow.pending||document.hidden||state.project?.mode!=='live'||!state.runtime?.available)return;
  liveFollow.active=true;liveFollow.generation++;liveFollow.context=liveContext();liveFollow.epoch=null;liveFollow.count=0;liveFollow.reason='';liveFollow.runPid=state.run?.running?state.run.pid:null;captureLiveFollow();
}
function clearDisplayedLive(reason){
  state.capabilities.live_mode=false;$('live-mode').disabled=true;$('live-mode').title=reason;
  state.runtime={...state.runtime,available:false,state:'unavailable',observation:null,actor_bindings:null,reason:{message:reason},historical_observation:true};
  state.runtime_correlation={available:false,status:'unavailable',reason,entities:{}};
  for(const entity of entities())if(entity.components?.RuntimeCorrelation)entity.components.RuntimeCorrelation={status:'unavailable',binding_confirmed:false,candidates:[],reason};
}
function captureLiveFollow(){
  if(!liveFollow.active||busy||liveFollow.pending||document.hidden){scheduleLiveFollow();return;}
  const generation=liveFollow.generation,context=liveFollow.context,controller=new AbortController(),epoch=liveFollow.epoch;
  liveFollow.controller=controller;const timeout=setTimeout(()=>controller.abort(),15000);
  const current=()=>generation===liveFollow.generation&&liveFollow.active&&context===liveContext()&&!document.hidden;
  const task=(async()=>{
    try{
      const response=await fetch('/api/runtime/observe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({include_actors:true,...(epoch?{expected_epoch_id:epoch}:{})}),signal:controller.signal});
      const data=await response.json();if(!current())return;
      if(!response.ok||data.error){
        const reason=typeof data.error==='string'?data.error:'Runtime guard rejected the capture';
        // Read authoritative cleared state once; this does not reconnect or capture.
        try{const refresh=await fetch('/api/state',{signal:controller.signal}),fresh=await refresh.json();if(current()&&refresh.ok&&fresh.project&&'scene' in fresh&&JSON.stringify([fresh.project.path,fresh.scene?.id])===context){state=fresh;}}
        catch{}
        if(!current())return;clearDisplayedLive(reason);stopLiveFollow(reason);render();return;
      }
      if(!data.project||!('scene' in data)||JSON.stringify([data.project.path,data.scene?.id])!==context)throw new Error('Project or scene changed during capture');
      if(!data.runtime?.available){state=data;stopLiveFollow(data.runtime?.reason?.message ?? 'Runtime observation unavailable');render();return;}
      const nextEpoch=acceptedEpoch(data.runtime);if(!nextEpoch)throw new Error('Capture did not return an accepted observation epoch');
      liveFollow.epoch=nextEpoch;liveFollow.count++;state=data;render();
    }catch(error){if(current()){const reason=error.name==='AbortError'?'Runtime capture timed out':`Runtime capture failed: ${error.message}`;clearDisplayedLive(reason);stopLiveFollow(reason);render();}}
    finally{clearTimeout(timeout);}
  })();
  liveFollow.pending=task;renderRuntimeControls();
  void task.finally(()=>{if(liveFollow.pending===task){liveFollow.pending=null;liveFollow.controller=null;renderRuntimeControls();scheduleLiveFollow();}});
}
document.addEventListener('visibilitychange',()=>{if(document.hidden&&liveFollow.active)stopLiveFollow('Page hidden; start again when ready');else renderRuntimeControls();});
window.addEventListener('pagehide',()=>{if(liveFollow.active)stopLiveFollow('Page closed');});

const buildButton=document.createElement('button');buildButton.id='build-button';buildButton.textContent='Build';buildButton.title='Build the project with supported edits or as a verified retail baseline';$('save-button').after(buildButton);
mountBuildReview({after:buildButton,getState:()=>state,busy:()=>busy,setBusy,onBuild:async review_key=>{if(await api('/api/build',{review_key}))showBuildReport();},onError:error=>notify(error.message,true)});
const buildDialog=document.createElement('dialog');buildDialog.className='project-dialog';buildDialog.id='build-report-dialog';document.body.append(buildDialog);
const buildReportButton=document.createElement('button');buildReportButton.id='build-report-button';buildReportButton.textContent='Build report';buildReportButton.title='Review the latest build';buildReportButton.hidden=true;buildButton.after(buildReportButton);buildReportButton.onclick=()=>showBuildReport();
mountBuildHistory({after:buildReportButton,getState:()=>state,busy:()=>busy,setBusy});
const exportProjectButton=document.createElement('button');exportProjectButton.id='export-project-button';exportProjectButton.textContent='Export disc';exportProjectButton.title='Export supported authored changes as a separate experimental disc';buildButton.after(exportProjectButton);exportProjectButton.onclick=()=>exportNpcDrafts();
const draftOutputReview=mountDraftOutputReview({after:exportProjectButton,getState:()=>state,busy:()=>busy,setBusy,onError:error=>notify(error.message,true)});
const exportHistoryButton=document.createElement('button');exportHistoryButton.id='export-history-button';exportHistoryButton.textContent='Export history';buildReportButton.after(exportHistoryButton);
exportHistoryButton.onclick=async()=>{
  if(busy)return;
  const dialog=document.createElement('dialog');dialog.id='export-history-dialog';dialog.className='project-dialog';
  const heading=document.createElement('h2');heading.textContent='Experimental exports';
  const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Loading saved exports…';
  const list=document.createElement('div');list.style.maxHeight='60vh';list.style.overflow='auto';
  const close=document.createElement('button');close.textContent='Close';close.onclick=()=>dialog.close();
  dialog.append(heading,status,list,close);document.body.append(dialog);dialog.addEventListener('close',()=>dialog.remove(),{once:true});dialog.showModal();
  const request=async(route,body)=>{const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const result=await response.json();if(!response.ok)throw new Error(result.error||'Export request failed');return result;};
  try{
    const result=await request('/api/exports',{});
    status.textContent=result.exports.length?`${result.exports.length} saved exports${result.truncated?' (newest 256 shown)':''}. File integrity and gameplay acceptance are separate checks.`:'No experimental exports saved in this project yet. Author scene edits or NPC drafts, then choose Export experimental disc.';
    for(const item of result.exports){
      const row=document.createElement('section'),label=document.createElement('h3');label.textContent=item.status==='completed'?`${item.scene_ids.filter(Boolean).map(id=>id.replace('scene://','')).join(', ')} · ${new Date(item.saved_at).toLocaleString()}`:'Incomplete export';row.append(label);
      const details=document.createElement('pre');details.style.whiteSpace='pre-wrap';details.style.overflowWrap='anywhere';row.append(details);
      if(item.status!=='completed'){details.textContent=`Incomplete or invalid export: ${item.error}`;list.append(row);continue;}
      const summary=item.change_summary;
      const changes=summary?`${summary.npc_draft_count===null?'NPC count not recorded':`${summary.npc_draft_count} NPC draft(s)`} · ${summary.categories.length?summary.categories.join(', '):'No categorized changes recorded'}`:'Change summary unavailable';
      details.textContent=`${item.scene_ids.filter(Boolean).join(', ')}
${changes}
${item.matches_current_inputs?'Matches current authored inputs':'Different authored inputs'}`;
      const provenance=document.createElement('details'),provenanceTitle=document.createElement('summary'),paths=document.createElement('pre');
      provenanceTitle.textContent='Saved files and source hashes';paths.style.whiteSpace='pre-wrap';paths.style.overflowWrap='anywhere';
      paths.textContent=`Disc: ${item.disc_path}
Report: ${item.report_path}
SHA-256: ${item.output_sha256}`+(item.input_project_path?`
Saved inputs: ${item.input_project_path}`:`
No saved input snapshot in this older export.`);
      provenance.append(provenanceTitle,paths);row.append(provenance);
      const check=document.createElement('button');check.textContent='Verify saved files';
      const outcome=document.createElement('p');outcome.setAttribute('role','status');outcome.textContent='File integrity not checked. Gameplay unverified.';
      check.onclick=async()=>{check.disabled=true;outcome.textContent='Checking disc and saved input hashes…';try{const verification=await request('/api/exports/verify',{id:item.id});outcome.textContent=`Disc hash verified${verification.snapshot_available?`; ${verification.snapshot_files_verified} saved input files verified`:'. No input snapshot available'}. Gameplay remains unverified.`;}catch(error){outcome.textContent=`Verification failed: ${error.message}`;}finally{check.disabled=false;}};
      row.append(check,outcome);
      if(item.input_project_path){const openCopy=document.createElement('button');openCopy.textContent='Open editable copy';openCopy.onclick=async()=>{if(busy)return;if(await api('/api/exports/open-copy',{id:item.id})){dialog.close();notify('Opened an editable copy. Saved export inputs are preserved.');}};row.append(openCopy);}
      list.append(row);
    }
  }catch(error){status.textContent=`Could not load exports: ${error.message}`;}
};
let npcPresetControls=null;
const templateDialog=document.createElement('dialog');templateDialog.id='template-dialog';document.body.append(templateDialog);
const templateButton=document.createElement('button');templateButton.className='template-library-button';templateButton.textContent='Authored actor templates…';$('assets').before(templateButton);
templateButton.onclick=()=>showTemplates();
const runButton=document.createElement('button');runButton.id='run-button';runButton.textContent='Build & Run';runButton.className='accent';buildButton.after(runButton);
const runDialog=document.createElement('dialog');runDialog.id='run-dialog';document.body.append(runDialog);
const runRibbon=document.createElement('div');runRibbon.className='run-ribbon';runRibbon.hidden=true;document.querySelector('.viewport-toolbar').after(runRibbon);
let runPoll=null, runRibbonKey=null;
runButton.onclick=()=>showRunDialog();
function showRunDialog(){
  const config=state.launch_config ?? {};
  runDialog.innerHTML=`<form id="run-form"><div class="dialog-heading"><h2>Build & Run</h2><button type="button" id="close-run" aria-label="Close">×</button></div><p>Launch a private copy of your selected runtime with this project's build.</p><label>Runtime executable<input id="run-exe" required value="${escapeHTML(config.runtime_executable)}" placeholder="C:\\path\\to\\LegaiaRecomp.exe" spellcheck="false"></label><label>BIOS image<input id="run-bios" required value="${escapeHTML(config.bios)}" placeholder="C:\\path\\to\\SCPH1001.BIN" spellcheck="false"></label><label>Game configuration<input id="run-config" required value="${escapeHTML(config.game_config)}" placeholder="C:\\path\\to\\game.toml" spellcheck="false"></label><label>Renderer<select id="run-renderer"><option value="software">Software</option><option value="opengl">OpenGL</option><option value="vulkan">Vulkan (requires runtime support)</option></select></label><label>Runtime debug port<input id="run-port" required type="number" min="1024" max="65535" value="${escapeHTML(config.debug_port ?? 4391)}"></label><p class="field-note">Each run has private mods, saves and logs under the project. Readiness verifies the game and enabled package; it does not establish gameplay correctness.</p><div id="run-summary"></div><div class="dialog-actions"><button type="submit" class="accent" id="launch-run">Build & launch</button></div><p class="dialog-error" role="alert"></p></form>`;
  $('run-renderer').value=config.renderer ?? 'software';
  $('close-run').onclick=()=>runDialog.close();
  $('run-form').onsubmit=async event=>{
    event.preventDefault();
    const config={runtime_executable:$('run-exe').value,bios:$('run-bios').value,game_config:$('run-config').value,debug_port:Number($('run-port').value),renderer:$('run-renderer').value};
    if(await api('/api/run/configure',config)){
      if(await api('/api/run',{}, {dialog:runDialog,success:'Private runtime launched. Checking identity and mod plan…'}))scheduleRunPoll();
    }
  };
  renderRunStatus();runDialog.showModal();
}
function renderRunStatus(){
  const run=state.run,active=run && (run.running || !['failed','exited','stopped'].includes(run.state));
  if(liveFollow.active&&liveFollow.runPid&&run?.pid===liveFollow.runPid&&!active){clearDisplayedLive('Owned runtime stopped');stopLiveFollow('Owned runtime stopped');renderInspector();draw();}
  runRibbon.hidden=!run;
  const ribbonKey=JSON.stringify([run?.state,run?.pid,run?.ready,active]);
  if(run && ribbonKey!==runRibbonKey){runRibbon.replaceChildren();const text=document.createElement('span');text.textContent=`Run ${run.state}${run.pid?' · PID '+run.pid:''}${run.ready?' · Identity and mod plan verified':''}`;const details=document.createElement('button');details.textContent='Details';details.onclick=showRunDialog;runRibbon.append(text,details);if(active){const stop=document.createElement('button');stop.textContent='Stop';stop.onclick=()=>api('/api/run/stop',{});runRibbon.append(stop);}if(run.ready){const attach=document.createElement('button');attach.textContent='Attach';attach.onclick=()=>api('/api/run/attach',{});runRibbon.append(attach);}}
  runRibbonKey=ribbonKey;
  if($('run-summary')){$('run-summary').innerHTML=run?`<p><strong>${escapeHTML(run.state)}</strong> · ${escapeHTML(run.reason ?? '')}</p><label>Run folder<input readonly value="${escapeHTML(run.directory)}"></label><details><summary>Runtime and package evidence</summary><pre class="diagnostic-detail">${escapeHTML(JSON.stringify({pid:run.pid,executable_sha256:run.runtime_executable_sha256,identity:run.runtime_identity,mods:run.mod_status},null,2))}</pre></details>`:'';$('launch-run').disabled=busy||!!active;}
  runButton.disabled=busy||!state.capabilities?.build_and_run||!canEdit()||!!active;
}
function scheduleRunPoll(){
  clearTimeout(runPoll);
  if(!state.run || (!state.run.running && ['failed','exited','stopped'].includes(state.run.state)))return;
  runPoll=setTimeout(async()=>{try{const response=await fetch('/api/run/status');const data=await response.json();if(response.ok){state.run=data.run;renderRunStatus();}}catch(error){notify('Runtime status is unavailable: '+error.message,true);}scheduleRunPoll();},2000);
}
buildButton.onclick=async()=>{if(await api('/api/build',{}))showBuildReport();};
const placementIssuesButton=document.createElement('button');placementIssuesButton.hidden=true;buildButton.after(placementIssuesButton);
const placementIssuesDialog=document.createElement('dialog');document.body.append(placementIssuesDialog);
placementIssuesButton.onclick=()=>{
  placementIssuesDialog.innerHTML='<div class="dialog-heading"><h2>Placement build issues</h2><button aria-label="Close placement issues">Close</button></div><p>These checks cover authored coordinates across imported scenes. Build still verifies all source data and other authored changes.</p>';
  placementIssuesDialog.querySelector('button').onclick=()=>placementIssuesDialog.close();
  for(const item of state.placement_build_issues ?? []){
    const section=document.createElement('section'),button=document.createElement('button');
    button.textContent=`${item.scene_name}: ${item.entity_id}`;
    button.onclick=async()=>{if(busy)return;placementIssuesDialog.close();if(item.scene_id!==state.scene?.id&&!await api('/api/scene',{scene_id:item.scene_id}))return;if(await api('/api/selection',{entity_id:item.entity_id}))frame(selected());};
    section.append(button);for(const issue of item.issues){const p=document.createElement('p');p.textContent=issue;section.append(p);}placementIssuesDialog.append(section);
  }
  placementIssuesDialog.showModal();
};
function renderBuildStatus(){
  const issueCount=(state.placement_build_issues ?? []).length;
  placementIssuesButton.hidden=!issueCount;placementIssuesButton.disabled=busy;
  placementIssuesButton.textContent=`Placement issues (${issueCount} ${issueCount===1?'actor':'actors'})`;
  buildReportButton.hidden=!state.build;buildReportButton.disabled=busy||!state.build;
  buildReportButton.textContent=state.build?.current===false?'Build report · stale':'Build report';
  buildReportButton.classList.toggle('stale',state.build?.current===false);
  if(buildDialog.open)renderBuildReport();
}
function validBuildReport(report){
  return report?.schema_version==='legaia.build-report.v1'&&validResourceRelocation(report.resource_relocation)&&Array.isArray(report.changes)&&report.changes.length<=65536&&report.changes.every(change=>change&&typeof change==='object'&&['scene','asset_id','field','scope'].every(key=>typeof change[key]==='string')&&'before' in change&&'after' in change)&&['overlay_bytes','scene_count','change_count'].every(key=>Number.isSafeInteger(report[key])&&report[key]>=0)&&report.validation&&typeof report.validation==='object'&&!Array.isArray(report.validation)&&Object.keys(report.validation).length<=64;
}
function validTexturePayloadAudit(diff){
  return diff&&typeof diff==='object'&&['palette_words_changed','image_bytes_changed','total_change_count'].every(key=>Number.isSafeInteger(diff[key])&&diff[key]>=0)&&(diff.pixel_indices_changed===null||Number.isSafeInteger(diff.pixel_indices_changed)&&diff.pixel_indices_changed>=0)&&typeof diff.changes_truncated==='boolean'&&Array.isArray(diff.changes)&&diff.changes.length<=256&&diff.changes.every(item=>item&&['palette_word','pixel_index','image_byte'].includes(item.kind)&&['before','after'].every(key=>Number.isSafeInteger(item[key])&&item[key]>=0)&& (item.kind==='pixel_index'?['x','y'].every(key=>Number.isSafeInteger(item[key])&&item[key]>=0):Number.isSafeInteger(item.kind==='palette_word'?item.word_index:item.image_byte_index)));
}
function projectSaveStatus(){
  if(!state.project?.dirty)return 'Project saved';
  const sections=state.project.unsaved_sections;
  return Array.isArray(sections)&&sections.length?`Unsaved: ${sections.join(', ')}`:'Project changes are not saved';
}
function buildValue(value){return typeof value==='string'?value:JSON.stringify(value) ?? 'Unknown';}
function buildChangeResource(change){
  if(typeof change.owner_id!=='string')return null;
  return assetRecords().find(record=>['texture','script'].includes(record.type)&&
    record.authoredRecord?.id===change.owner_id) ?? null;
}
function modelAuditLabel(row){
  if(row.kind==='primitive_removal')return `Object ${row.object_index} · Retail face ${row.primitive_index} removed · retained topology override`;
  const field=row.kind==='primitive_group'?`group ${row.group_index} · transparency · ${row.primitive_indices.length} shared rows`:row.kind==='primitive'?`face ${row.primitive_index} · ${row.field}${row.corner_index===undefined?'':` · corner ${row.corner_index}`}${row.axis?' · '+row.axis:''}`:`${row.kind} ${row.vector_index} · ${row.axis}`;
  return `Object ${row.object_index} · ${field}: ${row.before_value} → ${row.after_value}`;
}
async function openBuildChange(change,vector=null){
  if(busy)return;
  if(change.scope==='worldmap-menu-record-only'){buildDialog.close();await worldmapControls?.open(change.asset_id);return;}
  const scene=(state.scenes ?? []).find(item=>item.name===change.scene);
  if(!scene){notify('The source scene is no longer imported.',true);return;}
  const owner=change.owner_id,resource=buildChangeResource(change);
  buildDialog.close();
  if(scene.id!==state.scene?.id&&!await api('/api/scene',{scene_id:scene.id}))return;
  if(['source-MAP-trigger-cell-only','source-MAP-region-bounds-only'].includes(change.scope)){
    if(resourceKey!==resourceStateKey())await refreshResources();
    const source=assetRecords().find(item=>item.id===change.asset_id);
    if(!source){notify('The reported source cell is unavailable. Refresh or rebuild.',true);return;}
    selectSceneResource(source);if(source.type==='trigger')await inspectTriggerCells(source);else await inspectRegionBounds(source);return;
  }
  if(change.scope==='shared-scene-animation-record'){
    if(!Number.isInteger(change.frame_index)||!Number.isInteger(change.object_index)){notify('Animation channel identity is missing from this older report.',true);return;}
    if(!await api('/api/selection',{entity_id:owner}))return;
    const actor=selected();if(actor?.components?.Animation?.authored_channels?.animation_id!==change.asset_id){notify('This actor no longer contributes to the reported clip. Rebuild to inspect current changes.',true);return;}
    await openAnimationChannels(actor,{frame:change.frame_index,object:change.object_index});return;
  }
  if(change.field==='texture.tim'){
    const binding=state.texture_overrides?.[change.asset_id];
    if(!binding||binding.asset_sha256!==change.after){notify('The texture differs from this build report. Rebuild to inspect current changes.',true);return;}
    const record=assetRecords().find(item=>item.type==='texture'&&item.id===change.asset_id)??{id:change.asset_id,label:change.asset_id,data:{}};
    await openTexture(record,0,'effective');
    if(vector?.kind==='pixel_index'&&textureDialog.open&&textureSession?.record.id===change.asset_id)await openTexturePixel(vector.x,vector.y);
    return;
  }
  if(change.field==='model.shape'){
    const binding=state.model_overrides?.[change.asset_id];
    if(!binding||binding.source_sha256!==change.before||binding.asset_sha256!==change.after){notify('The model differs from this build report. Rebuild to inspect current changes.',true);return;}
    await openModel(change.asset_id,null,null,'authored');if(vector&&modelAssetId===change.asset_id&&$('model-dialog').open)await (vector.kind==='primitive_group'||vector.kind==='primitive'&&['clut','tpage'].includes(vector.field)?inspectModelMaterials(vector):vector.kind==='primitive'?inspectModelPrimitives(vector):openModelVectors(vector));return;
  }
  if(resource?.type==='texture'){await openTexture(resource);return;}
  if(['script-flag-bit-only','script-wait-target-only','script-branch-target-only'].includes(change.scope)){
    const pc=parseInt(change.asset_id.split('/').at(-1),16);
    const scriptOwner=resource?.type==='script'?{id:resource.authoredRecord.id,name:resource.label,partitionTwo:true}:entities().find(e=>e.id===owner);
    if(scriptOwner)await openActorScript(scriptOwner,false,null,null,pc);
    return;
  }
  if(resource?.type==='script'){
    await openActorScript({id:resource.authoredRecord.id,name:resource.label,partitionTwo:true},false,change.asset_id);
    return;
  }
  if(!await api('/api/selection',{entity_id:owner}))return;
  frame(selected());
  document.querySelector('.workspace-tabs [data-panel="viewport"]').click();
  if(change.field==='dialogue.text'||change.scope==='encoded-transition-entry-only'||change.scope==='script-model-selector-only')await openActorScript(selected(),false,change.asset_id);
}
function renderBuildReport(){
  const result=state.build;
  if(!result){buildDialog.innerHTML='<div class="dialog-heading"><h2>Build report unavailable</h2><button id="close-build" aria-label="Close build report">×</button></div><p>No build report is retained for this project.</p>';$('close-build').onclick=()=>buildDialog.close();return;}
  const report=result.report,valid=validBuildReport(report),current=result.current;
  const freshness=current===true?'Matches current authored state':current===false?'Authored state changed · rebuild to include current edits':'Freshness unavailable · rebuild to compare with the current project';
  buildDialog.innerHTML=`<div class="dialog-heading"><h2>${result.build_kind==='retail'?'Retail baseline build report':'Authored build report'}</h2><button id="close-build" aria-label="Close build report">×</button></div><p class="build-freshness ${current===true?'current':'stale'}">${freshness}</p><p>${result.build_kind==='retail'?'Retail baseline · no modified bytes':'Private authored mod package'}</p>${valid?`<div class="build-report-counts">${property('Changed fields',report.change_count)}${property('Scenes',report.scene_count)}${property('Overlay bytes',report.overlay_bytes.toLocaleString())}${report.resource_relocation?property('Relocation package bytes',report.resource_relocation.package_bytes.toLocaleString())+property('PROT growth bytes',report.resource_relocation.archive_growth_bytes.toLocaleString())+property('Rebuilt texture packs',report.resource_relocation.texture_pack_count):''}</div><section><h3>Package changes</h3><div id="build-changes"></div></section><section><h3>Build validation</h3><div id="build-validation"></div></section>`:'<p class="script-warning">A supported detailed report is unavailable. Build again with this service to review the changes and validation.</p>'}<p class="build-runtime-note">This report covers build validation. The authored-state match does not recheck package or disc integrity. Runtime execution and gameplay behavior are not verified here.</p><details class="resource-provenance"><summary>Package paths, hashes and build identity</summary><pre class="diagnostic-detail"></pre></details>`;
  $('close-build').onclick=()=>buildDialog.close();
  if(valid){
    const changes=$('build-changes');
    if(!report.changes.length){const empty=document.createElement('p');empty.className='field-note';empty.textContent=result.build_kind==='retail'?'No modified bytes: this package is the verified retail baseline.':'No field changes were listed in the build report.';changes.append(empty);}
    else{
      const wrap=document.createElement('div');wrap.className='script-table-wrap build-changes-table';const table=document.createElement('table');table.innerHTML='<thead><tr><th>Scene / asset</th><th>Field</th><th>Before</th><th>After</th><th>Scope</th></tr></thead><tbody></tbody>';
      for(const change of report.changes){const row=document.createElement('tr');for(const [index,value] of [`${change.scene}\n${change.asset_id}`,change.field+(Number.isInteger(change.frame_index)&&Number.isInteger(change.object_index)?` · frame ${change.frame_index}, object ${change.object_index}`:''),buildValue(change.before),buildValue(change.after),change.scope+(Number.isInteger(change.affected_grid_cell_count)?` · ${change.affected_grid_cell_count} grid cells`:'')].entries()){const cell=document.createElement('td');if(index===2||index===3){const text=document.createElement('pre');text.textContent=value;cell.append(text);}else if(index===0&&change.scope==='shared-scene-animation-record'&&Array.isArray(change.authored_owners)&&change.authored_owners.length){const label=document.createElement('div');label.textContent=value;cell.append(label);for(const owner of [...new Set(change.authored_owners)]){const link=document.createElement('button');link.type='button';link.textContent=`Inspect ${change.contributor_scope==='axis'?'value':'clip'} contributor ${owner.split('/').pop()} · frame ${change.frame_index}, object ${change.object_index}`;link.onclick=()=>openBuildChange({...change,owner_id:owner});cell.append(link);}}else if(index===0&&typeof change.owner_id==='string'&&(change.scope==='worldmap-menu-record-only'||['model.shape','texture.tim'].includes(change.field)||change.owner_id.includes('/actors/man-p1/')||buildChangeResource(change))){const link=document.createElement('button');link.type='button';link.textContent=value;link.title='Open authored source';link.onclick=()=>openBuildChange(change);cell.append(link);}else cell.textContent=value;if(index===4&&change.field==='model.shape'&&Array.isArray(change.coordinate_changes)){const details=document.createElement('details'),summary=document.createElement('summary'),vectors=document.createElement('pre');summary.textContent=`${change.coordinate_changes.length} model source field changes`;vectors.textContent=change.coordinate_changes.slice(0,256).map(item=>modelAuditLabel(item)).join('\n');details.append(summary,vectors);const seenVectors=new Set();for(const item of change.coordinate_changes.slice(0,256)){const key=JSON.stringify([item.object_index,item.kind,item.kind==='primitive'?item.primitive_index:item.vector_index]);if(seenVectors.has(key)||!Number.isInteger(item.object_index)||!Number.isInteger(item.kind==='primitive'?item.primitive_index:item.vector_index)||!['vertex','normal','primitive'].includes(item.kind))continue;seenVectors.add(key);const inspect=document.createElement('button');inspect.type='button';inspect.textContent=`Inspect object ${item.object_index} · ${item.kind==='primitive'?'face':item.kind} ${item.kind==='primitive'?item.primitive_index:item.vector_index}`;inspect.onclick=()=>openBuildChange(change,item);details.append(inspect);}if(change.coordinate_changes.length>256){const note=document.createElement('p');note.textContent='Showing the first 256 source field changes; the complete build audit retains every change.';details.append(note);}cell.append(details);}if(index===4&&change.field==='texture.tim'&&validTexturePayloadAudit(change.payload_changes)){const diff=change.payload_changes,details=document.createElement('details'),summary=document.createElement('summary'),values=document.createElement('pre');summary.textContent=`${diff.palette_words_changed} palette words · ${diff.pixel_indices_changed??'direct-color'} pixel indices · ${diff.image_bytes_changed} image bytes changed`;values.textContent=diff.changes.map(item=>`${item.kind==='palette_word'?`Palette word ${item.word_index}`:item.kind==='pixel_index'?`Pixel (${item.x}, ${item.y})`:`Image byte ${item.image_byte_index}`}: ${item.before} → ${item.after}`).join('\n');details.append(summary,values);for(const item of diff.changes.filter(item=>item.kind==='pixel_index')){const inspect=document.createElement('button');inspect.textContent=`Inspect pixel (${item.x}, ${item.y})`;inspect.onclick=()=>openBuildChange(change,item);details.append(inspect);}if(diff.changes_truncated){const note=document.createElement('p');note.textContent='Detail limited to the first 256 payload changes; counts include all changes.';details.append(note);}cell.append(details);}row.append(cell);}table.querySelector('tbody').append(row);}wrap.append(table);changes.append(wrap);
    }
    const labels={retail_provenance:'Retail provenance',unchanged_opaque_bytes:'Unchanged opaque bytes',lz_decode_round_trip:'LZS round trip',live_runtime:'Runtime test'},values={fresh_import_match:'Fresh import matched',not_required_no_MAN_overlay:'Not required · no compressed MAN changes',not_required_no_compressed_scene_overlay:'Not required · no compressed scene changes',not_required_unmodified_disc:'Not required · unmodified disc',not_run:'Not run'};
    for(const [key,value] of Object.entries(report.validation)){const item=document.createElement('div');item.className='build-validation-row';const label=document.createElement('span');label.textContent=labels[key] ?? key.replaceAll('_',' ');const outcome=document.createElement('strong');outcome.textContent=value===true?'Passed':value===false?'Failed':values[value] ?? buildValue(value);outcome.classList.toggle('failed',value===false);item.append(label,outcome);$('build-validation').append(item);}
  }
  const {report:details,...metadata}=result;buildDialog.querySelector('pre.diagnostic-detail').textContent=JSON.stringify(metadata,null,2);
}
function showBuildReport(){renderBuildReport();if(!buildDialog.open)buildDialog.showModal();}

document.querySelectorAll('[data-panel]').forEach(button=>{if(button.tagName==='BUTTON')button.onclick=()=>{document.querySelector('.workspace').dataset.panel=button.dataset.panel;document.querySelectorAll('.workspace-tabs button').forEach(tab=>tab.classList.toggle('active',tab===button));resize();};});

function notify(message, error=false) {
  $('toast').textContent=message; $('toast').classList.toggle('error',error); $('toast').hidden=false;
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>{$('toast').hidden=true;},error?8500:3200);
}
function setBusy(value) {
  const assetFocus=assetNavigation?.beforeRender();
  if($('shape-glb'))$('shape-glb').disabled=value||!!$('shape-file')?.files?.length||state.project?.mode!=='edit'||!state.capabilities?.model_glb_authoring;
  if($('project-settings-button'))$('project-settings-button').disabled=value||!state.capabilities?.project_settings;
  if($('project-copy-button'))$('project-copy-button').disabled=value||!state.capabilities?.project_copy;
  if($('project-animation-inputs'))$('project-animation-inputs').disabled=value||!state.project?.path;
  document.querySelectorAll('#script-report [data-script-family]').forEach(button=>button.disabled=value);
  busy=value;sceneCameraInspector?.update();if($('select-matching-actors'))hierarchyMatchSelect.disabled=!canSelectHierarchyMatches()||!hierarchyMatchIds.length||hierarchyMatchKey!==resourceStateKey();npcPresetControls?.update();triggerScriptsDialog?.refresh?.();triggerGroupDialog?.refresh?.();updateSceneFacePick();updateSceneIsolation();document.querySelectorAll('[data-scene-resource] button').forEach(button=>button.disabled=value);updateActorGroupSelection();updateScenePlacementSelection();if(value){cancelViewportGesture();cancelFollowTimer();}
  actorBatchTool.synchronize();
  document.querySelectorAll('[data-revert-component]').forEach(button=>button.disabled=value||!canEdit());
  document.querySelectorAll('.asset-card,.asset-info').forEach(button=>button.disabled=value);updateAssetPlacementActions();
  assetNavigation?.afterRender(assetFocus);
  assetPrevious.disabled=value||assetPage===0;assetNext.disabled=value||assetPage>=assetPages-1;
  document.querySelectorAll('.model-preview-button').forEach(button=>button.disabled=value||((button.dataset.animationEdit==='true'||button.dataset.inspectorEdit==='true')&&state.project?.mode!=='edit'));
  if($('inspect-actor-candidate'))$('inspect-actor-candidate').disabled=value;
  if($('npc-drafts-button'))$('npc-drafts-button').disabled=value;
  if($('inspect-npc-draft'))$('inspect-npc-draft').disabled=value;
  if($('export-npc-drafts'))$('export-npc-drafts').disabled=value||!canEdit();
  if($('export-project-button'))$('export-project-button').disabled=value||!canEdit();
  draftOutputReview.updateState();
  worldmapGeometryControls?.updateState();
  worldPlacementControls?.updateState();
  document.querySelectorAll('#draft-inspector-form input,#draft-inspector-form button,#draft-name-form input,#draft-name-form button,#draft-donor-form select,#draft-donor-form button,#duplicate-npc-draft,#repeat-npc-draft,#delete-npc-draft,#npc-presets-button').forEach(control=>control.disabled=value||!canEdit());
  for(const id of ['import-button','save-button','project-button','empty-import']) $(id).disabled=value;
  $('undo-button').disabled=value || worldmapDraftPending || !state.history?.can_undo;
  $('redo-button').disabled=value || worldmapDraftPending || !state.history?.can_redo;
  buildButton.disabled=value || worldmapDraftPending || !state.capabilities?.build || !canEdit();
  if($('build-review-button'))$('build-review-button').disabled=value||worldmapDraftPending||!state.capabilities?.build_review;
  $('save-button').disabled=value||worldmapDraftPending;worldmapControls?.updateState();projectAssetControls?.updateState();
  renderRunStatus();renderBuildStatus();
  if($('shape-remove-faces'))$('shape-remove-faces').disabled=value||!!shapeDraft||state.project?.mode!=='edit'||!state.capabilities?.model_face_removal;
  if($('shape-allocation'))$('shape-allocation').disabled=value||!!shapeDraft||state.project?.mode!=='edit'||!state.capabilities?.model_allocation_inspection;
  if($('shape-add-face'))$('shape-add-face').disabled=value||!!shapeDraft||state.project?.mode!=='edit'||!state.capabilities?.model_face_addition;
  if($('shape-add-vectors'))$('shape-add-vectors').disabled=value||!!shapeDraft||state.project?.mode!=='edit'||!state.capabilities?.model_vector_allocation;
  if($('shape-add-group'))$('shape-add-group').disabled=value||!!shapeDraft||state.project?.mode!=='edit'||!state.capabilities?.model_group_allocation;
  if($('shape-add-object'))$('shape-add-object').disabled=value||!!shapeDraft||state.project?.mode!=='edit'||!state.capabilities?.model_object_allocation;
  if($('shape-append-mesh'))$('shape-append-mesh').disabled=value||!!shapeDraft||state.project?.mode!=='edit'||!state.capabilities?.model_mesh_append;
  document.querySelectorAll('[data-axis],[data-component-property]').forEach(input=>input.disabled=value || !canEdit());
  document.querySelectorAll('[data-appearance-edit]').forEach(button=>button.disabled=value || !canEditAppearance() || button.dataset.unavailable==='true');
  document.querySelectorAll('[data-animation-edit]').forEach(button=>button.disabled=value||state.project.mode!=='edit');
  if($('script-operand-bundles'))$('script-operand-bundles').disabled=value||!canEditDialogue()||!state.capabilities?.script_operand_files;
  if($('resource-refresh'))$('resource-refresh').disabled=value || !state.capabilities?.resource_catalog;
  if($('scene-transitions'))$('scene-transitions').disabled=value || !state.capabilities?.scene_transitions;
  if($('project-transitions'))$('project-transitions').disabled=value||!state.capabilities?.scene_transitions;
  projectBookmarkNavigator?.updateState();
  if($('scene-flags'))$('scene-flags').disabled=value || !state.capabilities?.scene_flags;if($('project-flags'))$('project-flags').disabled=value||!state.capabilities?.scene_flags;
  if($('scene-text'))$('scene-text').disabled=value||!state.capabilities?.scene_text_search;
  if($('project-text'))$('project-text').disabled=value||!state.capabilities?.scene_text_search;
  if($('script-undo'))updateScriptActions();
  if($('texture-undo'))updateTextureActions();
  texturePngEditor?.updateState();
  textureResizeEditor?.update();
  textureSlotEditor?.update();
  sceneAnimationController?.updateState();
  modelMaterialsEditor?.updateState();
  if($('shape-materials'))$('shape-materials').disabled=value||Boolean(shapeDraft)||state.project?.mode!=='edit'||!state.capabilities?.model_material_authoring;
  savedActorSelections?.synchronize();savedSceneSelections?.synchronize();savedSceneViews?.synchronize();groupPresetTool?.synchronize();updateFieldToggle();renderRuntimeControls();if(!value)scheduleLiveFollow();synchronizeHistoricalPositions();
}
async function api(path, payload, {dialog,success,signal}={}) {
  if(busy) return false;
  if(sceneAnimationController?.active()&&path!=='/api/selection'){
    if(['/api/scene','/api/project/open','/api/project/new','/api/import','/api/mode'].includes(path))sceneAnimationController.stop();
    else{notify('Stop the scene animation preview before changing project or runtime state.',true);return false;}
  }
  if(worldmapDraftPending&&['/api/undo','/api/redo','/api/project/save','/api/project/save-reviewed','/api/build','/api/scene','/api/project/open','/api/import','/api/mode','/api/project/new'].includes(path)){notify('Apply or discard the world-map landmark draft first.',true);return false;}
  if(liveFollow.active){
    const reason=['/api/project/new','/api/project/open','/api/import'].includes(path)?'Project changed':path==='/api/scene'?'Scene changed':path==='/api/mode'?'Mode changed':path==='/api/run/stop'?'Owned runtime stopped':path.startsWith('/api/runtime')||path==='/api/run/attach'?'Manual runtime action':null;
    if(reason)stopLiveFollow(reason);
  }
  setBusy(true);
  // Serialize state-changing API work after this editor's in-flight capture.
  // Only explicit follow cancellation aborts that capture, never another request.
  if(dialog) dialog.querySelector('.dialog-error').textContent='';
  try {
    if(liveFollow.pending)await liveFollow.pending;
    const response=await fetch(path,{method:payload===undefined?'GET':'POST',headers:payload===undefined?{}:{'Content-Type':'application/json'},body:payload===undefined?undefined:JSON.stringify(payload),signal});
    const data=await response.json();
    if(signal?.aborted)throw new Error('Initial project-state request was cancelled.');
    if(!response.ok || data.error) throw new Error(typeof data.error==='string'?data.error:JSON.stringify(data.error ?? data));
    if(!data.project || !('scene' in data)) throw new Error('Project service returned an invalid state response.');
    if(path==='/api/selection'){sceneResourceSelection=null;clearEnvironmentGroupSelection();pendingEntityFrame=null;environmentSelection=null;npcDraftSelection=null;clearActorGroupSelection();actorGroupRangeAnchor=payload?.entity_id??null;}state=data; render();
    $('connection-dot').classList.add('connected');
    if(dialog) dialog.close();
    if(success) notify(success);
    return true;
  } catch(error) {
    // Failed runtime capture can clear transient state; a launch failure can
    // still leave an owned child that must remain reachable through Stop.
    if(path.startsWith('/api/run') || path.startsWith('/api/runtime') || path==='/api/mode'){
      try{const response=await fetch('/api/state');const fresh=await response.json();if(response.ok && fresh.project && 'scene' in fresh){state=fresh;render();}}catch{}
    }
    if(dialog) dialog.querySelector('.dialog-error').textContent=error.message;
    else notify(error.message,true);
    $('status').textContent=error.message;
    return false;
  } finally {setBusy(false);}
}
function entities(){return state.scene?.entities ?? [];}
let environmentSelection=null,environmentGroupSelection=[],environmentGroupKey=null,environmentGroupAnchor=null,environmentGroupInspection=null;
let environmentGroupTool=null,environmentLayoutTool=null,environmentRotationGroupTool=null;
let sharedEnvironmentMove=null;
let npcDraftSelection=null;
function selectedNpcDraft(){const value=state.actor_drafts?.[npcDraftSelection];return value?.scene_id===state.scene?.id?value:null;}
function frameNpcDraft(){
  const value=selectedNpcDraft(),id=npcDraftSelection;if(!value)return;
  if(sceneRepresentation==='retail'){representationSelect.value='authored';representationSelect.onchange();selectNpcDraft(id);}
  frame({id,components:{Transform:{imported:{position:{...value.position,y:null}}}}});
}
async function duplicateNpcDraft(id){
  const original=state.actor_drafts?.[id];
  if(busy||!canEdit()||id!==npcDraftSelection||original?.scene_id!==state.scene?.id||scenePose||shapeDraft||draft||groundPositionInspection||npcCreationInspection||actorGroupInspection||environmentGroupInspection||scenePlacementInspection||scenePlacementMode||currentPlacementSelection().length>1||npcGroundPlacement.active())return;
  try{const name=original.name.slice(0,115)+' copy',capture=captureNpcDuplication(state,id,name);
    if(!await api('/api/command',{type:'duplicate_actor_draft',entity_id:id,name}))return;
    const created=duplicatedNpcSelection(state,capture);clearScenePlacementSelection();selectNpcDraft(created);frameNpcDraft();revealHierarchyButton.click();document.querySelector('.workspace-tabs [data-panel="inspector"]').click();notify('NPC duplicated at the same position. Move the selected copy with X/Z or the viewport handles.');
  }catch(error){notify(error.message,true);}
}
function selectNpcDraft(id){sceneResourceSelection=null;clearEnvironmentGroupSelection();clearActorGroupSelection();pendingEntityFrame=null;npcDraftSelection=id;environmentSelection=null;cancelViewportGesture();renderHierarchy();renderInspector();$("frame-selected").disabled=false;draw();}
function environmentEntities(){return activeScenePreview()?.entities.filter(e=>e.kind==='environment') ?? [];}
function selectedEnvironment(){return environmentEntities().find(e=>e.entity_id===environmentSelection);}
function movableSelection(){
  if(currentNpcCreationInspection()||currentGroundPositionInspection()||scenePlacementMode||scenePlacementInspection||actorGroupInspection||actorGroupSelection.length||environmentGroupInspection||environmentGroupSelection.length>1)return null;
  if(sceneRepresentation!=="authored")return null;
  const npc=selectedNpcDraft();
  if(npc){if(!scenePreviewCurrent()||hiddenSceneEntities().has(npcDraftSelection))return null;return {id:npcDraftSelection,components:{Transform:{effective:{position:{...npc.position,y:null}}}}};}
  const environment=selectedEnvironment();
  if(!environment)return selected();
  if(!scenePreviewCurrent()||hiddenSceneEntities().has(environment.entity_id))return null;
  if(!environment.entity_id.includes('/decorations/')&&!(sharedEnvironmentMove?.id===environment.entity_id&&sharedEnvironmentMove?.key===resourceStateKey()))return null;
  return {id:environment.entity_id,components:{Transform:{effective:{position:environment.position}}}};
}
function rotationSelection(){
  const item=selectedEnvironment();if(sceneryTool.value!=='yaw'||busy||!item||!movableSelection()||!canEdit()||!scenePreviewCurrent()||!sceneModelsReady()||sceneRepresentation!=='authored'||scenePose||shapeDraft||actorGroupInspection||environmentGroupInspection||scenePlacementInspection||scenePlacementMode||wallSelectMode||wallInspection||pickScriptTargets||pickRuntimeNodes||fieldSpatialPick||environmentGroupSelection.length>1||hiddenSceneEntities().has(item.entity_id))return null;
  try{environmentYawMatrix(item,item.effective_transform?.rotation_psx.y??item.source_record.imported_transform.rotation_psx.y);return item;}catch{return null;}
}
function yawPreviewTransforms(){
  const transforms=new Map();if(environmentGroupInspection?.layer==='proposed'&&environmentGroupInspection.report.schema_version==='legaia.environment-rotation-group-review.v1')for(const row of environmentGroupInspection.report.targets){const item=environmentEntities().find(e=>e.entity_id===row.entity_id);if(item)transforms.set(row.entity_id,environmentYawMatrix(item,row.proposed.yaw));}if(!draft?.sceneryYaw||drag?.type!=='environment-yaw'||!transformGestureCurrent(drag))return transforms;
  const item=drag.rotationItem,binding=drag.rotationBinding,shared=drag.rotationShared;
  for(const row of environmentEntities()){
    if(shared?row.source_record?.object_record_index!==item.source_record.object_record_index:row.entity_id!==item.entity_id)continue;
    const cell=(row.source_record.source_record.grid_byte_offset-0x8000)/2;
    if(shared&&binding?.instances?.find(e=>e.cell_index===cell)?.rotation_psx?.y!==undefined)continue;
    transforms.set(row.entity_id,environmentYawMatrix(row,draft.yaw));
  }return transforms;
}
function previewBounds(id,hidden=new Set()){const view=sceneView();return sceneRenderer.bounds(view.positions,id,hidden,view.transforms);}
async function moveDecoration(identifier,axis,worldValue){
  if(sceneRepresentation!=='authored')return;
  const item=selectedEnvironment();if(!scenePreviewCurrent()||!item||item.entity_id!==identifier)return;
  if(!item.entity_id.includes('/decorations/')){await moveSharedEnvironment(item,axis,worldValue);return;}
  const source=item.source_record,cell=(source.source_record.grid_byte_offset-0x8000)/2;
  const binding=activeScenePreview()?.environment_authoring;
  const shared=binding?.edits?.find(e=>e.record_index===source.object_record_index);
  const instances=structuredClone(binding?.instances??[]);
  let edit=instances.find(e=>e.cell_index===cell);
  if(!edit){edit={cell_index:cell};instances.push(edit);}
  const inherited=shared?.offset?.[axis]??source.record_offset[axis];
  const current=edit.offset?.[axis]??inherited;
  const value=current+(worldValue-item.position[axis])*(axis==='z'?-1:1);
  if(!Number.isInteger(value)||value < -32768||value > 32767){notify('Move exceeds the supported scenery offset range.',true);return;}
  (edit.offset??={})[axis]=value;
  if(value===inherited){delete edit.offset[axis];if(!Object.keys(edit.offset).length)delete edit.offset;}
  const remaining=instances.filter(e=>e.offset||e.rotation_psx),edits=binding?.edits??[];
  await api('/api/command',remaining.length||edits.length?{type:'set_environment_transforms',entity_id:state.scene.id,value:{source_sha256:source.source_record.map_sha256,edits,instances:remaining}}:{type:'clear_environment_transforms',entity_id:state.scene.id});
}
async function moveSharedEnvironment(item,axis,worldValue){
  if(!canEdit()||sharedEnvironmentMove?.id!==item.entity_id||sharedEnvironmentMove?.key!==resourceStateKey())return;
  const source=item.source_record,binding=activeScenePreview()?.environment_authoring;
  if(!source.record_offset||!source.source_record?.map_sha256||!['x','z'].includes(axis))return;
  const edits=structuredClone(binding?.edits??[]),instances=binding?.instances??[];
  let edit=edits.find(e=>e.record_index===source.object_record_index);
  if(!edit){edit={record_index:source.object_record_index};edits.push(edit);}
  const inherited=source.record_offset[axis],current=edit.offset?.[axis]??inherited;
  const value=current+(worldValue-item.position[axis])*(axis==='z'?-1:1);
  if(!Number.isInteger(value)||value < -32768||value > 32767){notify('Move exceeds the supported scenery offset range.',true);return;}
  (edit.offset??={})[axis]=value;
  if(value===inherited){delete edit.offset[axis];if(!Object.keys(edit.offset).length)delete edit.offset;}
  const remaining=edits.filter(e=>e.offset||e.rotation_psx);
  await api('/api/command',remaining.length||instances.length?{type:'set_environment_transforms',entity_id:state.scene.id,value:{source_sha256:source.source_record.map_sha256,edits:remaining,instances}}:{type:'clear_environment_transforms',entity_id:state.scene.id});
}
function selected(){return selectedSceneResource()||selectedEnvironment()||selectedNpcDraft()?null:entities().find(e=>e.id===state.selection?.entity_id);}
function selectEnvironment(identifier){sceneResourceSelection=null;clearEnvironmentGroupSelection();clearActorGroupSelection();pendingEntityFrame=null;npcDraftSelection=null;environmentSelection=identifier;cancelViewportGesture();renderHierarchy();renderInspector();$('frame-selected').disabled=false;draw();}
function scenePlacementEligible(){return new Set([...entities().map(e=>e.id),...Object.entries(state.actor_drafts??{}).filter(([,d])=>d.scene_id===state.scene?.id).map(([id])=>id),...staticDecorations().map(e=>e.entity_id)]);}
function setSourcePlacementGroup(ids,focus){
  const eligible=scenePlacementEligible();ids=mergeScenePlacementSelection([],ids,eligible);
  if(!ids.length||!ids.includes(focus))throw new Error('The active placement must belong to the current group.');
  const key=resourceStateKey();
  const kind=scenePlacementSelectionKind(ids,{actors:new Set(entities().map(entity=>entity.id)),npcs:new Set(Object.entries(state.actor_drafts??{}).filter(([,draft])=>draft.scene_id===state.scene?.id).map(([id])=>id)),decorations:new Set(staticDecorations().map(entity=>entity.entity_id))});
  cancelViewportGesture();clearActorGroupSelection();clearEnvironmentGroupSelection();clearScenePlacementSelection();sceneResourceSelection=null;actorBoxMode=false;scenePlacementMode=false;scenePlacementBoxMode=false;
  if(kind==='actors'){actorGroupSelection=ids;actorGroupSelectionKey=key;actorGroupRangeAnchor=focus;}
  else if(kind==='scenery'){environmentGroupSelection=ids;environmentGroupKey=key;environmentGroupAnchor=focus;}
  else{scenePlacementMode=true;scenePlacementSelection=ids;scenePlacementKey=key;}
  environmentSelection=ids.includes(focus)&&!entities().some(entity=>entity.id===focus)&&!state.actor_drafts?.[focus]?focus:null;npcDraftSelection=state.actor_drafts?.[focus]?focus:null;
}
function clearScenePlacementSelection(){scenePlacementMode=false;scenePlacementBoxMode=false;scenePlacementSelection=[];scenePlacementKey=null;scenePlacementTool?.restore();}
function updateScenePlacementSelection(){
  if((scenePlacementMode||scenePlacementSelection.length)&&(!canEdit()||!scenePreviewCurrent()||sceneRepresentation!=='authored'||scenePlacementKey!==resourceStateKey()||scenePlacementSelection.some(id=>!scenePlacementEligible().has(id))))clearScenePlacementSelection();
  savedSceneSelections?.synchronize();scenePlacementTool?.refresh();updateSceneFocusButton();updateHierarchyPlacementMatchSelection();updateModelInstanceSelection();assetPlacementSelection?.synchronize();animationContributions?.synchronize();const host=document.querySelector('#scene-placement-tools');if(!host)return;
  host.querySelector('[data-mixed-select]').disabled=busy||!canEdit()||!scenePreviewCurrent()||sceneRepresentation!=='authored'||!!scenePose||!!shapeDraft||!!actorGroupInspection||!!environmentGroupInspection||!!wallSelectMode||!!wallInspection||!!scenePlacementInspection;
  host.querySelector('[data-mixed-box]').disabled=host.querySelector('[data-mixed-select]').disabled||!sceneModelsReady()||pickScriptTargets||pickRuntimeNodes;
  for(const name of ['visible','invert'])host.querySelector('[data-mixed-'+name+']').disabled=host.querySelector('[data-mixed-box]').disabled;
  if(host.querySelector('[data-mixed-box]').disabled&&!busy)scenePlacementBoxMode=false;
  host.querySelector('[data-mixed-box]').classList.toggle('active',scenePlacementBoxMode);host.querySelector('[data-mixed-box]').setAttribute('aria-pressed',String(scenePlacementBoxMode));
  host.querySelector('[data-mixed-select]').classList.toggle('active',scenePlacementMode);host.querySelector('[data-mixed-select]').setAttribute('aria-pressed',String(scenePlacementMode));host.querySelector('[data-mixed-clear]').disabled=busy||!scenePlacementSelection.length;
  host.querySelector('[role="status"]').textContent=`${scenePlacementSelection.length} scene placements · Imported actors + NPC drafts + static decorations · ${scenePlacementBoxMode?'Drag visible meshes; Ctrl/Command adds; Shift pans':scenePlacementMode?'Click to toggle selection':'Enable selection to choose a mixed group'}`;
}
async function toggleScenePlacement(id){
  sceneResourceSelection=null;
  if(busy||!scenePlacementMode||scenePlacementInspection||!scenePlacementEligible().has(id))return;
  const next=new Set(scenePlacementSelection);if(next.has(id))next.delete(id);else next.add(id);if(next.size>128){notify('Scene placement groups are limited to 128 entities.',true);return;}
  scenePlacementSelection=[...next].sort();scenePlacementKey=resourceStateKey();cancelViewportGesture();
  if(entities().some(e=>e.id===id)){environmentSelection=null;await api('/api/selection',{entity_id:id});}else if(state.actor_drafts?.[id]?.scene_id===state.scene.id){environmentSelection=null;npcDraftSelection=id;renderInspector();}else{environmentSelection=id;npcDraftSelection=null;renderInspector();}
  renderHierarchy();draw();
}
function scenePlacementPosition(row,temporary=true){
  const current=row.kind==='actor'?position(entities().find(e=>e.id===row.entity_id)):row.kind==='actor_draft'?activeScenePreview()?.entities.find(e=>e.entity_id===row.entity_id&&e.kind==='actor_draft')?.display_position:environmentEntities().find(e=>e.entity_id===row.entity_id)?.display_position;
  if(!current)return null;const result={...current,x:row.proposed.x,z:row.proposed.z};
  if(temporary&&draft?.scenePlacementGroup&&drag?.type==='scene-placement-group-transform')result[drag.handle.axis]+=draft.groupAmount;
  return result;
}
function scenePlacementCenter(temporary=true){
  if(scenePlacementInspection?.layer!=='proposed')return null;
  const points=scenePlacementInspection.report.targets.map(row=>scenePlacementPosition(row,temporary));if(points.some(p=>!p))return null;
  return Object.fromEntries(['x','y','z'].map(axis=>[axis,points.reduce((sum,p)=>sum+p[axis],0)/points.length]));
}
function frameScenePlacementGroup(report){const view=sceneView(),corners=report.targets.flatMap(row=>sceneRenderer?.bounds(view.positions,row.entity_id,new Set(),view.transforms)??[]);if(!corners.length)return;const lo={},hi={};for(const axis of ['x','y','z']){lo[axis]=Math.min(...corners.map(p=>p[axis]));hi[axis]=Math.max(...corners.map(p=>p[axis]));camera.target[axis]=(lo[axis]+hi[axis])/2;}camera.distance=Math.max(100,Math.hypot(...['x','y','z'].map(axis=>hi[axis]-lo[axis]))*1.8);cameraRevision++;draw();}
function staticDecorations(){return environmentEntities().filter(e=>e.entity_id.includes('/decorations/')&&e.source_record?.object_record_index>=4);}
function clearEnvironmentGroupSelection(){environmentGroupSelection=[];environmentGroupKey=null;environmentGroupAnchor=null;if(environmentGroupInspection){environmentGroupTool?.restore();environmentLayoutTool?.restore();environmentRotationGroupTool?.restore();}environmentGroupTool?.refresh();environmentLayoutTool?.refresh();environmentRotationGroupTool?.refresh();}
function updateEnvironmentGroupSelection(){
  if(environmentGroupSelection.length&&(!canEdit()||!scenePreviewCurrent()||environmentGroupKey!==resourceStateKey()||environmentGroupSelection.some(id=>!staticDecorations().some(e=>e.entity_id===id))))clearEnvironmentGroupSelection();
  environmentGroupTool?.refresh();environmentLayoutTool?.refresh();environmentRotationGroupTool?.refresh();
  const clear=document.querySelector('#environment-group-tools > button:last-child');if(clear)clear.disabled=busy||!environmentGroupSelection.length;
}
function toggleEnvironmentSelection(id){
  sceneResourceSelection=null;
  if(busy||!canEdit()||environmentGroupInspection)return;
  const eligible=staticDecorations().map(e=>e.entity_id);if(!eligible.includes(id)){notify('Scenery groups support static decoration instances.',true);return;}
  const next=new Set(environmentGroupSelection);if(!next.size&&eligible.includes(environmentSelection))next.add(environmentSelection);if(next.has(id))next.delete(id);else next.add(id);
  if(next.size>128){notify('Scenery group is limited to 128 instances.',true);return;}
  clearActorGroupSelection();npcDraftSelection=null;environmentSelection=id;environmentGroupSelection=[...next].sort();environmentGroupKey=resourceStateKey();environmentGroupAnchor=id;cancelViewportGesture();renderHierarchy();renderInspector();draw();
}
function selectEnvironmentRange(id,add=false){
  sceneResourceSelection=null;
  if(busy||!canEdit()||environmentGroupInspection)return;
  const eligible=new Set(staticDecorations().map(e=>e.entity_id));if(!eligible.has(id)){notify('Scenery groups support static decoration instances.',true);return;}
  const visible=[...$('hierarchy').querySelectorAll('.entity-row')].map(row=>row.title).filter(id=>eligible.has(id));
  const members=actorGroupRange(environmentGroupAnchor??environmentSelection,id,visible),next=new Set(add?environmentGroupSelection:[]);for(const member of members)next.add(member);
  if(next.size>128){notify('Scenery group is limited to 128 instances.',true);return;}
  clearActorGroupSelection();npcDraftSelection=null;environmentSelection=id;environmentGroupSelection=[...next].sort();environmentGroupKey=resourceStateKey();environmentGroupAnchor=id;cancelViewportGesture();renderHierarchy();renderInspector();draw();
}
function sceneryGroupPosition(row,temporary=true){
  const item=environmentEntities().find(e=>e.entity_id===row.entity_id);if(!item)return null;
  const result={...item.display_position,x:row.proposed.x,z:row.proposed.z};
  if(temporary&&draft?.sceneryGroup&&drag?.type==='environment-group-transform')result[drag.handle.axis]+=draft.groupAmount;
  return result;
}
function sceneryGroupCenter(temporary=true){
  if(environmentGroupInspection?.layer!=='proposed'||environmentGroupInspection.report.schema_version!=='legaia.environment-group-review.v1')return null;
  const points=environmentGroupInspection.report.targets.map(row=>sceneryGroupPosition(row,temporary));if(points.some(p=>!p))return null;
  return Object.fromEntries(['x','y','z'].map(axis=>[axis,points.reduce((sum,p)=>sum+p[axis],0)/points.length]));
}
function frameEnvironmentGroup(report){
  const rows=report?.targets??environmentGroupSelection.map(entity_id=>({entity_id})),view=sceneView();
  const corners=rows.flatMap(row=>sceneRenderer?.bounds(view.positions,row.entity_id,new Set(),view.transforms)??[]);if(!corners.length)return;
  for(const axis of ['x','y','z'])camera.target[axis]=(Math.min(...corners.map(p=>p[axis]))+Math.max(...corners.map(p=>p[axis])))/2;
  camera.distance=Math.max(800,Math.hypot(...['x','y','z'].map(axis=>Math.max(...corners.map(p=>p[axis]))-Math.min(...corners.map(p=>p[axis]))))*1.5);cameraRevision++;draw();
}
function frameEnvironment(){const item=selectedEnvironment();if(item)frame({id:item.entity_id,components:{Transform:{imported:{position:item.position}}}});}
function canEditAppearance(){return !sceneAnimationController?.active()&&(state.project?.mode ?? 'edit').toLowerCase()==='edit' && state.capabilities?.actor_appearance===true;}
function canEdit(){return !sceneAnimationController?.active()&&(state.project?.mode ?? 'edit').toLowerCase()==='edit' && state.capabilities?.edit_transform!==false;}
function displayPosition(value){const p={x:numeric(value?.x)?value.x:0,y:numeric(value?.y)?value.y:0,z:numeric(value?.z)?value.z:0},matrix=activeScenePreview()?.position_to_display;return matrix?{x:matrix[0]*p.x+matrix[1]*p.y+matrix[2]*p.z+matrix[3],y:matrix[4]*p.x+matrix[5]*p.y+matrix[6]*p.z+matrix[7],z:matrix[8]*p.x+matrix[9]*p.y+matrix[10]*p.z+matrix[11]}:p;}
function position(entity){
  const creation=currentNpcCreationInspection();if(creation?.report.review.preview_entity_id===entity.id)return {...creation.report.proposed_instance.display_position};
  const ground=currentGroundPositionInspection();if(ground&&ground.report.review.entity_id===entity.id)return {...ground.report[ground.layer+'_instance'].display_position};
  if(scenePose?.proposalDocument&&scenePose.inspectionLayer==='proposed'&&scenePose.key===sceneKey&&scenePreviewCurrent()){
    const displayed=scenePose.proposalDocument.entities.find(item=>item.entity_id===entity.id)?.display_position;
    if(displayed&&['x','y','z'].every(axis=>numeric(displayed[axis])))return {...displayed};
  }
  if(actorGroupInspection?.layer==='proposed'&&actorGroupInspection.key===resourceStateKey()&&scenePreviewCurrent()){
    const proposed=groupProposalPosition(entity.id);if(proposed)return proposed;
  }
  const source=sceneRepresentation==='retail'?entity.components?.Transform?.imported?.position:entity.components?.Transform?.effective?.position ?? entity.components?.Transform?.imported?.position;
  const preview=scenePreviewCurrent()?activeScenePreview()?.entities.find(item=>item.entity_id===entity.id):null;
  return displayPosition(preview?.preview_position??source);
}
function groupProposalPosition(id,temporary=true){
  const original=actorGroupInspection?.positions.get(id);if(!original)return null;const result={...original};
  if(temporary&&draft?.group&&drag?.type==='group-transform')result[drag.handle.axis]+=draft.groupAmount;
  return result;
}
function groupProposalCenter(temporary=true){
  if(actorGroupInspection?.layer!=='proposed'||!actorGroupInspection.proposal.delta)return null;
  const points=[...actorGroupInspection.positions.keys()].map(id=>groupProposalPosition(id,temporary));
  return Object.fromEntries(['x','y','z'].map(axis=>[axis,points.reduce((sum,p)=>sum+p[axis],0)/points.length]));
}
function authoredComponentLabels(entity){
  const labels={Transform:'Position',ActorAppearance:'Appearance',ActorAnimation:'Initial animation',AnimationChannels:'Animation channels',Dialogue:'Dialogue',Transitions:'Transitions',ScriptMovement:'Script movement',ScriptFacing:'Script facing'};
  return (entity.authored_components??[]).map(key=>labels[key]??key);
}
function authored(entity){return (entity.authored_components?.length??0)>0 || !!entity.components?.Animation?.authored_channels || Object.keys(entity.components?.Transform?.authored?.position ?? {}).length>0 || !!entity.components?.ActorAppearance?.authored?.donor_entity_id || !!entity.components?.ActorAnimation?.authored?.animation_asset_id || Object.keys(entity.components?.Dialogue?.authored?.runs ?? {}).length>0;}
function showDialog(id){const d=$(id);d.querySelector('.dialog-error')?.replaceChildren();d.showModal();}
document.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',()=>button.closest('dialog').close()));
$('project-button').onclick=()=>{ $('project-name-input').value=state.project?.name ?? 'Legaia project'; $('project-path-input').value=state.project?.path ?? '';showDialog('project-dialog'); };
mountProjectSettings({after:$('project-button'),getState:()=>state,busy:()=>busy,api,onError:error=>notify(error.message,true)});
mountProjectCopy({after:$('project-settings-button'),getState:()=>state,busy:()=>busy,setBusy,api});
for(const id of ['import-button','empty-import']) $(id).onclick=()=>{if(!$('disc-input').value)$('disc-input').value=state.project?.disc_path??'';showDialog('import-dialog');};
$('project-form').onsubmit=async event=>{event.preventDefault();await api('/api/project/new',{name:$('project-name-input').value,path:$('project-path-input').value},{dialog:$('project-dialog'),success:'Project created.'});};
$('open-project').onclick=async()=>{if(!$('project-path-input').reportValidity())return;await api('/api/project/open',{path:$('project-path-input').value},{dialog:$('project-dialog'),success:'Project opened.'});};
const sceneCatalog=document.createElement('section');sceneCatalog.id='import-scene-catalog';
sceneCatalog.innerHTML='<h3>Find a scene</h3><label>Name prefix<input id="catalog-prefix" placeholder="town, dolk, station…" spellcheck="false"></label><div class="dialog-actions"><button type="button" id="catalog-search">Read scene catalog</button><button type="button" id="catalog-previous" disabled>Previous</button><button type="button" id="catalog-next" disabled>Next</button></div><p id="catalog-status" role="status">Checks 16 structural blocks per page for metadata import readiness. Rendering and gameplay remain unverified.</p><div id="catalog-scenes"></div>';
$('scene-input').parentElement.before(sceneCatalog);
let catalogGeneration=0,catalogOffset=0,catalogNext=null;
function clearSceneCatalog(){catalogGeneration++;catalogOffset=0;catalogNext=null;$('catalog-status').textContent='Read the catalog for the current disc path and name prefix. Catalog checks metadata import readiness; rendering and gameplay remain unverified.';$('catalog-scenes').replaceChildren();$('catalog-previous').disabled=true;$('catalog-next').disabled=true;}
$('disc-input').addEventListener('input',clearSceneCatalog);$('catalog-prefix').oninput=clearSceneCatalog;
$('import-dialog').addEventListener('close',clearSceneCatalog);
async function readSceneCatalog(offset=0){
  if(busy)return;
  const disc=$('disc-input').value.trim(),prefix=$('catalog-prefix').value.trim();
  if(!disc){$('catalog-status').textContent='Enter your local disc image path first.';return;}
  const generation=++catalogGeneration;setBusy(true);$('catalog-search').disabled=true;$('catalog-previous').disabled=true;$('catalog-next').disabled=true;$('catalog-scenes').replaceChildren();$('catalog-status').textContent='Reading verified retail scene blocks…';
  try{
    const response=await fetch('/api/scene-catalog',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({disc,prefix,offset})});
    let result=await response.json();if(!response.ok||result.error)throw new Error(result.error||'Scene catalog failed');
    if(generation!==catalogGeneration||!$('import-dialog').open)return;
    result=decodeSceneCatalog(result,offset,prefix);
    catalogOffset=offset;catalogNext=result.next_offset;
    $('catalog-status').textContent=`${result.scenes.filter(row=>row.import_status==='supported').length} ready to import - ${result.scenes.filter(row=>row.import_status!=='supported').length} placement-only scenes - ${result.unsupported_blocks.length} unsupported blocks - scanned ${result.scanned_blocks} at offset ${offset} of ${result.total_blocks}. Model slots and actor references checked; rendering and gameplay remain unverified.`;
    for(const scene of result.scenes){
      const button=document.createElement('button');button.type='button';button.className='catalog-scene';button.textContent=`${scene.name} · ${scene.actor_count} actors · ${scene.man_source_kind==='raw_streaming_man'?'Streaming field':scene.man_source_kind==='descriptor_man'?'Compressed field':'Source format unknown'}`;button.title=scene.semantic_id;
      const status=document.createElement('p');status.textContent=scene.import_status==='supported'?`Metadata import ready · ${scene.scene_model_count} scene models · ${scene.global_model_count} global models · ${scene.unresolved_actor_model_count} unresolved actor model references`:`Placement readable · Import unavailable: ${scene.import_reason}`;
      button.disabled=scene.import_status!=='supported';button.onclick=()=>{if(scene.import_status!=='supported')return;$('scene-input').value=scene.name;$('catalog-status').textContent=`Selected ${scene.name}. Use Import scene to add it to the project. Rendering and gameplay remain unverified.`;};const preview=document.createElement('button');preview.type='button';preview.textContent='Preview '+scene.name+' before import';preview.disabled=scene.import_status!=='supported';preview.onclick=()=>{if(busy||generation!==catalogGeneration||scene.import_status!=='supported')return;const identity=result.source.disc_identity;$('import-dialog').close();openCatalogScenePreview({disc,scene:scene.name,discIdentity:identity,getState:()=>state,busy:()=>busy,onImport:importCatalogPreviewSelection,onError:error=>notify(error.message,true)});};$('catalog-scenes').append(button,status,preview);
    }
    if(result.unsupported_blocks.length){const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Unsupported structural blocks';details.append(summary);for(const block of result.unsupported_blocks){const row=document.createElement('p');row.textContent=`${block.name}: ${block.reason}`;details.append(row);}$('catalog-scenes').append(details);}
  }catch(error){if(generation===catalogGeneration)$('catalog-status').textContent=String(error.message);}
  finally{setBusy(false);$('catalog-search').disabled=false;$('catalog-previous').disabled=catalogOffset===0;$('catalog-next').disabled=catalogNext===null;}
}
$('catalog-search').onclick=()=>readSceneCatalog();$('catalog-previous').onclick=()=>readSceneCatalog(Math.max(0,catalogOffset-16));$('catalog-next').onclick=()=>{if(catalogNext!==null)readSceneCatalog(catalogNext);};
$('import-form').onsubmit=async event=>{event.preventDefault();$('status').textContent='Importing scene from local disc image…';await api('/api/import',{disc:$('disc-input').value,scene:$('scene-input').value},{dialog:$('import-dialog'),success:'Scene imported.'});};
const modelResolutionButton=document.createElement('button');modelResolutionButton.type='button';modelResolutionButton.id='model-resolution-button';modelResolutionButton.textContent='Inspect unresolved model references';
modelResolutionButton.onclick=()=>openModelResolution({getState:()=>state,busy:()=>busy,onError:error=>notify(error.message,true),onInspectSource:async source=>{const actor=entities().find(entity=>entity.id===source.source_actor_id);if(!actor)throw Error('Model source actor is unavailable in the active scene');await openActorScript(actor);},onSelect:async row=>{if(row.kind==='npc'){if(!state.actor_drafts?.[row.entity_id])throw Error('NPC source changed');selectNpcDraft(row.entity_id);frameNpcDraft();}else if(await api('/api/selection',{entity_id:row.entity_id}))frame(selected());}});transformTools.append(modelResolutionButton);
$('changes-button').onclick=()=>{if(!busy)openProjectChanges({save:(key,dialog)=>api('/api/project/save-reviewed',{source_key:key},{dialog,success:'Reviewed project changes saved.'})});};
$('save-button').onclick=()=>api('/api/project/save',{}, {success:'Project saved.'});
const draftsButton=document.createElement('button');draftsButton.id='npc-drafts-button';draftsButton.textContent='NPC drafts';draftsButton.onclick=()=>openNpcDrafts();$('save-button').after(draftsButton);
const actorBoxButton=document.createElement('button');actorBoxButton.id='actor-box-select';actorBoxButton.textContent='Box select actors';actorBoxButton.title='Drag over visible actor meshes; Ctrl/Command adds to the group. Shift-drag pans.';actorBoxButton.setAttribute('aria-pressed','false');
actorBoxButton.onclick=()=>{if(actorBoxButton.disabled)return;cancelViewportGesture();actorBoxMode=!actorBoxMode;actorBoxButton.classList.toggle('active',actorBoxMode);actorBoxButton.setAttribute('aria-pressed',String(actorBoxMode));draw();};transformTools.prepend(actorBoxButton);
const actorGroupTools=document.createElement('div');actorGroupTools.id='actor-group-selection';actorGroupTools.hidden=true;
actorGroupTools.innerHTML='<span role="status"></span><button type="button" data-frame-selection>Frame actor group</button><button type="button" data-review-selection>Review group placements</button><button type="button" data-review-components>Review group components</button><button type="button" data-clear-selection>Clear group</button>';
transformTools.after(actorGroupTools);
const environmentGroupHost=document.createElement('div');environmentGroupHost.id='environment-group-tools';transformTools.after(environmentGroupHost);
environmentGroupTool=mountEnvironmentGroup({host:environmentGroupHost,getState:()=>state,getSelection:()=>environmentGroupSelection,
  busy:()=>busy,setBusy,api,canReview:()=>canEdit()&&scenePreviewCurrent()&&sceneModelsReady()&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft&&!actorGroupInspection&&!scenePlacementInspection&&(!environmentGroupInspection||environmentGroupInspection.report.schema_version==='legaia.environment-group-review.v1'),
  onInspection:(report,layer)=>{cancelViewportGesture();if(report){environmentLayoutTool?.restore();environmentRotationGroupTool?.restore();}environmentGroupInspection=report?{report,layer}:null;draw();},onFrame:frameEnvironmentGroup,onError:error=>notify(typeof error==='string'?error:error.message,true)});
environmentLayoutTool=mountEnvironmentLayout({host:environmentGroupHost,getState:()=>state,getSelection:()=>environmentGroupSelection,
  busy:()=>busy,setBusy,api,canReview:()=>canEdit()&&scenePreviewCurrent()&&sceneModelsReady()&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft&&!actorGroupInspection&&!scenePlacementInspection&&(!environmentGroupInspection||environmentGroupInspection.report.schema_version==='legaia.environment-layout-review.v1'),
  onInspection:(report,layer)=>{cancelViewportGesture();if(report){environmentGroupTool?.restore();environmentRotationGroupTool?.restore();}environmentGroupInspection=report?{report,layer}:null;draw();},onFrame:frameEnvironmentGroup,onError:error=>notify(typeof error==='string'?error:error.message,true)});
environmentRotationGroupTool=mountEnvironmentRotationGroup({host:environmentGroupHost,getState:()=>state,getSelection:()=>environmentGroupSelection,
  busy:()=>busy,setBusy,api,canReview:()=>canEdit()&&scenePreviewCurrent()&&sceneModelsReady()&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft&&!actorGroupInspection&&!scenePlacementInspection&&!wallSelectMode&&!wallInspection&&(!environmentGroupInspection||environmentGroupInspection.report.schema_version==='legaia.environment-rotation-group-review.v1'),
  onInspection:(report,layer)=>{cancelViewportGesture();if(report){environmentGroupTool?.restore();environmentLayoutTool?.restore();}environmentGroupInspection=report?{report,layer}:null;draw();},onFrame:frameEnvironmentGroup,onError:error=>notify(typeof error==='string'?error:error.message,true)});
const scenePlacementHost=document.createElement('div');scenePlacementHost.id='scene-placement-tools';environmentGroupHost.after(scenePlacementHost);
scenePlacementHost.innerHTML='<button type="button" data-mixed-select aria-pressed="false">Select scene placements</button><button type="button" data-mixed-box aria-pressed="false" title="Drag over visible actor, NPC draft and static scenery pixels; Ctrl/Command adds, Shift pans.">Box select placements</button><button type="button" data-mixed-visible>Select visible placements</button><button type="button" data-mixed-invert>Invert visible placements</button><span role="status"></span><button type="button" data-mixed-clear>Clear placement group</button>';
scenePlacementHost.querySelector('[role="status"]').style.display='block';
scenePlacementHost.querySelector('[data-mixed-select]').onclick=()=>{if(busy||scenePlacementHost.querySelector('[data-mixed-select]').disabled)return;cancelViewportGesture();if(scenePlacementMode){scenePlacementMode=false;scenePlacementBoxMode=false;}else{clearActorGroupSelection();clearEnvironmentGroupSelection();actorBoxMode=false;scenePlacementMode=true;scenePlacementKey=resourceStateKey();}renderHierarchy();draw();};
scenePlacementHost.querySelector('[data-mixed-box]').onclick=()=>{if(busy||scenePlacementHost.querySelector('[data-mixed-box]').disabled)return;cancelViewportGesture();clearActorGroupSelection();clearEnvironmentGroupSelection();actorBoxMode=false;scenePlacementMode=true;scenePlacementBoxMode=!scenePlacementBoxMode;scenePlacementKey=resourceStateKey();renderHierarchy();draw();};
async function selectVisibleScenePlacements(invert=false){
  const control=scenePlacementHost.querySelector(invert?'[data-mixed-invert]':'[data-mixed-visible]');if(busy||control.disabled)return;
  try{
    const context=resourceStateKey(),sourceKey=state.scene_preview_source_key,revision=cameraRevision,viewWidth=width,viewHeight=height,eligible=scenePlacementEligible(),hits=sceneRenderer.pickRegion({x:0,y:0},{x:width,y:height},sceneView()).filter(id=>eligible.has(id));
    const next=invert?invertScenePlacementSelection(scenePlacementMode?scenePlacementSelection:currentPlacementSelection(),hits,eligible):mergeScenePlacementSelection([],hits,eligible);
    const focus=next.includes(environmentSelection)?environmentSelection:next.includes(state.selection?.entity_id)?state.selection.entity_id:next[0];
    if(focus&&entities().some(e=>e.id===focus)){if(!await api('/api/selection',{entity_id:focus}))return;}
    if(context!==resourceStateKey()||sourceKey!==state.scene_preview_source_key||revision!==cameraRevision||viewWidth!==width||viewHeight!==height||!scenePreviewCurrent()||!canEdit())throw new Error('Scene or camera changed. Repeat visible placement selection.');
    cancelViewportGesture();clearActorGroupSelection();clearEnvironmentGroupSelection();clearScenePlacementSelection();actorBoxMode=false;scenePlacementMode=true;scenePlacementBoxMode=false;scenePlacementSelection=next;scenePlacementKey=resourceStateKey();
    if(focus&&state.actor_drafts?.[focus]){environmentSelection=null;npcDraftSelection=focus;}else if(focus&&!entities().some(e=>e.id===focus)){environmentSelection=focus;npcDraftSelection=null;}else{environmentSelection=null;npcDraftSelection=null;}
    renderHierarchy();renderInspector();draw();notify(`${hits.length} visible placements · ${next.length} selected · visible mesh pixels`);
  }catch(error){notify(error.message,true);}
}
scenePlacementHost.querySelector('[data-mixed-visible]').onclick=()=>selectVisibleScenePlacements();
scenePlacementHost.querySelector('[data-mixed-invert]').onclick=()=>selectVisibleScenePlacements(true);
scenePlacementHost.querySelector('[data-mixed-clear]').onclick=()=>{clearScenePlacementSelection();renderHierarchy();draw();};
scenePlacementTool=mountScenePlacementGroup({host:scenePlacementHost,getState:()=>state,getSelection:()=>scenePlacementSelection,busy:()=>busy,setBusy,api,
  canReview:()=>canEdit()&&scenePreviewCurrent()&&sceneModelsReady()&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft&&!actorGroupInspection&&!environmentGroupInspection&&!wallSelectMode&&!wallInspection,
  onInspection:(report,layer)=>{cancelViewportGesture();scenePlacementMode=false;scenePlacementBoxMode=false;scenePlacementInspection=report?{report,layer}:null;draw();},onFrame:frameScenePlacementGroup,onError:error=>notify(typeof error==='string'?error:error.message,true)});
const clearScenery=document.createElement('button');clearScenery.textContent='Clear scenery group';clearScenery.onclick=()=>{clearEnvironmentGroupSelection();renderHierarchy();renderInspector();draw();};environmentGroupHost.append(clearScenery);
function clearActorGroupSelection(){actorGroupSelection=[];actorGroupSelectionKey=null;actorGroupRangeAnchor=null;updateActorGroupSelection();}
function updateActorGroupSelection(){
  if(actorGroupSelection.length&&(!canEdit()||actorGroupSelectionKey!==resourceStateKey()||actorGroupSelection.some(id=>!entities().some(e=>e.id===id)))){actorGroupSelection=[];actorGroupSelectionKey=null;actorGroupRangeAnchor=null;}
  actorBoxButton.disabled=busy||scenePlacementMode||!!scenePlacementInspection||wallSelectMode||!!wallInspection||!canEdit()||!!actorGroupInspection||!!scenePose||!!shapeDraft||!scenePreviewCurrent()||pickScriptTargets||pickRuntimeNodes;
  if(actorBoxButton.disabled&&actorBoxMode){actorBoxMode=false;actorBoxButton.setAttribute('aria-pressed','false');actorBoxButton.classList.remove('active');}
  actorGroupTools.hidden=!actorGroupSelection.length||!!actorGroupInspection;
  actorGroupTools.querySelector('span').textContent=`${actorGroupSelection.length} actor${actorGroupSelection.length===1?'':'s'} in group · Ctrl-click to toggle · Inspector shows focused actor`;
  actorGroupTools.querySelector('[data-review-selection]').disabled=busy||actorGroupSelection.length<2;actorGroupTools.querySelector('[data-review-components]').disabled=busy||actorGroupSelection.length<2;const appearanceButton=document.querySelector('[data-group-appearance]');if(appearanceButton)appearanceButton.disabled=busy||!canEdit()||actorGroupSelection.length<2||!!actorGroupInspection||!!scenePose;
  actorGroupTools.querySelector('[data-frame-selection]').disabled=busy||!actorGroupSelection.length||!scenePreviewCurrent();
  actorGroupTools.querySelector('[data-clear-selection]').disabled=busy;savedActorSelections?.synchronize();savedSceneSelections?.synchronize();savedSceneViews?.synchronize();groupPresetTool?.synchronize();
}
function toggleActorSelection(id){
  sceneResourceSelection=null;
  clearEnvironmentGroupSelection();
  if(busy||!canEdit()||actorGroupInspection)return;
  updateActorGroupSelection();
  try{actorGroupSelection=toggleActorGroupSelection(actorGroupSelection,id,entities().map(e=>e.id),selected()?.id);actorGroupSelectionKey=resourceStateKey();actorGroupRangeAnchor=id;cancelViewportGesture();updateActorGroupSelection();renderHierarchy();draw();}
  catch(error){notify(error.message,true);}
}
function setActorGroupMembers(members,add=false){
  clearEnvironmentGroupSelection();
  if(busy||!canEdit()||actorGroupInspection)return;
  const eligible=entities().map(e=>e.id),base=actorGroupSelection.length?actorGroupSelection:selected()?[selected().id]:[];
  actorGroupSelection=mergeActorGroupSelection(base,members,eligible,add);actorGroupSelectionKey=resourceStateKey();cancelViewportGesture();updateActorGroupSelection();renderHierarchy();draw();
}
function selectActorRange(id,add=false){
  sceneResourceSelection=null;
  clearEnvironmentGroupSelection();
  if(busy||!canEdit()||actorGroupInspection)return;
  const eligible=new Set(entities().map(e=>e.id)),visible=[...$('hierarchy').querySelectorAll('.entity-row')].map(row=>row.title).filter(id=>eligible.has(id));
  const anchor=actorGroupRangeAnchor??selected()?.id??id;
  try{setActorGroupMembers(actorGroupRange(anchor,id,visible),add);actorGroupRangeAnchor=visible.includes(anchor)?anchor:id;}
  catch(error){notify(error.message,true);}
}
function frameActorGroupSelection(){
  if(busy||!scenePreviewCurrent()||!actorGroupSelection.length)return;
  pendingEntityFrame=null;cancelViewportGesture();
  const points=entities().filter(e=>actorGroupSelection.includes(e.id)).map(position),min={},max={};
  for(const axis of ['x','y','z']){min[axis]=Math.min(...points.map(p=>p[axis]));max[axis]=Math.max(...points.map(p=>p[axis]));camera.target[axis]=(min[axis]+max[axis])/2;}
  camera.distance=Math.max(300,Math.hypot(max.x-min.x,max.y-min.y,max.z-min.z)*1.5);cameraRevision++;draw();
}
actorGroupTools.querySelector('[data-frame-selection]').onclick=frameActorGroupSelection;
actorGroupTools.querySelector('[data-review-selection]').onclick=()=>{if(!busy&&actorGroupSelection.length>=2)document.getElementById('actor-batch-button').click();};
actorGroupTools.querySelector('[data-clear-selection]').onclick=()=>{if(busy)return;clearActorGroupSelection();renderHierarchy();draw();};
const groupComponentDialog=document.createElement('dialog');groupComponentDialog.id='group-component-dialog';document.body.append(groupComponentDialog);
let groupComponentGeneration=0,groupComponentAbort=null;
groupComponentDialog.addEventListener('close',()=>{groupComponentGeneration++;if(groupComponentAbort){groupComponentAbort.abort();groupComponentAbort=null;setBusy(false);}});
actorGroupTools.querySelector('[data-review-components]').onclick=()=>{
  if(busy||!canEdit()||actorGroupSelection.length<2||actorGroupInspection)return;
  const ids=actorGroupSelection.slice(),context=resourceStateKey(),components=[...new Set((state.authored_assets??[]).filter(row=>ids.includes(row.id)).flatMap(row=>(row.component_reviews??[]).map(item=>item.component)))].sort();
  groupComponentDialog.replaceChildren();const heading=document.createElement('h2'),note=document.createElement('p'),select=document.createElement('select'),result=document.createElement('div'),error=document.createElement('p'),revert=document.createElement('button'),close=document.createElement('button');
  heading.textContent='Review actor group components';note.textContent=`${ids.length} imported actors. Revert removes the chosen authored component across this group, preserving imported evidence and other components. One Undo restores the affected actors.`;select.setAttribute('aria-label','Group component');
  for(const component of components){const option=document.createElement('option');option.value=component;option.textContent=component;select.append(option);}
  error.className='dialog-error';error.setAttribute('role','alert');revert.textContent='Revert reviewed group component';revert.dataset.revertGroupComponent='';revert.disabled=true;close.textContent='Close group component review';close.onclick=()=>groupComponentDialog.close();groupComponentDialog.append(heading,note,select,result,error,revert,close);
  let review=null;
  const current=()=>groupComponentDialog.open&&canEdit()&&context===resourceStateKey()&&JSON.stringify(ids)===JSON.stringify(actorGroupSelection);
  select.onchange=async()=>{
    const component=select.value,token=++groupComponentGeneration;groupComponentAbort?.abort();const controller=new AbortController();groupComponentAbort=controller;review=null;revert.disabled=true;result.replaceChildren();error.textContent='';setBusy(true);
    try{const response=await fetch('/api/actor-component-batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({actor_ids:ids,component}),signal:controller.signal}),report=await response.json();if(!response.ok||report.error)throw new Error(report.error||'Group component review failed');
      if(token!==groupComponentGeneration||!current()||select.value!==component)return;
      if(report.schema_version!=='legaia.actor-component-batch.v1'||report.component!==component||report.scene_id!==state.scene.id||!Array.isArray(report.targets)||report.targets.length!==ids.length||report.targets.some((row,index)=>row.entity_id!==ids[index]||typeof row.has_authored!=='boolean')||typeof report.review_key!=='string'||!/^[0-9a-f]{64}$/.test(report.review_key)||report.affected_count!==report.targets.filter(row=>row.has_authored).length)throw new Error('Invalid group component review');
      review=report;const count=document.createElement('p');count.textContent=`${report.affected_count} actors authored · ${ids.length-report.affected_count} inherit retail`;result.append(count);
      for(const row of report.targets){const details=document.createElement('details'),summary=document.createElement('summary'),data=document.createElement('pre');summary.textContent=`${entities().find(e=>e.id===row.entity_id)?.name??row.entity_id} · ${row.has_authored?'Authored':'Inherits retail'}`;data.className='diagnostic-detail';data.textContent=row.has_authored?JSON.stringify(row.authored,null,2):'No authored component; this actor will remain unchanged.';details.append(summary,data);result.append(details);}
    }catch(e){if(e.name!=='AbortError'&&token===groupComponentGeneration&&current())error.textContent=e.message;}
    finally{if(groupComponentAbort===controller){groupComponentAbort=null;setBusy(false);}select.disabled=busy;revert.disabled=busy||!current()||!review?.affected_count;}
  };
  revert.onclick=async()=>{if(busy||!current()||!review?.affected_count)return;const accepted=review;review=null;revert.disabled=true;select.disabled=true;
    if(await api('/api/command',{type:'revert_actor_group_component',scene_id:accepted.scene_id,actor_ids:ids,component:accepted.component,review_key:accepted.review_key},{success:`${accepted.component} reverted on ${accepted.affected_count} actors. Undo restores the group.`})){groupComponentDialog.close();}
    else if(groupComponentDialog.open){select.disabled=false;error.textContent='Group revert rejected. Choose the component again to refresh the review.';}
  };
  groupComponentDialog.showModal();if(components.length)select.onchange();else{select.disabled=true;note.textContent+=' This group has no supported authored components.';}
};
const actorGroupAppearance=mountGroupAppearance({after:actorGroupTools.querySelector('[data-review-components]'),getState:()=>state,getSelection:()=>actorGroupSelection,isBusy:()=>busy,canEdit,setBusy,api,
  canInspectScene:()=>sceneModelsReady()&&scenePreviewCurrent()&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft&&!actorGroupInspection,
  getScenePreview:()=>scenePreview,
  inspectScene:(proposed,report,returnToReview)=>{
    cancelViewportGesture();const failures=sceneRenderer.load(structuredClone(proposed));
    if(failures.length){sceneRenderer.load(structuredClone(scenePreview));throw new Error(failures.join('; '));}
    const appearanceContext=()=>JSON.stringify([resourceStateKey(),actorGroupSelection,entities().map(e=>[e.id,position(e)])]);const acceptedContext=appearanceContext();
    scenePose={isCurrent:()=>appearanceContext()===acceptedContext,key:sceneKey,name:'Proposed group appearance · not applied',returnToFile:returnToReview};
    scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`Proposed group appearance · not applied · ${report.targets.length} actors · ${proposed.entities.filter(e=>report.targets.some(r=>r.entity_id===e.entity_id)&&!e.renderable).length} unavailable models`;
    configureSceneInspectionComparison(proposed);
    for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('[aria-label="Scene preview rate"]').parentElement])control.hidden=true;
    const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to group appearance';
    frameShapeProposal({instance_scope:'all_model_instances',proposal_instances:report.targets},null);draw();
  }
});
const actorBatchTool=mountActorPlacementBatch({getState:()=>state,getEntities:entities,isBusy:()=>busy,canEdit,setBusy,api,notify,after:draftsButton,getSelection:()=>actorGroupSelection,
  canInspectScene:()=>scenePreviewCurrent()&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft,
  onSceneInspection:(inspection,layer)=>{cancelViewportGesture();actorGroupInspection=inspection?{...inspection,layer,key:resourceStateKey()}:null;draw();},
  frameGroup:inspection=>{
    const points=[];for(const [id,proposed] of inspection.positions){const entity=entities().find(item=>item.id===id);if(!entity)continue;const original=activeScenePreview()?.entities.find(item=>item.entity_id===id)?.display_position;if(original)points.push(original);points.push(proposed);}
    if(!points.length)return;const min={},max={};for(const axis of ['x','y','z']){min[axis]=Math.min(...points.map(p=>p[axis]));max[axis]=Math.max(...points.map(p=>p[axis]));camera.target[axis]=(min[axis]+max[axis])/2;}camera.distance=Math.max(200,Math.hypot(max.x-min.x,max.y-min.y,max.z-min.z)*1.5);cameraRevision++;draw();
  }});
async function importCatalogPreviewSelection(body,selection){
  if(!await api('/api/import',body,{success:'Previewed scene imported.'})||!selection)return;
  const scene='scene://'+body.scene,key=sceneRequestKey(),project=state.project?.path,source=state.project_copy_source_key;
  const fresh=()=>state.project?.mode==='edit'&&state.scene?.id===scene&&state.project?.path===project&&state.project_copy_source_key===source&&sceneRequestKey()===key;
  if(!fresh())return;
  const actor=entities().find(e=>e.id===selection.entity_id);
  if(actor){if(!await api('/api/selection',{entity_id:actor.id})||!fresh())return;frame(actor);revealHierarchyButton.click();document.querySelector('.workspace-tabs [data-panel="inspector"]').click();notify('Scene imported. Previewed actor selected in the Project.');return;}
  if(selection.kind!=='environment'){notify('Scene imported; previewed instance has no supported Project inspector.',true);return;}
  if(!modelsEnabled){notify('Scene imported; enable scene models to select the previewed environment instance.',true);return;}
  const deadline=performance.now()+30000;
  while(fresh()&&!scenePreviewCurrent()&&scenePendingKey===key&&performance.now()<deadline)await new Promise(resolve=>setTimeout(resolve,50));
  if(!fresh())return;
  const environment=environmentEntities().find(e=>e.entity_id===selection.entity_id);
  if(!environment||busy){notify('Scene imported; previewed environment selection is unavailable. Retry models and select it in the hierarchy.',true);return;}
  selectEnvironment(environment.entity_id);$('frame-selected').click();revealHierarchyButton.click();document.querySelector('.workspace-tabs [data-panel="inspector"]').click();notify('Scene imported. Previewed environment instance selected in the Project.');
}
$('history-button').onclick=()=>{if(!busy)openCommandHistory();};
$('undo-button').onclick=()=>api('/api/undo',{});
$('redo-button').onclick=()=>api('/api/redo',{});
$('edit-mode').onclick=()=>api('/api/mode',{mode:'edit'});
$('live-mode').onclick=()=>api('/api/mode',{mode:'live'});
const hierarchyQueryStatus=document.createElement('p');hierarchyQueryStatus.id='hierarchy-query-status';hierarchyQueryStatus.setAttribute('role','status');hierarchyQueryStatus.className='field-note';
const hierarchyQueryHelp=document.createElement('details');hierarchyQueryHelp.className='hierarchy-query-help';hierarchyQueryHelp.innerHTML='<summary>Hierarchy search syntax</summary><p>AND terms, quoted phrases and -exclusions. Fields: name, id, type, component, authored, visibility. Types: actor, npc-draft, environment, transition, trigger, region, collision, script. Example: type:actor -authored:true. Component searches authored actor component names/labels. Authored is true/false for actors and true for NPC drafts; scenery/resource authorship is unknown here. Visibility shown/hidden means the editor hidden-entity set, including hide/isolation state; resource visibility is unknown. Loading, occlusion, gameplay visibility and group folds are separate.</p>';
const hierarchyMatchSelect=document.createElement('button');hierarchyMatchSelect.id='select-matching-actors';hierarchyMatchSelect.type='button';hierarchyMatchSelect.textContent='Select matching actors';hierarchyMatchSelect.disabled=true;let hierarchyMatchIds=[],hierarchyMatchKey=null;
$('entity-search').maxLength=2048;$('entity-search').placeholder='Name, id:, type:, authored:…';$('entity-search').parentElement.after(hierarchyQueryStatus,hierarchyMatchSelect,hierarchyQueryHelp);
const canSelectHierarchyMatches=()=>!busy&&canEdit()&&!actorGroupInspection&&!scenePlacementInspection&&!environmentGroupInspection&&!wallInspection&&!scenePose&&!shapeDraft;
hierarchyMatchSelect.onclick=()=>{if(!canSelectHierarchyMatches()||hierarchyMatchKey!==resourceStateKey()||!hierarchyMatchIds.length||hierarchyMatchIds.length>128)return;try{const hidden=hiddenSceneEntities(),tokens=parseHierarchyQuery($('entity-search').value),ids=matchingActorIds(entities().map(e=>hierarchyActorRecord(e,hidden)),tokens);if(JSON.stringify(ids)!==JSON.stringify(hierarchyMatchIds))throw Error('Hierarchy results changed. Search again.');clearScenePlacementSelection();sceneResourceSelection=null;environmentSelection=null;npcDraftSelection=null;setActorGroupMembers(ids,false);renderInspector();notify(ids.length+' matching actors selected. Project content unchanged.');}catch(error){notify(error.message,true);}};
const hierarchyPlacementMatchSelect=document.createElement('button');hierarchyPlacementMatchSelect.id='select-matching-placements';hierarchyPlacementMatchSelect.type='button';hierarchyPlacementMatchSelect.textContent='Select matching placements';hierarchyPlacementMatchSelect.disabled=true;hierarchyMatchSelect.after(hierarchyPlacementMatchSelect);
let hierarchyPlacementMatchIds=[],hierarchyPlacementMatchKey=null;
function updateHierarchyPlacementMatchSelection(){
  const button=$('select-matching-placements');if(!button)return;button.disabled=true;hierarchyPlacementMatchIds=[];hierarchyPlacementMatchKey=null;
  try{parseHierarchyQuery($('entity-search').value);const ids=matchingHierarchyPlacementIds($('hierarchy'),scenePlacementEligible());hierarchyPlacementMatchIds=ids;hierarchyPlacementMatchKey=resourceStateKey();button.title=ids.length+' matching imported actors, NPC drafts and static decorations';button.disabled=!canSelectHierarchyMatches()||!scenePreviewCurrent()||sceneRepresentation!=='authored'||wallSelectMode||!ids.length;}
  catch(error){button.title=error.message;}
}
hierarchyPlacementMatchSelect.onclick=async()=>{
  if(hierarchyPlacementMatchSelect.disabled||busy||hierarchyPlacementMatchKey!==resourceStateKey())return;
  try{
    const key=resourceStateKey(),source=state.scene_preview_source_key,query=$('entity-search').value,eligible=scenePlacementEligible(),ids=mergeScenePlacementSelection([],matchingHierarchyPlacementIds($('hierarchy'),eligible),eligible);parseHierarchyQuery(query);
    if(JSON.stringify(ids)!==JSON.stringify(hierarchyPlacementMatchIds))throw new Error('Hierarchy results changed. Search again.');
    const active=hierarchySelectedIdentity(),focus=ids.includes(active)?active:ids[0];if(entities().some(entity=>entity.id===focus)&&!await api('/api/selection',{entity_id:focus}))return;
    if(key!==resourceStateKey()||source!==state.scene_preview_source_key||query!==$('entity-search').value||!scenePreviewCurrent()||!canSelectHierarchyMatches()||sceneRepresentation!=='authored'||wallSelectMode)throw new Error('Hierarchy source or query changed. Search again.');
    setSourcePlacementGroup(ids,focus);
    renderHierarchy();renderInspector();draw();notify(ids.length+' matching placements selected. Project content unchanged.');
  }catch(error){notify(error.message,true);}
};
$('entity-search').oninput=renderHierarchy;
const revealHierarchyButton=document.createElement('button');revealHierarchyButton.id='reveal-hierarchy-selection';revealHierarchyButton.type='button';revealHierarchyButton.textContent='Reveal selection';revealHierarchyButton.title='Clear hierarchy search, expand the selected group and focus the selected row';$('entity-search').parentElement.after(revealHierarchyButton);
function hierarchySelectedIdentity(){return selectedSceneResource()?.id??(selectedNpcDraft()?npcDraftSelection:null)??selectedEnvironment()?.entity_id??selected()?.id??null;}
revealHierarchyButton.onclick=()=>{
  if(busy)return;const current=currentPlacementSelection(),active=hierarchySelectedIdentity(),ids=current.length>1?current:active?[active]:[];if(!ids.length)return;
  const focus=ids.includes(active)?active:ids[0];$('entity-search').value='';renderHierarchy();
  if(!revealHierarchyEntities($('hierarchy'),ids,focus))notify('One or more selected placements have no available hierarchy row.',true);
};

$('frame-all').onclick=()=>frame();
function updateSceneFocusButton(){
  const group=currentPlacementSelection().length>1;
  $('frame-selected').disabled=busy||(group? !scenePreviewCurrent()||!sceneModelsReady():!['trigger','region'].includes(selectedSceneResource()?.type)&&!selected()&&!selectedEnvironment()&&!selectedNpcDraft());
  $('frame-selected').title=group?'Frame selected placement group (F)':'Frame selected entity (F)';
}
function frameSceneSelection(){
  if(busy)return;
  const ids=currentPlacementSelection();
  if(ids.length>1){
    if(!scenePreviewCurrent()||!sceneModelsReady()){notify('Load the current scene geometry before framing the placement group.',true);return;}
    cancelViewportGesture();frameScenePlacementGroup({targets:ids.map(entity_id=>({entity_id}))});return;
  }
  if(selectedSceneResource())frameSceneResource();else if(selectedNpcDraft())frameNpcDraft();else if(selectedEnvironment())frameEnvironment();else if(selected())frame(selected());
}
$('frame-selected').onclick=frameSceneSelection;
$('grid-toggle').onclick=()=>{grid=!grid;$('grid-toggle').classList.toggle('active',grid);$('grid-toggle').setAttribute('aria-pressed',grid);draw();};
let stabilitySourceAudit=null;
let stabilityChecks=null;
$('diagnostics-dialog').addEventListener('close',()=>{if($('diagnostics-dialog').open)return;stabilityChecks?.dispose();stabilityChecks=null;});
$('diagnostics-dialog').addEventListener('close',()=>{if($('diagnostics-dialog').open)return;stabilitySourceAudit?.dispose();stabilitySourceAudit=null;});
$('diagnostics-button').onclick=()=>{
  $('diagnostics').replaceChildren();
  const diagnostics=state.diagnostics ?? [];
  if(!diagnostics.length){const p=document.createElement('p');p.textContent='No project diagnostics reported.';$('diagnostics').append(p);}
  for(const diagnostic of diagnostics){const item=document.createElement('div');item.className='diagnostic';const title=document.createElement('strong');title.textContent=diagnostic.code ?? diagnostic.severity ?? 'Diagnostic';const p=document.createElement('p');p.textContent=diagnostic.message ?? (typeof diagnostic==='string'?diagnostic:JSON.stringify(diagnostic));item.append(title,p);$('diagnostics').append(item);}
  if(scenePreview||sceneError){const details=document.createElement('details');details.className='scene-preview-evidence';details.innerHTML='<summary>Scene model evidence and limits</summary><pre></pre>';details.querySelector('pre').textContent=JSON.stringify({source_key:sceneKey,error:sceneError,metrics:scenePreview?.metrics,limits:scenePreview?.limits,entities:scenePreview?.entities},null,2);$('diagnostics').append(details);}
  const check=document.createElement('button');check.textContent='Check SDK stability sources…';check.onclick=()=>{if(busy)return;stabilitySourceAudit?.dispose();const path=state.project?.path;stabilitySourceAudit=openStabilitySourceAudit({current:()=>$('diagnostics-dialog').open&&path===state.project?.path,busy:()=>busy,onError:error=>notify(error.message,true)});};$('diagnostics').append(check);
  $('diagnostics-dialog').showModal();
  const freshCheck=document.createElement('button');freshCheck.textContent='Run Fresh SDK Stability Checks…';freshCheck.onclick=()=>{if(busy)return;stabilityChecks?.dispose();const path=state.project?.path;stabilityChecks=openStabilityChecks({current:()=>$('diagnostics-dialog').open&&path===state.project?.path,busy:()=>busy,onError:error=>notify(error.message,true)});};$('diagnostics').append(freshCheck);
};
groupPresetTool=mountPresetBatch({after:actorGroupTools,getState:()=>state,getSelection:()=>actorGroupSelection,isBusy:()=>busy,canEdit,
  canAuthor:()=>canEdit()&&!actorGroupInspection&&!scenePose&&!shapeDraft,setBusy,api,
  canInspectScene:()=>sceneModelsReady()&&scenePreviewCurrent()&&sceneRepresentation==='authored'&&!scenePose&&!actorGroupInspection&&!shapeDraft,
  getScenePreview:()=>scenePreview,
  inspectScene:(proposed,report,returnToReview,isCurrent,onDiscard)=>{
    cancelViewportGesture();const failures=sceneRenderer.load(structuredClone(proposed));if(failures.length){sceneRenderer.load(structuredClone(scenePreview));throw new Error(failures.join('; '));}
    scenePose={key:sceneKey,name:'Proposed actor group preset · not applied',returnToFile:returnToReview,isCurrent,onDiscard};
    scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent='Proposed group preset · not applied';configureSceneInspectionComparison(proposed);
    for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('[aria-label="Scene preview rate"]').parentElement])control.hidden=true;
    const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to group preset';draw();
  }
});
function sceneViewState(){const preview=activeScenePreview();return {...state,scene_view_entity_ids:(preview?.entities??[]).map(e=>e.entity_id),scene_view_renderable_ids:(preview?.entities??[]).filter(e=>e.renderable).map(e=>e.entity_id),scene_view_map_sha256:staticDecorations()[0]?.source_record?.source_record?.map_sha256??preview?.assets?.find(a=>a.pose_kind==='source_heightfield')?.preview?.source_record?.map_sha256??null};}
savedSceneViews=mountSceneViews({
  after:$('actor-box-select'),getState:sceneViewState,isBusy:()=>busy,canEdit,
  getDisplay:()=>{hiddenSceneEntities();if(!scenePreviewCurrent())throw new Error('Wait for the current scene before saving visibility.');return {camera:structuredClone(camera),representation:sceneRepresentation,layers:{...sceneLayers},grid,hierarchy:captureSceneViewHierarchy($('entity-search').value,hierarchyGroupState,JSON.stringify([state.project?.path,state.scene?.id])),visibility:captureSceneViewVisibility(sceneHidden,sceneIsolated?.ids,sceneViewState())};},
  canRecall:()=>canEdit()&&!scenePose&&!actorGroupInspection&&!shapeDraft&&!environmentGroupInspection&&!scenePlacementInspection&&!wallInspection,api,
  recall:async(value,projectPath,current)=>{
    const check=()=>{if(!current()||state.project.path!==projectPath||!canEdit()||scenePose||actorGroupInspection||shapeDraft||environmentGroupInspection||scenePlacementInspection||wallInspection||!state.scene_views?.some(row=>row.id===value.id&&row.review_key===value.review_key))throw new Error('Saved view context changed. Review it again.');};
    if(!await api('/api/state',undefined))return false;check();
    if(unavailableSceneViewNpcs(value,state).length)throw new Error('Saved NPC visibility is unavailable. Restore the missing drafts or replace the view.');
    if(value.scene_id!==state.scene.id&&!await api('/api/scene',{scene_id:value.scene_id}))return false;
    check();let display;
    if(value.display.visibility&&['authored','retail'].includes(value.display.representation)&&sceneRepresentation!==value.display.representation){representationSelect.value=value.display.representation;representationSelect.onchange();}
    if(value.display.visibility){const deadline=performance.now()+60000;while(!scenePreviewCurrent()){check();if(sceneError||!modelsEnabled||performance.now()>deadline)throw new Error(sceneError||'Scene preview is not ready for view recall');await new Promise(resolve=>setTimeout(resolve,50));}check();}
    display=decodeSavedSceneView(value,sceneViewState());
    cancelViewportGesture();pendingEntityFrame=null;coordinateProbe=null;
    if(sceneRepresentation!==display.representation){representationSelect.value=display.representation;representationSelect.onchange();}
    Object.assign(camera,display.camera);projectionSelect.value=camera.projection;document.querySelector('.viewport-type').textContent=camera.projection==='orthographic'?'Orthographic':'Perspective';
    Object.assign(sceneLayers,display.layers);
    if(Object.hasOwn(display,'grid')){grid=display.grid;$('grid-toggle').classList.toggle('active',grid);$('grid-toggle').setAttribute('aria-pressed',String(grid));}
    if(display.visibility){sceneHiddenScope=JSON.stringify([state.project?.path,state.scene?.id]);sceneHidden=new Set(display.visibility.hidden_entity_ids);const ids=sceneViewIsolationIds(display.visibility);sceneIsolated=ids.length?{ids,key:sceneRequestKey()}:null;}
    for(const layer of ['actors','scenery','ground']){const button=$('scene-layer-'+layer);if(button){button.classList.toggle('active',sceneLayers[layer]);button.setAttribute('aria-pressed',String(sceneLayers[layer]));}}
    if(display.hierarchy){$('entity-search').value=display.hierarchy.query;hierarchyGroupState.scope=JSON.stringify([state.project?.path,state.scene?.id]);hierarchyGroupState.collapsed=new Set(display.hierarchy.collapsed_groups);}
    cameraRevision++;renderHierarchy();draw();return true;
  }
});
savedActorSelections=mountActorSelectionSets({after:$('actor-box-select'),getState:()=>state,getSelection:()=>actorGroupSelection,isBusy:()=>busy,canEdit,
  canRecall:()=>canEdit()&&!scenePose&&!actorGroupInspection&&!shapeDraft,api,
  recall:async(value,projectPath)=>{
    if(state.project.path!==projectPath)throw new Error('Project changed before selection recall');
    if(value.scene_id!==state.scene.id&&!await api('/api/scene',{scene_id:value.scene_id}))return false;
    const ids=decodeSavedActorSelection(value,state);
    if(!await api('/api/selection',{entity_id:ids[0]}))return false;
    if(state.project.path!==projectPath)throw new Error('Project changed during selection recall');
    if(!state.actor_selection_sets.some(row=>row.id===value.id&&row.review_key===value.review_key))throw new Error('Saved selection changed during recall. Review it again.');
    decodeSavedActorSelection(value,state);actorGroupSelection=mergeActorGroupSelection([],ids,entities().map(entity=>entity.id));actorGroupSelectionKey=resourceStateKey();actorGroupRangeAnchor=ids[0];cancelViewportGesture();renderHierarchy();draw();return true;
  }
});
function currentPlacementSelection(){
  if(scenePlacementSelection.length)return scenePlacementSelection.slice();
  if(actorGroupSelection.length)return actorGroupSelection.slice();
  if(environmentGroupSelection.length)return environmentGroupSelection.slice();
  if(environmentSelection&&scenePlacementEligible().has(environmentSelection))return [environmentSelection];
  if(npcDraftSelection&&scenePlacementEligible().has(npcDraftSelection))return [npcDraftSelection];
  return selected()?[selected().id]:[];
}
function sceneSelectionState(){return {...state,scene_selection_eligible_ids:[...scenePlacementEligible()],scene_selection_map_sha256:staticDecorations()[0]?.source_record?.source_record?.map_sha256??null};}
savedSceneSelections=mountSceneSelectionSets({host:scenePlacementHost,getState:sceneSelectionState,getSelection:currentPlacementSelection,isBusy:()=>busy,canEdit,api,
  canRecall:()=>canEdit()&&modelsEnabled&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft&&!actorGroupInspection&&!environmentGroupInspection&&!scenePlacementInspection&&!wallInspection&&!wallSelectMode,
  onError:error=>notify(typeof error==='string'?error:error.message,true),
  recall:async(value,projectPath,current)=>{
    const check=()=>{if(!current()||state.project.path!==projectPath||!canEdit()||sceneRepresentation!=='authored'||scenePose||shapeDraft||actorGroupInspection||environmentGroupInspection||scenePlacementInspection||wallInspection||wallSelectMode||!state.scene_selection_sets?.some(row=>row.id===value.id&&row.review_key===value.review_key))throw new Error('Saved scene selection changed during recall. Review it again.');};
    check();if(!await api('/api/state',undefined))return false;check();
    if(value.scene_id!==state.scene?.id&&!await api('/api/scene',{scene_id:value.scene_id}))return false;check();
    const deadline=performance.now()+60000;
    while(!scenePreviewCurrent()){check();if(sceneError||!modelsEnabled||performance.now()>deadline)throw new Error(sceneError||'Scene preview is not ready for placement recall');await new Promise(resolve=>setTimeout(resolve,50));}
    check();const sourceKey=state.project_copy_source_key;
    const response=await fetch('/api/scene-selection-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({selection_set_id:value.id,review_key:value.review_key})});const report=await response.json();check();
    if(!response.ok||report.error)throw new Error(report.error||'Saved placement verification failed');
    if(report.schema_version!=='legaia.scene-selection-review.v1'||report.read_only!==true||report.project_source_key!==sourceKey||state.project_copy_source_key!==sourceKey||report.scene_id!==value.scene_id||report.id!==value.id||report.review_key!==value.review_key||report.import_sha256!==value.import_sha256||report.map_sha256!==value.map_sha256||JSON.stringify(report.entity_ids)!==JSON.stringify(value.entity_ids))throw new Error('Saved placement sources changed during recall');
    const ids=decodeSavedSceneSelection(value,sceneSelectionState());
    clearScenePlacementSelection();clearActorGroupSelection();clearEnvironmentGroupSelection();
    const actorIds=ids.filter(id=>entities().some(entity=>entity.id===id)),npcIds=ids.filter(id=>state.actor_drafts?.[id]?.scene_id===state.scene.id),decorIds=ids.filter(id=>!actorIds.includes(id)&&!npcIds.includes(id));
    if(actorIds.length){if(!await api('/api/selection',{entity_id:actorIds[0]}))return false;check();decodeSavedSceneSelection(value,sceneSelectionState());}else if(npcIds.length){environmentSelection=null;npcDraftSelection=npcIds[0];}else{environmentSelection=decorIds[0];npcDraftSelection=null;}
    if(npcIds.length>1||[actorIds,npcIds,decorIds].filter(group=>group.length).length>1){scenePlacementSelection=ids;scenePlacementKey=resourceStateKey();scenePlacementMode=false;}
    else if(actorIds.length>1){actorGroupSelection=ids;actorGroupSelectionKey=resourceStateKey();actorGroupRangeAnchor=ids[0];}
    else if(decorIds.length){environmentGroupSelection=ids;environmentGroupKey=resourceStateKey();environmentGroupAnchor=ids[0];}
    cancelViewportGesture();renderHierarchy();renderInspector();draw();return true;
  }
});

document.addEventListener('keydown',event=>{
  if(event.key==='Escape'&&drag){event.preventDefault();cancelViewportGesture();return;}
  if(event.key==='Escape'&&scenePlacementMode){event.preventDefault();scenePlacementMode=false;draw();return;}
  if(event.key==='Escape'&&wallSelectMode){event.preventDefault();wallSelectMode=false;updateFieldToggle();draw();return;}
  if(event.target.matches('input,textarea') || document.querySelector('dialog[open]')) return;
  if((event.ctrlKey||event.metaKey)&&!event.altKey&&!event.shiftKey&&event.key.toLowerCase()==='d'&&!event.target.matches('select,[contenteditable]')&&!event.target.isContentEditable&&selectedNpcDraft()){
    event.preventDefault();if(!event.repeat)duplicateNpcDraft(npcDraftSelection);return;
  }
  if((event.ctrlKey||event.metaKey) && event.key.toLowerCase()==='s'){event.preventDefault();if(!busy)api('/api/project/save',{}, {success:'Project saved.'});}
  if((event.ctrlKey||event.metaKey) && event.key.toLowerCase()==='z'){event.preventDefault();const redo=event.shiftKey;if(redo?state.history?.can_redo:state.history?.can_undo)api(redo?'/api/redo':'/api/undo',{});}
  if(event.key.toLowerCase()==='f'&&!event.ctrlKey&&!event.metaKey&&!event.altKey&&!event.target.matches('select,[contenteditable]')&&!event.target.isContentEditable){event.preventDefault();frameSceneSelection();}
});
window.addEventListener('beforeunload',event=>{if(state.project?.dirty){event.preventDefault();event.returnValue='';}});

function render(){
  updateEnvironmentGroupSelection();
  updateActorGroupSelection();actorBatchTool.synchronize();savedActorSelections?.synchronize();savedSceneSelections?.synchronize();savedSceneViews?.synchronize();groupPresetTool?.synchronize();
  draftsButton.textContent=`NPC drafts (${Object.keys(state.actor_drafts??{}).length})`;
  if(['transform','group-transform','environment-group-transform','scene-placement-group-transform'].includes(drag?.type)&&!transformGestureCurrent(drag))cancelViewportGesture();
  $('project-name').textContent=state.project?.name ?? 'No project';
  $('dirty').hidden=!state.project?.dirty;
  $('scene-name').textContent=state.scene?.name ?? 'No scene imported';
  $('viewport-title').textContent=state.scene?.name ?? 'Scene';
  $('entity-count').textContent=entities().length;
  $('asset-count').textContent=(state.active_scene_assets ?? []).length;
  $('diagnostic-count').textContent=(state.diagnostics ?? []).length;
  $('viewport-empty').hidden=!!state.scene?.id;
  sceneSelect.replaceChildren();for(const scene of state.scenes ?? []){const option=document.createElement('option');option.value=scene.id;option.textContent=scene.name;option.selected=scene.id===state.scene?.id;sceneSelect.append(option);}sceneSelect.hidden=(state.scenes ?? []).length<2;
  const live=(state.project?.mode ?? 'edit').toLowerCase()==='live';
  $('edit-mode').classList.toggle('active',!live);$('live-mode').classList.toggle('active',live);$('live-mode').disabled=!state.capabilities?.live_mode;
  document.querySelector('.inspector-panel .tag').textContent=live?'LIVE':'EDIT';
  $('live-mode').title=state.capabilities?.live_mode?'Observe runtime state':state.runtime?.reason?.message ?? 'Runtime observation is unavailable';
  reconcileLiveFollow();renderRuntimeControls();
  document.querySelector('.preview-badge').firstChild.textContent=live?'AUTHORED SCENE · LIVE OBSERVATIONS SEPARATE':'SCENE PREVIEW';
  updateSceneFocusButton();
  $('status').textContent=state.scene?.id ? `${state.scene.name} · ${entities().length} entities · ${state.project?.dirty?'Changes not saved':'Project ready'}` : 'Ready · Create or open a project to begin';
  renderHierarchy();renderAssets();renderInspector();
  templateButton.disabled=!state.capabilities?.authored_transform_templates;
  if(templateDialog.open)renderTemplates();
  renderRunStatus();renderBuildStatus();scheduleRunPoll();
  if(lastSceneId!==state.scene?.id){lastSceneId=state.scene?.id;frame();}else draw();
  refreshScenePreview();
}
function activeScenePreview(){return scenePreview&&state.capabilities?.scene_preview&&state.scene_preview_source_key&&sceneProjectPath===state.project?.path&&scenePreview.scene_id===state.scene?.id&&scenePreview.representation===sceneRepresentation?scenePreview:null;}
function scenePreviewCurrent(){return !!activeScenePreview()&&sceneKey===sceneRequestKey()&&!sceneError;}
function sceneModelsReady(){return modelsEnabled&&activeScenePreview()&&sceneRenderer&&!sceneRenderer.lost&&!sceneError;}
function sceneView(){const positions=new Map(entities().map(entity=>[entity.id,draft?.id===entity.id?draft.position:position(entity)]));if(environmentGroupInspection?.layer==='proposed')for(const row of environmentGroupInspection.report.targets){const proposed=sceneryGroupPosition(row);if(proposed)positions.set(row.entity_id,proposed);}if(scenePlacementInspection?.layer==='proposed')for(const row of scenePlacementInspection.report.targets){const proposed=scenePlacementPosition(row);if(proposed)positions.set(row.entity_id,proposed);}if(draft&&!draft.group&&!draft.sceneryYaw)positions.set(draft.id,draft.position);const ground=currentGroundPositionInspection();if(ground)positions.set(ground.report.review.entity_id,{...ground.report[ground.layer+'_instance'].display_position});return {normalDiagnostic:sceneNormalDiagnostic,normalGeometryKeys:sceneNormalDiagnostic?new Set(scenePose?.report?.tracks.filter(track=>track.normal_pose).map(track=>track.geometry_key)??[]):undefined,transforms:yawPreviewTransforms(),camera,basis:basis(),width,height,grid,hiddenEntities:hiddenSceneEntities(),positions};}
let sceneFacePickMode=false,floorPickMode=false;
const sceneFacePickButton=document.createElement('button');sceneFacePickButton.id='scene-face-pick';sceneFacePickButton.textContent='Pick model face';sceneFacePickButton.title='Click a visible authored model surface to open its Current native face';sceneFacePickButton.setAttribute('aria-pressed','false');$('frame-selected').after(sceneFacePickButton);
let sceneRuler=null;
const npcGroundPlacement=mountNpcGroundPlacement({after:document.querySelector('.viewport-toolbar'),getKey:()=>JSON.stringify([resourceStateKey(),state.project_copy_source_key,sceneRequestKey()]),available:()=>!sceneRuler?.picking()&&!transitionArrivalOverlay&&!npcArrivalOverlay&&canMeasureScene(),getDocument:activeScenePreview,getSceneId:()=>state.scene?.id,pickVertex:p=>sceneRenderer.pickSurfaceVertex(p.x,p.y,sceneView()),onChange:()=>resize(),onError:error=>notify(error.message,true)});
let groundPositionInspection=null,npcCreationInspection=null;
const groundPositionBar=document.createElement('div');groundPositionBar.id='ground-position-preview';groundPositionBar.className='viewport-toolbar';groundPositionBar.hidden=true;groundPositionBar.innerHTML='<span role="status"></span><button type="button" data-current>Current position</button><button type="button" data-proposed>Proposed position</button><button type="button" data-return>Return to position Inspector</button><button type="button" data-close>Close position preview</button>';npcGroundPlacement.bar.after(groundPositionBar);
function scenePositionPreviewAvailable(){return !!state.capabilities?.actor_position_preview&&canEdit()&&scenePreviewCurrent()&&sceneModelsReady()&&sceneRepresentation==='authored'&&!scenePendingKey&&!scenePose&&!shapeDraft&&!draft&&!actorGroupInspection&&!environmentGroupInspection&&!scenePlacementInspection&&!scenePlacementMode&&!wallInspection&&!wallSelectMode&&!transitionArrivalOverlay&&!npcArrivalOverlay&&!sceneRuler?.picking()&&!npcGroundPlacement.active();}
function groundPositionPreviewAvailable(){return !npcCreationInspection&&scenePositionPreviewAvailable();}
function npcCreationSceneAvailable(){return !!state.capabilities?.npc_creation_preview&&!groundPositionInspection&&scenePositionPreviewAvailable();}
const npcCreationBar=document.createElement('div');npcCreationBar.id='npc-creation-preview';npcCreationBar.className='viewport-toolbar';npcCreationBar.hidden=true;npcCreationBar.innerHTML='<span role="status"></span><button type="button" data-frame>Frame prospective NPC</button><button type="button" data-return>Return to NPC creation</button>';groundPositionBar.after(npcCreationBar);
function clearNpcCreationInspection(owner){const value=npcCreationInspection;if(!value||owner!==undefined&&value.owner!==owner)return;npcCreationInspection=null;npcCreationBar.hidden=true;if(scenePreviewCurrent()&&sceneRequestKey()===value.key&&sceneRenderer){const failures=sceneRenderer.load(structuredClone(scenePreview));if(failures.length)sceneError=failures.join('; ');}resize();}
function currentNpcCreationInspection(){const value=npcCreationInspection;if(value&&(!value.current()||!npcCreationSceneAvailable()||sceneRequestKey()!==value.key)){value.resume();return null;}return value;}
function updateNpcCreationInspection(){const value=currentNpcCreationInspection();npcCreationBar.hidden=!value;if(!value)return;const row=value.report.proposed_instance;npcCreationBar.querySelector('[role="status"]').textContent=`Prospective NPC: ${row.name} · X ${row.position.x}, Z ${row.position.z}. ${row.preview_height_status==='source_surface'?'Height derived from source terrain; authored Y unknown.':'Height unresolved; display plane is a placeholder.'} Not created; gameplay unverified.`;for(const button of npcCreationBar.querySelectorAll('button'))button.disabled=busy;}
npcCreationBar.querySelector('[data-frame]').onclick=()=>{const value=currentNpcCreationInspection();if(value&&!busy)frame({id:value.report.review.preview_entity_id});};
npcCreationBar.querySelector('[data-return]').onclick=()=>{const value=currentNpcCreationInspection();if(value&&!busy)value.resume();};
function currentGroundPositionInspection(){if(groundPositionInspection&&(!groundPositionInspection.current()||!groundPositionPreviewAvailable())){groundPositionInspection=null;groundPositionBar.hidden=true;}return groundPositionInspection;}
function showGroundPositionInspection(report,current){cancelViewportGesture();groundPositionInspection=report?{report,current,layer:'proposed'}:null;groundPositionBar.hidden=!report;updateGroundPositionInspection();resize();}
function updateGroundPositionInspection(){const value=currentGroundPositionInspection();groundPositionBar.hidden=!value;if(!value)return;const row=value.report[value.layer+'_instance'],position=row.position;groundPositionBar.querySelector('[role="status"]').textContent=`${value.layer==='proposed'?'Proposed':'Current'} X ${position.x}, Z ${position.z}. ${row.preview_height_status==='explicit'?'Existing authored/source Y preserved.':row.preview_height_status==='source_surface'?'Height derived from source terrain; authored Y remains unknown.':'Height unresolved; display plane is a placeholder.'} Project unchanged; gameplay unverified.`;for(const button of groundPositionBar.querySelectorAll('button'))button.disabled=busy;groundPositionBar.querySelector('[data-current]').setAttribute('aria-pressed',String(value.layer==='current'));groundPositionBar.querySelector('[data-proposed]').setAttribute('aria-pressed',String(value.layer==='proposed'));}
for(const layer of ['current','proposed'])groundPositionBar.querySelector('[data-'+layer+']').onclick=()=>{const value=currentGroundPositionInspection();if(!value||busy)return;value.layer=layer;updateGroundPositionInspection();frame({id:value.report.review.entity_id});};
groundPositionBar.querySelector('[data-return]').onclick=()=>{if(!currentGroundPositionInspection()||busy)return;document.querySelector('.workspace-tabs [data-panel="inspector"]').click();};
groundPositionBar.querySelector('[data-close]').onclick=()=>showGroundPositionInspection(null);
function mountExistingGroundPosition(host,kind,id){
  const context=()=>{const target=kind==='npc'&&npcDraftSelection===id?selectedNpcDraft():kind==='actor'&&selected()?.id===id&&!selectedNpcDraft()&&!selectedEnvironment()?selected():null;if(!target)return null;return {project:state.project?.path,scene:state.scene?.id,source:state.project_copy_source_key,preview:state.scene_preview_source_key,id,position:kind==='npc'?target.position:target.components.Transform.effective.position};};
  if(!context())return;
  const owner=Symbol('ground-position-preview');
  mountSceneGroundPosition({host,kind,id,getContext:context,busy:()=>busy,canEdit,canPreview:groundPositionPreviewAvailable,
    previewPosition:async(request,signal)=>{const captured=structuredClone(context()),instance=structuredClone(activeScenePreview()?.entities.find(row=>row.entity_id===id));const post=async(route,body)=>{const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),value=await response.json();if(!response.ok)throw Error(value.error||'Position preview failed');return value;};const reviewed=await post('/api/actor-position-review',request);if(!/^[a-f0-9]{64}$/.test(reviewed.review_key??''))throw Error('Position review returned no valid source receipt.');const report=await post('/api/actor-position-scene',{...request,review_key:reviewed.review_key});if(report.review?.review_key!==reviewed.review_key)throw Error('Position review changed during projection.');return decodeGroundPositionPreview(report,captured,kind,request.position,instance);},
    onPreview:(report,current)=>{if(!report){if(groundPositionInspection?.owner===owner)showGroundPositionInspection(null);return;}showGroundPositionInspection(report,current);groundPositionInspection.owner=owner;document.querySelector('.workspace-tabs [data-panel="viewport"]').click();frame({id});},beginPick:(resume,options)=>{npcGroundPlacement.begin(result=>{if(host.isConnected&&context()){resume(result);document.querySelector('.workspace-tabs [data-panel="inspector"]').click();}},options);document.querySelector('.workspace-tabs [data-panel="viewport"]').click();},apply:command=>api('/api/command',command,{success:'Proposed X/Z applied. Save persists the position; gameplay remains unverified.'}),onError:error=>notify(error.message,true)});
}
function canMeasureScene(){return !currentNpcCreationInspection()&&!busy&&canEdit()&&scenePreviewCurrent()&&sceneModelsReady()&&sceneRepresentation==='authored'&&!scenePendingKey&&!scenePose&&!shapeDraft&&!draft&&!actorGroupInspection&&!environmentGroupInspection&&!scenePlacementInspection&&!scenePlacementMode&&!actorBoxMode&&!wallSelectMode&&!wallInspection&&!sceneFacePickMode&&!pickScriptTargets&&!pickHistoricalSamples&&!pickRuntimeNodes&&!fieldSpatialPick&&!floorPickMode;}
sceneRuler=mountSceneRuler({after:sceneFacePickButton,getContext:()=>({project_path:state.project?.path??'',scene_id:state.scene?.id??'',source_key:state.scene_preview_source_key??'',representation:sceneRepresentation,preview_key:sceneKey,hidden_entities:[...hiddenSceneEntities()].sort()}),available:canMeasureScene,busy:()=>busy,pickVertex:p=>sceneRenderer.pickSurfaceVertex(p.x,p.y,sceneView()),onDraw:()=>{updateSceneFacePick();draw();},notify});
function canPickSceneFace(allowBusy=false){return !currentNpcCreationInspection()&&!sceneRuler?.picking()&&(allowBusy||!busy)&&canEdit()&&scenePreviewCurrent()&&sceneModelsReady()&&sceneRepresentation==='authored'&&!scenePendingKey&&!scenePose&&!shapeDraft&&!draft&&!actorGroupInspection&&!environmentGroupInspection&&!scenePlacementInspection&&!scenePlacementMode&&!actorBoxMode&&!wallSelectMode&&!wallInspection&&!pickScriptTargets&&!pickRuntimeNodes&&!fieldSpatialPick&&!floorPickMode;}
function updateSceneFacePick(){sceneFacePickButton.disabled=!canPickSceneFace();if(sceneFacePickButton.disabled)sceneFacePickMode=false;sceneFacePickButton.classList.toggle('active',sceneFacePickMode);sceneFacePickButton.setAttribute('aria-pressed',String(sceneFacePickMode));}
sceneFacePickButton.onclick=()=>{if(!canPickSceneFace())return;sceneFacePickMode=!sceneFacePickMode;updateSceneFacePick();if(sceneFacePickMode)notify('Click a visible model surface. Drag still orbits; picking is display only.');};
async function inspectSceneFace(point,gesture){
 if(!canPickSceneFace()||gesture.context!==resourceStateKey()||gesture.sourceKey!==state.scene_preview_source_key||gesture.cameraRevision!==cameraRevision||gesture.width!==width||gesture.height!==height)throw new Error('Scene changed during face picking. Try again on Current.');
 const document=activeScenePreview(),key=sceneKey,context=primitiveContext(),current=()=>canPickSceneFace(true)&&activeScenePreview()===document&&sceneKey===key&&JSON.stringify(primitiveContext())===JSON.stringify(context);
 const hit=sceneRenderer.pickSurface(point.x,point.y,sceneView());if(!hit){notify('No visible model surface at this point.');return;}
 const entity=document.entities.find(e=>e.entity_id===hit.entity_id&&e.geometry_key===hit.geometry_key&&e.renderable),geometry=document.assets.find(a=>a.geometry_key===hit.geometry_key&&a.asset_id===entity?.asset_id);
 if(!entity||!geometry)throw new Error('Picked surface has no Current asset owner.');
 let face;setBusy(true);try{const response=await fetch('/api/model-primitive-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:entity.asset_id})}),value=await response.json();if(!response.ok||value.error)throw new Error(value.error||'Current face source unavailable.');if(!current())throw new Error('Scene changed while loading face ownership.');const source=decodeModelPrimitives(value,entity.asset_id,context);face=nativeSceneFaceAtTriangle(geometry,source,hit.triangle_index);}finally{setBusy(false);}
 if(!current())throw new Error('Picked face source is stale.');
 if(state.actor_drafts?.[entity.entity_id])selectNpcDraft(entity.entity_id);else if(environmentEntities().some(e=>e.entity_id===entity.entity_id))selectEnvironment(entity.entity_id);else{environmentSelection=null;if(!await api('/api/selection',{entity_id:entity.entity_id}))throw new Error('Picked entity selection failed.');}
 if(!current())throw new Error('Picked face source changed during selection.');
 await openModel(entity.asset_id,null,null,state.model_overrides?.[entity.asset_id]?'authored':'imported',entity.entity_id);
 if(!current()||modelAssetId!==entity.asset_id||!$('model-dialog').open)throw new Error('Current model could not be opened for this surface.');
 await inspectModelPrimitives(face);
}
function updateSceneBadge(){
  updateSceneFacePick();
  if($('texture-scene-uses'))$('texture-scene-uses').disabled=busy||!scenePreviewCurrent();
  comparisonNotice.hidden=sceneRepresentation!=='retail';
  const draftCount=Object.values(state.actor_drafts??{}).filter(item=>item.scene_id===state.scene?.id).length;
  $('entity-count').textContent=entities().length+environmentEntities().length+draftCount;
  const ready=sceneModelsReady(),count=ready?sceneRenderer.instances.length:0;
  const hidden=hiddenSceneEntities(),visible=ready?sceneRenderer.instances.filter(instance=>!hidden.has(instance.entity_id)).length:0;
  const visibilityId=visibilitySelection(),visibilityItem=activeScenePreview()?.entities.find(e=>e.entity_id===visibilityId);
  updateSceneIsolation();
  $('hide-selected').disabled=!visibilityId;
  $('hide-selected').textContent=sceneHidden.has(visibilityId)?'Show selected':'Hide selected';
  $('hide-model').disabled=!visibilityItem?.asset_id;
  $('show-hidden').disabled=sceneHidden.size===0;
  $('show-hidden').textContent=sceneHidden.size?`Show hidden (${sceneHidden.size})`:'Show hidden';
  $('scene-models').hidden=!ready;
  modelToggle.hidden=!state.capabilities?.scene_preview;modelToggle.textContent=sceneError?'Retry models':'Models';modelToggle.title=sceneError ?? 'Show supported SDK meshes at authored placements';
  document.querySelector('.preview-badge span').textContent=sceneError?'Models unavailable · placement markers remain usable':scenePendingKey?(ready?'Updating scene · showing previous preview (scenery editing paused)':'Loading supported scene models…'):ready?`${currentNpcCreationInspection()?'Prospective NPC · not created · ':''}${sceneRepresentation==='retail'?'Retail comparison · ':'Authored · '}${count} / ${activeScenePreview()?.entities.length??0} meshes loaded · ${visible} visible · approximate blends`:modelsEnabled?'Placement markers · model data unavailable':'Placement markers · models hidden';
  $('coordinate-note').textContent=environmentEntities().length?'Environment: imported transforms · Actors: unknown height/facing use preview conventions':'Unknown actor heights are shown on the ground plane.';
  $('coordinate-note').title=JSON.stringify(activeScenePreview()?.limits ?? []);
}
async function refreshScenePreview(){
  const key=sceneRequestKey();
  if(!state.capabilities?.scene_preview||!key||!modelsEnabled){sceneAbort?.abort();scenePendingKey=null;updateSceneBadge();return;}
  if(activeScenePreview()&&sceneKey===key){sceneAbort?.abort();sceneAbort=null;scenePendingKey=null;sceneFailedKey=null;sceneError=null;updateSceneBadge();return;}
  if(scenePendingKey===key||sceneFailedKey===key){updateSceneBadge();return;}
  const preserveCamera=sceneLoadedId===state.scene?.id && sceneProjectPath===state.project?.path;
  sceneAbort?.abort();const controller=new AbortController();sceneAbort=controller;scenePendingKey=key;sceneError=null;if(!preserveCamera){scenePreview=null;sceneRenderer?.clear();}
  const expectedScene=state.scene?.id,revision=cameraRevision;updateSceneBadge();draw();
  try{
    if(!sceneRenderer){const module=await import('/scene-renderer.js');if(controller.signal.aborted)return;sceneRenderer=new module.SceneRenderer($('scene-models'),message=>{sceneError=message;updateSceneBadge();draw();});}
    const response=await fetch('/api/scene-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({representation:sceneRepresentation}),signal:controller.signal});
    const data=await response.json();if(!response.ok||data.error)throw new Error(typeof data.error==='string'?data.error:'Scene preview failed');
    if(controller.signal.aborted||sceneRequestKey()!==key||state.scene?.id!==expectedScene)return;
    if(data.project_source_key!==state.scene_preview_source_key||data.representation!==sceneRepresentation||data.scene_id!==expectedScene)throw new Error('Scene preview source changed while loading; retry models.');
    if(!Array.isArray(data.position_to_display)||data.position_to_display.length!==16||!data.position_to_display.every(numeric))throw new Error('SDK did not provide a valid scene display conversion.');
    clearScenePose(false);const failures=sceneRenderer.load(data);if(!data.entities.some(e=>e.entity_id===environmentSelection))environmentSelection=null;scenePreview=data;sceneProjectPath=state.project?.path;sceneLoadedId=data.scene_id;sceneKey=key;sceneFailedKey=null;scenePendingKey=null;updateAssetPlacementActions();
    if(failures.length)notify(`${failures.length} model assets could not be rendered; their placement markers remain available.`,true);
    renderHierarchy();renderInspector();
    const waiting=pendingEntityFrame;pendingEntityFrame=null;
    if(waiting&&waiting.key===key&&waiting.scene===state.scene?.id&&waiting.project===state.project?.path&&waiting.projectSource===state.project_copy_source_key&&waiting.selection===hierarchySelectedIdentity()&&waiting.revision===cameraRevision&&!drag)frame(waiting.entity);
    else if(!preserveCamera&&revision===cameraRevision&&!drag)frame();else draw();
  }catch(error){if(error.name!=='AbortError'&&sceneRequestKey()===key){sceneFailedKey=key;sceneError=error.message;scenePendingKey=null;if(!preserveCamera)sceneRenderer?.clear();renderInspector();notify(error.message,true);}}
  finally{if(sceneAbort===controller){sceneAbort=null;scenePendingKey=null;updateSceneBadge();sceneAnimationController?.updateState();draw();}}
}
const hierarchyGroupState={scope:null,collapsed:new Set()};
const hierarchyNavigation=mountHierarchyNavigation($('hierarchy'),()=>[state.project?.path,state.scene?.id]);
function hierarchyActorRecord(entity,hidden){return {id:entity.id,name:entity.name,type:'actor',components:[...(entity.authored_components??[]),...authoredComponentLabels(entity)],authored:authored(entity)?'true':'false',visibility:hidden.has(entity.id)?'hidden':'shown'};}
function renderHierarchy(){
  const focusSnapshot=hierarchyNavigation.beforeRender();
  const list=$('hierarchy');list.setAttribute('aria-multiselectable','true');list.replaceChildren();
  const filter=$('entity-search').value,hidden=hiddenSceneEntities();let tokens;
  hierarchyMatchIds=[];hierarchyMatchKey=null;hierarchyMatchSelect.disabled=true;hierarchyPlacementMatchIds=[];hierarchyPlacementMatchKey=null;hierarchyPlacementMatchSelect.disabled=true;
  try{tokens=parseHierarchyQuery(filter);$('entity-search').setAttribute('aria-invalid','false');}catch(error){$('entity-search').setAttribute('aria-invalid','true');hierarchyQueryStatus.textContent=error.message;const p=document.createElement('div');p.className='empty-panel';p.textContent='Fix the hierarchy query to show results.';list.append(p);hierarchyNavigation.afterRender(focusSnapshot);return;}
  const matches=(id,name,type,components=[],authorship='unknown')=>hierarchyMatches({id,name,type,components,authored:authorship,visibility:['environment','npc-draft'].includes(type)?(hidden.has(id)?'hidden':'shown'):'unknown'},tokens);
  const actors=entities().filter(e=>hierarchyMatches(hierarchyActorRecord(e,hidden),tokens));
  try{hierarchyMatchIds=matchingActorIds(entities().map(e=>hierarchyActorRecord(e,hidden)),tokens);hierarchyMatchKey=resourceStateKey();hierarchyMatchSelect.disabled=!canSelectHierarchyMatches()||!hierarchyMatchIds.length;}catch(error){hierarchyQueryStatus.textContent=error.message;}

  if(actors.length){const heading=document.createElement('div');heading.className='field-note';heading.dataset.hierarchyGroupHeading='actors';heading.textContent=`Actors (${actors.length})`;list.append(heading);}
  for(const entity of actors){
    const row=document.createElement('button');row.className='entity-row';row.setAttribute('role','treeitem');row.setAttribute('aria-selected',!selectedSceneResource()&&!selectedEnvironment()&&!selectedNpcDraft()&&entity.id===state.selection?.entity_id);row.classList.toggle('selected',!selectedSceneResource()&&!selectedEnvironment()&&!selectedNpcDraft()&&entity.id===state.selection?.entity_id);row.title=entity.id;
    row.innerHTML=`<span class="entity-icon">◇</span><span class="entity-name">${escapeHTML(entity.name ?? entity.id)}</span>${authored(entity)?'<span class="authored-dot" title="Authored override"></span>':''}`;
    const badge=row.querySelector('.authored-dot');if(badge){const labels=authoredComponentLabels(entity);badge.title=labels.length?`Authored: ${labels.join(', ')}`:'Authored override';badge.setAttribute('aria-label',badge.title);}
    row.classList.toggle('group-selected',scenePlacementSelection.includes(entity.id)||actorGroupSelection.includes(entity.id));row.setAttribute('aria-selected',String(scenePlacementSelection.length?scenePlacementSelection.includes(entity.id):actorGroupSelection.length?actorGroupSelection.includes(entity.id):row.classList.contains('selected')));row.onclick=event=>{if(scenePlacementMode){toggleScenePlacement(entity.id);return;}if(event.shiftKey){selectActorRange(entity.id,event.ctrlKey||event.metaKey);return;}if(event.ctrlKey||event.metaKey){toggleActorSelection(entity.id);return;}environmentSelection=null;api('/api/selection',{entity_id:entity.id});};row.ondblclick=()=>frame(entity);list.append(row);
  }
  const environment=environmentEntities().filter(e=>matches(e.entity_id,e.name,'environment'));
  const npcDrafts=Object.entries(state.actor_drafts??{}).filter(([id,item])=>item.scene_id===state.scene?.id&&matches(id,item.name,'npc-draft',[],'true'));
  if(npcDrafts.length){const heading=document.createElement('div');heading.className='field-note';heading.dataset.hierarchyGroupHeading='npc-drafts';heading.textContent=`NPC drafts (${npcDrafts.length})`;list.append(heading);}
  for(const [id,item] of npcDrafts){const row=document.createElement('button');row.className='entity-row';row.setAttribute('role','treeitem');row.textContent=`${item.name} · ${sceneRepresentation==='retail'?'Authored only':'Draft'}`;row.title=id;row.onclick=()=>scenePlacementMode?toggleScenePlacement(id):selectNpcDraft(id);row.classList.toggle('group-selected',scenePlacementSelection.includes(id));row.setAttribute("aria-selected",String(scenePlacementSelection.length?scenePlacementSelection.includes(id):id===npcDraftSelection));row.classList.toggle("selected",id===npcDraftSelection);list.append(row);}
  if(environment.length){const heading=document.createElement('div');heading.className='field-note';heading.dataset.hierarchyGroupHeading='environment';heading.textContent=`Environment (${environment.length})`;list.append(heading);}
  for(const item of environment){const row=document.createElement('button');row.className='entity-row';row.setAttribute('role','treeitem');row.setAttribute('aria-selected',String(scenePlacementSelection.length?scenePlacementSelection.includes(item.entity_id):environmentGroupSelection.length?environmentGroupSelection.includes(item.entity_id):item.entity_id===environmentSelection));row.classList.toggle('selected',item.entity_id===environmentSelection);row.classList.toggle('group-selected',scenePlacementSelection.includes(item.entity_id)||environmentGroupSelection.includes(item.entity_id));row.textContent=item.name;row.title=item.entity_id;row.onclick=event=>{if(scenePlacementMode){toggleScenePlacement(item.entity_id);return;}if(event.shiftKey){selectEnvironmentRange(item.entity_id,event.ctrlKey||event.metaKey);return;}if(event.ctrlKey||event.metaKey){toggleEnvironmentSelection(item.entity_id);return;}selectEnvironment(item.entity_id);};row.ondblclick=()=>{selectEnvironment(item.entity_id);frameEnvironment();};list.append(row);}
  if(resourceKey===resourceStateKey())for(const [kind,label] of [['transition','Transitions'],['trigger','Triggers'],['region','Regions'],['collision','Collision'],['script','Scripts']]){
    const records=assetRecords().filter(record=>record.type===kind&&record.sceneId===state.scene?.id&&matches(record.id,record.label,kind));
    if(!records.length)continue;
    const heading=document.createElement('div');heading.className='field-note';heading.dataset.hierarchyGroupHeading=kind;heading.textContent=`${label} (${records.length})`;list.append(heading);
    for(const record of records){const row=document.createElement('button');row.className='entity-row scene-resource-row';row.setAttribute('role','treeitem');row.title=record.id;row.textContent=record.label;row.dataset.resourceId=record.id;row.setAttribute('aria-selected',String(record.id===sceneResourceSelection));row.classList.toggle('selected',record.id===sceneResourceSelection);row.onclick=()=>selectSceneResource(record);row.ondblclick=()=>selectSceneResource(record,true);list.append(row);}
  }
  if(!list.children.length){const p=document.createElement('div');p.className='empty-panel';p.textContent=entities().length?'No matching entities.':'Imported actors will appear here.';list.append(p);}
  hierarchyQueryStatus.textContent=`${list.querySelectorAll('.entity-row').length} matching rows · ${actors.length} actors${actors.length>128?' · Narrow to 128 actors for group selection':''}`;
  for(const row of list.querySelectorAll('.entity-row')){
    if(!hidden.has(row.title))continue;
    row.classList.add('viewport-hidden');
    const badge=document.createElement('small');badge.textContent='Hidden';badge.style.marginLeft='auto';
    row.append(badge);row.setAttribute('aria-label',`${row.textContent} in viewport`);
  }
  const groupScope=JSON.stringify([state.project?.path,state.scene?.id]);mountHierarchyGroups(list,{state:hierarchyGroupState,scope:groupScope,filter,current:()=>groupScope===JSON.stringify([state.project?.path,state.scene?.id]),onVisibility:()=>hierarchyNavigation.afterRender(hierarchyNavigation.beforeRender())});
  updateHierarchyPlacementMatchSelection();
  revealHierarchyButton.disabled=busy||!hierarchySelectedIdentity()&&currentPlacementSelection().length<2;revealHierarchyButton.title=currentPlacementSelection().length>1?'Clear search and reveal every selected placement; keep focus on the active member':'Clear search and reveal the active selection';
  hierarchyNavigation.afterRender(focusSnapshot);
}
// Search SDK records already present in project state, including their provenance.
const assetTools=document.createElement('div');assetTools.className='asset-tools';
assetTools.innerHTML='<label class="asset-search-label"><input id="asset-search" type="search" placeholder="Search ID, type, scene, provenance…" aria-label="Search asset database"></label><select id="asset-category" aria-label="Asset category"><option value="all">All records</option><option value="authored">Authored assets</option><option value="model">Models</option><option value="actor">Actors</option><option value="scene">Imported scenes</option><option value="texture">Textures</option><option value="animation">Animations</option><option value="audio">Audio</option><option value="script">Scripts</option><option value="dialogue">Dialogue</option><option value="flag">Flag references</option><option value="transition">Transitions</option><option value="collision">Collision</option><option value="trigger">Triggers</option><option value="region">Regions</option><option value="worldmap">World-map landmarks</option></select><span id="asset-results" role="status"></span><button id="resource-refresh">Refresh scene resources</button><span id="resource-status" role="status">Resource catalog has not been loaded.</span>';
$('assets').before(assetTools);
const assetScope=document.createElement('details');assetScope.className='asset-scope';assetScope.innerHTML='<summary>Catalog scope</summary><p>Choose active scene resources or explicitly refresh imported project resources. Coverage and source memberships distinguish supported imported metadata from runtime state.</p>';$('assets').after(assetScope);
mountScriptOperandBundle({after:assetTools,getState:()=>state,context:()=>JSON.stringify([resourceStateKey(),state.project?.mode,state.authored_assets]),canEdit:canEditDialogue,busy:()=>busy,setBusy,api,onError:error=>notify(error.message,true)});
const assetMetadataPin=createAssetMetadataPin();
const assetDetails=document.createElement('dialog');assetDetails.id='asset-details';document.body.append(assetDetails);assetDetails.addEventListener('close',()=>{if(assetDetails.open)return;assetPlacementSelection?.dispose();assetPlacementSelection=null;animationContributions?.dispose();animationContributions=null;});
let assetPage=0,assetPages=1,assetPageSignature=null;
const assetPager=document.createElement('div');assetPager.className='dialog-actions';assetPager.dataset.assetPages='';assetPager.style.flexWrap='wrap';
const assetPrevious=document.createElement('button'),assetNext=document.createElement('button'),assetPageStatus=document.createElement('span');
assetPrevious.type=assetNext.type='button';assetPrevious.textContent='Previous assets';assetNext.textContent='Next assets';assetPageStatus.setAttribute('role','status');
assetPager.append(assetPrevious,assetPageStatus,assetNext);$('assets').before(assetPager);assetPager.hidden=true;
assetPrevious.onclick=()=>{if(busy||assetPage<=0)return;assetPage--;renderAssets();};assetNext.onclick=()=>{if(busy||assetNext.disabled)return;assetPage++;renderAssets();};
assetNavigation=mountAssetNavigation($('assets'),()=>[state.project?.path,state.scene?.id,projectAssetControls?.scope(),projectAssetControls?.filter()],delta=>{if(busy||projectAssetControls?.scope()!=='project'||assetPage+delta<0||assetPage+delta>=assetPages)return false;assetPage+=delta;renderAssets();return true;});
$('asset-search').oninput=renderAssets;$('asset-category').onchange=renderAssets;
const assetSearchHelp=document.createElement('details');assetSearchHelp.id='asset-search-help';assetSearchHelp.innerHTML='<summary>Search filters</summary><p>Use name:, id:, type:, scene:, model:, confidence: or provenance:. Combine terms to narrow results; quote phrases and prefix a term with - to exclude it.</p><p>Examples: <code>type:model scene:town01 confidence:confirmed</code> · <code>name:&quot;Actor 0012&quot; -type:script</code>. Confidence searches recorded claims; a match does not confirm every property. Model filters include recorded imported and authored references, without proving runtime use. Project scope searches all retained imported memberships; active scope covers the refreshed scene. Project provenance searches include retained import/catalog hashes and source evidence. A match keeps the chosen source membership.</p>';assetTools.append(assetSearchHelp);
const assetKeyboardHelp=document.createElement('p');assetKeyboardHelp.id='asset-keyboard-help';assetKeyboardHelp.textContent='Tab enters asset results. Up/Down browse records; Left/Right choose Open or Details. Home/End jump to the first/last visible record. PageUp/PageDown browse imported-project pages. Enter/Space activate the focused action.';assetSearchHelp.append(assetKeyboardHelp);$('assets').setAttribute('aria-describedby',assetKeyboardHelp.id);
let resourceRecords=[],resourceLimitations=[],resourceContextKey=null,resourceKey=null,resourcePendingKey=null,resourceAbort=null,resourceError=null;
const resourceStateKey=()=>JSON.stringify([state.project?.path,state.scene?.id,state.scene_preview_source_key,state.scene_flag_state_key,state.scene_transition_state_key,state.scene_region_state_key,state.scene_trigger_state_key]);
let flagResourceDialog=null,transitionResourceDialog=null;
$('resource-refresh').onclick=refreshResources;
const transitionsButton=document.createElement('button');transitionsButton.id='scene-transitions';transitionsButton.textContent='Scene transitions';$('resource-refresh').after(transitionsButton);
let projectBookmarkNavigator=null;
const projectTransitionsButton=document.createElement('button');projectTransitionsButton.id='project-transitions';projectTransitionsButton.textContent='Project transitions';transitionsButton.after(projectTransitionsButton);projectTransitionsButton.onclick=()=>openSceneTransitions(true);
mountMeshSourceLibrary({after:projectTransitionsButton,getState:()=>state,busy:()=>busy,setBusy,onOpen:(record,catalog)=>navigateMeshSource({record,catalog,getState:()=>state,busy:()=>busy||!!shapeDraft||!!$('shape-file').files?.length,readLibrary:async path=>{const response=await fetch('/api/mesh-source-library',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_project_path:path})}),value=await response.json();if(!response.ok||value.error)throw new Error(value.error??'Mesh input library verification failed.');return value;},changeScene:id=>api('/api/scene',{scene_id:id}),openModel:(id,layer)=>openModel(id,null,null,layer)}),onError:error=>notify(error.message,true)});
mountModelSourceLibrary({after:projectTransitionsButton,getState:()=>state,busy:()=>busy,setBusy,onApplied:next=>{state=next;render();notify('Model input receipt removed. Save project to persist.');},onOpen:(record,catalog)=>navigateModelSource({record,catalog,getState:()=>state,busy:()=>busy||!!shapeDraft||!!$('shape-file').files?.length,readLibrary:async path=>{const response=await fetch('/api/model-source-library',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_project_path:path})}),value=await response.json();if(!response.ok||value.error)throw new Error(value.error??'Model input library verification failed.');return value;},changeScene:id=>api('/api/scene',{scene_id:id}),openModel:(id,layer)=>openModel(id,null,null,layer)}),onError:error=>notify(error.message,true)});
mountAnimationSourceLibrary({after:projectTransitionsButton,getState:()=>state,busy:()=>busy,setBusy,onApplied:next=>{state=next;render();notify('Animation input receipt removed. Save project to persist.');},onOpen:(record,catalog)=>navigateAnimationSource({record,catalog,getState:()=>state,busy:()=>busy,readLibrary:async path=>{const response=await fetch('/api/animation-source-library',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_project_path:path})}),value=await response.json();if(!response.ok||value.error)throw new Error(value.error??'Animation input library verification failed.');return value;},changeScene:id=>api('/api/scene',{scene_id:id}),refreshAssets:async()=>{await refreshResources();if(resourceKey!==resourceStateKey())throw new Error('Refresh source scene resources before opening the saved clip.');},getAssets:()=>assetRecords(true),openActor:async id=>{if(!await api('/api/selection',{entity_id:id}))throw new Error('The source actor could not be selected.');frame(selected());document.querySelector('.workspace-tabs [data-panel="viewport"]').click();},openClip:clip=>openAnimationResource(clip)}),onError:error=>notify(error.message,true)});
projectBookmarkNavigator=mountProjectScriptBookmarks({after:projectTransitionsButton,getState:()=>state,busy:()=>busy||worldmapDraftPending||scriptDrafts.size>0||!!sceneAnimationController?.active(),onError:error=>notify(error.message,true),onOpen:async bookmark=>{
  const projectPath=state.project.path;
  const qualified=()=>{const row=(state.script_bookmarks??[]).find(value=>value.id===bookmark.id);if(state.project.path!==projectPath||!row||row.review_key!==bookmark.review_key)throw new Error('Bookmark or project changed before navigation.');return row;};
  qualified();
  if(bookmark.scene_id!==state.scene?.id&&!await api('/api/scene',{scene_id:bookmark.scene_id}))return;
  qualified();if(state.scene_view_source_key!==bookmark.import_sha256)throw new Error('Bookmark imported scene witness differs from this scene.');
  const owner=bookmark.owner_id.includes('/scripts/man-p2/')?{id:bookmark.owner_id,name:bookmark.name,partitionTwo:true}:entities().find(row=>row.id===bookmark.owner_id);
  if(!owner)throw new Error('Bookmarked script owner is unavailable in this imported scene.');
  if(!owner.partitionTwo){if(!await api('/api/selection',{entity_id:owner.id}))return;qualified();}
  await openActorScript(owner,false,null,null,null,null,bookmark);
}});

const transitionsContext=(projectWide=false)=>JSON.stringify([resourceStateKey(),projectWide?state.project_transition_state_key:null]);
const transitionsDialog=document.createElement('dialog');transitionsDialog.id='scene-transitions-dialog';document.body.append(transitionsDialog);
let transitionsAbort=null,transitionWorkspace=null;
transitionsDialog.addEventListener('close',()=>{transitionWorkspace?.dispose();transitionWorkspace=null;if(transitionsAbort){transitionsAbort.abort();transitionsAbort=null;setBusy(false);}transitionsDialog.replaceChildren();});
transitionsButton.onclick=()=>openSceneTransitions();
async function openSceneTransitions(projectWide=false){
  if(busy||!state.capabilities?.scene_transitions)return;
  const key=transitionsContext(projectWide),controller=new AbortController();transitionsAbort=controller;setBusy(true);
  const context={projectWide,projectPath:state.project.path,sceneId:state.scene?.id,sourceKey:projectWide?state.project_transition_state_key:state.scene_preview_source_key,transitionStateKey:state.scene_transition_state_key,sceneIds:(state.scenes??[]).map(scene=>scene.id).sort()};
  transitionsDialog.dataset.sourceContext=key;transitionsDialog.dataset.projectWide=String(projectWide);
  transitionsDialog.innerHTML='<div class="dialog-heading"><h2>Scene transitions</h2><button id="close-scene-transitions" aria-label="Close scene transitions">×</button></div><p id="transitions-summary">Verifying scene scripts…</p><div id="transitions-graph"></div><p class="dialog-error" role="alert"></p>';
  transitionsDialog.querySelector('h2').textContent=projectWide?'Project transitions':'Scene transitions';
  $('close-scene-transitions').onclick=()=>transitionsDialog.close();transitionsDialog.showModal();
  const current=()=>transitionsDialog.open&&!controller.signal.aborted&&key===transitionsContext(projectWide);
  try{
    const response=await fetch(projectWide?'/api/project-transitions':'/api/scene-transitions',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',signal:controller.signal});
    const result=await response.json();if(!response.ok||result.error)throw new Error(result.error ?? 'Transition discovery failed');
    if(controller.signal.aborted||!transitionsDialog.open)return;
    if(!current())throw new Error('Transition source changed; reopen the graph.');
    const graph=decodeTransitionGraph(result,context);
    $('transitions-summary').textContent=`${graph.edges.length} encoded scene-change references · ${graph.coverage.script_count} scripts inspected · ${graph.coverage.partial_script_count} partial · ${graph.coverage.unavailable_script_count} unavailable. Gameplay reachability has not been evaluated.`;
    transitionWorkspace=mountTransitionGraphWorkspace($('transitions-graph'),graph,{activeSceneId:state.scene?.id,isCurrent:current,
      onError:error=>{if(current())transitionsDialog.querySelector('.dialog-error').textContent=error.message;},
      onInspect:async edge=>{if(busy||!current())return;transitionsDialog.close();if(edge.source!==state.scene?.id&&!await api('/api/scene',{scene_id:edge.source}))return;const owner=edge.partition===2?{id:edge.owner_id,name:edge.script_name,partitionTwo:true}:entities().find(entity=>entity.id===edge.owner_id);if(!owner){notify('The source script owner is unavailable.',true);return;}await openActorScript(owner,false,null,null,edge.reference.pc);},
      onInspectEntry:state.project?.mode==='edit'&&state.capabilities?.resource_catalog?async edge=>{if(busy||!current())return;const root=state.project?.path,projectKey=state.project_transition_state_key;transitionsDialog.close();await openGraphTransitionEntry(edge,root,projectKey);}:null,
      onOpenScene:async node=>{if(busy||!node.imported||!current())return;transitionsDialog.close();await api('/api/scene',{scene_id:node.id});}
    });
  }catch(error){if(error.name!=='AbortError'&&!controller.signal.aborted&&transitionsAbort===controller&&transitionsDialog.open){transitionWorkspace?.dispose();transitionWorkspace=null;$('transitions-graph').replaceChildren();$('transitions-summary').textContent='Transition graph unavailable.';transitionsDialog.querySelector('.dialog-error').textContent=error.message;}}
  finally{if(transitionsAbort===controller){transitionsAbort=null;setBusy(false);}}
}
const textButton=document.createElement('button');textButton.id='scene-text';textButton.textContent='Search scene text';transitionsButton.after(textButton);
const projectTextButton=document.createElement('button');projectTextButton.id='project-text';projectTextButton.textContent='Search project text';textButton.after(projectTextButton);
const textDialog=document.createElement('dialog');textDialog.id='scene-text-dialog';document.body.append(textDialog);let textAbort=null;
const textContextKey=(projectWide=false)=>JSON.stringify([resourceStateKey(),projectWide?state.project_text_state_key:state.scene_text_state_key]);
textDialog.addEventListener('close',()=>textAbort?.abort());
textButton.onclick=()=>openTextSearch();projectTextButton.onclick=()=>openTextSearch(true);
async function openTextSearch(projectWide=false){
  if(busy||!state.capabilities?.scene_text_search)return;
  const key=textContextKey(projectWide),controller=new AbortController();textAbort=controller;textDialog.dataset.sourceContext=key;textDialog.dataset.projectWide=String(projectWide);setBusy(true);
  textDialog.innerHTML='<div class="dialog-heading"><h2>Search supported scene text</h2><button aria-label="Close text search">Close</button></div><p data-text-summary>Verifying source text runs…</p><label>Search text or owner<input type="search" aria-label="Search scene text"></label><label>Layer<select aria-label="Text search layer"><option value="all">All text layers</option><option value="retail">Retail</option><option value="effective">Effective</option><option value="authored">Authored overrides</option></select></label><div class="dialog-actions"><button data-text-prev>Previous</button><span data-text-page></span><button data-text-next>Next</button></div><div data-text-results></div><details><summary>Coverage and limits</summary><pre class="diagnostic-detail" data-text-evidence></pre></details><p class="dialog-error" role="alert"></p>';
  textDialog.querySelector('[aria-label="Close text search"]').onclick=()=>textDialog.close();textDialog.showModal();
  if(projectWide){textDialog.querySelector('h2').textContent='Search supported project text';textDialog.querySelector('input').placeholder='Text, owner or imported scene';}
  try{
    const response=await fetch(projectWide?'/api/project-text':'/api/scene-text',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',signal:controller.signal}),data=await response.json();
    if(controller.signal.aborted||!textDialog.open)return;
    if(!response.ok)throw new Error(data.error);
    const identity=projectWide?data.schema==='legaia.project-text.v1'&&data.project_path===state.project.path&&data.project_text_state_key===state.project_text_state_key:
      data.schema==='legaia.scene-text.v1'&&data.text_state_key===state.scene_text_state_key&&data.scene_id===state.scene?.id&&data.source_key===state.scene_preview_source_key;
    if(key!==textContextKey(projectWide)||!identity||data.read_only!==true||!Array.isArray(data.runs)||data.runs.length>(projectWide?32768:8192))throw new Error('Text source changed or returned invalid bounds.');
    textDialog.querySelector('[data-text-summary]').textContent=`${data.runs.length} supported glyph runs · ${data.coverage.script_count} scripts inspected · ${data.coverage.partial_script_count} partial · ${data.coverage.unavailable_script_count} unavailable. Unknown/unvisited bytes and unsupported dialogue are excluded. Story reachability is not evaluated.`;
    if(projectWide)textDialog.querySelector('[data-text-summary]').textContent+=` ${data.scenes.length} imported scenes inspected; ${data.scenes.filter(s=>s.status==='unavailable').length} scene catalogs unavailable.`;
    textDialog.querySelector('[data-text-evidence]').textContent=JSON.stringify({scenes:data.scenes,coverage:data.coverage,restrictions:data.restrictions,limitations:data.limitations},null,2);
    const search=textDialog.querySelector('input'),layer=textDialog.querySelector('select'),list=textDialog.querySelector('[data-text-results]'),prev=textDialog.querySelector('[data-text-prev]'),next=textDialog.querySelector('[data-text-next]');let page=0;
    const render=()=>{
      const query=search.value.toLowerCase(),mode=layer.value,filtered=data.runs.filter(run=>{
        if(mode==='authored'&&run.authored_text===null)return false;
        const values=mode==='all'?[run.retail_text,run.effective_text,run.authored_text]:[run[mode+'_text']];
        return [...values,run.scene_name,run.owner_id,run.id,run.script_name,run.kind].some(value=>typeof value==='string'&&value.toLowerCase().includes(query));
      });page=Math.min(page,Math.max(0,Math.ceil(filtered.length/25)-1));list.replaceChildren();prev.disabled=page===0;next.disabled=(page+1)*25>=filtered.length;textDialog.querySelector('[data-text-page]').textContent=`${filtered.length} matches · page ${page+1} of ${Math.max(1,Math.ceil(filtered.length/25))}`;
      for(const run of filtered.slice(page*25,(page+1)*25)){
        const row=document.createElement('article');row.className='text-search-run';const label=document.createElement('strong');label.textContent=`${projectWide?run.scene_name+' · ':''}${run.script_name} · ${run.kind==='menu_label'?`Menu option ${run.option_index+1}`:'Dialogue'} · ${scriptOffset(run.pc)} · ${run.capacity} source bytes`;row.append(label);
        for(const [name,value] of [['Retail',run.retail_text],['Authored',run.authored_text],['Effective',run.effective_text]]){const title=document.createElement('small'),text=document.createElement('pre');title.textContent=name;text.textContent=value??(name==='Authored'?'No override':'Unavailable');row.append(title,text);}
        if(run.validation_error){const error=document.createElement('p');error.className='field-note';error.textContent=run.validation_error;row.append(error);}
        const button=document.createElement('button');button.textContent='Open text editor';button.dataset.textRun=run.id;button.onclick=async()=>{
          if(busy||!textDialog.open||key!==textContextKey(projectWide))return;
          if(projectWide&&run.scene_id!==state.scene?.id){textDialog.close();if(!await api('/api/scene',{scene_id:run.scene_id}))return;}
          const owner=run.partition===2?{id:run.owner_id,name:run.script_name,partitionTwo:true}:entities().find(e=>e.id===run.owner_id);
          if(!owner){notify('The text owner is no longer available.',true);return;}textDialog.close();await openActorScript(owner,false,run.id);
          const input=[...scriptDialog.querySelectorAll('[data-run-input]')].find(item=>item.dataset.runInput===run.id);if(input)input.scrollIntoView({block:'center'});
        };row.append(button);list.append(row);
      }
      if(!filtered.length){const empty=document.createElement('p');empty.textContent='No supported glyph runs match this search.';list.append(empty);}
    };prev.onclick=()=>{page--;render();};next.onclick=()=>{page++;render();};search.oninput=layer.onchange=()=>{page=0;render();};render();
  }catch(error){if(error.name!=='AbortError'&&textDialog.open)textDialog.querySelector('.dialog-error').textContent=error.message;}
  finally{if(textAbort===controller){textAbort=null;setBusy(false);}}
}
const flagsButton=document.createElement('button');flagsButton.id='scene-flags';flagsButton.textContent='Flag references';textButton.after(flagsButton);
const projectFlagsButton=document.createElement('button');projectFlagsButton.id='project-flags';projectFlagsButton.textContent='Project flag references';flagsButton.after(projectFlagsButton);projectFlagsButton.onclick=()=>openFlagReferences(true);
const flagsDialog=document.createElement('dialog');flagsDialog.id='scene-flags-dialog';document.body.append(flagsDialog);
let flagsAbort=null;
const flagContext=(projectWide=false)=>JSON.stringify([resourceStateKey(),projectWide?state.project_flag_state_key:null]);
flagsDialog.addEventListener('close',()=>{if(flagsAbort){flagsAbort.abort();flagsAbort=null;setBusy(false);}flagsDialog.replaceChildren();});
flagsButton.onclick=()=>openFlagReferences(false);
async function openFlagReferences(projectWide=false){
  if(busy||!state.capabilities?.scene_flags)return;
  const key=flagContext(projectWide),controller=new AbortController();flagsAbort=controller;setBusy(true);
  flagsDialog.dataset.projectWide=String(projectWide);flagsDialog.dataset.sourceContext=key;
  flagsDialog.innerHTML='<div class="dialog-heading"><h2>Flag references</h2><button aria-label="Close flag references">×</button></div><p class="flags-summary">Verifying scene scripts…</p><input type="search" aria-label="Search flag references" placeholder="Search bank, index, script or operation"><div class="flags-results"></div><p class="dialog-error" role="alert"></p>';
  flagsDialog.querySelector('h2').textContent=projectWide?'Project flag references':'Flag references';flagsDialog.querySelector('.flags-summary').textContent=projectWide?'Verifying imported scene scripts…':'Verifying scene scripts…';
  flagsDialog.querySelector('button').onclick=()=>flagsDialog.close();flagsDialog.showModal();
  try{
    const response=await fetch(projectWide?'/api/project-flags':'/api/scene-flags',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',signal:controller.signal});
    const result=await response.json();if(!response.ok||result.error)throw new Error(result.error??'Flag discovery failed');
    if(controller.signal.aborted||!flagsDialog.open)return;
    if(key!==flagContext(projectWide)||(!projectWide&&(result.scene_id!==state.scene?.id||result.source_key!==state.scene_preview_source_key||result.flag_state_key!==state.scene_flag_state_key))||(projectWide&&(result.source_key!==state.project_flag_state_key||result.project_path!==state.project?.path||JSON.stringify(result.scene_ids)!==JSON.stringify((state.scenes??[]).map(scene=>scene.id).sort())))||result.read_only!==true||!Array.isArray(result.groups)||result.groups.length>(projectWide?32768:16384))throw new Error('Flag references do not match the current scene source.');
    const summary=flagsDialog.querySelector('.flags-summary'),list=flagsDialog.querySelector('.flags-results'),search=flagsDialog.querySelector('input');
    if(projectWide){const coverage=document.createElement('details');coverage.innerHTML='<summary>Imported scene coverage</summary>';appendResourceTable(coverage,['Scene','Status','References / reason'],result.scenes.map(scene=>[scene.scene_name,scene.status,scene.status==='verified'?String(scene.reference_count):scene.reason]),'No imported scenes.');list.before(coverage);}
    const captured=result.runtime_snapshot,snapshot=document.createElement('details');snapshot.innerHTML='<summary>Captured runtime node flags</summary>';list.before(snapshot);
    const captureNote=document.createElement('p');captureNote.textContent=captured?.available?`Epoch boundary frame ${captured.frame} · ${captured.epoch_id}. ${captured.note}`:projectWide?'This project-wide view contains retail and authored operands. Inspect scene captures separately.':'No matching guarded capture. Use the Live bridge to capture this scene, then reopen this view.';snapshot.append(captureNote);
    if(captured?.available)appendResourceTable(snapshot,['Epoch-scoped node','Captured word','Set bit indices'],captured.nodes.map(node=>[node.id,node.value_hex,node.set_bits.join(', ')||'None']),'No supported flag fields in this capture.');
    const pager=document.createElement('div');pager.className='dialog-actions';pager.innerHTML='<button aria-label="Previous flag page">Previous</button><span role="status"></span><button aria-label="Next flag page">Next</button>';list.before(pager);
    const previous=pager.querySelector('button'),next=pager.querySelector('button:last-child'),pageStatus=pager.querySelector('span');let page=0;
    const render=()=>{
      const query=search.value.trim().toLowerCase(),groups=result.groups.filter(group=>[group.scene_name??'',group.id,group.script_name,group.bank,String(group.index),...group.references.flatMap(ref=>[ref.operation,ref.authored_index===null?'':String(ref.authored_index),String(ref.effective_index)])].join(' ').toLowerCase().includes(query));
      const pages=Math.max(1,Math.ceil(groups.length/100));page=Math.min(page,pages-1);const start=page*100,end=Math.min(start+100,groups.length);
      summary.textContent=`${projectWide?`${result.scenes.length} imported scenes (${result.scenes.filter(scene=>scene.status==='unavailable').length} unavailable) · `:''}${result.reference_count} encoded references (${result.authored_reference_count??0} authored) · ${result.groups.length} source-qualified groups · ${result.coverage.script_count} scripts (${result.coverage.partial_script_count} partial, ${result.coverage.unavailable_script_count} unavailable). Showing ${groups.length?start+1:0}–${end} of ${groups.length} matches. Groups use retail indices; references show authored/effective operands. Runtime values are unresolved.`;
      previous.disabled=page===0;next.disabled=page+1>=pages;pageStatus.textContent=`Page ${page+1} of ${pages}`;
      list.replaceChildren();
      for(const group of groups.slice(start,end)){
        const row=document.createElement('section');row.className='resource-provenance';
        row.innerHTML=`<h3>${projectWide?escapeHTML(group.scene_name)+' · ':''}${escapeHTML(group.bank)} ${escapeHTML(group.index)} · ${escapeHTML(group.script_name)}</h3><p>${escapeHTML(group.scope)} · ${escapeHTML(resourceLabel(group.script_status))} · ${group.extended_target===null?'Current script context':`Unresolved extended target ${escapeHTML(group.extended_target)}`}</p><p>${group.references.map(ref=>`${escapeHTML(scriptOffset(ref.pc))}: ${escapeHTML(ref.mnemonic)} (${escapeHTML(resourceLabel(ref.status))}) · Retail ${escapeHTML(ref.retail_index??ref.index)} · Authored ${ref.authored_index==null?'none':escapeHTML(ref.authored_index)} · Effective ${escapeHTML(ref.effective_index??ref.index)}`).join(' · ')}</p><button>Inspect source script</button><details><summary>Source provenance and encoded operands</summary><pre></pre></details>`;
        row.querySelector('pre').textContent=JSON.stringify(group,null,2);
        const inspect=async(pc=null)=>{if(busy||key!==flagContext(projectWide))return;flagsDialog.close();if(projectWide&&group.scene_id!==state.scene?.id&&!await api('/api/scene',{scene_id:group.scene_id}))return;const owner=group.partition===2?{id:group.owner_id,name:group.script_name,partitionTwo:true}:entities().find(entity=>entity.id===group.owner_id);if(!owner){notify('The source script owner is unavailable.',true);return;}flagsDialog.close();openActorScript(owner,false,null,null,pc);};
        row.querySelector('button').onclick=()=>inspect();
        const references=document.createElement('div');references.className='dialog-actions';
        for(const ref of group.references){const button=document.createElement('button');button.textContent=`Inspect ${scriptOffset(ref.pc)} · ${ref.mnemonic}`;button.onclick=()=>inspect(ref.pc);references.append(button);}
        row.querySelector('details').before(references);
        list.append(row);
      }
      for(const note of result.limitations??[]){const p=document.createElement('p');p.className='field-note';p.textContent=note;list.append(p);}
    };
    previous.onclick=()=>{page--;render();};next.onclick=()=>{page++;render();};search.oninput=()=>{page=0;render();};render();
  }catch(error){if(error.name!=='AbortError'&&flagsDialog.open)flagsDialog.querySelector('.dialog-error').textContent=error.message;}
  finally{if(flagsAbort===controller){flagsAbort=null;setBusy(false);}}
};
function synchronizeResources(){
  modelFaceRemovalEditor?.updateState();
  modelAllocationEditor?.updateState();
  modelFaceAdditionEditor?.updateState();
  modelVectorAllocationEditor?.updateState();modelVertexMoveEditor?.updateState();
  modelMeshAppendEditor?.updateState();
  modelGroupAllocationEditor?.updateState();
  modelObjectAllocationEditor?.updateState();
  modelPrimitiveEditor?.updateState();
  modelMaterialsEditor?.updateState();
  sceneAnimationController?.updateState();
  if(animationGlbEditor){if(selected()?.id!==animationGlbEntityId)animationGlbEditor.dispose();else animationGlbEditor.updateState();}
  if(animationAllocationEditor){if(selected()?.id!==animationAllocationEntityId)animationAllocationEditor.dispose();else animationAllocationEditor.updateState();}
  if(animationRecordLibrary){if(animationRecordAssetId===null&&selected()?.id!==animationRecordEntityId)animationRecordLibrary.dispose();else animationRecordLibrary.updateState();}
  if(retainedAnimationEditor){if(retainedAnimationAssetId===null&&selected()?.id!==retainedAnimationEntityId)retainedAnimationEditor.dispose();else retainedAnimationEditor.updateState();}
  if(retainedAnimationGlbEditor){if(retainedAnimationGlbAssetId===null&&selected()?.id!==retainedAnimationGlbEntityId)retainedAnimationGlbEditor.dispose();else retainedAnimationGlbEditor.updateState();}
  modelGlbEditor?.updateState();
  texturePngEditor?.updateState();
  textureResizeEditor?.update();
  textureSlotEditor?.update();
  if(transitionsDialog.open&&transitionsDialog.dataset.sourceContext!==transitionsContext(transitionsDialog.dataset.projectWide==='true'))transitionsDialog.close();
  if(flagsDialog.open&&flagsDialog.dataset.sourceContext!==flagContext(flagsDialog.dataset.projectWide==='true'))flagsDialog.close();
  if(textDialog.open&&textDialog.dataset.sourceContext!==textContextKey(textDialog.dataset.projectWide==='true'))textDialog.close();
  const current=resourceStateKey();
  if(resourceContextKey!==current){
    if(flagResourceDialog?.open)flagResourceDialog.close();
    if(transitionResourceDialog?.open)transitionResourceDialog.close();
    if(transitionsDialog.open)transitionsDialog.close();
    if(flagsDialog.open)flagsDialog.close();
    if(textDialog.open)textDialog.close();
    resourceContextKey=current;clearFieldSpatial();sceneResourceSelection=null;clearFieldMap();clearTriggerScript();if(fieldDialog.open)fieldDialog.close();
    resourceAbort?.abort();resourceRecords=[];resourceLimitations=[];resourceKey=null;resourcePendingKey=null;resourceError=null;
    if(textureDialog.open&&!(textureCommandPending&&textureSession?.projectKey===textureProjectKey()))textureDialog.close();if(animationResourceDialog.open)animationResourceDialog.close();if(scriptResourceDialog.open)scriptResourceDialog.close();
  }
  updateFieldToggle();
  transitionsButton.hidden=projectTransitionsButton.hidden=!state.capabilities?.scene_transitions;transitionsButton.disabled=projectTransitionsButton.disabled=busy||!state.capabilities?.scene_transitions;
  flagsButton.hidden=projectFlagsButton.hidden=!state.capabilities?.scene_flags;flagsButton.disabled=projectFlagsButton.disabled=busy||!state.capabilities?.scene_flags;
  textButton.hidden=!state.capabilities?.scene_text_search;textButton.disabled=busy||!state.capabilities?.scene_text_search;
  projectTextButton.hidden=!state.capabilities?.scene_text_search;projectTextButton.disabled=busy||!state.capabilities?.scene_text_search;
  $('resource-refresh').hidden=!state.capabilities?.resource_catalog;$('resource-refresh').disabled=busy||!state.capabilities?.resource_catalog;
  $('resource-status').textContent=!state.capabilities?.resource_catalog?'Resource catalog is unavailable in this service.':resourceError ?? (resourcePendingKey?'Verifying scene resources…':resourceKey?`${resourceRecords.length} verified resource records`:'Refresh to load textures, animations, scripts, dialogue, flag references, transitions and field-map metadata.');
}
async function refreshResources(){
  if(busy||!state.capabilities?.resource_catalog)return;
  clearFieldSpatial();sceneResourceSelection=null;clearFieldMap();clearTriggerScript();draw();
  const key=resourceStateKey(),sceneId=state.scene?.id,sourceKey=state.scene_preview_source_key,controller=new AbortController();
  resourceAbort?.abort();resourceAbort=controller;resourcePendingKey=key;resourceError=null;resourceRecords=[];resourceLimitations=[];resourceKey=null;setBusy(true);renderAssets();renderHierarchy();renderInspector();
  try{
    const response=await fetch('/api/resource-catalog',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',signal:controller.signal});
    const result=await response.json();if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Resource catalog verification failed');
    if(controller.signal.aborted||key!==resourceStateKey())return;
    if(result.scene_id!==sceneId||result.source_key!==sourceKey||result.flag_state_key!==state.scene_flag_state_key||result.transition_state_key!==state.scene_transition_state_key||result.region_state_key!==state.scene_region_state_key||result.trigger_state_key!==state.scene_trigger_state_key||!Array.isArray(result.records)||result.records.length>4096||new Set(result.records.map(record=>record.semantic_id)).size!==result.records.length||result.records.some(record=>typeof record.semantic_id!=='string'||!['audio','texture','animation','script','dialogue','flag','transition','collision','trigger','region','worldmap'].includes(record.asset_kind)))throw new Error('Resource catalog returned stale or invalid records.');
    for(const record of result.records){if(record.asset_kind==='flag')decodeFlagResource(record);else if(record.asset_kind==='transition')decodeTransitionResource(record);else if(record.scope==='authored-retained')decodeRetainedAnimationAsset(record);}
    resourceLimitations=result.limitations ?? [];resourceRecords=[...new Map(result.records.map(record=>[record.semantic_id,{...record,catalog_limitations:result.limitations}])).values()];resourceKey=key;resourcePendingKey=null;renderAssets();renderHierarchy();renderInspector();
  }catch(error){if(error.name!=='AbortError'&&key===resourceStateKey()){resourceError=error.message;notify(error.message,true);}}
  finally{if(resourceAbort===controller){resourceAbort=null;resourcePendingKey=null;}setBusy(false);synchronizeResources();}
}
function assetRecords(activeOnly=false){
  const projectScope=!activeOnly&&projectAssetControls?.scope()==='project';
  const records=new Map((projectScope?projectAssetControls.records():[
    ...(state.active_scene_assets ?? []).map(asset=>({id:asset.id,type:asset.kind ?? 'model',label:asset.name ?? asset.label ?? `Model ${asset.id.split('/').at(-1)}`,source:asset.source_record?.prot_entry_name ?? asset.scope ?? 'Imported',sceneId:asset.scene_id,data:asset})),
    ...entities().map(actor=>({id:actor.id,type:'actor',label:actor.name ?? actor.id,source:state.scene?.name ?? state.scene?.id,sceneId:state.scene?.id,data:actor})),
    ...(state.scenes ?? []).map(scene=>({id:scene.id,type:'scene',label:scene.name ?? scene.id,source:scene.name ?? scene.id,data:scene})),
    ...resourceRecords.map(record=>({id:record.semantic_id,type:record.asset_kind,label:record.name ?? record.semantic_id,source:record.scope?.startsWith('global-')?record.scope:(record.source_record?.prot_entry_name ?? state.scene?.name),sceneId:state.scene?.id,data:record}))
  ]).map(record=>[record.id,record]));
  for(const authored of state.authored_assets ?? []){
    if(typeof authored.id!=='string'||!['actor','model','texture','template','script','scene','worldmap'].includes(authored.kind))continue;
    const assetId=authored.kind==='script'?(authored.script_id ?? authored.id):authored.id,existing=records.get(assetId);
    if(activeOnly&&!existing&&authored.scene_id&&authored.scene_id!==state.scene?.id)continue;
    if(projectScope&&projectAssetControls.filter()!=='all'&&!existing&&authored.scene_id!==projectAssetControls.filter())continue;
    records.set(assetId,{...(existing ?? {id:assetId,type:authored.kind,label:authored.name ?? authored.id,source:authored.source_scene ?? authored.scene_id ?? 'Project library',data:{source_record:authored.source_record}}),sceneId:existing?.sceneId??authored.scene_id,authored:authored.authored ?? {},changes:authored.changes ?? [],authoredRecord:authored});
  }
  return [...records.values()];
}
function initialAssetUsage(record,modelReferences){
  if(record.type==='model')return modelReferences.filter(ref=>ref.target_id===record.id);
  if(record.type!=='animation')return [];
  const bindings=record.data?.bindings??[],references=new Map();
  for(const ref of modelReferences){
    const imported=ref.imported&&bindings.some(binding=>binding.actor_semantic_id===ref.source_id&&binding.model_asset_semantic_id===ref.target_id);
    const effective=ref.effective&&bindings.some(binding=>binding.actor_semantic_id===ref.effective_donor_id&&binding.model_asset_semantic_id===ref.target_id);
    if(!imported&&!effective)continue;
    const previous=references.get(ref.source_id);
    references.set(ref.source_id,{source_id:ref.source_id,scene_id:ref.scene_id,source_name:ref.source_name,kind:ref.kind,
      imported:!!(imported||previous?.imported),effective:!!(effective||previous?.effective)});
  }
  return [...references.values()];
}
function showAssetDetails(record,lookup=()=>assetRecords()){
  assetPlacementSelection?.dispose();assetPlacementSelection=null;animationContributions?.dispose();animationContributions=null;
  const isAuthored=!!record.authoredRecord,inspectorId=assetInspectorDefinition(state.inspector_schema,record);
  assetDetails.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-asset-details" aria-label="Close asset details">×</button></div>${inspectorId?'':property('Stable ID',record.id)+property('Record type',record.type)+property(record.data?.scope?.startsWith('global-')?'Source scope':'Source scene',record.authoredRecord?.source_scene ?? record.source)}${isAuthored?`<section class="asset-authored-details"><h3>Authored project settings</h3><p>${escapeHTML(record.changes.join(' · ') || 'Authored project metadata')}</p><pre class="diagnostic-detail" id="asset-authored-data"></pre><button id="open-authored-asset">${record.type==='template'?'Open template library':record.type==='texture'?'Inspect texture':record.type==='model'?'Inspect authored model':record.type==='script'?'Open script workspace':record.type==='scene'?'Open scene':'Select actor'}${record.type!=='template'&&record.sceneId!==state.scene?.id?' in source scene':''}</button></section>`:''}<details ${isAuthored?'':'open'}><summary>${isAuthored?'Imported source provenance':'SDK source and provenance'}</summary><pre id="asset-source-data" class="diagnostic-detail"></pre></details>`;
  const exportContext=resourceStateKey(),exportSnapshot=JSON.stringify(record);
  const exportCurrent=()=>assetDetails.open&&exportContext===resourceStateKey()&&JSON.stringify(lookup().find(item=>item.id===record.id))===exportSnapshot;
  const evidence=document.createElement('div');evidence.className='dialog-actions';evidence.style.flexWrap='wrap';
  try{mountAssetRecordDownload(evidence,{record,getState:()=>state,current:exportCurrent,busy:()=>busy,onError:error=>notify(error.message,true)});}catch(error){const note=document.createElement('p');note.className='field-note';note.textContent=error.message;evidence.append(note);}
  try{mountAssetMetadataComparison(evidence,{record,getState:()=>state,current:exportCurrent,busy:()=>busy,pin:assetMetadataPin,onError:error=>notify(error.message,true)});}catch(error){const note=document.createElement('p');note.className='field-note';note.textContent=error.message;evidence.append(note);}
  $('asset-source-data').parentElement.before(evidence);
  if(record.type!=='template'&&state.build_review_source_key){const button=document.createElement('button');button.textContent='Inspect saved Build records...';button.dataset.assetBuildHistory='';button.onclick=()=>{if(busy||!exportCurrent())return;assetDetails.close();openAssetBuildHistory({record,getState:()=>state,current:()=>exportContext===resourceStateKey()&&JSON.stringify(lookup().find(item=>item.id===record.id))===exportSnapshot,busy:()=>busy,setBusy,onError:error=>notify(error.message,true)});};evidence.append(button);}
  if(record.type==='model')assetPlacementSelection=mountModelPlacementUsers(evidence,{assetId:record.id,current:exportCurrent,busy:()=>busy,
    getContext:()=>canSelectHierarchyMatches()&&scenePreviewCurrent()&&sceneRepresentation==='authored'&&!wallSelectMode?{projectPath:state.project.path,sceneId:state.scene.id,sourceKey:state.scene_preview_source_key,projectSourceKey:state.project_copy_source_key,rows:activeScenePreview().entities,eligible:scenePlacementEligible()}:null,
    onSelect:async(ids,current)=>{const active=visibilitySelection(),focus=ids.includes(active)?active:ids[0];if(await selectCurrentModelPlacementGroup(record.id,focus,current)&&current())assetDetails.close();},onError:error=>notify(error.message,true)});
  if(record.type==='animation')assetPlacementSelection=mountAnimationPlacementUsers(evidence,{assetId:record.id,current:exportCurrent,busy:()=>busy,
    getContext:()=>canSelectHierarchyMatches()&&scenePreviewCurrent()&&sceneRepresentation==='authored'&&!wallSelectMode?{projectPath:state.project.path,sceneId:state.scene.id,sourceKey:state.scene_preview_source_key,projectSourceKey:state.project_copy_source_key,rows:entities(),eligible:scenePlacementEligible(),drafts:state.actor_drafts,references:state.model_references.filter(ref=>ref.scene_id===state.scene.id),bindings:record.data?.bindings??[]}:null,
    onSelect:async(ids,current)=>{const active=visibilitySelection(),focus=ids.includes(active)?active:ids[0];const held=()=>current()&&JSON.stringify(ids)===JSON.stringify(currentAnimationPlacementIds({rows:entities(),eligible:scenePlacementEligible(),sceneId:state.scene.id,drafts:state.actor_drafts,references:state.model_references.filter(ref=>ref.scene_id===state.scene.id),bindings:record.data?.bindings??[]},record.id));if(await selectCurrentPlacementGroup(ids,focus,held)&&held())assetDetails.close();},onError:error=>notify(error.message,true)});
  if(record.type==='animation'&&record.data?.source_record?.record_sha256)animationContributions=mountAnimationContributions(evidence,{record,current:exportCurrent,busy:()=>busy,getContext:()=>({projectPath:state.project.path,sceneId:state.scene.id,sourceKey:state.project_copy_source_key,entities:entities()}),onSelect:async(owner,current)=>{const okay=await selectCurrentPlacementGroup([owner],owner,current);if(okay&&current())assetDetails.close();return okay;},onError:error=>notify(error.message,true)});
  const source=isAuthored?(record.authoredRecord.source_record ?? record.data?.source_record ?? record.data?.components?.RetailMetadata ?? {note:'No additional imported provenance is attached to this authored record.'}):record.data;
  $('asset-source-data').textContent=JSON.stringify(source,null,2);
  if(record.projectMembership){
    const membership=document.createElement('section'),label=document.createElement('label'),choice=document.createElement('select'),note=document.createElement('p');
    const authoredNpc=record.data?.layer==='authored'&&record.authoredRecord?.draft===true;
    membership.dataset.projectAssetMembership='';label.textContent=authoredNpc?'Authored NPC owning scene':'Imported source membership';choice.setAttribute('aria-label',label.textContent);
    for(const variant of record.projectMembership.variants){const option=document.createElement('option');option.value=variant.scene_id;option.textContent=(state.scenes??[]).find(scene=>scene.id===variant.scene_id)?.name??variant.scene_id;choice.append(option);}
    choice.value=record.sceneId;choice.disabled=busy||record.projectMembership.variants.length<2||projectAssetControls?.filter()!=='all';
    note.className='field-note';note.textContent=authoredNpc?'This authored NPC belongs to the selected project scene. The import hash identifies scene context, not a retail origin for this draft; membership does not prove runtime spawning or visibility.':'Each source membership retains its own recorded bindings and provenance. Choose a source before opening its inspector; membership does not prove runtime use.';
    const key=record.projectMembership.sourceKey;
    choice.onchange=()=>{if(busy||key!==state.project_assets_source_key||!projectAssetControls?.chooseVariant(record.id,choice.value))return;const next=assetRecords().find(item=>item.id===record.id);if(next){assetDetails.close();showAssetDetails(next);}};
    label.append(choice);membership.append(label,note);$('asset-source-data').parentElement.before(membership);
  }
  if(state.capabilities?.asset_references&&record.type!=='template'){
    const button=document.createElement('button');button.textContent='Inspect asset references…';button.id='inspect-asset-references';const key=state.asset_reference_source_key;
    button.onclick=()=>{if(busy||key!==state.asset_reference_source_key)return;assetDetails.close();openAssetReferences({record,initialScope:record.sceneId&&record.sceneId!==state.scene?.id?'project':'active',getState:()=>state,busy:()=>busy,onError:error=>notify(error.message,true),onNavigate:async node=>{
      if(!node.available||!(state.scenes??[]).some(scene=>scene.id===node.scene_id))throw new Error('Reference source scene is not imported.');
      if(node.scene_id!==state.scene?.id&&!await api('/api/scene',{scene_id:node.scene_id}))return;
      if(node.kind==='audio'&&node.id.startsWith('audio-input://legaia/midi/')){openMidiInput({record:{id:node.id},getContext:()=>({assetId:node.id,projectPath:state.project?.path,sourceKey:state.project_assets_source_key}),busy:()=>busy,onError:error=>notify(error.message,true)});return;}
      if(node.kind==='audio'&&node.id.startsWith('audio-input://legaia/wav/')){openAudioInput({record:{id:node.id},getContext:()=>({assetId:node.id,projectPath:state.project?.path,sourceKey:state.project_assets_source_key}),busy:()=>busy,onError:error=>notify(error.message,true)});return;}
      if(!['actor','model','scene'].includes(node.kind))await refreshResources();
      const target=assetRecords().find(item=>item.id===node.id);if(!target)throw new Error('Referenced asset is absent from the current catalog.');showAssetDetails(target);
    },onInspectInstruction:async site=>{
      if(!state.capabilities?.actor_script_preview||!(state.scenes??[]).some(scene=>scene.id===site.scene_id))throw new Error('Reference script source is not available in this project.');
      if(site.scene_id!==state.scene?.id&&!await api('/api/scene',{scene_id:site.scene_id}))return;
      await refreshResources();
      if(state.scene?.id!==site.scene_id||resourceKey!==resourceStateKey())throw new Error('Reference source catalog could not be refreshed.');
      const record=resourceRecords.find(row=>row.semantic_id===site.script_id);
      qualifyAssetReferenceInstructionSite(site,record,state.scene_preview_source_key);
      const owner=site.partition===2?{id:site.owner_id,name:record.name,partitionTwo:true}:entities().find(entity=>entity.id===site.owner_id);
      if(!owner)throw new Error('Reference script owner is unavailable.');
      await openActorScript(owner,false,null,null,site.pc);
    }});};$('asset-source-data').parentElement.before(button);
  }
  if(inspectorId){
    const section=document.createElement('section');section.dataset.assetInspector=record.type;
    const context=resourceStateKey(),snapshot=JSON.stringify(record),contract=JSON.stringify([state.inspector_schema,state.capabilities]);
    const current=()=>assetDetails.open&&context===resourceStateKey()&&contract===JSON.stringify([state.inspector_schema,state.capabilities])&&JSON.stringify(lookup().find(item=>item.id===record.id))===snapshot;
    mountAssetInspector(section,{schema:state.inspector_schema,record,capabilities:state.capabilities,current,busy:()=>busy,
      activate:async (item,action)=>{if(!current())return;assetDetails.close();if(action==='inspect-landmark-destination'){const label=item.data?.destination_source_label;if(!label)return;$('import-button').click();$('catalog-prefix').value=label;clearSceneCatalog();$('catalog-search').click();}else await activateAsset(item,action);},onError:error=>notify(error.message,true)});
    const triggerBindingInspector=mountTriggerBindingInspector(section,{record,getState:()=>state,current,busy:()=>busy,onInspect:async node=>{
      if(!current())return;const target=lookup().find(item=>item.id===node.id&&item.type==='script'&&item.sceneId===state.scene?.id);
      if(!target)throw new Error('Source script is absent from the current catalog. Refresh resources.');
      assetDetails.close();await openActorScript({id:target.data.owner_semantic_id,name:target.label,partitionTwo:true});
    }});
    if(triggerBindingInspector)assetDetails.addEventListener('close',triggerBindingInspector.dispose,{once:true});
    $('asset-source-data').parentElement.before(section);
    $('asset-source-data').parentElement.open=false;
    // These record types use the SDK inspector tool rather than a duplicate authored button.
    const old=$('open-authored-asset');if(old)old.remove();
  }

  if(['model','animation'].includes(record.type)){
    const usage=document.createElement('section');usage.innerHTML=`<h3>Used by</h3><p>${record.type==='model'?'Initial model assignments across imported scenes.':'Verified initial animation bindings and authored donor assignments.'} Scripts may change these assignments during gameplay.</p>`;
    const references=initialAssetUsage(record,state.model_references??[]),usageContext=modelUsageContext(state);
    for(const ref of references){const button=document.createElement('button');Object.assign(button.style,{maxWidth:'100%',whiteSpace:'normal',overflowWrap:'anywhere',textAlign:'left'});button.textContent=`${ref.source_name??ref.source_id} · ${ref.kind==='draft_initial_model_assignment'?'NPC draft':`${ref.imported?'Imported':''}${ref.imported&&ref.effective?' + ':''}${ref.effective?'Effective':''}`}`;button.title=ref.source_id;button.onclick=async()=>{if(busy||usageContext!==modelUsageContext(state))return;assetDetails.close();if(ref.scene_id!==state.scene?.id&&!await api('/api/scene',{scene_id:ref.scene_id}))return;if(ref.kind==='draft_initial_model_assignment'){selectNpcDraft(ref.source_id);frameNpcDraft();}else if(await api('/api/selection',{entity_id:ref.source_id}))frame(selected());};usage.append(button);}
    if(!references.length){const empty=document.createElement('p');empty.textContent='No imported or effective initial actor assignments in this project.';usage.append(empty);}
    if(record.type==='model'){
      const groups=(state.scenes??[]).map(scene=>({scene,ids:effectiveModelUsers(state,record.id,scene.id)})).filter(row=>row.ids.length>=2&&row.ids.length<=128);
      if(groups.length){
        const controls=document.createElement('div');controls.className='dialog-actions';
        const choice=document.createElement('select');choice.setAttribute('aria-label','Scene of effective model users');
        for(const group of groups){const option=document.createElement('option');option.value=group.scene.id;option.textContent=`${group.scene.name} · ${group.ids.length} effective actors`;choice.append(option);}
        const selectGroup=document.createElement('button');selectGroup.textContent='Select effective actor users';selectGroup.dataset.selectModelUsers='true';selectGroup.disabled=busy||!canEdit();
        selectGroup.onclick=async()=>{
          if(busy||!canEdit()||scenePose||actorGroupInspection||shapeDraft)return;
          try{
            const sceneId=choice.value,expected=groups.find(group=>group.scene.id===sceneId)?.ids;
            if(!expected||usageContext!==modelUsageContext(state))throw new Error('Model usage changed; reopen the asset details');
            const response=await fetch('/api/state'),fresh=await response.json();if(!response.ok||fresh.project?.mode!=='edit'||usageContext!==modelUsageContext(fresh))throw new Error('Model usage changed; refresh the project and reopen the asset');
            assetDetails.close();
            if(sceneId!==state.scene.id&&!await api('/api/scene',{scene_id:sceneId}))return;
            validateModelUserSelection(state,record.id,sceneId,expected);
            if(!await api('/api/selection',{entity_id:expected[0]}))return;
            if(!canEdit()||usageContext!==modelUsageContext(state))throw new Error('Model usage changed during selection');
            const ids=validateModelUserSelection(state,record.id,sceneId,expected);
            actorGroupSelection=mergeActorGroupSelection([],ids,entities().map(entity=>entity.id));actorGroupSelectionKey=resourceStateKey();actorGroupRangeAnchor=ids[0];cancelViewportGesture();renderHierarchy();frameActorGroupSelection();draw();
            notify(`Selected ${ids.length} effective actor users. Scripts may replace initial assignments.`);
          }catch(error){notify(error.message,true);}
        };
        controls.append(choice,selectGroup);usage.append(controls);
        const note=document.createElement('p');note.className='field-note';note.textContent='Selects effective initial model users in one imported scene for existing group tools. Retail-only users and authored NPC drafts remain separate. No component is authored.';usage.append(note);
      }
    }

    $('asset-source-data').parentElement.before(usage);
  }
  if(isAuthored){$('asset-authored-data').textContent=JSON.stringify(record.authored,null,2);if($('open-authored-asset'))$('open-authored-asset').onclick=()=>{assetDetails.close();activateAsset(record);};}
  if(record.authoredRecord?.component_reviews?.length){
    const section=document.createElement('section'),title=document.createElement('h3'),note=document.createElement('p');
    title.textContent='Review authored components';note.textContent='Revert removes every authored setting in the chosen component. Imported data stays available; other components stay authored. Undo restores the removed settings. Shared animation and scenery changes can affect other instances.';
    section.append(title,note);
    const projectPath=state.project?.path;
    for(const review of record.authoredRecord.component_reviews){
      const details=document.createElement('details'),summary=document.createElement('summary'),data=document.createElement('pre'),button=document.createElement('button');
      summary.textContent=review.component;data.className='diagnostic-detail';data.textContent=JSON.stringify(review.authored,null,2);
      button.type='button';button.dataset.revertComponent=review.component;button.textContent=`Revert ${review.component} component`;button.disabled=busy||!canEdit();
      button.onclick=async()=>{
        if(busy||!canEdit()||!assetDetails.open||projectPath!==state.project?.path)return;
        if(await api('/api/command',{type:'revert_authored_component',entity_id:record.authoredRecord.id,component:review.component,review_key:review.review_key},{success:`${review.component} reverted. Undo can restore it.`})){
          if(!assetDetails.open||projectPath!==state.project?.path)return;
          assetDetails.close();const current=assetRecords().find(item=>item.authoredRecord?.id===record.authoredRecord.id);
          if(current)showAssetDetails(current);
        }
      };
      details.append(summary,data,button);section.append(details);
    }
    $('asset-authored-data').before(section);
  }
  if(isAuthored&&record.type==='actor'&&record.authored?.AnimationChannels){
    const actions=document.createElement('div');actions.className='dialog-actions';
    for(const [label,preview] of [['Edit animation channels',false],['Preview authored animation',true]]){
      const button=document.createElement('button');button.textContent=label;button.disabled=busy||(!preview&&state.project.mode!=='edit');
      button.onclick=async()=>{
        if(busy)return;assetDetails.close();
        if(record.sceneId!==state.scene?.id&&!await api('/api/scene',{scene_id:record.sceneId}))return;
        if(!await api('/api/selection',{entity_id:record.id}))return;
        const actor=selected();if(!actor)return;
        if(preview)await openModel(actor.components.ModelRenderer.asset_id,'authored-channels',actor.id);
        else await openAnimationChannels(actor);
      };actions.append(button);
    }
    $('asset-authored-data').before(actions);
  }
  $('close-asset-details').onclick=()=>assetDetails.close();assetDetails.showModal();assetPlacementSelection?.synchronize();animationContributions?.synchronize();
}
function projectAssetContext(){return state.capabilities?.project_assets?{projectPath:state.project.path,sourceKey:state.project_assets_source_key,scenes:(state.scenes??[]).map(({id,name})=>({id,name})),activeSceneId:state.scene?.id??null}:null;}
async function resolveProjectAsset(record){
  if(!record.projectMembership)return record;
  const variant=projectAssetVariant(record,projectAssetContext()),expected=record.projectMembership.sourceKey;
  if(record.sceneId!==state.scene?.id&&!await api('/api/scene',{scene_id:record.sceneId}))return null;
  if(expected!==state.project_assets_source_key)throw new Error('Project sources changed during navigation. Refresh project resources.');
  if(variant.source_catalog_key!==null){
    await refreshResources();
    if(resourceKey!==resourceStateKey())throw new Error('The selected source catalog could not be verified. Refresh scene resources and retry.');
    const fresh=resourceRecords.find(row=>row.semantic_id===record.id&&row.asset_kind===record.type);
    qualifyProjectCatalogVariant(variant,fresh,state.scene_preview_source_key);
  }
  const current=assetRecords().find(row=>row.id===record.id);
  if(!current?.projectMembership||current.sceneId!==variant.scene_id||current.projectMembership.sourceKey!==expected)throw new Error('The selected source membership is no longer current. Refresh project resources.');
  return current;
}
async function activateAsset(record,action=null){
  if(busy)return;
  try{record=await resolveProjectAsset(record);if(!record)return;}catch(error){notify(error.message,true);return;}
  if(record.data?.source_kind==='retained_midi_input'&&(action==='inspect-midi-input'||action===null)){openMidiInput({record,getContext:()=>({assetId:record.id,projectPath:state.project?.path,sourceKey:state.project_assets_source_key}),busy:()=>busy,onError:error=>notify(error.message,true)});return;}
  if(action==='inspect-audio-input'||action===null&&record.data?.source_kind==='retained_wav_input'){openAudioInput({record,getContext:()=>({assetId:record.id,projectPath:state.project?.path,sourceKey:state.project_assets_source_key}),busy:()=>busy,onError:error=>notify(error.message,true)});return;}
  if(action==='inspect-audio-bank'){openAudioBank({record,canEdit:()=>state.project?.mode==='edit',apply:api,getAuthoringKey:()=>state.project_copy_source_key,getContext:()=>({assetId:record.id,sceneId:state.scene?.id,projectPath:state.project?.path,sourceKey:state.scene_preview_source_key,entryHash:record.data?.source_record?.sha256,bankHash:record.data?.bank_inspection?.bank_sha256}),busy:()=>busy,onError:error=>notify(error.message,true)});return;}
  if(action==='edit-sequence-replacement'){if(canEdit())openSequenceReplacement({getContext:()=>({assetId:record.id,entryHash:record.data?.source_record?.sha256,sceneId:state.scene?.id,authoringKey:state.project_copy_source_key,projectPath:state.project?.path}),busy:()=>busy,canEdit,apply:api,onError:error=>notify(error.message,true)});return;}
  if(action==='inspect-audio-sequence'){openAudioSequence({record,getContext:()=>({assetId:record.id,sceneId:state.scene?.id,projectPath:state.project?.path,sourceKey:state.scene_preview_source_key,entryHash:record.data?.source_record?.sha256}),busy:()=>busy,canEdit,apply:api,getAuthoringKey:()=>state.project_copy_source_key,onError:error=>notify(error.message,true)});return;}
  if(action==='edit-npc-appearance'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC appearance target changed. Reopen Asset Details.');openNpcAppearanceInspector(record.id);return;}
  if(action==='edit-npc-dialogue'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC dialogue target changed. Reopen Asset Details.');openNpcDialogue({entityId:record.id,getState:()=>state,isBusy:()=>busy,canEdit,api});return;}
  if(action==='reset-npc-script'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC reset target changed. Reopen Asset Details.');openNpcScriptReset({entityId:record.id,getState:()=>state,isBusy:()=>busy,canEdit,api});return;}
  if(action==='edit-npc-animation-operands'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw Error('NPC animation target changed. Reopen Asset Details.');openNpcAnimationOperands({entityId:record.id,getState:()=>state,isBusy:()=>busy,canEdit,api});return;}
  if(action==='edit-npc-effect-colors'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC color target changed. Reopen Asset Details.');openNpcEffectColors({entityId:record.id,getState:()=>state,isBusy:()=>busy,canEdit,api});return;}
  if(action==='edit-npc-transitions'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC arrival target changed. Reopen Asset Details.');openNpcTransitions({entityId:record.id,getState:()=>state,isBusy:()=>busy,canEdit,api,onPreview:openNpcArrivalDestination});return;}
  if(action==='edit-npc-facing'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC facing target changed. Reopen Asset Details.');openNpcFacing({entityId:record.id,getState:()=>state,isBusy:()=>busy,canEdit,api});return;}
  if(action==='edit-npc-model-selectors'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC model selector target changed. Reopen Asset Details.');openNpcModelSelectors({entityId:record.id,getState:()=>state,isBusy:()=>busy,canEdit,api});return;}
  if(action==='edit-npc-system-flags'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC system selector target changed. Reopen Asset Details.');openNpcSystemFlags({entityId:record.id,getState:()=>state,isBusy:()=>busy,canEdit,api});return;}
  if(action==='edit-npc-flags'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC flags target changed. Reopen Asset Details.');openNpcFlags({entityId:record.id,getState:()=>state,isBusy:()=>busy,canEdit,api});return;}
  if(action==='edit-npc-branches'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC branches target changed. Reopen Asset Details.');openNpcBranches({entityId:record.id,getState:()=>state,isBusy:()=>busy,canEdit,api});return;}
  if(action==='edit-npc-waits'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC waits target changed. Reopen Asset Details.');openNpcWaits({entityId:record.id,getState:()=>state,isBusy:()=>busy,canEdit,api});return;}
  if(action==='edit-npc-movement'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC script movement target changed. Reopen Asset Details.');openNpcMovement({entityId:record.id,getState:()=>state,isBusy:()=>busy,canEdit,api,showTargets:showNpcMovementTargets});return;}
  if(action==='inspect-npc-build-script'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC Build target changed. Reopen Asset Details.');openNpcBuildScript({entityId:record.id,getState:()=>state,isBusy:()=>busy,renderInstructions:appendScriptInstructions});return;}
  if(action==='inspect-npc-current-script'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('Current NPC target changed. Reopen Asset Details.');openNpcCurrentScript({entityId:record.id,getState:()=>state,isBusy:()=>busy,renderInstructions:appendScriptInstructions,showTargets:showNpcMovementTargets,onPreviewArrival:openNpcArrivalDestination,canEdit,api});return;}
  if(action==='inspect-npc-donor-script'){const donor=npcDonorScript(record);if(!donor||state.actor_drafts?.[record.id]?.donor_entity_id!==donor||state.actor_drafts[record.id].scene_id!==state.scene?.id)throw new Error('NPC retail donor changed. Reopen Asset Details.');openNpcDonorScript({entityId:record.id,getState:()=>state,isBusy:()=>busy,renderInstructions:appendScriptInstructions});return;}
  if(action==='inspect-npc-donor-model'){const model=npcDonorModel(record);if(!model||!state.model_references?.some(ref=>ref.source_id===record.id&&ref.target_id===model&&ref.scene_id===record.sceneId&&ref.kind==='draft_initial_model_assignment'&&ref.effective_donor_id===(record.authoredRecord.authored?.appearance?.donor_entity_id??record.authoredRecord.donor_entity_id)))throw new Error('NPC donor model assignment changed. Reopen Asset Details.');openModel(model,null,null,'imported');return;}
  if(action==='inspect-asset-region-bounds'){await inspectRegionBounds(record);return;}
  if(action==='inspect-asset-trigger-cells'){await inspectTriggerCells(record);return;}
  if(action==='inspect-asset-trigger-scripts'){await inspectTriggerScripts(record);return;}
  if(action==='inspect-asset-trigger-group'){await inspectTriggerGroup(record);return;}
  if(record.type==='worldmap'){if(/^worldmap:\/\/map0[123]\/placements$/.test(record.id))worldPlacementControls?.open(record.id.split('/')[2]);else await worldmapControls?.open(record.id==='worldmap://legaia/menu'?null:record.id);return;}
  if(record.type==='template'){showTemplates();return;}
  if(record.authoredRecord&&['actor','texture','script','model'].includes(record.type)&&record.sceneId!==state.scene?.id){
    if(!record.sceneId){notify('This authored item does not identify an imported source scene.',true);return;}
    if(!await api('/api/scene',{scene_id:record.sceneId}))return;
  }
  if(record.type==='script'&&record.authoredRecord){
    await openActorScript({id:record.authoredRecord.id,name:record.label,partitionTwo:true});
  }else if(record.type==='actor'&&record.authoredRecord?.draft){
    selectNpcDraft(record.id);frameNpcDraft();document.querySelector('.workspace-tabs [data-panel="viewport"]').click();
  }else if(record.type==='actor'){
    if(await api('/api/selection',{entity_id:record.id})){frame(selected());document.querySelector('.workspace-tabs [data-panel="viewport"]').click();}
  }else if(record.type==='scene'){
    if(await api('/api/scene',{scene_id:record.id}))document.querySelector('.workspace-tabs [data-panel="viewport"]').click();
  }else if(record.type==='model')openModel(record.id,null,null,record.authoredRecord?'authored':'imported');
  else if(record.type==='texture')openTexture(record);
  else if(record.type==='animation')openAnimationResource(record);
  else if(['collision','trigger','region'].includes(record.type))openFieldResource(record);
  else if(['script','dialogue'].includes(record.type))openScriptResource(record);
  else if(record.type==='flag')inspectFlagResource(record);
  else if(record.type==='transition')inspectTransitionResource(record);
  else showAssetDetails(record);
}
async function openGraphTransitionEntry(edge,root,projectKey){
  const current=()=>root===state.project?.path&&projectKey===state.project_transition_state_key&&state.project?.mode==='edit';
  try{if(busy||!current())return;if(edge.source!==state.scene?.id&&!await api('/api/scene',{scene_id:edge.source}))return;if(!current()||state.scene?.id!==edge.source)throw new Error('Project or transition graph changed during source navigation.');
    await refreshResources();if(busy||!current()||state.scene?.id!==edge.source||resourceKey!==resourceStateKey())throw new Error('Fresh source resources are unavailable. Refresh the transition graph.');
    const record=assetRecords().find(row=>row.id===edge.id);qualifyTransitionGraphEntry(edge,record);inspectTransitionResource(record);
  }catch(error){notify(error.message,true);}
}
function inspectFlagResource(record){
  if(busy||resourceKey!==resourceStateKey())return;
  const context=resourceStateKey(),snapshot=JSON.stringify(record);
  const current=()=>context===resourceStateKey()&&resourceKey===context&&JSON.stringify(assetRecords().find(item=>item.id===record.id))===snapshot;
  const data=decodeFlagResource(record.data),owner=data.partition===2?{id:data.owner_id,name:data.script_name,partitionTwo:true}:entities().find(entity=>entity.id===data.owner_id);
  flagResourceDialog=openFlagResource({record,current,busy:()=>busy,canInspect:()=>!!owner&&state.capabilities?.actor_script_preview===true,
    onInspect:async pc=>{if(!current()||busy||!owner)return false;await openActorScript(owner,false,null,null,pc);return true;},onError:error=>notify(error.message,true)});
}
function inspectTransitionResource(record){
  if(busy||resourceKey!==resourceStateKey())return;
  const context=resourceStateKey(),snapshot=JSON.stringify(record);
  const current=()=>context===resourceStateKey()&&resourceKey===context&&JSON.stringify(assetRecords().find(item=>item.id===record.id))===snapshot;
  try{
    const data=decodeTransitionResource(record.data),owner=data.partition===2?{id:data.owner_id,name:data.script_name,partitionTwo:true}:entities().find(entity=>entity.id===data.owner_id);
    const canNavigate=target=>state.capabilities?.project_navigation===true&&(state.scenes??[]).some(scene=>scene.id===target);
    transitionResourceDialog=openTransitionResource({record,current,busy:()=>busy,canInspect:()=>!!owner&&state.capabilities?.actor_script_preview===true,canNavigate,
      onInspect:async pc=>{if(!current()||busy||!owner)return false;await openActorScript(owner,false,null,null,pc);return scriptDialog.open&&scriptEntity?.id===owner.id;},
      onNavigate:async target=>{if(!current()||busy||!canNavigate(target))return false;transitionResourceDialog?.close();return !!await api('/api/scene',{scene_id:target});},
      canPreview:()=>state.project?.mode==='edit'&&state.capabilities?.scene_preview===true,
      onPreview:async()=>{
        if(!current()||busy||!canNavigate(data.target)||state.project?.mode!=='edit')return false;
        const sourceKey=state.scene_preview_source_key,projectKey=state.project_transition_state_key;setBusy(true);
        try{
          const response=await fetch('/api/transition-arrival-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:record.id,source_key:sourceKey})}),value=await response.json();
          if(!current()||!transitionResourceDialog?.open)return false;if(!response.ok)throw new Error(value.error||'Arrival inspection failed');
          const report=decodeTransitionArrivalPreview(value,record.id,sourceKey,projectKey);
          transitionResourceDialog.close();setBusy(false);if(!await api('/api/scene',{scene_id:report.destination_scene_id}))return false;
          if(!transitionArrivalCurrent(report,state))throw new Error('Destination arrival context changed. Reopen the source transition.');
          document.querySelector('.workspace-tabs [data-panel="viewport"]').click();transitionArrivalOverlay=report;transitionArrivalHeight=0;transitionArrivalTools.querySelector('input').value='0';transitionArrivalTools.querySelector('input').removeAttribute('aria-invalid');setBusy(false);discardArrivalDraft();frameTransitionArrival();return true;
        }finally{setBusy(false);draw();}
      },
      onError:error=>notify(error.message,true)});
  }catch(error){notify(error.message,true);}
}
function renderAssets(){
  const assetFocus=assetNavigation.beforeRender();
  synchronizeResources();
  const projectScope=projectAssetControls?.scope()==='project';
  const list=$('assets'),category=$('asset-category').value;let query=[],searchError=null;try{query=parseAssetQuery($('asset-search').value);}catch(error){searchError=error.message;}
  $('asset-search').setAttribute('aria-invalid',String(!!searchError));
  assetScope.querySelector('p').textContent=`Models and actors come from the active imported scene; shared models retain that scene’s source variant. Scenes lists imported scenes. Authored assets gathers project-wide NPC drafts, actor edits, script dialogue edits, model and texture replacements and transform templates without a resource refresh. Refresh adds scene texture candidates, referenced scene-header animations and saved retained clips, actor and partition-two scripts, dialogue, source-scoped flag reference groups, decoded transition assets and supported field-map metadata; it also lists global world-map menu records and eight supported shared field clips, without claiming current actor playback or complete runtime coverage. ${state.capabilities?.actor_script_preview?'Script inspection and supported dialogue text tools are available from an actor’s Inspector.':'Script and dialogue inspection is not available in this service.'} Audio lists supported global source VAB/SEQ headers and sound packs; scene playback, events and waveforms remain unverified. ${resourceLimitations.map(limit=>typeof limit==='string'?limit:JSON.stringify(limit)).join(' ')}`;
  if(projectScope)assetScope.querySelector('p').textContent='Project resources retain each recorded source scene and its provenance. Choose a source membership in Details before opening a shared asset. Discovery verifies imported sources without changing project data. Partial or unavailable coverage is listed above; residency, reachability and current playback remain unobserved.';
  const records=assetRecords(),filtered=searchError?[]:records.filter(record=>(category==='all'||(category==='authored'?(!!record.authoredRecord||record.data?.authored_animation_record===true):record.type===category&&(category!=='actor'||projectScope||record.sceneId===state.scene?.id)))&&assetMatchesQuery(record,query));
  list.replaceChildren();$('asset-count').textContent=records.length;$('asset-results').textContent=searchError??`${filtered.length} / ${records.length} records`;
  const pageSignature=JSON.stringify([projectScope,projectAssetControls?.filter(),state.project_assets_source_key,category,$('asset-search').value]);
  if(pageSignature!==assetPageSignature){assetPage=0;assetPageSignature=pageSignature;}
  const pages=Math.max(1,Math.ceil(filtered.length/128));assetPages=pages;assetPage=Math.min(assetPage,pages-1);
  assetPager.hidden=!projectScope;assetPrevious.disabled=busy||assetPage===0;assetNext.disabled=busy||assetPage>=pages-1;
  assetPageStatus.textContent=`Page ${assetPage+1} / ${pages} · ${filtered.length} matching assets`;
  const visible=projectScope?filtered.slice(assetPage*128,(assetPage+1)*128):filtered;
  for(const record of visible){
    const row=document.createElement('div');row.className='asset-result';row.dataset.assetKey=record.id;
    const card=document.createElement('button');card.className='asset-card';card.dataset.assetAction='open';card.title=record.id;card.innerHTML=`<strong>${escapeHTML(record.label)}${(record.authoredRecord||record.data?.authored_animation_record)?'<span class="asset-authored-badge">Authored</span>':''}</strong><small>${escapeHTML(record.type)} · ${escapeHTML(record.authoredRecord?.source_scene ?? record.source)}</small>${record.authoredRecord?`<span class="asset-change-summary">${escapeHTML(record.changes.join(' · ') || 'Authored project settings')}</span>`:''}<code>${escapeHTML(record.id)}</code>`;
    card.disabled=busy;card.onclick=()=>activateAsset(record);
    const info=document.createElement('button');info.className='asset-info';info.dataset.assetAction='details';info.textContent='ⓘ';info.title='View stable ID, source and provenance';info.setAttribute('aria-label',`Details for ${record.label}`);info.disabled=busy;info.onclick=()=>showAssetDetails(record);row.append(card,info);
    if(record.type==='model'){
      row.style.display='grid';row.style.gridTemplateColumns='minmax(0,1fr) 28px';
      const action=document.createElement('button');action.type='button';action.dataset.assetAction='placements';action.dataset.assetPlacementAction=record.id;action.style.cssText='grid-column:1 / -1;white-space:normal;text-align:left';action.setAttribute('aria-label','Select editable instances of '+record.id);
      const key=resourceStateKey(),snapshot=JSON.stringify(record),current=()=>key===resourceStateKey()&&record.sceneId===state.scene?.id&&JSON.stringify(assetRecords().find(row=>row.id===record.id))===snapshot;
      const members=()=>{if(!current()||!canSelectHierarchyMatches()||!scenePreviewCurrent()||sceneRepresentation!=='authored'||wallSelectMode)throw Error('Use the current authored scene with a qualified model source.');return modelPlacementIdsForAsset(activeScenePreview().entities,record.id,scenePlacementEligible());};
      action.refreshPlacementAction=()=>{action.disabled=true;action.textContent='Select editable instances';try{const ids=members();action.textContent=`Select editable instances (${ids.length})`;action.disabled=!ids.length;action.title='Includes qualified hidden placements; excludes unsupported source cells and runtime-only objects.';}catch(error){action.title=error.message;}};
      action.onclick=async()=>{if(action.disabled)return;try{const ids=members(),focus=ids.includes(visibilitySelection())?visibilitySelection():ids[0];if(await selectCurrentModelPlacementGroup(record.id,focus,current)){frameSceneSelection();document.querySelector('.workspace-tabs [data-panel="inspector"]').click();}}catch(error){notify(error.message,true);}};
      const assign=document.createElement('button');assign.type='button';assign.dataset.assetAction='appearance';assign.dataset.assetPlacementAction=record.id;assign.style.cssText='grid-column:1 / -1;white-space:normal;text-align:left';assign.textContent='Choose donor appearance';assign.setAttribute('aria-label','Choose donor appearance for '+record.id);
      assign.refreshPlacementAction=()=>{assign.disabled=busy||!current()||!canEditAppearance()||!selected()&&!selectedNpcDraft()||currentPlacementSelection().length>1&&actorGroupSelection.length<2;const target=actorGroupSelection.length>=2?{name:actorGroupSelection.length+' imported actors'}:selectedNpcDraft()??selected();assign.title=target?'Choose a verified model/animation donor pair for '+target.name:'Select one imported actor or NPC draft first.';};
      assign.onclick=()=>{if(assign.disabled||!current())return;if(actorGroupSelection.length>=2)actorGroupAppearance.open(record.id);else if(selectedNpcDraft())openNpcAppearanceInspector(npcDraftSelection,record.id);else openAppearanceOptions(selected(),record.id);};row.append(action,assign);
      const create=document.createElement('button');create.type='button';create.dataset.assetAction='create-npc';create.dataset.assetPlacementAction=record.id;create.style.cssText='grid-column:1 / -1;white-space:normal;text-align:left';create.textContent='Create NPC from model';create.setAttribute('aria-label','Create NPC from '+record.id);
      create.refreshPlacementAction=()=>{create.disabled=true;try{if(busy||!current()||!canEdit()||!state.capabilities?.actor_candidate_inspection)throw Error('Use a current imported model in Edit mode with the Project disc available.');const ids=retailModelDonors(state,record.id,record.sceneId);create.disabled=!ids.length;create.title=ids.length?`Choose from ${ids.length} Retail donors; script and initial animation are inherited. Placement is explicit.`:'No imported Retail actor uses this model in the active scene.';}catch(error){create.title=error.message;}};
      create.onclick=()=>{if(create.disabled||!current())return;try{openModelNpcCreation(record,current);}catch(error){notify(error.message,true);}};row.append(create);
    }
    list.append(row);
  }
  if(!filtered.length){const p=document.createElement('p');p.className='field-note';p.textContent=searchError??(category==='authored'?(records.some(record=>record.authoredRecord)?'No matching authored assets. Try an actor, texture, scene or change description.':'No authored assets yet. Edit an actor, replace a texture or capture a transform template; project edits appear here across scenes.'):projectScope&&!projectAssetControls.sourceReport()?'Use Refresh project resources to verify the imported project inventory.':['audio','texture','animation','script','dialogue','flag','transition','collision','trigger','region'].includes(category)&&!resourceKey&&!projectScope?(state.capabilities?.resource_catalog?'Use Refresh scene resources to verify and load this category.':'Resource catalogs are unavailable in this service.'):records.length?'No matching records. Try a stable ID, model type, scene name or source term.':'Import a scene to populate the catalog.');list.append(p);}
  updateAssetPlacementActions();assetNavigation.afterRender(assetFocus);
}
const fieldDialog=document.createElement('dialog');fieldDialog.id='field-map-dialog';document.body.append(fieldDialog);
const fieldToggle=document.createElement('button');fieldToggle.id='field-map-toggle';fieldToggle.textContent='Base collision';fieldToggle.hidden=true;fieldToggle.setAttribute('aria-pressed','false');$('grid-toggle').after(fieldToggle);
const fieldNote=document.createElement('div');fieldNote.className='field-map-note';fieldNote.hidden=true;fieldNote.setAttribute('role','status');document.querySelector('.viewport-toolbar').after(fieldNote);
const collisionLayer=document.createElement('select');collisionLayer.setAttribute('aria-label','Collision preview layer');collisionLayer.innerHTML='<option value="imported">Retail collision</option><option value="effective">Effective collision</option>';fieldToggle.after(collisionLayer);
let fieldMap=null,fieldKey=null,fieldAbort=null,fieldPending=false,wallSelectMode=false,wallSelection=null,wallInspection=null,wallRectangleTool=null,floorRectangleTool=null,floorHeightTool=null;
let fieldSpatial=null,fieldSpatialKey=null,fieldSpatialAbort=null,fieldSpatialPending=false,fieldSpatialVisible=false,fieldSpatialPick=false;
let regionAnnotations=[],regionInspection=null,regionBoundsDialog=null;
let triggerAnnotations=[],triggerInspection=null,triggerCellsDialog=null;
let triggerScriptsDialog=null,triggerGroupDialog=null,triggerGroupInspection=null;
const fieldSpatialToggle=document.createElement('button');fieldSpatialToggle.id='field-spatial-toggle';fieldSpatialToggle.textContent='Source cells';fieldSpatialToggle.setAttribute('aria-pressed','false');collisionLayer.after(fieldSpatialToggle);
const fieldSpatialPickButton=document.createElement('button');fieldSpatialPickButton.id='field-spatial-pick';fieldSpatialPickButton.textContent='Pick source cell';fieldSpatialPickButton.setAttribute('aria-pressed','false');fieldSpatialToggle.after(fieldSpatialPickButton);
const fieldSpatialLayer=document.createElement('select');fieldSpatialLayer.id='field-spatial-layer';fieldSpatialLayer.setAttribute('aria-label','Source cell representation');for(const [value,label] of [['imported','Retail source cells'],['effective','Effective source cells']]){const option=document.createElement('option');option.value=value;option.textContent=label;fieldSpatialLayer.append(option);}fieldSpatialLayer.value='effective';fieldSpatialPickButton.after(fieldSpatialLayer);
const fieldSpatialNote=document.createElement('div');fieldSpatialNote.className='field-map-note';fieldSpatialNote.id='field-spatial-note';fieldSpatialNote.hidden=true;fieldSpatialNote.setAttribute('role','status');fieldNote.after(fieldSpatialNote);
function fieldSpatialCurrent(){return fieldSpatial&&fieldSpatialKey===resourceStateKey()&&resourceKey===resourceStateKey();}
function selectedSceneResource(){return sceneResourceSelection&&resourceKey===resourceStateKey()?assetRecords().find(record=>record.id===sceneResourceSelection&&record.sceneId===state.scene?.id&&['trigger','region','collision','script','transition'].includes(record.type)):null;}
function selectSceneResource(record,frameNow=false){
  if(busy||resourceKey!==resourceStateKey()||!resourceRecords.some(row=>row.semantic_id===record.id)||record.sceneId!==state.scene?.id)return;
  cancelViewportGesture();clearActorGroupSelection();clearEnvironmentGroupSelection();clearScenePlacementSelection();pendingEntityFrame=null;environmentSelection=null;npcDraftSelection=null;sceneResourceSelection=record.id;
  renderHierarchy();renderInspector();$('frame-selected').disabled=!['trigger','region'].includes(record.type);draw();if(frameNow){if(['trigger','region'].includes(record.type))frameSceneResource();else activateAsset(record);}
}
function clearFieldSpatial(){triggerGroupDialog?.dispose?.();triggerScriptsDialog?.dispose?.();regionBoundsDialog?.dispose?.();triggerCellsDialog?.dispose?.();regionInspection=null;regionAnnotations=[];triggerGroupInspection=null;triggerInspection=null;triggerAnnotations=[];fieldSpatialAbort?.abort();fieldSpatialAbort=null;fieldSpatial=null;fieldSpatialKey=null;fieldSpatialPending=false;fieldSpatialVisible=false;fieldSpatialPick=false;fieldSpatialNote.hidden=true;}
function updateFieldSpatialTools(){
  fieldSpatialToggle.hidden=!state.capabilities?.field_map_preview;fieldSpatialToggle.disabled=busy||fieldSpatialPending;fieldSpatialToggle.classList.toggle('active',fieldSpatialVisible&&!!fieldSpatialCurrent());fieldSpatialToggle.setAttribute('aria-pressed',String(fieldSpatialVisible&&!!fieldSpatialCurrent()));
  fieldSpatialPickButton.hidden=fieldSpatialToggle.hidden;fieldSpatialPickButton.disabled=busy||fieldSpatialPending||!fieldSpatialVisible||!fieldSpatialCurrent()||wallSelectMode||pickScriptTargets||pickRuntimeNodes||scenePlacementMode||actorBoxMode;
  if(fieldSpatialPickButton.disabled)fieldSpatialPick=false;fieldSpatialPickButton.classList.toggle('active',fieldSpatialPick);fieldSpatialPickButton.setAttribute('aria-pressed',String(fieldSpatialPick));
  fieldSpatialLayer.hidden=fieldSpatialToggle.hidden;fieldSpatialLayer.disabled=busy||fieldSpatialPending||!fieldSpatialCurrent()||!!regionInspection||!!triggerInspection||!!triggerGroupInspection;
  fieldSpatialNote.hidden=!fieldSpatialVisible||!fieldSpatialCurrent();
}
async function loadFieldSpatial(){
  if(busy||!state.capabilities?.field_map_preview)return false;
  if(resourceKey!==resourceStateKey())await refreshResources();
  if(busy||resourceKey!==resourceStateKey())return false;
  if(fieldSpatialCurrent()){fieldSpatialVisible=true;updateFieldSpatialTools();renderInspector();draw();return true;}
  const candidates=assetRecords().filter(record=>record.type==='collision');if(candidates.length!==1){notify('No single verified field MAP is available for source cells.',true);return false;}
  const key=resourceStateKey(),sceneId=state.scene?.id,controller=new AbortController();fieldSpatialAbort?.abort();fieldSpatialAbort=controller;fieldSpatialPending=true;setBusy(true);updateFieldSpatialTools();
  try{
    const response=await fetch('/api/field-map-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:candidates[0].id,layer:'imported'}),signal:controller.signal});
    const result=await response.json();if(!response.ok||result.error)throw new Error(result.error??'Source cell verification failed.');
    if(controller.signal.aborted||key!==resourceStateKey())return false;
    validateFieldMap(result,candidates[0],key);if(result.region_state_key!==state.scene_region_state_key||result.trigger_state_key!==state.scene_trigger_state_key)throw new Error('Source cell overrides changed during preview. Refresh resources.');const spatial=decodeFieldSpatial(result.spatial,sceneId);
    for(const row of spatial.records){const resource=resourceRecords.find(record=>record.semantic_id===row.id);if(!resource||resource.asset_kind!==row.kind||JSON.stringify(resource.source_record)!==JSON.stringify(row.source_record))throw new Error('Source cells differ from the current resource catalog. Refresh resources.');}
    regionAnnotations=decodeRegionBoundsAnnotations(result.region_bounds,spatial);
    for(const annotation of regionAnnotations){const source=resourceRecords.find(row=>row.semantic_id===annotation.region_id);if(!source||['x0','z0','x1','z1'].some(key=>source.encoded?.[key]!==annotation.values_layers.imported[key]))throw new Error('Region annotation corners differ from the source catalog.');}
    triggerAnnotations=decodeTriggerCellsAnnotations(result.trigger_cells,spatial);
    for(const annotation of triggerAnnotations){const source=resourceRecords.find(row=>row.semantic_id===annotation.trigger_id);if(!source||['tile_x','tile_z'].some(key=>source.encoded?.[key]!==annotation.values_layers.imported[key]))throw new Error('Trigger annotation coordinates differ from the source catalog.');}
    fieldSpatial=spatial;fieldSpatialKey=key;fieldSpatialVisible=true;fieldSpatialNote.textContent=`${spatial.records.filter(row=>row.kind==='trigger').length} trigger cells · ${spatial.records.filter(row=>row.kind==='region').length} region bounds · Y=0 reference plane, height unknown · Trigger: world >> 7 · Region: (world - 64) >> 7 · Activation unverified`;
    renderHierarchy();renderInspector();return true;
  }catch(error){if(error.name!=='AbortError'){clearFieldSpatial();notify(error.message,true);}return false;}
  finally{if(fieldSpatialAbort===controller){fieldSpatialAbort=null;fieldSpatialPending=false;}setBusy(false);updateFieldSpatialTools();draw();}
}
fieldSpatialToggle.onclick=async()=>{if(busy)return;cancelViewportGesture();if(fieldSpatialVisible){fieldSpatialVisible=false;fieldSpatialPick=false;updateFieldSpatialTools();draw();}else await loadFieldSpatial();};
fieldSpatialLayer.onchange=()=>{if(busy||fieldSpatialLayer.disabled)return;cancelViewportGesture();renderInspector();draw();};
fieldSpatialPickButton.onclick=()=>{if(busy||fieldSpatialPickButton.disabled)return;cancelViewportGesture();fieldSpatialPick=!fieldSpatialPick;updateFieldSpatialTools();draw();};
async function frameSceneResource(){
  const record=selectedSceneResource();if(!record||!['trigger','region'].includes(record.type)||busy)return;
  const key=resourceStateKey();if(!await loadFieldSpatial()||key!==resourceStateKey()||sceneResourceSelection!==record.id)return;
  const row=fieldSpatialRows().find(item=>item.id===record.id);if(!row)return;const framed=fieldSpatialFrame(row);camera.target={...framed.target};camera.distance=framed.distance;cameraRevision++;draw();
}
function fieldSpatialRows(){
  if(!fieldSpatialCurrent())return [];
  const byId=new Map([...regionAnnotations.map(row=>[row.region_id,row]),...triggerAnnotations.map(row=>[row.trigger_id,row])]);
  const group=triggerGroupInspection?.key===resourceStateKey()?new Map(triggerGroupGeometry(triggerGroupInspection.report,triggerGroupInspection.layer).map(row=>[row.id,row])):new Map();
  return fieldSpatial.records.map(row=>{
    if(group.has(row.id))return {...row,...group.get(row.id)};
    if(regionInspection?.key===resourceStateKey()&&regionInspection.report.region_id===row.id)return {...row,...regionBoundsGeometry(regionInspection.report,regionInspection.layer)};
    if(triggerInspection?.key===resourceStateKey()&&triggerInspection.report.trigger_id===row.id)return {...row,...triggerCellsGeometry(triggerInspection.report,triggerInspection.layer)};
    const annotation=fieldSpatialLayer.value==='effective'?byId.get(row.id):null;
    if(!annotation)return row;
    const bounds=annotation.world_bounds_layers.effective;
    return {...row,world_bounds:{...bounds},world_center:{x:(bounds.x_min+bounds.x_max)/2,y:0,z:(bounds.z_min+bounds.z_max)/2}};
  });
}
async function inspectRegionBounds(record){
  if(busy||!canEdit()||record.type!=='region'||resourceKey!==resourceStateKey())return;
  const key=resourceStateKey(),snapshot=JSON.stringify(record),sceneId=state.scene?.id,projectPath=state.project?.path;
  if(!await loadFieldSpatial()||key!==resourceStateKey())return;
  selectSceneResource(record);fieldSpatialPick=false;
  const current=()=>key===resourceStateKey()&&resourceKey===key&&JSON.stringify(assetRecords().find(row=>row.id===record.id))===snapshot;
  triggerCellsDialog?.dispose?.();regionBoundsDialog?.dispose?.();
  regionBoundsDialog=openRegionBounds({record,getState:()=>state,busy:()=>busy,setBusy,current,
    api:async(route,body)=>{const ok=await api(route,body);if(ok&&route==='/api/region-bounds-apply'&&state.scene?.id===sceneId&&state.project?.path===projectPath){fieldSpatialLayer.value='effective';await refreshResources();const next=assetRecords().find(row=>row.id===record.id);if(next){selectSceneResource(next);await loadFieldSpatial();}}return ok;},
    onInspection:(report,layer)=>{cancelViewportGesture();regionInspection=report?{report,layer,key:resourceStateKey()}:null;updateFieldSpatialTools();renderInspector();draw();},
    onFrame:(report,layer)=>{const framed=fieldSpatialFrame(regionBoundsGeometry(report,layer));camera.target={...framed.target};camera.distance=framed.distance;cameraRevision++;draw();},
    onError:error=>notify(error.message,true)});
}
async function inspectTriggerGroup(record){
  if(busy||!canEdit()||resourceKey!==resourceStateKey())return;
  const key=resourceStateKey(),snapshot=JSON.stringify(record),sceneId=state.scene?.id,projectPath=state.project?.path;
  if(!await loadFieldSpatial()||key!==resourceStateKey())return;
  selectSceneResource(record);fieldSpatialPick=false;triggerGroupDialog?.dispose?.();triggerScriptsDialog?.dispose?.();triggerCellsDialog?.dispose?.();regionBoundsDialog?.dispose?.();
  const current=()=>key===resourceStateKey()&&resourceKey===key&&JSON.stringify(assetRecords().find(row=>row.id===record.id))===snapshot;
  triggerGroupDialog=openTriggerGroup({record,records:assetRecords(),getState:()=>state,current,busy:()=>busy,setBusy,
    api:async(route,body)=>{const ok=await api(route,body);if(ok&&state.scene?.id===sceneId&&state.project?.path===projectPath){await refreshResources();const next=assetRecords().find(row=>row.id===record.id);if(next)selectSceneResource(next);}return ok;},
    onInspection:(report,layer)=>{cancelViewportGesture();triggerGroupInspection=report?{report,layer,key:resourceStateKey()}:null;updateFieldSpatialTools();renderInspector();draw();},
    onFrame:(report,layer)=>{const framed=triggerGroupFrame(report,layer);camera.target={...framed.target};camera.distance=framed.distance;cameraRevision++;draw();},
    onError:error=>notify(error.message,true)});
}
async function inspectTriggerScripts(record){
  if(busy||!canEdit()||record.type!=='trigger'||resourceKey!==resourceStateKey())return;
  const key=resourceStateKey(),snapshot=JSON.stringify(record),sceneId=state.scene?.id,projectPath=state.project?.path;
  selectSceneResource(record);regionBoundsDialog?.dispose?.();triggerCellsDialog?.dispose?.();triggerScriptsDialog?.dispose?.();
  const current=()=>key===resourceStateKey()&&resourceKey===key&&JSON.stringify(assetRecords().find(row=>row.id===record.id))===snapshot;
  triggerScriptsDialog=openTriggerScripts({record,getState:()=>state,busy:()=>busy,setBusy,current,
    api:async(route,body)=>{const ok=await api(route,body);if(ok&&state.scene?.id===sceneId&&state.project?.path===projectPath){await refreshResources();const next=assetRecords().find(row=>row.id===record.id);if(next)selectSceneResource(next);}return ok;},
    onInspect:id=>openActorScript({id:id.replace('script://','scene://'),name:'Trigger target '+id,partitionTwo:true}),
    onError:error=>notify(error.message,true)});
}
async function inspectTriggerCells(record){
  if(busy||!canEdit()||record.type!=='trigger'||resourceKey!==resourceStateKey())return;
  const key=resourceStateKey(),snapshot=JSON.stringify(record),sceneId=state.scene?.id,projectPath=state.project?.path;
  if(!await loadFieldSpatial()||key!==resourceStateKey())return;
  selectSceneResource(record);fieldSpatialPick=false;
  const current=()=>key===resourceStateKey()&&resourceKey===key&&JSON.stringify(assetRecords().find(row=>row.id===record.id))===snapshot;
  regionBoundsDialog?.dispose?.();triggerCellsDialog?.dispose?.();
  triggerCellsDialog=openTriggerCells({record,getState:()=>state,busy:()=>busy,setBusy,current,
    api:async(route,body)=>{const ok=await api(route,body);if(ok&&route==='/api/trigger-cells-apply'&&state.scene?.id===sceneId&&state.project?.path===projectPath){fieldSpatialLayer.value='effective';await refreshResources();const next=assetRecords().find(row=>row.id===record.id);if(next){selectSceneResource(next);await loadFieldSpatial();}}return ok;},
    onInspection:(report,layer)=>{cancelViewportGesture();triggerInspection=report?{report,layer,key:resourceStateKey()}:null;updateFieldSpatialTools();renderInspector();draw();},
    onFrame:(report,layer)=>{const framed=fieldSpatialFrame(triggerCellsGeometry(report,layer));camera.target={...framed.target};camera.distance=framed.distance;cameraRevision++;draw();},
    onError:error=>notify(error.message,true)});
}
function renderSceneResourceInspector(record){
  const host=$('inspector'),key=resourceStateKey();host.replaceChildren();$('selection-summary').textContent=`${record.label} · Source resource`;
  const section=document.createElement('section');section.className='component scene-resource-inspector';section.dataset.sceneResource=record.id;host.append(section);
  const current=()=>resourceKey===resourceStateKey()&&key===resourceStateKey()&&sceneResourceSelection===record.id;
  mountAssetInspector(section,{schema:state.inspector_schema,record,capabilities:state.capabilities,current,busy:()=>busy,activate:async (item,action)=>{if(current()&&!busy)await activateAsset(item,action);},onError:error=>notify(error.message,true)});
  if(record.type==='script'&&record.data?.partition===2){
    const owner=record.data.owner_semantic_id,projectPath=state.project?.path,sceneId=state.scene?.id;
    if(typeof owner==='string')mountScriptOwnerInspector(host,{owner,getState:()=>state,current,editable:canEditDialogue,busy:()=>busy,api,placement:'end',
      onInspect:component=>openActorScript({id:owner,name:record.label,partitionTwo:true},false,null,null,null,component),
      onReset:async()=>{if(projectPath!==state.project?.path||sceneId!==state.scene?.id)return;await refreshResources();if(projectPath!==state.project?.path||sceneId!==state.scene?.id)return;const fresh=assetRecords().find(item=>item.id===record.id&&item.type==='script'&&item.sceneId===sceneId);if(fresh)selectSceneResource(fresh);},
      onError:error=>notify(error.message,true)});
  }
  const actions=document.createElement('div');actions.className='dialog-actions';section.append(actions);
  if(['trigger','region'].includes(record.type)){
    const frameButton=document.createElement('button');frameButton.id='frame-source-cell';frameButton.textContent='Frame source cell';frameButton.disabled=busy;frameButton.onclick=()=>{if(current())frameSceneResource();};actions.append(frameButton);
    const row=fieldSpatialCurrent()?fieldSpatialRows().find(item=>item.id===record.id):null;
    const summary=document.createElement('p');summary.className='field-note';summary.id='source-cell-coordinates';summary.textContent=row?`${triggerGroupInspection?.key===resourceStateKey()&&triggerGroupInspection.report.trigger_ids.includes(record.id)?({imported:'Retail group cell',current:'Current group cell',proposed:'Proposed group cell - not applied'}[triggerGroupInspection.layer]):triggerInspection?.key===resourceStateKey()&&triggerInspection.report.trigger_id===record.id?({imported:'Retail trigger cell',current:'Current trigger cell',proposed:'Proposed trigger cell'}[triggerInspection.layer]):regionInspection?.key===resourceStateKey()&&regionInspection.report.region_id===record.id?({imported:'Retail region bounds',current:'Current region bounds',proposed:'Proposed region bounds'}[regionInspection.layer]):fieldSpatialLayer.value==='effective'?'Effective source cells':'Retail source cells'} · X [${row.world_bounds.x_min}, ${row.world_bounds.x_max}) · Z [${row.world_bounds.z_min}, ${row.world_bounds.z_max}) · guest units · Y=0 reference plane, height unknown · Activation unverified`:'Frame source cell to load its verified X/Z bounds. Height and activation are unknown.';section.append(summary);
  }
  const details=document.createElement('button');details.id='source-resource-details';details.textContent='Asset details and references';details.disabled=busy;details.onclick=()=>{if(current()&&!busy)showAssetDetails(record);};actions.append(details);
  const source=document.createElement('details');source.className='resource-provenance';const title=document.createElement('summary');title.textContent='Source record and provenance';const pre=document.createElement('pre');pre.className='diagnostic-detail';pre.textContent=JSON.stringify(record.data,null,2);source.append(title,pre);section.append(source);
}
const wallTools=document.createElement('div');wallTools.id='wall-viewport-tools';transformTools.after(wallTools);
const wallSelectButton=document.createElement('button');wallSelectButton.id='wall-select-mode';wallSelectButton.textContent='Select wall rectangle';wallSelectButton.setAttribute('aria-pressed','false');wallTools.append(wallSelectButton);
function wallSourceCurrent(){return canEdit()&&scenePreviewCurrent()&&sceneRepresentation==='authored'&&fieldMap&&fieldKey===resourceStateKey()&&!scenePose&&!shapeDraft&&!actorGroupInspection&&!environmentGroupInspection&&!scenePlacementInspection&&!scenePlacementMode;}
wallRectangleTool=mountWallRectangle({host:wallTools,getState:()=>state,busy:()=>busy,setBusy,api,sourceCurrent:wallSourceCurrent,hasDraft:()=>false,closeInspector:()=>{if(fieldDialog.open)fieldDialog.close();},
  onInspection:(report,layer)=>{if(report){const details=wallTools.closest('details');if(details)details.open=true;}cancelViewportGesture();wallSelectMode=false;wallSelection=null;if(fieldDialog.open)fieldDialog.close();wallInspection=report?{report,layer}:null;updateFieldToggle();draw();},
  onFrame:report=>{const g=wallSelectionGeometry(report.rectangle);camera.target={x:(g.x_min+g.x_max)/2,y:0,z:(g.z_min+g.z_max)/2};camera.distance=Math.max(200,Math.hypot(g.x_max-g.x_min,g.z_max-g.z_min)*2.5);cameraRevision++;draw();}});
floorRectangleTool=mountFloorRectangle({host:wallTools,getState:()=>state,busy:()=>busy,setBusy,api,
  sourceCurrent:()=>wallSourceCurrent()||!!(scenePose?.floorInspection&&canEdit()&&scenePreviewCurrent()&&sceneRepresentation==='authored'&&fieldMap&&fieldKey===resourceStateKey()),
  onRestore:()=>{if(scenePose?.floorInspection){clearScenePose();draw();}},
  onScene:async(request,report,{signal,isCurrent,returnToEditor})=>{
    const loadedKey=sceneKey,loadedSource=state.scene_preview_source_key;
    if(!isCurrent()||!scenePreviewCurrent()||sceneRepresentation!=='authored')throw Error('Refresh Current before inspecting floor selectors.');
    const response=await fetch('/api/floor-rectangle-scene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request),signal}),value=await response.json();
    if(!response.ok||value.error)throw Error(value.error||'Floor scene proposal failed');
    if(!isCurrent()||sceneKey!==loadedKey||state.scene_preview_source_key!==loadedSource||value.schema_version!=='legaia.floor-rectangle-scene.v1'||value.scene_preview_source_key!==loadedSource||value.scene?.scene_id!==state.scene.id||value.scene?.representation!=='authored'||JSON.stringify(decodeFloorRectangle(value.review,report.project_source_key,report.scene_id,report.rectangle,report.cell_edits??null))!==JSON.stringify(report))throw Error('Floor scene differs from the reviewed Current context.');
    try{cancelViewportGesture();const proposed=structuredClone(value.scene),failures=sceneRenderer.load(proposed);if(failures.length)throw Error(failures.join('; '));
      scenePose={key:sceneKey,name:'Proposed floor selectors - not applied',floorInspection:true,returnToFile:returnToEditor,afterRestore:returnToEditor,isCurrent:()=>state.scene_preview_source_key===loadedSource&&state.project_copy_source_key===report.project_source_key};
      scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`Proposed floor selectors - not applied · ${report.effective_change_count} changes · reference terrain and placement heights; ramps/gameplay unverified`;configureSceneInspectionComparison(proposed);
      for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('label')])control.hidden=true;
      const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to floor review';const details=wallTools.closest('details');if(details)details.open=true;
      camera.target={x:(report.rectangle.column_start+report.rectangle.column_end)*64,y:0,z:(report.rectangle.row_start+report.rectangle.row_end)*64};camera.distance=Math.max(400,Math.hypot(report.rectangle.column_end-report.rectangle.column_start+1,report.rectangle.row_end-report.rectangle.row_start+1)*320);cameraRevision++;draw();
    }catch(error){clearScenePose();if(scenePreviewCurrent())sceneRenderer.load(structuredClone(scenePreview));draw();throw error;}
  }});
floorHeightTool=mountFloorHeights({host:wallTools,getState:()=>state,busy:()=>busy,setBusy,api,
  sourceCurrent:()=>wallSourceCurrent()||!!(scenePose?.floorHeightInspection&&canEdit()&&scenePreviewCurrent()&&sceneRepresentation==='authored'&&fieldMap&&fieldKey===resourceStateKey()),
  onRestore:()=>{if(scenePose?.floorHeightInspection){clearScenePose();draw();}},
  onScene:async(request,report,{signal,isCurrent,returnToEditor})=>{
    const loadedKey=sceneKey,loadedSource=state.scene_preview_source_key;
    if(!isCurrent()||!scenePreviewCurrent()||sceneRepresentation!=='authored')throw Error('Refresh Current before inspecting floor heights.');
    const response=await fetch('/api/floor-height-scene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request),signal}),value=await response.json();
    if(!response.ok||value.error)throw Error(value.error||'Floor scene proposal failed');
    if(!isCurrent()||sceneKey!==loadedKey||state.scene_preview_source_key!==loadedSource||value.schema_version!=='legaia.floor-height-scene.v1'||value.scene_preview_source_key!==loadedSource||value.scene?.scene_id!==state.scene.id||value.scene?.representation!=='authored'||JSON.stringify(decodeFloorHeights(value.review,report.project_source_key,report.scene_id,report.proposed))!==JSON.stringify(report))throw Error('Floor scene differs from the reviewed Current context.');
    try{cancelViewportGesture();const proposed=structuredClone(value.scene),failures=sceneRenderer.load(proposed);if(failures.length)throw Error(failures.join('; '));
      scenePose={key:sceneKey,name:'Proposed floor heights - not applied',floorHeightInspection:true,returnToFile:returnToEditor,afterRestore:returnToEditor,isCurrent:()=>state.scene_preview_source_key===loadedSource&&state.project_copy_source_key===report.project_source_key};
      scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`Proposed floor heights - not applied · ${report.effective_change_count} changes · reference terrain and placement heights; ramps/gameplay unverified`;configureSceneInspectionComparison(proposed);
      for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('label')])control.hidden=true;
      const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to height review';const details=wallTools.closest('details');if(details)details.open=true;
      draw();
    }catch(error){clearScenePose();if(scenePreviewCurrent())sceneRenderer.load(structuredClone(scenePreview));draw();throw error;}
  }});
const floorPickButton=document.createElement('button');floorPickButton.id='floor-selector-pick';floorPickButton.textContent='Pick floor selector';floorPickButton.setAttribute('aria-pressed','false');wallTools.append(floorPickButton);
function canPickFloorSelector(){return !sceneRuler?.picking()&&!busy&&!fieldPending&&canEdit()&&scenePreviewCurrent()&&sceneModelsReady()&&sceneRepresentation==='authored'&&!scenePendingKey&&!scenePose&&!shapeDraft&&!draft&&!actorGroupInspection&&!environmentGroupInspection&&!scenePlacementInspection&&!scenePlacementMode&&!actorBoxMode&&!wallSelectMode&&!wallInspection&&!sceneFacePickMode&&!pickScriptTargets&&!pickRuntimeNodes&&!fieldSpatialPick;}
floorPickButton.onclick=async()=>{if(!canPickFloorSelector())return;if(floorPickMode){floorPickMode=false;updateFieldToggle();return;}if(!fieldMap||fieldKey!==resourceStateKey()){if(resourceKey!==resourceStateKey())await refreshResources();const records=assetRecords().filter(r=>r.type==='collision');if(records.length!==1||!await loadFieldMap(records[0])){notify('Load one verified source collision map before picking floor selectors.',true);return;}}if(!canPickFloorSelector()||!wallSourceCurrent())return;cancelViewportGesture();floorPickMode=true;updateFieldToggle();updateSceneFacePick();notify('Click visible ground to edit its nearest triangle corner selector. Drag still orbits; Apply requires Review.');};
function pickFloorSelector(point,gesture){
 if(!canPickFloorSelector()||!wallSourceCurrent()||gesture.context!==resourceStateKey()||gesture.sourceKey!==state.scene_preview_source_key||gesture.projectKey!==state.project_copy_source_key||gesture.cameraRevision!==cameraRevision||gesture.width!==width||gesture.height!==height)throw Error('Floor picking context changed; pick from Current again.');
 const document=activeScenePreview(),hit=sceneRenderer.pickSurface(point.x,point.y,sceneView());if(!hit){notify('No visible ground at this point.');return;}
 const entity=document.entities.find(e=>e.entity_id===hit.entity_id&&e.geometry_key===hit.geometry_key&&e.renderable),geometry=document.assets.find(a=>a.geometry_key===hit.geometry_key&&a.asset_id===entity?.asset_id);
 if(!entity||entity.asset_id!==`environment://${state.scene.id.replace('scene://','')}/field-map/ground`||entity.pose_kind!=='source_heightfield'||!geometry)throw Error('Pick visible source ground; models in front of it are not floor selectors.');
 const picked=nativeFloorSelectorAtTriangle(geometry,hit.triangle_index,point,v=>project({x:v[0],y:-v[1],z:v[2]}));
 if(fieldDialog.open)fieldDialog.close();floorRectangleTool.open({row_start:picked.row,row_end:picked.row,column_start:picked.column,column_end:picked.column,tier:picked.tier});
 notify(`Current floor row ${picked.row}, column ${picked.column}, tier ${picked.tier}${picked.edge_clamped?' - outer preview corner uses the clamped edge selector':''}. Fresh Review required.`);
}
wallSelectButton.onclick=async()=>{
  if(busy||wallSelectButton.disabled)return;floorPickMode=false;cancelViewportGesture();wallSelection=null;
  if(wallSelectMode){wallSelectMode=false;updateFieldToggle();draw();return;}
  if(!fieldMap||fieldKey!==resourceStateKey()){
    if(resourceKey!==resourceStateKey())await refreshResources();
    const candidates=assetRecords().filter(record=>record.type==='collision');
    if(candidates.length!==1||!await loadFieldMap(candidates[0])){notify('Load one verified source collision map before selecting walls.',true);return;}
  }
  if(!wallSourceCurrent())return;actorBoxMode=false;wallSelectMode=true;updateActorGroupSelection();updateFieldToggle();draw();notify('Drag source grid cells on the Y=0 reference plane; release to review wall bits.');
};
function wallGestureCurrent(gesture){return !busy&&wallSourceCurrent()&&!wallInspection&&gesture.context===resourceStateKey()&&gesture.sourceKey===state.project_copy_source_key&&gesture.cameraRevision===cameraRevision&&gesture.width===width&&gesture.height===height;}
function wallRectangleAt(gesture,p){return wallDragRectangle(gesture.wallStart,wallCellAt(groundAt(p.x,p.y,0)));}
const fieldMapScope='Base blocked grid only · Y = 0 is a display placeholder, not decoded height. Runtime/script paints and actors are excluded. Canonical positive-X range only; wrapping and boundary aliases are not shown. Lines are drawn over models.';
function updateFieldToggle(){
  fieldToggle.hidden=!state.capabilities?.field_map_preview;fieldToggle.disabled=busy||fieldPending;
  wallSelectButton.hidden=fieldToggle.hidden;wallSelectButton.disabled=busy||fieldPending||!canEdit()||!scenePreviewCurrent()||sceneRepresentation!=='authored'||!!scenePose||!!shapeDraft||!!actorGroupInspection||!!environmentGroupInspection||!!wallInspection||scenePlacementMode||!!scenePlacementInspection;
  if(!wallSourceCurrent()){wallSelectMode=false;wallSelection=null;}wallSelectButton.classList.toggle('active',wallSelectMode);wallSelectButton.setAttribute('aria-pressed',String(wallSelectMode));wallRectangleTool?.refresh();floorRectangleTool?.refresh();floorHeightTool?.refresh();
  floorPickButton.hidden=fieldToggle.hidden;floorPickButton.disabled=!canPickFloorSelector();if(floorPickButton.disabled||!wallSourceCurrent())floorPickMode=false;floorPickButton.classList.toggle('active',floorPickMode);floorPickButton.setAttribute('aria-pressed',String(floorPickMode));
  collisionLayer.hidden=fieldToggle.hidden;collisionLayer.disabled=busy||fieldPending;
  fieldToggle.classList.toggle('active',!!fieldMap);fieldToggle.setAttribute('aria-pressed',!!fieldMap);fieldToggle.textContent=fieldPending?'Loading collision…':collisionLayer.value==='effective'?'Effective collision':'Base collision';
}
function clearFieldMap(){
  fieldAbort?.abort();fieldAbort=null;fieldMap=null;fieldKey=null;fieldPending=false;fieldNote.hidden=true;floorPickMode=false;wallSelectMode=false;wallSelection=null;wallRectangleTool?.restore();floorRectangleTool?.restore();floorHeightTool?.restore();updateFieldToggle();
}
function validateFieldMap(result,record,key){
  if(key!==resourceStateKey()||result.source_key!==state.scene_preview_source_key||result.scene_id!==state.scene?.id||result.semantic_id!==record.id||result.asset_kind!=='collision'||result.coordinate_system!=='psx_guest_xz')throw new Error('Field map source changed while loading. Refresh scene resources and retry.');
  if(!Array.isArray(result.rectangles)||result.rectangles.length>65536||result.rectangles.some(r=>!r||![r.x_min,r.x_max,r.z_min,r.z_max].every(numeric)||r.x_min>r.x_max||r.z_min>r.z_max)||!Array.isArray(result.triggers)||result.triggers.length>65536)throw new Error('Field map service returned invalid or oversized geometry.');
  if(result.authored_changes!==undefined&&(!Array.isArray(result.authored_changes)||result.authored_changes.length>4096||result.authored_changes.some(r=>!r||!Number.isInteger(r.row)||r.row<1||r.row>127||!Number.isInteger(r.column)||r.column<0||r.column>127||!Number.isInteger(r.quadrant)||r.quadrant<0||r.quadrant>3||typeof r.before_value!=='boolean'||typeof r.after_value!=='boolean')))throw new Error('Collision service returned invalid authored changes.');
  return result;
}
async function loadFieldMap(record){
  if(busy||!state.capabilities?.field_map_preview||resourceKey!==resourceStateKey())return false;
  clearFieldMap();draw();const key=resourceStateKey(),layer=collisionLayer.value,controller=new AbortController();fieldAbort=controller;fieldPending=true;setBusy(true);
  try{
    const response=await fetch('/api/field-map-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:record.id,layer}),signal:controller.signal});
    const result=await response.json();if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Field map verification failed');
    if(controller.signal.aborted)return false;
    if(result.representation!==layer)throw new Error('Collision service did not return the requested layer.');
    if(fieldDialog.open)fieldDialog.querySelector('.dialog-error').textContent='';
    fieldMap=validateFieldMap(result,record,key);fieldKey=key;const changes=fieldMap.authored_changes??[],added=changes.filter(r=>r.after_value).length,removed=changes.filter(r=>!r.after_value).length;fieldNote.textContent=`${layer==='effective'?'EFFECTIVE source':'RETAIL source'} · ${fieldMap.rectangles.length} blocked rectangles${changes.length?` · Added ${added} (green solid) · Removed ${removed} (pink dashed)`:''} · ${fieldMapScope}`;fieldNote.title=(fieldMap.limitations ?? []).map(value=>typeof value==='string'?value:JSON.stringify(value)).join(' ');fieldNote.hidden=false;return true;
  }catch(error){clearFieldMap();if(error.name!=='AbortError'){notify(error.message,true);if(fieldDialog.open)fieldDialog.querySelector('.dialog-error').textContent=error.message;}return false;}
  finally{if(fieldAbort===controller)fieldAbort=null;fieldPending=false;setBusy(false);draw();}
}
fieldToggle.onclick=async()=>{
  if(busy)return;if(fieldMap){clearFieldMap();draw();return;}
  if(resourceKey!==resourceStateKey())await refreshResources();
  const candidates=assetRecords().filter(record=>record.type==='collision');
  if(candidates.length!==1){notify(candidates.length?'Choose a collision record in the asset browser.':'No verified base collision record is available for this scene.',true);return;}
  await loadFieldMap(candidates[0]);
};
collisionLayer.onchange=async()=>{updateFieldToggle();if(busy||!fieldMap)return;const record=assetRecords().find(r=>r.id===fieldMap.semantic_id&&r.type==='collision');if(record)await loadFieldMap(record);else{clearFieldMap();draw();}};
function openFieldResource(record){
  if(busy||resourceKey!==resourceStateKey())return;
  selectSceneResource(record);
  const collision=record.type==='collision',data=record.data;
  fieldDialog.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-field-map" aria-label="Close field map inspector">×</button></div>${property('Stable ID',record.id)}${property('Record type',collision?'Base collision grid':record.type==='region'?'Encoded region record':'Encoded trigger record')}<p class="field-note">${collision?fieldMapScope:'Read-only encoded trigger or region fields. Destination scenes, runtime activation and story conditions are not inferred.'}</p><div id="field-record-summary"></div>${collision?'<button id="show-base-collision" class="accent">Show base collision</button>':''}<details class="resource-provenance"><summary>Source provenance and complete metadata</summary><pre class="diagnostic-detail"></pre></details><p class="dialog-error" role="alert"></p>`;
  const summary=$('field-record-summary');
  for(const [key,value] of Object.entries(data))if(!['id','semantic_id','asset_kind','kind','name','layer','scene_id','reference_commit','collision_id','source_record','catalog_limitations','limitations'].includes(key)&&value!==null&&['string','number','boolean'].includes(typeof value))summary.insertAdjacentHTML('beforeend',property(key.replaceAll('_',' '),value));
  for(const [key,label] of [['encoded','Encoded source fields'],['tile_bounds','Half-open tile bounds'],['destination_world','Decoded intra-scene destination (X/Z only)'],['script_reference','Unresolved script reference']]){
    if(data[key]&&typeof data[key]==='object'){const heading=document.createElement('h3');heading.textContent=label;summary.append(heading);appendResourceTable(summary,['Field','Source value'],Object.entries(data[key]).map(([field,value])=>[field.replaceAll('_',' '),value]),'No fields supplied.');}
  }
  if(collision&&Array.isArray(data.elevation_overrides)){
    const heading=document.createElement('h3');heading.textContent='Ramp height adjustments';summary.append(heading);
    const note=document.createElement('p');note.className='field-note';note.textContent='Read-only kind-2 records, primary then fallback; first matching tile wins. Values are Y adjustments to the four-corner height mean when object-cell flag 0x0800 is set, not complete floor heights. Subcells are ordered (0,0), (1,0), (0,1), (1,1); positive Y points down.';summary.append(note);
    const filter=document.createElement('input');filter.type='search';filter.className='ramp-filter';filter.placeholder='Filter ramps, e.g. 25 26';filter.setAttribute('aria-label','Filter ramp records');summary.append(filter);
    const count=document.createElement('p');count.className='field-note';count.setAttribute('role','status');summary.append(count);
    const table=document.createElement('div');summary.append(table);
    const renderRamps=()=>{
      const terms=filter.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      const rows=data.elevation_overrides.filter(row=>{const words=[row.table_source,String(row.record_index),String(row.tile_x),String(row.tile_z)].map(String);return terms.every(term=>words.includes(term));});
      count.textContent=`${rows.length} / ${data.elevation_overrides.length} ramp records · filter matches table, row or tile coordinates`;
      table.replaceChildren();appendResourceTable(table,['Table / row','Tile X','Tile Z','Signed coarse','Subcell ΔY'],rows.map(row=>[`${row.table_source} / ${row.record_index}`,row.tile_x,row.tile_z,row.coarse_signed,(row.subcell_delta_y ?? []).join(', ')]),'No matching ramp records.');
    };
    filter.oninput=renderRamps;renderRamps();
  }
  if(!collision){const coordinates=document.createElement('p');coordinates.className='field-note';coordinates.textContent='Source cells use their own X/Z quantization: triggers use world >> 7; regions use (world - 64) >> 7. Viewport outlines use Y=0 as a reference plane; height and activation are unknown.';summary.append(coordinates);}
  const limits=document.createElement('p');limits.className='field-note';limits.textContent=(data.limitations ?? []).map(value=>typeof value==='string'?value:JSON.stringify(value)).join(' ');summary.append(limits);
  fieldDialog.querySelector('pre').textContent=JSON.stringify(data,null,2);$('close-field-map').onclick=()=>fieldDialog.close();
  if(collision){$('show-base-collision').disabled=!state.capabilities?.field_map_preview;$('show-base-collision').onclick=async()=>{if(await loadFieldMap(record)){fieldDialog.close();document.querySelector('.workspace-tabs [data-panel="viewport"]').click();}};}
  if(collision){
    const editButton=document.createElement('button');editButton.textContent='Edit source wall bits';editButton.disabled=state.project.mode!=='edit';summary.append(editButton);
    editButton.onclick=async()=>{
      if(busy||state.project.mode!=='edit')return;collisionLayer.value='effective';if(!await loadFieldMap(record)||!fieldDialog.open)return;
      editButton.disabled=true;const snapshot=fieldMap,key=resourceStateKey(),scene=state.scene.id;
      const form=document.createElement('form');form.innerHTML='<h3>Source wall edit</h3><p>Only the selected wall bit changes. Floor tiers, runtime actors and script collision paints are separate.</p><label>Grid row<input name="row" type="number" min="1" max="127" step="1" value="1" required></label><label>Grid column<input name="column" type="number" min="0" max="127" step="1" value="0" required></label><label>Quadrant<select name="quadrant"><option value="0">0 · low X / low Z</option><option value="1">1 · high X / low Z</option><option value="2">2 · low X / high Z</option><option value="3">3 · high X / high Z</option></select></label><label><input name="blocked" type="checkbox"> Blocked in source grid</label><p class="collision-cell-status"></p><button type="submit">Apply wall bit</button><button type="button" class="clear-collision">Clear scene wall edits</button>';
      summary.append(form);const status=form.querySelector('.collision-cell-status');
      const cell=()=>({row:Number(form.elements.row.value),column:Number(form.elements.column.value),quadrant:Number(form.elements.quadrant.value)});
      const refresh=()=>{const c=cell(),rectangle=snapshot.rectangles.find(r=>r.row===c.row&&r.column===c.column&&r.quadrant===c.quadrant);form.elements.blocked.checked=!!rectangle;const x=c.column*128+(c.quadrant&1)*64,z=c.row*128-128+(c.quadrant>>1)*64;status.textContent=`Effective: ${rectangle?'blocked':'unblocked'} · integer X (${x}, ${x+64}], Z [${z}, ${z+64})`;};
      let draftCell=cell(),appliedBlocked=false;
      const discard=document.createElement('button');discard.type='button';discard.textContent='Discard unapplied wall change';form.append(discard);
      const appliedLabel=document.createElement('label');appliedLabel.textContent='Applied wall edits';const applied=document.createElement('select');applied.setAttribute('aria-label','Applied wall edits');appliedLabel.append(applied);form.prepend(appliedLabel);
      const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent='Choose an authored cell…';applied.append(placeholder);
      const wallEdits=[...(snapshot.authored?.edits??[])].sort((a,b)=>a.row-b.row||a.column-b.column||a.quadrant-b.quadrant);
      for(const [index,edit] of wallEdits.entries()){const option=document.createElement('option');option.value=String(index);option.textContent=`Row ${edit.row} · column ${edit.column} · quadrant ${edit.quadrant} · ${edit.blocked?'blocked':'unblocked'}`;applied.append(option);}
      const restore=document.createElement('button');restore.type='button';restore.textContent='Restore selected cell to retail';form.append(restore);
      const sameCell=(a,b)=>a.row===b.row&&a.column===b.column&&a.quadrant===b.quadrant;
      const dirty=()=>form.elements.blocked.checked!==appliedBlocked;
      const updateDraft=()=>{discard.disabled=!dirty();for(const name of ['row','column','quadrant'])form.elements[name].disabled=dirty();applied.disabled=dirty()||!wallEdits.length;restore.disabled=dirty()||!wallEdits.some(e=>sameCell(e,cell()));form.querySelector('[type="submit"]').disabled=!dirty();const index=wallEdits.findIndex(e=>sameCell(e,cell()));applied.value=index<0?'':String(index);};
      const selectCell=()=>{draftCell=cell();refresh();appliedBlocked=form.elements.blocked.checked;updateDraft();};
      applied.onchange=()=>{if(dirty()){updateDraft();return;}const edit=wallEdits[Number(applied.value)];if(!edit||applied.value==='')return;for(const name of ['row','column','quadrant'])form.elements[name].value=edit[name];selectCell();};
      for(const name of ['row','column','quadrant'])form.elements[name].oninput=()=>{if(dirty()){for(const axis of ['row','column','quadrant'])form.elements[axis].value=draftCell[axis];return;}selectCell();};
      form.elements.blocked.oninput=updateDraft;discard.onclick=()=>{form.elements.blocked.checked=appliedBlocked;updateDraft();};selectCell();
      const locateCell=document.createElement('button');locateCell.type='button';locateCell.textContent='Locate cell in viewport';form.append(locateCell);
      locateCell.onclick=async()=>{
        if(busy||resourceStateKey()!==key||state.scene.id!==scene||!form.reportValidity())return;
        if(dirty()){fieldDialog.querySelector('.dialog-error').textContent='Apply or discard the wall change before locating its cell.';return;}
        const c=cell(),point={x:c.column*128+(c.quadrant&1)*64+32,y:0,z:c.row*128-128+(c.quadrant>>1)*64+32},sourceKey=state.scene_preview_source_key;
        setBusy(true);locateCell.disabled=true;
        try{
          const response=await fetch('/api/terrain-point',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({x:point.x,z:point.z,source_key:sourceKey})});
          const result=await response.json();if(!response.ok)throw new Error(result.error||'Terrain sampling failed');
          if(resourceStateKey()!==key||state.scene.id!==scene||result.source_key!==state.scene_preview_source_key||result.scene_id!==scene)throw new Error('Scene changed while locating the cell');
          if(result.position?.y!==null&&!numeric(result.position?.y))throw new Error('Terrain sample returned an invalid height');
          point.y=result.position.y??0;
          coordinateProbe={point,context:JSON.stringify([state.project?.path,state.scene?.id])};cancelViewportGesture();camera.target=displayPosition(point);camera.distance=1000;cameraRevision++;
          fieldDialog.close();document.querySelector('.workspace-tabs [data-panel="viewport"]').click();draw();
          notify(result.position.y===null?'No source terrain at this cell; locator uses a Y=0 display placeholder.':'Cell located using source terrain elevation; runtime height remains unverified.');
        }catch(error){fieldDialog.querySelector('.dialog-error').textContent=error.message;}
        finally{locateCell.disabled=false;setBusy(false);}
      };
      const apply=async command=>{if(busy||state.project.mode!=='edit'||resourceStateKey()!==key||state.scene.id!==scene)return;await api('/api/command',command,{dialog:fieldDialog,success:'Source wall edits updated. Save project to persist.'});};
      const applyEdits=edits=>apply(edits.length?{type:'set_collision_walls',entity_id:scene,value:{source_sha256:snapshot.asset.source_record.containing_span_sha256,edits}}:{type:'clear_collision_walls',entity_id:scene});
      const rectangleButton=document.createElement('button');rectangleButton.textContent='Edit wall rectangle…';summary.append(rectangleButton);rectangleButton.onclick=()=>{if(dirty()){notify('Apply or discard the single-cell wall change first.',true);return;}if(busy||resourceStateKey()!==key||state.scene.id!==scene)return;fieldDialog.close();wallRectangleTool.open();};
      const floorButton=document.createElement('button');floorButton.textContent='Edit floor tiers…';summary.append(floorButton);floorButton.onclick=()=>{if(dirty()){notify('Apply or discard the single-cell wall change first.',true);return;}if(busy||resourceStateKey()!==key||state.scene.id!==scene)return;fieldDialog.close();floorRectangleTool.open();};
      const heightButton=document.createElement('button');heightButton.textContent='Edit floor heights…';summary.append(heightButton);heightButton.onclick=()=>{if(dirty()){notify('Apply or discard the single-cell wall change first.',true);return;}if(busy||resourceStateKey()!==key||state.scene.id!==scene)return;fieldDialog.close();floorHeightTool.open();};
      restore.onclick=()=>{if(dirty()||!form.reportValidity())return;return applyEdits(wallEdits.filter(e=>!sameCell(e,cell())));};
      form.onsubmit=async event=>{event.preventDefault();if(!dirty()||!form.reportValidity())return;const c=cell(),edits=wallEdits.filter(e=>!sameCell(e,c)),change=snapshot.authored_changes?.find(e=>sameCell(e,c)),retailBlocked=change?change.before_value:appliedBlocked;if(form.elements.blocked.checked!==retailBlocked)edits.push({...c,blocked:form.elements.blocked.checked});await applyEdits(edits);};
      form.querySelector('.clear-collision').disabled=!snapshot.authored?.edits?.length;form.querySelector('.clear-collision').onclick=()=>apply({type:'clear_collision_walls',entity_id:scene});
    };
  }
  if(record.type==='region'&&state.capabilities?.field_region_authoring){const button=document.createElement('button');button.id='edit-field-region-bounds';button.textContent='Edit region bounds';button.onclick=()=>{if(busy)return;fieldDialog.close();inspectRegionBounds(record);};summary.append(button);}
  if(record.type==='trigger'&&record.data?.table_source==='primary'&&state.capabilities?.field_trigger_authoring){const button=document.createElement('button');button.id='edit-field-trigger-cell';button.textContent='Edit trigger cell';button.onclick=()=>{if(busy)return;fieldDialog.close();inspectTriggerCells(record);};summary.append(button);}
  if(record.type==='trigger'&&state.capabilities?.trigger_script_preview&&(data.script_reference?.partition===2||data.trigger_type==='partition_2_trigger')){
    const button=document.createElement('button');button.className='accent';button.id='inspect-trigger-script';button.textContent='Inspect referenced script';button.onclick=()=>openTriggerScript(record);summary.append(button);
  }
  fieldDialog.showModal();
}
const triggerScriptDialog=document.createElement('dialog');triggerScriptDialog.id='trigger-script-dialog';document.body.append(triggerScriptDialog);
let triggerScriptAbort=null,triggerScriptRequest=0;
function clearTriggerScript(close=true){
  triggerScriptRequest++;const pending=triggerScriptAbort;triggerScriptAbort=null;pending?.abort();if(pending)setBusy(false);
  if(close&&triggerScriptDialog.open)triggerScriptDialog.close();triggerScriptDialog.replaceChildren();
}
triggerScriptDialog.addEventListener('close',()=>clearTriggerScript(false));
function validateTriggerScript(result,record,key){
  const expected=record.data.script_reference?.record_index ?? record.data.encoded?.record_index;
  if(result.read_only!==true||key!==resourceStateKey()||result.source_key!==state.scene_preview_source_key||result.scene_id!==state.scene?.id||result.trigger_id!==record.id||result.partition!==2||!Number.isInteger(result.record_index)||result.record_index<0||(Number.isInteger(expected)&&result.record_index!==expected)||typeof result.script_id!=='string')throw new Error('Referenced script source changed or did not match the trigger. Refresh resources and retry.');
  if(!result.record||![result.record.byte_offset,result.record.byte_length,result.record.script_offset].every(value=>Number.isSafeInteger(value)&&value>=0))throw new Error('Referenced script record bounds are invalid.');
  const report=result.inspection;
  if(!report||typeof report.status!=='string')throw new Error('Referenced script inspection is missing.');
  for(const [key,max] of [['instructions',65536],['dialogues',4096],['opaque_regions',65536],['stops',4096]])if(!Array.isArray(report[key])||report[key].length>max||report[key].some(row=>!row||typeof row!=='object'||Array.isArray(row)))throw new Error('Referenced script report contains invalid or oversized arrays.');
  if(report.instructions.some(row=>!Number.isInteger(row.pc)||row.pc<0||typeof row.mnemonic!=='string'||!Array.isArray(row.successors)||row.successors.length>64||row.successors.some(next=>!next||!Number.isInteger(next.pc))))throw new Error('Referenced script instructions are invalid.');
  let tokens=0;
  for(const dialogue of report.dialogues){if(!Number.isInteger(dialogue.pc)||typeof dialogue.text!=='string'||dialogue.text.length>131072||!Array.isArray(dialogue.tokens)||dialogue.tokens.some(token=>!token||typeof token!=='object'))throw new Error('Referenced dialogue data is invalid.');tokens+=dialogue.tokens.length;}
  if(tokens>65536)throw new Error('Referenced dialogue token count exceeds the preview limit.');
  return report;
}
async function openTriggerScript(record){
  if(busy||!state.capabilities?.trigger_script_preview||resourceKey!==resourceStateKey())return;
  clearTriggerScript();fieldDialog.close();const key=resourceStateKey(),request=++triggerScriptRequest,controller=new AbortController();triggerScriptAbort=controller;
  triggerScriptDialog.innerHTML=`<div class="dialog-heading"><h2>Referenced partition-2 script</h2><button id="close-trigger-script" aria-label="Close referenced script">×</button></div><div class="trigger-script-navigation"><button id="back-trigger">Back to trigger</button><span>Read only · source inspection</span></div><div id="trigger-script-report"><p>Verifying the trigger reference and bounded script record…</p></div><p class="dialog-error" role="alert"></p>`;
  $('close-trigger-script').onclick=()=>clearTriggerScript();$('back-trigger').onclick=()=>{clearTriggerScript();if(key===resourceStateKey())openFieldResource(record);};triggerScriptDialog.showModal();setBusy(true);
  try{
    const response=await fetch('/api/trigger-script',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:record.id}),signal:controller.signal});
    const text=await response.text();if(text.length>8388608)throw new Error('Referenced script exceeds the bounded preview size.');const result=JSON.parse(text);if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Referenced script inspection failed');
    if(controller.signal.aborted||request!==triggerScriptRequest||!triggerScriptDialog.open)return;
    const report=validateTriggerScript(result,record,key);renderTriggerScript(result,report);
    const edit=document.createElement('button');edit.textContent='Open dialogue workspace';
    edit.onclick=()=>{if(busy)return;clearTriggerScript();openActorScript({id:result.script_id.replace(/^script:\/\//,'scene://'),name:`Partition 2 script ${result.record_index}`,triggerId:record.id});};
    triggerScriptDialog.querySelector('.trigger-script-navigation').append(edit);
  }catch(error){if(error.name!=='AbortError'&&request===triggerScriptRequest&&triggerScriptDialog.open){$('trigger-script-report').replaceChildren();triggerScriptDialog.querySelector('.dialog-error').textContent=error.message;}}
  finally{if(triggerScriptAbort===controller){triggerScriptAbort=null;setBusy(false);}}
}
function appendScriptOperands(cell,instruction,menuEditors=new Map(),focusMenuRun=null){
  const operands=instruction.operands;
  const hasCaptureSummary=appendCaptureSummary(cell,instruction);
  if(instruction.mnemonic==='DIALOGUE_SEGMENT'){const text=document.createElement('p');text.textContent=operands?.text??'';cell.append(text);return;}
  if(instruction.target_context!==null&&instruction.target_context!==undefined){
    const context=document.createElement('p');context.className='script-warning';
    context.textContent=`Extended target ${instruction.target_context}: actor identity is unresolved.`;cell.append(context);
  }
  if(instruction.mnemonic==='ACTOR_POSITION'&&Array.isArray(operands?.encoded_xyz)&&operands.encoded_xyz.length===3){
    const summary=document.createElement('p');
    const immediate=operands.mode==='immediate';
    const axes=operands.encoded_xyz.map((value,index)=>`${'XYZ'[index]}: ${immediate&&value===65535?'leave unchanged':value}`).join(', ');
    summary.textContent=`${axes}. ${immediate?'Immediate assignment':`Timed movement (${operands.ticks} encoded ticks; interpolation unresolved)`}. Runtime position is not observed.`;
    cell.append(summary);
  }
  if(instruction.mnemonic==='SET_ACTOR_MODEL'&&Number.isInteger(operands?.model_selector_signed)){
    const summary=document.createElement('p');summary.textContent=`Model selector ${operands.model_selector_signed} (u16 ${operands.model_selector_u16}). High-pool flag ${operands.high_pool_flag?'set':'clear'}. Runtime pool bases and resolved model asset are unknown; branch execution is not observed.`;cell.append(summary);
  }
  if(['NPC_RUN','MOVE_TO'].includes(instruction.mnemonic)&&Number.isFinite(operands?.target_position?.x)&&Number.isFinite(operands?.target_position?.z)){
    const target=operands.target_position,summary=document.createElement('p');
    summary.textContent=`${instruction.mnemonic==='MOVE_TO'?'Teleport':'Script'} target X ${target.x}, Z ${target.z}. Y is unresolved.${operands.parked_target?' Parked/off-field target.':''} Branch execution and current actor position are not observed.`;
    const locate=document.createElement('button');locate.type='button';locate.className='script-locate-target';locate.textContent='Locate target…';
    const context=JSON.stringify([state.project?.path,state.scene?.id]);
    locate.onclick=()=>{
      if(context!==JSON.stringify([state.project?.path,state.scene?.id]))return;
      cell.closest('dialog')?.close();
      for(const axis of ['x','z'])locateDialog.querySelector(`[name="${axis}"]`).value=target[axis];
      const height=locateDialog.querySelector('[name="y"]');height.value='';height.placeholder='Enter a reference height; script Y is unknown';
      locateDialog.showModal();height.focus();
    };
    cell.append(summary,locate);
  }
  if(instruction.mnemonic==='DIALOGUE_PICKER'&&Array.isArray(operands?.options)){
    const options=document.createElement('ol');
    for(const option of operands.options){
      const item=document.createElement('li');item.textContent=`${option.label} — encoded target ${scriptOffset(option.encoded_target)}`;
      for(const run of menuEditors.get(`${instruction.pc}:${option.index}`)??[]){
        const layers=document.createElement('p');layers.className='instruction-operand-layers';
        layers.textContent=`Label run ${scriptOffset(run.pc)} · Retail ${JSON.stringify(run.retail)} · Authored ${run.authored===null?'none':JSON.stringify(run.authored)} · Effective ${JSON.stringify(run.effective)}`;
        item.append(layers);
        if(focusMenuRun){const edit=document.createElement('button');edit.type='button';edit.textContent='Open label editor';edit.dataset.menuRun=run.id;
          edit.setAttribute('aria-label',`Open menu option ${option.index+1} label editor at ${scriptOffset(run.pc)}`);edit.onclick=()=>focusMenuRun(run.id);item.append(edit);}
      }
      options.append(item);
    }
    const note=document.createElement('p');note.className='field-note';note.textContent='Runtime choice and pager continuation are unresolved. Decoded choice paths can be inspected through the successor links.';
    cell.append(options,note);
  }
  const details=document.createElement('details'),label=document.createElement('summary'),raw=document.createElement('pre');
  label.textContent='Encoded operands';raw.textContent=typeof operands==='string'?operands:JSON.stringify(operands??{},null,2);
  details.open=!hasCaptureSummary&&!['ACTOR_POSITION','DIALOGUE_PICKER','NPC_RUN','MOVE_TO','SET_ACTOR_MODEL'].includes(instruction.mnemonic);details.append(label,raw);cell.append(details);
}
function appendScriptInstructions(host,report,identity=report.semantic_id??report.script_id??'Inspected script',movementAuthoring=report.movement_authoring,onSelect=null,walkthroughOptions=null){
  host.replaceChildren();host.classList.remove('script-table-wrap');
  const unvisited=new Set(walkthroughOptions?[...(report.unvisited_instructions??[]),...(report.unvisited_dialogues??[])].map(row=>row.pc):[]);
  const messages=[...(report.dialogues??[]),...(walkthroughOptions?report.unvisited_dialogues??[]:[])].map(message=>({pc:message.pc,mnemonic:'DIALOGUE_SEGMENT',operands:{text:message.text},
    successors:[{pc:message.pc+message.length,condition:'encoded_continuation'}]}));
  const instructions=[...(report.instructions??[]),...(walkthroughOptions?report.unvisited_instructions??[]:[]),...messages].sort((a,b)=>a.pc-b.pc),byPC=new Map(instructions.map(item=>[item.pc,item])),rows=new Map(),incoming=new Map(),history=[];
  let selectedPC=null;
  const navigation=document.createElement('div');navigation.className='script-path-navigation';
  const back=document.createElement('button');back.textContent='Back to previous instruction';back.disabled=true;
  const status=document.createElement('p');status.className='field-note';status.setAttribute('role','status');status.textContent='Follow decoded successors or select an offset. These links do not simulate execution.';
  const predecessors=document.createElement('div');predecessors.className='script-predecessors';
  navigation.append(back,status,predecessors);host.append(navigation);
  const targets=instructions.filter(row=>['MOVE_TO','NPC_RUN'].includes(row.mnemonic)&&
    row.operands?.coordinate_system==='retail_field_world_units'&&numeric(row.operands?.target_position?.x)&&numeric(row.operands?.target_position?.z))
    .map(row=>({pc:row.pc,mnemonic:row.mnemonic,position:{...row.operands.target_position},context:row.target_context,parked:!!row.operands.parked_target}));
  if(targets.length&&!walkthroughOptions){
    const tools=document.createElement('div');tools.className='script-target-controls';
    const label=document.createElement('label');label.textContent='Reference Y ';
    const height=document.createElement('input');height.type='number';height.step='any';height.min='-1000000000';height.max='1000000000';height.required=true;height.setAttribute('aria-label','Script targets reference Y');height.placeholder='Script height is unknown';label.append(height);
    const show=document.createElement('button');show.type='button';show.className='script-show-targets';show.textContent=`Show ${targets.length} targets in scene`;show.disabled=targets.length>256;
    const note=document.createElement('p');note.className='field-note';note.textContent=targets.length>256?'This report exceeds the 256-marker overlay limit. Locate individual instructions instead.':'All markers use your reference Y. No movement path, current actor position or executed branch is inferred; parked targets remain included.';
    const layer=document.createElement('select');layer.setAttribute('aria-label','Script target layer');
    const importedOption=document.createElement('option');importedOption.value='retail';importedOption.textContent='Retail source targets';
    const effectiveOption=document.createElement('option');effectiveOption.value='authored';effectiveOption.textContent='Authored effective targets';
    const effective=new Map((movementAuthoring?.targets??[]).map(target=>[target.pc,target]));
    effectiveOption.disabled=movementAuthoring?.supported!==true||!!movementAuthoring?.unresolved_overrides?.length||!targets.every(target=>{const item=effective.get(target.pc);return item?.mnemonic===target.mnemonic&&numeric(item.effective_values?.x)&&numeric(item.effective_values?.z);});
    layer.append(importedOption,effectiveOption);
    const key=resourceStateKey();
    show.onclick=()=>{
      if(busy||key!==resourceStateKey()||!height.reportValidity()||!height.value.trim()||!numeric(Number(height.value)))return;
      if(layer.value==='authored'&&effectiveOption.disabled)return;
      const chosen=layer.value==='authored'?targets.map(target=>({...target,position:{...target.position,...effective.get(target.pc).effective_values},parked:!!effective.get(target.pc).effective_parked_target})):targets;
      scriptTargetOverlay?.onClear?.();
      scriptTargetOverlay={key,identity,targets:chosen,representation:layer.value,height:Number(height.value),partial:report.status==='partial'};
      const targetSelect=scriptTargetTools.querySelector('select');targetSelect.replaceChildren();
      for(const target of chosen){const option=document.createElement('option');option.value=target.pc;option.textContent=`${scriptOffset(target.pc)} ${target.mnemonic} · X ${target.position.x}, Z ${target.position.z}`;targetSelect.append(option);}
      host.closest('dialog')?.close();frameScriptTargets();
    };
    tools.append(layer,label,show,note);navigation.prepend(tools);
  }
  for(const instruction of instructions)for(const next of instruction.successors??[]){
    if(!incoming.has(next.pc))incoming.set(next.pc,new Set());incoming.get(next.pc).add(instruction.pc);
  }
  function select(pc,remember=true,reveal=true){
    if(!rows.has(pc))return false;
    const disassembly=host.closest('details.script-instructions');if(disassembly)disassembly.open=true;
    if(remember&&selectedPC!==null&&selectedPC!==pc)history.push(selectedPC);
    if(rows.has(selectedPC))rows.get(selectedPC).classList.remove('script-path-selected');
    selectedPC=pc;const row=rows.get(pc);row.classList.add('script-path-selected');if(reveal){row.scrollIntoView({block:'nearest'});row.focus({preventScroll:true});}
    back.disabled=!history.length;status.textContent=`Selected ${scriptOffset(pc)} · ${byPC.get(pc).mnemonic} · Decoded incoming edges (execution unknown)`;
    predecessors.replaceChildren();
    for(const source of incoming.get(pc)??[]){const button=document.createElement('button');button.textContent=`From ${scriptOffset(source)}`;button.onclick=()=>select(source);predecessors.append(button);}
    if(!predecessors.childNodes.length)predecessors.textContent='No decoded incoming edges in this report.';
    onSelect?.(pc);
    return true;
  }
  back.onclick=()=>{if(history.length)select(history.pop(),false);};
  const flowOverview=mountScriptFlowOverview(navigation,{selectInstruction:pc=>select(pc),label:walkthroughOptions?'Current NPC source flow':'Retail source flow'});
  flowOverview.update(report);
  const walkthroughKey=resourceStateKey();
  mountScriptWalkthrough(navigation,{report,selection:()=>selectedPC,selectInstruction:(pc,reveal=true)=>select(pc,true,reveal),busy:()=>busy,
    current:()=>host.isConnected&&walkthroughKey===resourceStateKey(),
    getContext:()=>({project_path:state.project?.path,scene_id:state.scene?.id,script_id:identity,project_source_key:state.project_copy_source_key,record_sha256:report.record?.sha256,representation:'retail_source'}),
    requalify:async({signal})=>{
      const route=identity.includes('/actors/man-p1/')?'/api/actor-script':'/api/partition-two-script';
      const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:identity.replace(/^script:\/\//,'scene://')}),signal});
      const raw=await response.text();if(raw.length>4*1024*1024)throw Error('Script requalification exceeds inspection bounds.');const source=JSON.parse(raw);
      if(!response.ok||source.error||source.record?.sha256!==report.record?.sha256)throw Error('Retail script source changed.');
      const check=await fetch('/api/state',{signal}),value=await check.json();
      if(!check.ok||value.project?.path!==state.project?.path||value.scene?.id!==state.scene?.id||value.project_copy_source_key!==state.project_copy_source_key||walkthroughKey!==resourceStateKey())throw Error('Authoritative project context changed.');return true;
    },onError:error=>notify(error.message,true),...(walkthroughOptions??{})});
  let pathStart=null;
  const pathTools=document.createElement('details');pathTools.className='script-path-query';pathTools.innerHTML='<summary>Find a decoded instruction path</summary><p>Choose a start instruction, then select a destination. This finds one shortest route through encoded successors. Conditions are retained but not evaluated; hidden or undecoded execution remains unknown.</p><button type="button" data-path-start>Use selected instruction as path start</button><p data-path-source>No path start selected.</p><button type="button" data-path-find>Find path to selected instruction</button><p data-path-result role="status"></p><div data-path-steps></div>';
  navigation.append(pathTools);
  pathTools.querySelector('[data-path-start]').onclick=()=>{if(selectedPC===null)return;pathStart=selectedPC;pathTools.querySelector('[data-path-source]').textContent=`Start ${scriptOffset(pathStart)} · ${byPC.get(pathStart).mnemonic}`;pathTools.querySelector('[data-path-result]').textContent='Select a destination, then Find path.';pathTools.querySelector('[data-path-steps]').replaceChildren();};
  pathTools.querySelector('[data-path-find]').onclick=()=>{
    const resultHost=pathTools.querySelector('[data-path-result]'),steps=pathTools.querySelector('[data-path-steps]');steps.replaceChildren();
    if(pathStart===null||selectedPC===null){resultHost.textContent='Select a decoded start and destination first.';return;}
    try{
      const result=findDecodedPath(instructions,pathStart,selectedPC);
      if(result.status==='no_decoded_path'){resultHost.textContent=`No decoded path from ${scriptOffset(pathStart)} to ${scriptOffset(selectedPC)}. ${result.visited_count} boundaries searched; ${result.undecoded_target_count} outgoing targets are not decoded. This does not prove gameplay cannot reach the destination.`;for(const pc of result.undecoded_targets){const note=document.createElement('p');const stop=(report.stops??[]).find(item=>item.pc===pc);note.textContent=`Undecoded ${scriptOffset(pc)}${stop?.reason?' · '+stop.reason:''}`;steps.append(note);}return;}
      resultHost.textContent=`Possible encoded path: ${result.path.length} instructions · ${result.path.length-1} edges · conditions not evaluated${result.path.length>256?' · showing first 256 instructions':''}.`;
      for(const item of result.path.slice(0,256)){const row=document.createElement('p'),button=document.createElement('button');button.textContent=`Inspect ${scriptOffset(item.pc)} · ${byPC.get(item.pc).mnemonic}`;button.onclick=()=>select(item.pc);row.append(button);if(item.condition!==null){const condition=document.createElement('span');condition.textContent=' · via '+(typeof item.condition==='string'?item.condition:JSON.stringify(item.condition));row.append(condition);}steps.append(row);}
    }catch(error){resultHost.textContent=error.message;}
  };

  const search=document.createElement('input');search.type='search';search.setAttribute('aria-label','Search decoded script paths');search.placeholder='Text, instruction, operand or offset';search.maxLength=256;
  const previous=document.createElement('button');previous.textContent='Previous match';
  const next=document.createElement('button');next.textContent='Next match';
  const matchesStatus=document.createElement('p');matchesStatus.className='field-note';matchesStatus.setAttribute('role','status');
  const searchBar=document.createElement('div');searchBar.className='script-path-search';searchBar.append(search,previous,next);navigation.prepend(searchBar,matchesStatus);
  const searchable=instructions.map(node=>({pc:node.pc,text:`${scriptOffset(node.pc)} ${node.mnemonic} ${JSON.stringify(node.operands??{})}`.toLowerCase()}));
  let matches=[],matchIndex=-1;
  function updateMatches(){
    const query=search.value.trim().toLowerCase();matches=query?searchable.filter(node=>node.text.includes(query)).map(node=>node.pc):[];matchIndex=-1;
    previous.disabled=next.disabled=!matches.length;
    matchesStatus.textContent=query?`${matches.length} matching decoded paths`:'Search covers decoded paths only; opaque bytes are excluded.';
  }
  function stepMatch(direction){if(!matches.length)return;matchIndex=matchIndex<0?(direction>0?0:matches.length-1):(matchIndex+direction+matches.length)%matches.length;select(matches[matchIndex]);matchesStatus.textContent=`Match ${matchIndex+1} of ${matches.length}`;}
  search.oninput=updateMatches;search.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();stepMatch(event.shiftKey?-1:1);}};
  previous.onclick=()=>stepMatch(-1);next.onclick=()=>stepMatch(1);updateMatches();

  const wrap=document.createElement('div');wrap.className='script-table-wrap';wrap.innerHTML='<table><thead><tr><th>Record offset</th><th>Instruction</th><th>Operands</th><th>Successors</th></tr></thead><tbody></tbody></table>';host.append(wrap);
  const body=wrap.querySelector('tbody'),operandEditors=instructionOperandEditors(report),menuEditors=menuLabelEditors(report),operandKey=resourceStateKey();
  const focusMenuRun=host.closest('dialog')===scriptDialog?id=>{
    if(busy||!scriptDialog.open||report!==scriptReport||operandKey!==resourceStateKey())return;
    const input=[...scriptDialog.querySelectorAll('[data-run-input]')].find(item=>item.dataset.runInput===id);
    if(!input)return;input.closest('form').scrollIntoView({block:'center'});input.focus({preventScroll:true});
  }:null;
  for(const instruction of instructions){
    const row=document.createElement('tr');row.tabIndex=-1;rows.set(instruction.pc,row);
    const offset=document.createElement('td'),jump=document.createElement('button');jump.textContent=scriptOffset(instruction.pc);jump.setAttribute('aria-label',`Select instruction ${scriptOffset(instruction.pc)}`);jump.onclick=()=>select(instruction.pc);offset.append(jump);row.append(offset);
    const mnemonic=document.createElement('td');mnemonic.textContent=instruction.mnemonic+(unvisited.has(instruction.pc)?' · unvisited source anchor':'');row.append(mnemonic);
    const operands=document.createElement('td');appendScriptOperands(operands,instruction,menuEditors,focusMenuRun);row.append(operands);
    const editor=operandEditors.get(instruction.pc);
    if(editor){
      const layers=document.createElement('p');layers.className='instruction-operand-layers';
      const describe=values=>Object.entries(values).map(([field,value])=>`${field}: ${value}`).join(', ')||'none';
      layers.textContent=`Retail ${describe(editor.retail)} · Authored ${describe(editor.authored)} · Effective ${describe(editor.effective)}`;operands.append(layers);
      if(host.closest('dialog')===scriptDialog){
        const edit=document.createElement('button');edit.type='button';edit.textContent='Open operand editor';edit.setAttribute('aria-label',`Open operand editor at ${scriptOffset(instruction.pc)}`);
        edit.onclick=()=>{if(busy||operandKey!==resourceStateKey())return;
          const form=[...scriptDialog.querySelectorAll(`.${editor.kind}-entry`)].find(item=>item.dataset[editor.kind+'Id']===editor.id);
          if(!form)return;form.scrollIntoView({block:'center'});form.querySelector('input:not(:disabled)')?.focus({preventScroll:true});
        };operands.append(edit);
      }
    }
    const successors=document.createElement('td');
    for(const next of instruction.successors??[]){
      const condition=next.condition?(typeof next.condition==='string'?next.condition:JSON.stringify(next.condition)):'';
      if(byPC.has(next.pc)){const button=document.createElement('button');button.textContent=`To ${scriptOffset(next.pc)}${condition?' · '+condition:''}`;button.onclick=()=>{if(selectedPC!==instruction.pc)select(instruction.pc);select(next.pc);};successors.append(button);}
      else{const note=document.createElement('p');note.className='field-note';const stop=(report.stops??[]).find(item=>item.pc===next.pc);note.textContent=`${scriptOffset(next.pc)} · Not decoded${condition?' · '+condition:''}${stop?.reason?' · '+stop.reason:''}`;successors.append(note);}
    }
    if(!(instruction.successors??[]).length)successors.textContent='No decoded successor';
    row.append(successors);body.append(row);
  }
  if(!instructions.length){status.textContent='No instructions were decoded.';wrap.hidden=true;}
  return {select,selected:()=>selectedPC};
}
function renderTriggerScript(result,report){
  const host=$('trigger-script-report');
  host.innerHTML=`<p class="script-summary">${report.instructions.length} decoded instructions · ${report.dialogues.length} dialogue segments · ${escapeHTML(report.status==='decoded_supported_paths'?'Supported paths decoded':resourceLabel(report.status))}</p>${property('Script ID',result.script_id)}${property('Partition / record',`2 / ${result.record_index}`)}${property('Decoded MAN byte offset',result.record.byte_offset)}${property('Record byte length',result.record.byte_length)}${property('Script offset in record',scriptOffset(result.record.script_offset))}<p class="field-note">Offsets are relative to this bounded script record. Decoding does not establish trigger activation, branch execution or story state. Substitution tokens remain placeholders. Open the dialogue workspace to check which text runs support editing.</p><div id="trigger-script-warnings"></div><section><h3>Decoded dialogue</h3><div id="trigger-script-dialogues"></div></section><details class="script-instructions" ${report.dialogues.length?'':'open'}><summary>Instruction paths (${report.instructions.length})</summary><div id="trigger-script-instructions"></div></details><details class="script-raw"><summary>Source bounds, raw bytes and complete provenance</summary><pre class="diagnostic-detail"></pre></details>`;
  const warnings=$('trigger-script-warnings');
  if(report.opaque_regions.length||report.stops.length){const notice=document.createElement('p');notice.className='script-warning';notice.textContent=`${report.opaque_regions.length} opaque regions · ${report.stops.length} decoder stops. Unsupported and unvisited bytes remain unresolved.`;warnings.append(notice);}
  for(const item of report.opaque_regions){const line=document.createElement('p');line.className='field-note';line.textContent=`${scriptOffset(item.pc)} · ${item.length ?? 'Unknown'} opaque bytes: ${item.reason ?? 'Unresolved region'}`;warnings.append(line);}
  for(const item of report.stops){const line=document.createElement('p');line.className='field-note';line.textContent=`Stopped at ${scriptOffset(item.pc)}: ${item.reason ?? 'Unsupported path'}`;warnings.append(line);}
  for(const limit of result.limitations ?? []){const line=document.createElement('p');line.className='field-note';line.textContent=typeof limit==='string'?limit:JSON.stringify(limit);warnings.append(line);}
  const dialogues=$('trigger-script-dialogues');if(!report.dialogues.length)dialogues.textContent='No dialogue was decoded in these paths.';
  for(const dialogue of report.dialogues){const card=document.createElement('article');card.className='script-dialogue-card';card.innerHTML=`<small>Imported segment · ${escapeHTML(scriptOffset(dialogue.pc))} · ${escapeHTML(dialogue.length ?? 'Unknown')} bytes</small><p></p><details><summary>Text tokens and source span</summary><pre class="diagnostic-detail"></pre></details>`;card.querySelector('p').textContent=dialogue.text;card.querySelector('pre').textContent=JSON.stringify(dialogue,null,2);dialogues.append(card);}
  appendScriptInstructions($('trigger-script-instructions'),{...report,record:result.record},result.script_id,result.movement_authoring);
  host.querySelector('.script-raw pre').textContent=JSON.stringify(result,null,2);
}
function drawFieldMap(){
  if(!fieldMap||fieldKey!==resourceStateKey())return;
  ctx.save();ctx.strokeStyle='#e1ac688f';ctx.fillStyle='#d39d4b10';ctx.lineWidth=1;
  const deltas=(fieldMap.authored_changes??[]).map(change=>{const x=change.column*128+(change.quadrant&1)*64,z=change.row*128-128+(change.quadrant>>1)*64;return {x_min:x,x_max:x+64,z_min:z,z_max:z+64,added:change.after_value};});
  for(const rectangle of [...fieldMap.rectangles,...deltas]){
    if(rectangle.added!==undefined){ctx.strokeStyle=rectangle.added?'#68f0ac':'#ff91b8';ctx.fillStyle=rectangle.added?'#68f0ac30':'#ff91b818';ctx.lineWidth=3;ctx.setLineDash(rectangle.added?[]:[6,4]);}
    const points=[[rectangle.x_min,rectangle.z_min],[rectangle.x_max,rectangle.z_min],[rectangle.x_max,rectangle.z_max],[rectangle.x_min,rectangle.z_max]].map(([x,z])=>project({x,y:0,z}));
    if(points.some(p=>!p||!numeric(p.x)||!numeric(p.y))||points.every(p=>p.x<0)||points.every(p=>p.x>width)||points.every(p=>p.y<0)||points.every(p=>p.y>height))continue;
    ctx.beginPath();ctx.moveTo(points[0].x,points[0].y);for(const point of points.slice(1))ctx.lineTo(point.x,point.y);ctx.closePath();ctx.fill();ctx.stroke();
  }
  ctx.restore();
}
function drawWallSelection(){
  const polygons=[];
  if(wallSelection){const g=wallSelectionGeometry(wallSelection);polygons.push({...g,color:'#68f0ac',fill:'#68f0ac25'});}
  if(wallInspection&&wallSourceCurrent()&&wallInspection.report.project_source_key===state.project_copy_source_key){const g=wallRectangleGeometry(wallInspection.report,wallInspection.layer);for(const cell of g.cells)polygons.push({x_min:g.x+cell.x,x_max:g.x+cell.x+64,z_min:g.z+cell.z,z_max:g.z+cell.z+64,color:cell.changed?'#68f0ac':'#b6cad7',fill:cell.blocked?'#dc9851a0':'#314359c0'});}
  ctx.save();ctx.lineWidth=2;ctx.setLineDash([]);
  for(const item of polygons){const points=[[item.x_min,item.z_min],[item.x_max,item.z_min],[item.x_max,item.z_max],[item.x_min,item.z_max]].map(([x,z])=>project({x,y:0,z}));if(points.some(p=>!p))continue;ctx.strokeStyle=item.color;ctx.fillStyle=item.fill;ctx.beginPath();ctx.moveTo(points[0].x,points[0].y);for(const p of points.slice(1))ctx.lineTo(p.x,p.y);ctx.closePath();ctx.fill();ctx.stroke();}
  ctx.restore();
}
const textureDialog=document.createElement('dialog');textureDialog.id='texture-dialog';document.body.append(textureDialog);
let textureRequest=0,textureAbort=null,textureSession=null,texturePreview=null,textureCommandPending=false;
let texturePngEditor=null;
const textureProjectKey=()=>JSON.stringify([state.project?.path,state.scene?.id]);
const canEditTexture=()=>state.capabilities?.texture_replacement===true&&(state.project?.mode ?? 'edit').toLowerCase()==='edit';
textureDialog.addEventListener('close',()=>{textureRequest++;textureAbort?.abort();if(texturePaletteDialog.open)texturePaletteDialog.close();if(texturePixelDialog.open)texturePixelDialog.close();if(textureFileDialog.open)textureFileDialog.close();if(textureRectangleDialog.open)textureRectangleDialog.close();if(textureUsageDialog.open)textureUsageDialog.close();});
function textureAuthored(){if(textureSession?.record.id?.startsWith('texture-new://'))return state.texture_additions?.[textureSession.record.id]??null;return state.texture_overrides?state.texture_overrides[textureSession?.record.id] ?? null:texturePreview?.authored ?? null;}
async function openTexturePng(){
  if(busy||!canEditTexture()||!textureSession||!texturePreview||$('texture-file')?.files?.length||!state.capabilities?.texture_png_authoring)return;
  const assetId=textureSession.record.id,paletteIndex=textureSession.paletteIndex;
  texturePngEditor?.dispose();textureDialog.close();
  texturePngEditor=await openTexturePngEditor({assetId,paletteIndex,
    getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id??null,mode:state.project.mode,sourceKey:state.scene_preview_source_key}),
    busy:()=>busy,setBusy,onError:error=>notify(error.message??String(error),true),
    onApplied:next=>{state=next;render();notify('PNG texture applied. Save project to persist.');},
    canPreviewScene:()=>scenePreviewCurrent()&&sceneRepresentation==='authored',
    onScenePreview:(request,report,controls)=>inspectReviewedTextureProposal('/api/texture-png-scene-preview',assetId,request,report,controls,'PNG texture','Return to PNG review')});
}
let textureSlotEditor=null;
function openNewTextureSlot(){
  if(busy||!canEditTexture()||!textureSession||!texturePreview||$('texture-file')?.files?.length||!state.capabilities?.texture_slot_authoring)return;
  const assetId=textureSession.record.id;
  textureSlotEditor?.dispose();textureDialog.close();
  textureSlotEditor=openTextureSlotEditor({assetId,
    getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id??null,mode:state.project.mode,sourceKey:state.scene_preview_source_key}),
    busy:()=>busy,setBusy,onError:error=>notify(error.message??String(error),true),
    onApplied:next=>{state=next;render();notify('Authored texture slot applied. Save project to persist.');}});
}
let textureResizeEditor=null;
async function openTextureResize(){
  if(busy||!canEditTexture()||!textureSession||!texturePreview||$('texture-file')?.files?.length||!state.capabilities?.texture_resize_authoring)return;
  const assetId=textureSession.record.id,paletteIndex=textureSession.paletteIndex;
  textureResizeEditor?.dispose();textureDialog.close();
  textureResizeEditor=await openTextureResizeEditor({assetId,paletteIndex,
    getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id??null,mode:state.project.mode,sourceKey:state.scene_preview_source_key}),
    busy:()=>busy,setBusy,onError:error=>notify(error.message??String(error),true),
    onApplied:next=>{state=next;render();notify('Texture resized. Save project to persist.');},
    canPreviewScene:()=>scenePreviewCurrent()&&sceneRepresentation==='authored',
    onScenePreview:(request,report,controls)=>inspectReviewedTextureProposal('/api/texture-resize-scene-preview',assetId,request,report,controls,'resize','Return to resize review')});
}
async function inspectReviewedTextureProposal(route,assetId,request,report,{returnToEditor,isCurrent,signal},label,returnLabel){
  if(!isCurrent()||!scenePreviewCurrent()||sceneRepresentation!=='authored'||scenePreview.project_source_key!==report.project_source_key)throw new Error('Refresh the effective scene before inspecting the texture proposal.');
  const loadedKey=sceneKey,source=report.project_source_key;
  const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request),signal}),posed=await response.json();
  if(!response.ok||posed.error)throw new Error(posed.error||'Texture scene proposal failed');
  if(!isCurrent()||!scenePreviewCurrent()||sceneRepresentation!=='authored'||loadedKey!==sceneKey||state.scene_preview_source_key!==source||posed.asset_id!==assetId||posed.review_key!==report.review_key||posed.proposed_sha256!==report.proposed_sha256||posed.project_source_key!==source||!Array.isArray(posed.proposal_assets)||!Array.isArray(posed.affected_instances)||!Array.isArray(posed.unavailable_geometry_keys))throw new Error('Texture proposal differs from the reviewed source or current scene.');
  const proposedScene=structuredClone(scenePreview),seen=new Set();
  for(const row of posed.proposal_assets){const geometry=proposedScene.assets.find(a=>a.geometry_key===row.geometry_key);if(!geometry||geometry.asset_id!==row.asset_id||seen.has(row.geometry_key)||!Array.isArray(row.preview?.textures))throw new Error('Texture proposal geometry differs from the current scene.');seen.add(row.geometry_key);geometry.preview.textures=row.preview.textures;}
  try{
    stopScenePosePlayback();const failures=sceneRenderer.load(proposedScene);if(failures.length)throw new Error(failures.join('; '));
    scenePose={key:sceneKey,name:`Proposed ${label} · not applied`,returnToFile:returnToEditor,afterRestore:returnToEditor,isCurrent:()=>state.scene_preview_source_key===source};
    scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`Proposed ${label} · not applied · ${posed.affected_material_count} changed materials · ${posed.affected_instances.length} instances · ${posed.unavailable_geometry_keys.length} unavailable geometries`;
    configureSceneInspectionComparison(proposedScene);
    for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('label')])control.hidden=true;
    const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent=returnLabel;
    frameShapeProposal({instance_scope:'all_model_instances',proposal_instances:posed.affected_instances.map(entity_id=>({entity_id}))},null);draw();
  }catch(error){clearScenePose();draw();throw error;}

}
function updateTextureActions(){
  if(!$('texture-undo'))return;
  const pending=!!$('texture-file').files?.length,authored=textureAuthored(),supported=!!state.capabilities?.texture_replacement;
  $('texture-authoring').hidden=!supported;$('texture-history').hidden=!supported;$('texture-layer-label').hidden=!supported;
  $('texture-layer').disabled=busy;$('texture-palette').disabled=busy;
  $('texture-preview-file').disabled=busy||!canEditTexture()||!pending;$('texture-file').disabled=busy||!canEditTexture();$('texture-apply').disabled=busy||!canEditTexture()||!pending;
  $('texture-discard').hidden=!pending;$('texture-discard').disabled=busy;
  $('texture-clear').disabled=busy||pending||!canEditTexture()||!authored;
  if($('texture-new-slot'))$('texture-new-slot').disabled=busy||pending||!canEditTexture()||!state.capabilities?.texture_slot_authoring||!texturePreview;
  if($('texture-resize'))$('texture-resize').disabled=busy||pending||!canEditTexture()||!state.capabilities?.texture_resize_authoring||!texturePreview;
  if($('texture-png'))$('texture-png').disabled=busy||pending||!canEditTexture()||!state.capabilities?.texture_png_authoring||!texturePreview;
  $('texture-undo').disabled=busy||pending||!canEditTexture()||!state.history?.can_undo;
  $('texture-redo').disabled=busy||pending||!canEditTexture()||!state.history?.can_redo;
  $('texture-save').disabled=busy||pending||!state.project?.dirty;$('texture-source').disabled=busy;
  $('texture-edit-palette').disabled=busy||pending||!canEditTexture()||!texturePreview||![4,8].includes(texturePreview.bpp);
  $('texture-scene-uses').disabled=busy||!scenePreviewCurrent();$('texture-fill-rectangle').disabled=$('texture-edit-palette').disabled;$('texture-copy-rectangle').disabled=$('texture-edit-palette').disabled;
  for(const id of ['texture-source-json','texture-effective-json'])$(id).disabled=busy||!texturePreview||![4,8].includes(texturePreview.bpp);
  const newSlot=textureSession?.record.id?.startsWith('texture-new://');
  if(newSlot){
    $('texture-new-slot').textContent='Edit authored texture slot';
    $('texture-layer-label').hidden=true;
    for(const id of ['texture-file','texture-preview-file','texture-apply','texture-clear','texture-source','texture-source-json','texture-effective-json','texture-edit-palette','texture-fill-rectangle','texture-copy-rectangle','texture-resize','texture-png','texture-glb-source','texture-glb-retain']){$(id).disabled=true;$(id).hidden=true;}
    $('texture-file').closest('label').hidden=true;
    $('texture-preview-file').parentElement.hidden=true;
    $('texture-authoring').querySelector('h3').textContent='Authored slot';
    $('texture-file-status').textContent='New authored TIM slot - no Retail counterpart. Inspect pixels here and assign its page in the model material editor.';
  }
  $('texture-project-status').textContent=pending?'Selected file is not applied. Apply or discard before project actions.':busy?'Verifying…':projectSaveStatus();
  $('texture-authored').textContent=authored?`Authored TIM replacement · ${authored.byte_length} bytes · SHA-256 ${authored.asset_sha256?.slice(0,12) ?? 'unavailable'}`:'No authored replacement · effective pixels inherit the imported TIM.';
  if(authored?.glb_source){const receipt=authored.glb_source;$('texture-authored').textContent+=` | GLB image ${receipt.image_index} (${receipt.name??'unnamed'}) | GLB SHA-256 ${receipt.glb_sha256} | input PNG SHA-256 ${receipt.png_sha256}`;}
  if(newSlot&&authored)$('texture-authored').textContent=`Authored TIM slot ${authored.slot_index} - ${authored.byte_length} bytes - SHA-256 ${authored.asset_sha256.slice(0,12)}`;
  $('texture-authored').style.overflowWrap='anywhere';
  $('texture-glb-source').disabled=busy||!authored?.glb_source?.glb_byte_length;
  $('texture-glb-retain').disabled=busy||pending||!canEditTexture()||!authored?.glb_source||!!authored.glb_source.glb_byte_length||!state.scene_preview_source_key;
}
async function openTexture(record,paletteIndex=0,layer='effective'){
  if(busy)return;if(!state.capabilities?.texture_preview){notify('Texture decoding is unavailable in this service.',true);return;}
  const key=resourceStateKey(),continuing=textureDialog.open&&textureSession?.record.id===record.id&&textureSession.projectKey===textureProjectKey();
  const authoredBinding=state.texture_overrides?.[record.id],trustedAuthored=!!authoredBinding&&typeof state.scene?.id==='string'&&authoredBinding.source_scene_id===state.scene.id;
  if(!continuing&&resourceKey!==key&&!trustedAuthored){notify('Refresh scene resources or open a current authored texture binding to inspect this texture.',true);return;}
  if(!continuing){
    textureSession={record,projectKey:textureProjectKey(),paletteIndex,layer};texturePreview=null;
    textureDialog.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-texture" aria-label="Close texture preview">×</button></div><div id="texture-history" class="texture-history" hidden><button id="texture-undo">Undo</button><button id="texture-redo">Redo</button><button id="texture-save">Save project</button><span id="texture-project-status"></span></div><div class="texture-view-controls"><label id="texture-layer-label" hidden>Preview layer<select id="texture-layer" aria-label="Texture preview layer"><option value="effective">Effective</option><option value="imported">Imported</option></select></label><label id="texture-palette-label" hidden>Palette<select id="texture-palette" aria-label="Texture palette"></select></label></div><p id="texture-summary">Verifying texture source…</p><div class="texture-bitmap-wrap"><canvas id="texture-bitmap" aria-label="Decoded texture pixels"></canvas></div><section id="texture-authoring" hidden><h3>Authored replacement</h3><p id="texture-authored"></p><button id="texture-source">Download original TIM</button><button id="texture-glb-source">Download retained GLB source</button><button id="texture-glb-retain">Retain original GLB source</button><button id="texture-source-json">Download retail texture JSON</button><button id="texture-effective-json">Download effective texture JSON</button><button id="texture-png">Edit texture through PNG</button><button id="texture-resize">Resize image</button><button id="texture-new-slot">Import new texture slot</button><button id="texture-scene-uses">Inspect scene texture uses</button><button id="texture-edit-palette">Edit selected palette</button><button id="texture-fill-rectangle">Fill indexed rectangle</button><button id="texture-copy-rectangle">Copy indexed rectangle</button><label>Replacement TIM or indexed JSON<input id="texture-file" type="file" accept=".tim,.json" aria-label="Replacement TIM or JSON file"></label><p id="texture-file-status" class="field-note">Choose TIM up to 1 MiB or source-bound indexed JSON up to 16 MiB. Keep dimensions, bit depth, palette counts and pixel rows fixed.</p><div class="run-actions"><button id="texture-preview-file" disabled>Preview selected texture</button><button id="texture-apply" class="accent" disabled>Apply replacement</button><button id="texture-discard" hidden>Discard selected file</button><button id="texture-clear" disabled>Clear override</button></div></section><p class="field-note">Shift-click an indexed texture pixel to edit its palette index. Palette and layer selection only affect inspection. Static texture candidates do not establish runtime VRAM residency. PSX semi-transparent blending is not reconstructed.</p><details class="resource-provenance"><summary>Texture source and limitations</summary><pre class="diagnostic-detail"></pre></details><p class="dialog-error" role="alert"></p>`;
    $('close-texture').onclick=()=>textureDialog.close();
    $('texture-undo').onclick=()=>textureProjectAction('/api/undo',{});$('texture-redo').onclick=()=>textureProjectAction('/api/redo',{});$('texture-save').onclick=()=>textureProjectAction('/api/project/save',{});
    $('texture-clear').onclick=()=>textureProjectAction('/api/command',{type:'clear_texture_replacement',asset_id:record.id});
    $('texture-glb-retain').onclick=()=>{if(busy)return;const session=textureSession;openTextureSourceRetention({assetId:session.record.id,binding:structuredClone(textureAuthored()),getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id,mode:state.project.mode,sourceKey:state.scene_preview_source_key}),busy:()=>busy,setBusy,onApplied:next=>{state=next;render();notify('Original GLB retained. Save project to persist.');}});};
    $('texture-glb-source').onclick=downloadTextureGlbSource;$('texture-preview-file').onclick=previewTextureFile;$('texture-source').onclick=downloadOriginalTexture;$('texture-apply').onclick=applyTextureReplacement;
    $('texture-source-json').onclick=()=>downloadTextureJSON('imported');$('texture-effective-json').onclick=()=>downloadTextureJSON('effective');
    $('texture-png').onclick=openTexturePng;$('texture-resize').onclick=openTextureResize;$('texture-new-slot').onclick=openNewTextureSlot;
    $('texture-discard').onclick=()=>{$('texture-file').value='';$('texture-file-status').textContent='No replacement file selected.';updateTextureActions();};
    $('texture-file').onchange=()=>{const file=$('texture-file').files?.[0];if(file&&(!/\.(tim|json)$/i.test(file.name)||file.size<1||file.size>(/\.json$/i.test(file.name)?16777216:1048576))){$('texture-file').value='';$('texture-file-status').textContent='Choose a nonempty TIM up to 1 MiB or indexed JSON up to 16 MiB.';}else $('texture-file-status').textContent=file?`${file.name} · ${file.size} bytes · not applied`:'No replacement file selected.';updateTextureActions();};
    $('texture-layer').onchange=()=>openTexture(record,textureSession.paletteIndex,$('texture-layer').value);
    $('texture-scene-uses').onclick=openTextureSceneUses;$('texture-edit-palette').onclick=openTexturePalette;$('texture-fill-rectangle').onclick=()=>openTextureRectangle();$('texture-copy-rectangle').onclick=()=>openTextureRectangle(true);
    $('texture-bitmap').onclick=event=>{if(!event.shiftKey)return;const bitmap=$('texture-bitmap'),rect=bitmap.getBoundingClientRect();if(!rect.width||!rect.height)return;
      // Click coordinates may round just outside a fractional canvas edge.
      const x=Math.max(0,Math.min(bitmap.width-1,Math.floor((event.clientX-rect.left)*bitmap.width/rect.width))),y=Math.max(0,Math.min(bitmap.height-1,Math.floor((event.clientY-rect.top)*bitmap.height/rect.height)));openTexturePixel(x,y);};
    if(!textureDialog.open)textureDialog.showModal();
  }
  textureSession.paletteIndex=paletteIndex;textureSession.layer=layer;$('texture-layer').value=layer;
  setBusy(true);const request=++textureRequest,controller=new AbortController();textureAbort?.abort();textureAbort=controller;
  textureDialog.querySelector('.dialog-error').textContent='';$('texture-bitmap').width=1;$('texture-bitmap').height=1;$('texture-summary').textContent=`Verifying ${layer} texture palette ${paletteIndex}…`;textureDialog.querySelector('pre').textContent='';
  try{
    const response=await fetch('/api/texture-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:record.id,palette_index:paletteIndex,...(state.capabilities?.texture_replacement?{layer}:{})}),signal:controller.signal});
    const result=await response.json();if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Texture decoding failed');
    if(request!==textureRequest||!textureDialog.open||key!==resourceStateKey())return;
    if(result.source_key!==state.scene_preview_source_key||result.scene_id!==state.scene?.id||result.semantic_id!==record.id||result.palette_index!==paletteIndex||(state.capabilities?.texture_replacement&&result.layer!==layer)||!Number.isInteger(result.width)||!Number.isInteger(result.height)||result.width<1||result.height<1||result.width*result.height>4194304||!Number.isInteger(result.palette_count)||result.palette_count<0||result.palette_count>4096||typeof result.rgba_base64!=='string'||result.rgba_base64.length>22369624)throw new Error('Texture service returned invalid or oversized pixels.');
    const bytes=Uint8ClampedArray.from(atob(result.rgba_base64),value=>value.charCodeAt(0));if(bytes.length!==result.width*result.height*4)throw new Error('Decoded texture dimensions do not match the pixel data.');
    texturePreview=result;const bitmap=$('texture-bitmap');bitmap.width=result.width;bitmap.height=result.height;bitmap.getContext('2d').putImageData(new ImageData(bytes,result.width,result.height),0,0);
    $('texture-summary').textContent=`${layer==='imported'?'Imported TIM':result.authored?'Effective authored TIM':'Effective imported TIM'} · ${result.width} × ${result.height} pixels · ${result.bpp} bpp${result.palette_count>0?' · '+result.palette_count+' palettes':''}`;
    $('texture-palette-label').hidden=result.palette_count<=1;$('texture-palette').replaceChildren();
    for(let index=0;index<result.palette_count;index++){const option=document.createElement('option');option.value=index;option.textContent=`Palette ${index}`;$('texture-palette').append(option);}
    $('texture-palette').value=paletteIndex;$('texture-palette').onchange=()=>openTexture(record,Number($('texture-palette').value),textureSession.layer);
    const {rgba_base64,stp_base64,...provenance}=result;textureDialog.querySelector('pre').textContent=JSON.stringify({...provenance,stp_flags_present:typeof stp_base64==='string',catalog_record:record.data},null,2);
  }catch(error){if(error.name!=='AbortError'&&textureDialog.open)textureDialog.querySelector('.dialog-error').textContent=error.message;}
  finally{if(textureAbort===controller)textureAbort=null;setBusy(false);}
}
const textureUsageDialog=document.createElement('dialog');textureUsageDialog.id='texture-usage-dialog';document.body.append(textureUsageDialog);
function openTextureSceneUses(){
  if(busy||!textureSession||!scenePreviewCurrent())return;
  const session=textureSession,key=sceneRequestKey(),source=activeScenePreview(),usage=textureSceneUsage(source,session.record.id);
  textureUsageDialog.innerHTML='<div class="dialog-heading"><h2>Scene texture uses</h2><button aria-label="Close scene texture uses">×</button></div><p data-summary></p><p>Static image or CLUT address contributors in the current decoded scene preview. This does not establish runtime upload order, conditional visibility or palette animation. Unresolved materials may have additional users.</p><input type="search" aria-label="Search texture uses" placeholder="Search model, instance or material"><div data-pages></div><div data-results></div><p class="field-note" data-coverage></p>';
  textureUsageDialog.querySelector('button').onclick=()=>textureUsageDialog.close();
  textureUsageDialog.querySelector('[data-summary]').textContent=`${usage.representation??sceneRepresentation} scene · ${usage.matches.reduce((n,g)=>n+g.materials.length,0)} static material matches · ${usage.matching_instance_count} matching instances · ${usage.candidates.length} partial candidate geometries`;
  textureUsageDialog.querySelector('[data-coverage]').textContent=`Coverage: ${usage.textured_material_count} textured materials examined; ${usage.unresolved_material_count} unresolved materials and ${usage.unavailable_instance_count} unavailable instances. No matches means none in this decoded snapshot, not that the texture is unused in the game.`;
  const selectMatches=document.createElement('button');selectMatches.type='button';selectMatches.dataset.selectTextureMatches='';selectMatches.textContent='Select matched placements';selectMatches.disabled=true;
  const selectNote=document.createElement('p');selectNote.className='field-note';selectNote.textContent='Selects all qualified decoded placement matches, including hidden members; excludes partial candidates, unavailable geometry and ground. Search and pages filter the list only.';
  textureUsageDialog.querySelector('[data-pages]').before(selectMatches,selectNote);
  const selectionCurrent=()=>textureUsageDialog.open&&textureDialog.open&&session===textureSession&&scenePreviewCurrent()&&source===activeScenePreview()&&key===sceneRequestKey();
  let matchedIds=[];
  try{matchedIds=textureMatchedPlacementIds(source,session.record.id,scenePlacementEligible());selectMatches.textContent=`Select matched placements (${matchedIds.length})`;selectMatches.disabled=!matchedIds.length||!canSelectHierarchyMatches()||sceneRepresentation!=='authored'||wallSelectMode;}catch(error){selectMatches.title=error.message;}
  selectMatches.onclick=async()=>{
    if(selectMatches.disabled||!selectionCurrent()||!canSelectHierarchyMatches()||sceneRepresentation!=='authored'||wallSelectMode)return;
    try{
      const ids=textureMatchedPlacementIds(activeScenePreview(),session.record.id,scenePlacementEligible());
      if(JSON.stringify(ids)!==JSON.stringify(matchedIds))throw new Error('Texture placement matches changed. Reopen scene texture uses.');
      const active=visibilitySelection(),focus=ids.includes(active)?active:ids[0];selectMatches.disabled=true;
      if(await selectCurrentPlacementGroup(ids,focus,()=>selectionCurrent()&&JSON.stringify(ids)===JSON.stringify(textureMatchedPlacementIds(activeScenePreview(),session.record.id,scenePlacementEligible())))){textureUsageDialog.close();textureDialog.close();}
    }catch(error){notify(error.message,true);}finally{if(selectionCurrent())selectMatches.disabled=!matchedIds.length||!canSelectHierarchyMatches()||sceneRepresentation!=='authored'||wallSelectMode;}
  };
  const list=textureUsageDialog.querySelector('[data-results]'),search=textureUsageDialog.querySelector('input'),pager=textureUsageDialog.querySelector('[data-pages]');pager.className='dialog-actions';pager.innerHTML='<button>Previous</button><span></span><button>Next</button>';let page=0;
  const rows=[...usage.matches.map(group=>({...group,matched:true})),...usage.candidates.map(group=>({...group,matched:false}))];
  const render=()=>{const query=search.value.trim().toLowerCase(),filtered=rows.filter(group=>[group.asset_id,...group.instances.map(instance=>instance.id),...group.materials.map(material=>String(material.material_index))].join(' ').toLowerCase().includes(query)),pages=Math.max(1,Math.ceil(filtered.length/20));page=Math.min(page,pages-1);pager.querySelector('span').textContent=`Page ${page+1} of ${pages} · ${filtered.length} geometries`;pager.querySelector('button').disabled=page===0;pager.querySelector('button:last-child').disabled=page+1>=pages;list.replaceChildren();
    for(const group of filtered.slice(page*20,page*20+20)){const section=document.createElement('section');section.className='resource-provenance';section.innerHTML=`<h3>${escapeHTML(group.asset_id)}</h3><p>${group.matched?'Static address match':'Partial candidate · unresolved material'} · ${group.instances.length} decoded scene instances</p><p>${group.materials.map(material=>`Material ${material.material_index} · ${escapeHTML(material.status)}${material.reason?' · '+escapeHTML(material.reason):''}`).join('<br>')}</p>`;
      for(const instance of group.instances){const button=document.createElement('button');button.textContent=`Locate ${instance.kind} · ${instance.id.split('/').pop()}`;button.title=instance.id;button.onclick=async()=>{if(busy||session!==textureSession||!scenePreviewCurrent()||key!==sceneRequestKey()){notify('Scene texture uses are stale. Reopen against the current preview.',true);return;}textureUsageDialog.close();textureDialog.close();document.querySelector('.workspace-tabs [data-panel="viewport"]').click();if(instance.kind==='environment'){selectEnvironment(instance.id);frameEnvironment();}else if(state.actor_drafts?.[instance.id]){selectNpcDraft(instance.id);frameNpcDraft();}else if(await api('/api/selection',{entity_id:instance.id}))frame(selected());};section.append(button);}
      list.append(section);
    }
    if(!filtered.length){const empty=document.createElement('p');empty.textContent='No decoded scene contributors match this query.';list.append(empty);}
  };pager.querySelector('button').onclick=()=>{page--;render();};pager.querySelector('button:last-child').onclick=()=>{page++;render();};search.oninput=()=>{page=0;render();};render();textureUsageDialog.showModal();
}
const textureRectangleDialog=document.createElement('dialog');textureRectangleDialog.id='texture-rectangle-dialog';textureRectangleDialog.className='project-dialog';document.body.append(textureRectangleDialog);
async function openTextureRectangle(copy=false){
  if(busy||!textureSession||!canEditTexture()||$('texture-file').files?.length||![4,8].includes(texturePreview?.bpp))return;
  if(textureSession.layer!=='effective')await openTexture(textureSession.record,textureSession.paletteIndex,'effective');
  const session=textureSession,view=texturePreview,key=textureProjectKey();if(busy||!view||session.layer!=='effective')return;setBusy(true);
  try{
    const response=await fetch('/api/texture-palette-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:session.record.id,palette_index:session.paletteIndex})}),source=await response.json();
    if(!response.ok||source.error)throw new Error(source.error||'Palette unavailable');
    if(textureSession!==session||key!==textureProjectKey()||!textureDialog.open)return;
    if(source.asset_id!==session.record.id||source.palette_index!==session.paletteIndex||![16,256].includes(source.entry_count)||source.words?.length!==source.entry_count||!/^([0-9a-f]{64})$/.test(source.effective_sha256))throw new Error('Invalid rectangle palette source');
    if((view.authored?.asset_sha256??source.source_sha256)!==source.effective_sha256)throw new Error('Texture changed since preview; reopen the rectangle editor');
    textureRectangleDialog.innerHTML=`<h2>${copy?'Copy':'Fill'} indexed texture rectangle</h2><p>Draft preview · not applied. Existing palette indices only. The image index affects every palette using this image; surrounding pixels and palette words stay unchanged.</p><p>${view.width} × ${view.height} · ${view.bpp} bpp · inspected palette ${session.paletteIndex}</p><div class="texture-bitmap-wrap"><canvas id="texture-rectangle-bitmap" aria-label="Rectangle ${copy?'copy':'fill'} draft pixels"></canvas></div><form>${[...(copy?[['source_x','Source left X',0,view.width-1,0],['source_y','Source top Y',0,view.height-1,0]]:[]),['x',copy?'Destination left X':'Left X',0,view.width-1,0],['y',copy?'Destination top Y':'Top Y',0,view.height-1,0],['width','Rectangle width',1,view.width,1],['height','Rectangle height',1,view.height,1],...(copy?[]:[['palette_entry','Fill palette index',0,source.entry_count-1,0]])].map(([name,label,min,max,value])=>`<label>${label}<input name="${name}" aria-label="${label}" type="number" step="1" min="${min}" max="${max}" value="${value}" required></label>`).join('')}<p data-region></p><button type="submit">Apply rectangle ${copy?'copy':'fill'}</button><button type="button" data-discard>Discard rectangle draft</button><button type="button" data-close>Close rectangle editor</button><p class="dialog-error" role="alert"></p></form>`;
    const form=textureRectangleDialog.querySelector('form'),canvas=$('texture-rectangle-bitmap');canvas.width=view.width;canvas.height=view.height;
    const original=Uint8ClampedArray.from(atob(view.rgba_base64),v=>v.charCodeAt(0)),ctx=canvas.getContext('2d');
    const values=()=>Object.fromEntries(['x','y','width','height',...(copy?['source_x','source_y']:['palette_entry'])].map(name=>[name,Number(form.elements[name].value)]));
    const valid=v=>Object.values(v).every(Number.isInteger)&&form.checkValidity()&&v.x+v.width<=view.width&&v.y+v.height<=view.height&&(!copy||(v.source_x+v.width<=view.width&&v.source_y+v.height<=view.height));
    const drawDraft=()=>{const v=values(),ok=valid(v),pixels=new Uint8ClampedArray(original);if(ok){if(copy){for(let row=0;row<v.height;row++)for(let col=0;col<v.width;col++){const offset=((v.source_y+row)*view.width+v.source_x+col)*4;pixels.set(original.subarray(offset,offset+4),((v.y+row)*view.width+v.x+col)*4);}}else{const word=source.words[v.palette_entry],expand=n=>(n<<3)|(n>>2),rgba=[expand(word&31),expand((word>>5)&31),expand((word>>10)&31),word===0?0:255];for(let y=v.y;y<v.y+v.height;y++)for(let x=v.x;x<v.x+v.width;x++)pixels.set(rgba,(y*view.width+x)*4);}}ctx.putImageData(new ImageData(pixels,view.width,view.height),0,0);if(ok){if(copy){ctx.strokeStyle='#78ccff';ctx.strokeRect(v.source_x+.5,v.source_y+.5,v.width-1,v.height-1);}ctx.strokeStyle='#ffdc6a';ctx.lineWidth=1;ctx.strokeRect(v.x+.5,v.y+.5,v.width-1,v.height-1);}form.querySelector('[data-region]').textContent=ok?`${v.width*v.height} pixels targeted · X ${v.x}…${v.x+v.width-1}, Y ${v.y}…${v.y+v.height-1} · ${copy?`from (${v.source_x}, ${v.source_y}); overlaps read the original draft source`:`index ${v.palette_entry}`}. PSX semi-transparent blending is not reconstructed.`:'Choose a nonempty rectangle wholly inside the texture.';form.querySelector('[type=submit]').disabled=!ok;};
    form.oninput=drawDraft;form.querySelector('[data-close]').onclick=()=>textureRectangleDialog.close();form.querySelector('[data-discard]').onclick=()=>{form.reset();drawDraft();};
    form.onsubmit=async event=>{event.preventDefault();const v=values();if(busy||!valid(v)||session!==textureSession||key!==textureProjectKey())return;textureCommandPending=true;try{if(await api(copy?'/api/texture-index-copy':'/api/texture-index-rectangle',{asset_id:session.record.id,...v,expected_sha256:source.effective_sha256},{dialog:textureRectangleDialog,success:`Rectangle ${copy?'copy':'fill'} applied. Save project to persist.`})){textureRectangleDialog.close();await openTexture(session.record,session.paletteIndex,'effective');}}finally{textureCommandPending=false;}};
    drawDraft();textureRectangleDialog.showModal();
  }catch(error){if(textureDialog.open)textureDialog.querySelector('.dialog-error').textContent=error.message;}finally{setBusy(false);}
}
const texturePaletteDialog=document.createElement('dialog');texturePaletteDialog.id='texture-palette-dialog';texturePaletteDialog.className='project-dialog';document.body.append(texturePaletteDialog);
async function openTexturePalette(){
  if(busy||!textureSession||!canEditTexture()||$('texture-file').files?.length)return;
  const session=textureSession,key=textureProjectKey();setBusy(true);
  try{
    const response=await fetch('/api/texture-palette-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:session.record.id,palette_index:session.paletteIndex})}),source=await response.json();
    if(!response.ok||source.error)throw new Error(source.error||'Palette unavailable');
    if(textureSession!==session||key!==textureProjectKey()||!textureDialog.open)return;
    if(source.asset_id!==session.record.id||source.palette_index!==session.paletteIndex||![16,256].includes(source.entry_count)||source.words?.length!==source.entry_count||source.retail_words?.length!==source.entry_count||[...source.words,...source.retail_words].some(v=>!Number.isInteger(v)||v<0||v>65535)||!/^([0-9a-f]{64})$/.test(source.effective_sha256))throw new Error('Invalid palette source');
    texturePaletteDialog.innerHTML='<h2>Edit texture palette</h2><p>Effective palette words, independent of the displayed texture layer. Bits 0–4 red, 5–9 green, 10–14 blue, 15 STP. Zero is transparent; STP behavior depends on the material. One entry can affect many pixels and materials.</p><form><label>Entry<input name="entry" type="number" min="0" step="1" value="0" aria-label="Palette entry" required></label><label>Unsigned16 word<input name="word" type="number" min="0" max="65535" step="1" aria-label="Palette word" required></label><p data-values></p><p data-bits></p><button type="button" data-retail>Use retail palette word</button><button type="submit">Apply palette word</button><button type="button" data-discard>Discard palette draft</button><button type="button" data-close>Close palette editor</button><p class="dialog-error" role="alert"></p></form>';
    const form=texturePaletteDialog.querySelector('form'),entry=form.elements.entry,word=form.elements.word;entry.max=source.entry_count-1;
    const bits=()=>{const value=Number(word.value);form.querySelector('[data-bits]').textContent=word.value.trim()&&Number.isInteger(value)&&value>=0&&value<=65535?`Draft RGB5 ${value&31}, ${(value>>5)&31}, ${(value>>10)&31} · STP ${(value>>15)&1} · ${value===0?'transparent':'nonzero palette word'}`:'Enter an unsigned16 integer word.';};
    const load=()=>{const index=Number(entry.value),valid=entry.value.trim()&&Number.isInteger(index)&&index>=0&&index<source.entry_count;entry.disabled=false;word.disabled=!valid;word.value=valid?source.words[index]:'';form.querySelector('[data-values]').textContent=valid?`Retail ${source.retail_words[index]} · Effective ${source.words[index]} · Palette ${source.palette_index}`:'Choose an existing palette entry';form.querySelector('[type=submit]').disabled=!valid;form.querySelector('[data-retail]').disabled=!valid;bits();};
    entry.oninput=load;word.oninput=()=>{entry.disabled=true;bits();};form.querySelector('[data-retail]').onclick=()=>{word.value=source.retail_words[Number(entry.value)];entry.disabled=true;bits();};form.querySelector('[data-discard]').onclick=load;form.querySelector('[data-close]').onclick=()=>texturePaletteDialog.close();
    form.onsubmit=async event=>{event.preventDefault();if(busy||!form.reportValidity()||textureSession!==session||key!==textureProjectKey())return;textureCommandPending=true;
      try{if(await api('/api/texture-palette-word',{asset_id:session.record.id,palette_index:session.paletteIndex,entry_index:Number(entry.value),word:Number(word.value),expected_sha256:source.effective_sha256},{dialog:texturePaletteDialog,success:'Palette word updated. Save project to persist.'})){texturePaletteDialog.close();await openTexture(session.record,session.paletteIndex,'effective');}}finally{textureCommandPending=false;}
    };load();texturePaletteDialog.showModal();
  }catch(error){if(textureDialog.open)textureDialog.querySelector('.dialog-error').textContent=error.message;}finally{setBusy(false);}
}
const texturePixelDialog=document.createElement('dialog');texturePixelDialog.id='texture-pixel-dialog';texturePixelDialog.className='project-dialog';document.body.append(texturePixelDialog);
async function openTexturePixel(x,y){
  if(busy||!textureSession||!canEditTexture()||$('texture-file').files?.length||![4,8].includes(texturePreview?.bpp))return;
  const session=textureSession,key=textureProjectKey();setBusy(true);
  try{
    const response=await fetch('/api/texture-pixel-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:session.record.id,palette_index:session.paletteIndex,x,y})}),source=await response.json();
    if(!response.ok||source.error)throw new Error(source.error||'Pixel unavailable');
    if(textureSession!==session||key!==textureProjectKey()||!textureDialog.open)return;
    if(source.asset_id!==session.record.id||source.pixel?.x!==x||source.pixel?.y!==y||![16,256].includes(source.entry_count)||source.words?.length!==source.entry_count)throw new Error('Invalid pixel source');
    texturePixelDialog.innerHTML='<h2>Edit indexed texture pixel</h2><p data-source></p><p>Uses the effective texture even when the imported layer is displayed. An image index selects a colour in every palette that uses this image. Other packed pixels, palette words and headers stay unchanged.</p><form><label>Palette index<input name="index" type="number" min="0" step="1" aria-label="Pixel palette index" required></label><p data-colour></p><button type="button" data-retail>Use retail pixel index</button><button type="submit">Apply pixel index</button><button type="button" data-discard>Discard pixel draft</button><button type="button" data-close>Close pixel editor</button><p class="dialog-error" role="alert"></p></form>';
    texturePixelDialog.querySelector('[data-source]').textContent=`Pixel X ${x}, Y ${y} · ${source.pixel.bpp} bpp · Retail index ${source.retail_entry} · Effective index ${source.pixel.palette_entry} · Inspected palette ${source.palette_index}`;
    const form=texturePixelDialog.querySelector('form'),input=form.elements.index;input.max=source.entry_count-1;
    const preview=()=>{const index=Number(input.value),valid=input.value.trim()&&Number.isInteger(index)&&index>=0&&index<source.entry_count,word=valid?source.words[index]:0;form.querySelector('[data-colour]').textContent=valid?`Palette word ${word} · RGB5 ${word&31}, ${(word>>5)&31}, ${(word>>10)&31} · STP ${(word>>15)&1}${word===0?' · transparent':''}`:'Choose an existing palette index';form.querySelector('[type=submit]').disabled=!valid;};
    const discard=()=>{input.value=source.pixel.palette_entry;preview();};input.oninput=preview;form.querySelector('[data-retail]').onclick=()=>{input.value=source.retail_entry;preview();};form.querySelector('[data-discard]').onclick=discard;form.querySelector('[data-close]').onclick=()=>texturePixelDialog.close();
    form.onsubmit=async event=>{event.preventDefault();if(busy||!form.reportValidity()||textureSession!==session||key!==textureProjectKey())return;textureCommandPending=true;
      try{if(await api('/api/texture-pixel-index',{asset_id:session.record.id,x,y,palette_entry:Number(input.value),expected_sha256:source.effective_sha256},{dialog:texturePixelDialog,success:'Pixel index updated. Save project to persist.'})){texturePixelDialog.close();await openTexture(session.record,session.paletteIndex,'effective');}}finally{textureCommandPending=false;}
    };discard();texturePixelDialog.showModal();
  }catch(error){if(textureDialog.open)textureDialog.querySelector('.dialog-error').textContent=error.message;}finally{setBusy(false);}
}
async function textureProjectAction(route,body){
  if(busy||!textureSession)return;
  const session=textureSession;textureCommandPending=true;textureDialog.querySelector('.dialog-error').textContent='';
  try{if(await api(route,body)){if(textureDialog.open&&session.projectKey===textureProjectKey()){await openTexture(session.record,session.paletteIndex,session.layer);$('texture-file-status').textContent=state.project?.dirty?'No replacement file selected. Project changes are not saved.':'No replacement file selected. Project saved.';}}else textureDialog.querySelector('.dialog-error').textContent=$('status').textContent;}
  finally{textureCommandPending=false;updateTextureActions();}
}
const textureFileDialog=document.createElement('dialog');textureFileDialog.id='texture-file-dialog';document.body.append(textureFileDialog);
async function previewTextureFile(){
  if(busy||!canEditTexture())return;
  const session=textureSession,file=$('texture-file').files?.[0],format=/\.json$/i.test(file?.name??'')?'json':'tim';
  if(!session||!file||file.size<1||file.size>(format==='json'?16777216:1048576)||!/\.(tim|json)$/i.test(file.name))return;
  const current=()=>textureDialog.open&&session===textureSession&&session.projectKey===textureProjectKey()&&$('texture-file').files?.[0]===file;
  setBusy(true);textureDialog.querySelector('.dialog-error').textContent='';
  try{
    const content=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('The selected texture file could not be read.'));reader.readAsDataURL(file);});
    if(!current())return;
    const response=await fetch('/api/texture-file-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:session.record.id,format,palette_index:session.paletteIndex,content_base64:content})}),result=await response.json();
    if(!current())return;
    if(!response.ok||result.error)throw new Error(result.error||'Texture file preview unavailable');
    if(result.asset_id!==session.record.id||result.input_format!==format||result.palette_index!==session.paletteIndex||result.representation!=='proposed_file'||result.project_changed!==false||!Number.isInteger(result.width)||!Number.isInteger(result.height)||result.width<1||result.height<1||result.width*result.height>4194304)throw new Error('Invalid texture proposal response');
    const bytes=Uint8ClampedArray.from(atob(result.rgba_base64),v=>v.charCodeAt(0));if(bytes.length!==result.width*result.height*4)throw new Error('Invalid texture proposal pixels');
    const comparison=decodeRetailComparison(result.retail_comparison,result.source_sha256,{bpp:result.bpp,width:result.width,height:result.height});
    const changes=(label,diff)=>`<h3>${escapeHTML(label)}</h3><p>${diff.palette_words_changed} palette words · ${diff.pixel_indices_changed??'direct-color'} pixel indices · ${diff.image_bytes_changed} image bytes changed.</p><pre>${escapeHTML(diff.changes.map(item=>`${item.kind==='palette_word'?`Palette word ${item.word_index}`:item.kind==='pixel_index'?`Pixel (${item.x}, ${item.y})`:`Image byte ${item.image_byte_index}`}: ${item.before} → ${item.after}`).join('\n')||'No payload changes.')}</pre>${diff.changes_truncated?'<p>Detail limited to the first 256 changes; counts include all changes.</p>':''}`;
    textureFileDialog.innerHTML=`<div class="dialog-heading"><h2>Proposed texture file</h2><button id="close-texture-file" aria-label="Close proposed texture">×</button></div><p>Proposed file · not applied · ${escapeHTML(file.name)}</p><p>${result.width} × ${result.height} · ${result.bpp} bpp · palette ${result.palette_index}</p><div class="texture-bitmap-wrap"><canvas id="texture-file-bitmap" aria-label="Proposed texture pixels"></canvas></div>${changes('Compared with current authored texture',result.current_changes)}${changes('Compared with '+retailComparisonLabel(comparison),result.retail_changes)}<details><summary>Source hashes and limits</summary><pre>${escapeHTML(JSON.stringify({retail:result.source_sha256,current:result.effective_sha256,proposed:result.candidate_sha256},null,2))}</pre><p>Layout and payload checked. Compressed-carrier capacity and gameplay appearance require Build and later verification. PSX semi-transparent blending is not reconstructed.</p></details><button id="return-texture-file">Return to selected file</button>`;
    const canvas=$('texture-file-bitmap');canvas.width=result.width;canvas.height=result.height;canvas.getContext('2d').putImageData(new ImageData(bytes,result.width,result.height),0,0);
    if(scenePreviewCurrent()&&sceneRepresentation==='authored'){
      const inspect=document.createElement('button');inspect.type='button';inspect.textContent='Inspect proposed texture in scene';textureFileDialog.append(inspect);
      const loadedKey=sceneKey,sceneSource=scenePreview.project_source_key;
      inspect.onclick=async()=>{
        if(busy||!textureFileDialog.open||!current()||!scenePreviewCurrent()||loadedKey!==sceneKey||sceneRepresentation!=='authored')return;
        setBusy(true);
        try{
          const response=await fetch('/api/texture-file-scene-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:session.record.id,format,palette_index:session.paletteIndex,content_base64:content,candidate_sha256:result.candidate_sha256,source_key:sceneSource})}),posed=await response.json();
          if(!textureFileDialog.open||!current()||!scenePreviewCurrent()||loadedKey!==sceneKey)return;
          if(!response.ok||posed.error)throw new Error(posed.error||'Texture scene proposal failed');
          if(posed.asset_id!==session.record.id||posed.candidate_sha256!==result.candidate_sha256||posed.project_source_key!==sceneSource||!Array.isArray(posed.proposal_assets)||!Array.isArray(posed.affected_instances))throw new Error('Texture scene proposal differs from file inspection');
          const proposedScene=structuredClone(scenePreview),seen=new Set();
          for(const row of posed.proposal_assets){const geometry=proposedScene.assets.find(a=>a.geometry_key===row.geometry_key);if(!geometry||geometry.asset_id!==row.asset_id||seen.has(row.geometry_key)||!Array.isArray(row.preview?.textures))throw new Error('Texture proposal geometry differs from scene');seen.add(row.geometry_key);geometry.preview.textures=row.preview.textures;}
          stopScenePosePlayback();const failures=sceneRenderer.load(proposedScene);if(failures.length)throw new Error(failures.join('; '));
          const returnToTextureFile=()=>{if(session!==textureSession||session.projectKey!==textureProjectKey()||loadedKey!==sceneKey||$('texture-file').files?.[0]!==file||state.project.mode!=='edit')return false;textureDialog.showModal();textureFileDialog.showModal();return true;};
          scenePose={key:sceneKey,name:'Proposed texture · not applied',returnToFile:returnToTextureFile,afterRestore:returnToTextureFile};
          scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`Proposed texture · not applied · ${posed.affected_material_count} changed materials · ${posed.affected_instances.length} instances · ${posed.unavailable_geometry_keys.length} unavailable geometries`;
          configureSceneInspectionComparison(proposedScene);
          for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('label')])control.hidden=true;
          const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to texture file';
          textureFileDialog.close();textureDialog.close();frameShapeProposal({instance_scope:'all_model_instances',proposal_instances:posed.affected_instances.map(entity_id=>({entity_id}))},null);draw();
        }catch(error){if(current()){clearScenePose();textureDialog.querySelector('.dialog-error').textContent=error.message;draw();}}finally{setBusy(false);}
      };
    }
    $('close-texture-file').onclick=$('return-texture-file').onclick=()=>textureFileDialog.close();textureFileDialog.showModal();
  }catch(error){if(current())textureDialog.querySelector('.dialog-error').textContent=error.message;}
  finally{setBusy(false);updateTextureActions();}
}
async function applyTextureReplacement(){
  if(busy||!canEditTexture())return;
  const file=$('texture-file').files?.[0],session=textureSession,jsonUpload=/\.json$/i.test(file?.name??'');if(!session||!file||file.size<1||file.size>(jsonUpload?16777216:1048576)||!/\.(tim|json)$/i.test(file.name))return;
  setBusy(true);textureDialog.querySelector('.dialog-error').textContent='';
  let encoded;
  try{encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('The selected texture file could not be read.'));reader.readAsDataURL(file);});}
  catch(error){textureDialog.querySelector('.dialog-error').textContent=error.message;return;}
  finally{setBusy(false);}
  if(session!==textureSession||!textureDialog.open||session.projectKey!==textureProjectKey()||$('texture-file').files?.[0]!==file)return;
  textureCommandPending=true;
  try{if(await api(jsonUpload?'/api/texture-json-replacement':'/api/texture-replacement',{asset_id:session.record.id,...(jsonUpload?{json_base64:encoded}:{tim_base64:encoded})})){$('texture-file').value='';$('texture-file-status').textContent=state.project?.dirty?'Replacement applied. Save the project to keep it.':'Replacement accepted. Project unchanged.';if(textureDialog.open&&session.projectKey===textureProjectKey())await openTexture(session.record,session.paletteIndex,'effective');}else textureDialog.querySelector('.dialog-error').textContent=$('status').textContent;}
  finally{textureCommandPending=false;updateTextureActions();}
}
async function downloadTextureJSON(layer){
  if(busy||!textureSession)return;const session=textureSession;setBusy(true);
  try{
    const response=await fetch('/api/texture-json-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:session.record.id,layer})}),result=await response.json();
    if(!response.ok||result.error)throw new Error(result.error||'Texture JSON unavailable');
    if(session!==textureSession||session.projectKey!==textureProjectKey()||!textureDialog.open)return;
    if(result.asset_id!==session.record.id||result.layer!==layer||typeof result.json_base64!=='string'||result.json_base64.length>22369624)throw new Error('Invalid texture JSON download');
    const bytes=Uint8Array.from(atob(result.json_base64),v=>v.charCodeAt(0)),url=URL.createObjectURL(new Blob([bytes],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download=`texture-${layer}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    $('texture-file-status').textContent=`${layer} indexed JSON downloaded · complete palette words and pixel rows bound to retail source hash.`;
  }catch(error){if(textureDialog.open)textureDialog.querySelector('.dialog-error').textContent=error.message;}finally{setBusy(false);}
}
async function downloadTextureGlbSource(){
  if(busy||!textureSession)return;const session=textureSession,key=textureProjectKey(),binding=state.texture_overrides?.[session.record.id],receipt=binding?.glb_source;if(!receipt?.glb_byte_length)return;
  setBusy(true);textureDialog.querySelector('.dialog-error').textContent='';let url;
  try{
    const response=await fetch('/api/texture-glb-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:session.record.id,expected_sha256:binding.asset_sha256})});
    const raw=await response.text();if(raw.length>46*1024*1024)throw new Error('Retained GLB response exceeds its bounded envelope.');const result=JSON.parse(raw);
    if(!response.ok||result.error)throw new Error(result.error||'Retained GLB source download failed');
    if(session!==textureSession||key!==textureProjectKey()||result.schema_version!=='legaia.texture-glb-source.v1'||result.asset_id!==session.record.id||result.effective_sha256!==binding.asset_sha256||result.read_only!==true||result.project_changed!==false||!result.source||Object.keys(result.source).length!==5||Object.keys(receipt).some(field=>result.source[field]!==receipt[field]))throw new Error('Retained GLB source differs from this texture or project.');
    if(typeof result.glb_base64!=='string'||result.glb_base64.length>44739244||!/^[A-Za-z0-9+/]*={0,2}$/.test(result.glb_base64))throw new Error('Retained GLB has invalid bounded file bytes.');
    const bytes=Uint8Array.from(atob(result.glb_base64),char=>char.charCodeAt(0));if(bytes.length!==receipt.glb_byte_length||bytes.length>32*1024*1024)throw new Error('Retained GLB size differs from its receipt.');
    const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),value=>value.toString(16).padStart(2,'0')).join('');if(hash!==receipt.glb_sha256||session!==textureSession||key!==textureProjectKey())throw new Error('Retained GLB bytes or texture context changed.');
    url=URL.createObjectURL(new Blob([bytes],{type:'model/gltf-binary'}));const link=document.createElement('a');link.href=url;link.download=`texture-source-${hash}.glb`;link.click();
    $('texture-file-status').textContent='Retained GLB source downloaded. Edit externally, then import its image with a fresh native binding.';
  }catch(error){if(textureDialog.open&&session===textureSession)textureDialog.querySelector('.dialog-error').textContent=error.message;}
  finally{if(url){const release=url;setTimeout(()=>URL.revokeObjectURL(release),1000);}setBusy(false);}
}
async function downloadOriginalTexture(){
  if(busy||!textureSession)return;setBusy(true);textureDialog.querySelector('.dialog-error').textContent='';
  try{
    const response=await fetch('/api/texture-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:textureSession.record.id})}),result=await response.json();
    if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Original TIM download failed');
    if(typeof result.tim_base64!=='string'||result.tim_base64.length>1398104)throw new Error('Original TIM exceeds the supported download size.');
    const bytes=Uint8Array.from(atob(result.tim_base64),value=>value.charCodeAt(0));if(!bytes.length||bytes.length>1048576)throw new Error('Invalid original TIM size.');
    const filename=String(result.filename ?? 'original-texture.tim').split(/[\\/]/).at(-1),url=URL.createObjectURL(new Blob([bytes],{type:'application/octet-stream'})),link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    $('texture-file-status').textContent='Original TIM downloaded. Edit its pixels or palettes in a TIM-aware tool, keeping the source layout.';
  }catch(error){textureDialog.querySelector('.dialog-error').textContent=error.message;}
  finally{setBusy(false);}
}
const animationResourceDialog=document.createElement('dialog');animationResourceDialog.id='animation-resource-dialog';document.body.append(animationResourceDialog);
function animationPreviewChoices(record,actorEntities,modelReferences){
  const choices=[];
  for(const ref of initialAssetUsage(record,modelReferences)){
    const entity=actorEntities.find(actor=>actor.id===ref.source_id);
    if(!entity)continue;
    if(ref.imported)choices.push({key:entity.id+'|imported',entity,
      assetId:entity.components.ModelRenderer.asset_id,clipId:'scene-header',
      layer:ref.effective&&!entity.components.ActorAppearance?.authored?.donor_entity_id?'Imported + Effective':'Imported'});
    if(ref.effective&&entity.components.ActorAppearance?.authored?.donor_entity_id)choices.push({key:entity.id+'|authored',entity,
      assetId:entity.components.ActorAppearance.effective.asset_id,clipId:'authored-appearance',layer:'Authored effective'});
  }
  return choices;
}
function openAnimationResource(record){
  if(busy||resourceKey!==resourceStateKey())return;
  if(record.data?.scope==='authored-retained'){
    openRetainedAnimationAsset({record,getState:()=>state,busy:()=>busy,onError:e=>notify(e.message,true),
      onEdit:({assetId,entityId,row})=>inspectRetainedAnimationContent({id:entityId},row,assetId),
      onGlb:({assetId,entityId,row})=>inspectRetainedAnimationGlb({id:entityId},row,assetId),
      onLifecycle:({assetId,entityId,row})=>inspectSavedAnimationRecords({id:entityId},row,assetId),
      getAssignmentTarget:()=>selected()?.id??null,onAssign:({assetId,targetEntityId,row})=>{const entity=entities().find(entity=>entity.id===targetEntityId);if(!entity)throw new Error('Assignment target changed. Reopen the retained clip.');return inspectSavedAnimationRecords(entity,row,assetId,true);},
      onModel:id=>openModel(id),onActor:async id=>{if(await api('/api/selection',{entity_id:id})){frame(selected());document.querySelector('.workspace-tabs [data-panel="viewport"]').click();}},
      onPreview:(data,value)=>openModel(data.model_asset_id,'allocated-record',data.retained_record.entity_id,'authored',null,value)});
    return;
  }

  const data=record.data;
  if(data.scope==='global-field'){
    const preview=data.preview,available=preview&&state.assets.some(asset=>asset.id===preview.asset_id);
    animationResourceDialog.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-animation-resource" aria-label="Close animation resource">×</button></div>${property('Stable ID',record.id)}${property('Frames',data.frame_count)}${property('Rigid channels',data.bone_count)}<p>Shared field clip with a verified reference model association. This does not establish which scene actors are playing it or its current runtime timing.</p><button id="preview-global-animation" ${available?'':'disabled'}>Preview reference clip</button><details class="resource-provenance"><summary>Model association, source and limits</summary><pre></pre></details>`;
    animationResourceDialog.querySelector('pre').textContent=JSON.stringify(data,null,2);
    $('close-animation-resource').onclick=()=>animationResourceDialog.close();
    $('preview-global-animation').onclick=()=>{if(busy||!available)return;animationResourceDialog.close();openModel(preview.asset_id,preview.clip_id);};
    animationResourceDialog.showModal();return;
  }
  const candidates=animationPreviewChoices(record,entities(),state.model_references??[]);
  animationResourceDialog.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-animation-resource" aria-label="Close animation resource">×</button></div>${property('Stable ID',record.id)}${property('Frames',data.frame_count)}${property('Rigid channels',data.bone_count)}<p>Retail playback timing is unresolved. Choose an imported binding or an authored effective assignment; previews preserve that distinction.</p>${candidates.length?'<label>Actor assignment<select id="resource-animation-actor" aria-label="Animation actor"><option value="">Choose an actor assignment…</option></select></label><div class="dialog-actions"><button id="select-resource-actor" disabled>Select actor</button><button id="preview-resource-animation" class="accent" disabled>Preview animation</button></div>':'<p class="field-note">No verified actor assignment is available in the active scene. The record remains available for source inspection.</p>'}<details class="resource-provenance"><summary>Animation bindings, source and limits</summary><pre class="diagnostic-detail"></pre></details>`;
  $('close-animation-resource').onclick=()=>animationResourceDialog.close();animationResourceDialog.querySelector('pre').textContent=JSON.stringify(data,null,2);
  if(candidates.length){
    for(const candidate of candidates){const option=document.createElement('option');option.value=candidate.key;option.textContent=`${candidate.entity.name} · ${candidate.layer} · ${candidate.assetId.split('/').at(-1)}`;$('resource-animation-actor').append(option);}
    const choice=()=>candidates.find(candidate=>candidate.key===$('resource-animation-actor').value);
    $('resource-animation-actor').onchange=()=>{const missing=!choice();$('select-resource-actor').disabled=missing;$('preview-resource-animation').disabled=missing;};
    $('select-resource-actor').onclick=async()=>{const candidate=choice();if(candidate&&await api('/api/selection',{entity_id:candidate.entity.id})){animationResourceDialog.close();frame(selected());document.querySelector('.workspace-tabs [data-panel="viewport"]').click();}};
    $('preview-resource-animation').onclick=()=>{const candidate=choice();if(candidate){animationResourceDialog.close();openModel(candidate.assetId,candidate.clipId,candidate.entity.id);}};
  }
  animationResourceDialog.showModal();
}
const scriptResourceDialog=document.createElement('dialog');scriptResourceDialog.id='script-resource-dialog';document.body.append(scriptResourceDialog);
function resourceValue(value){return value===null||value===undefined?'Unknown':typeof value==='object'?JSON.stringify(value):String(value);}
function resourceLabel(value){return resourceValue(value).replaceAll('_',' ');}
function openScriptResource(record){
  if(record.authoredRecord&&record.type==='script'){activateAsset(record);return;}
  if(busy||resourceKey!==resourceStateKey())return;
  const data=record.data,actor=entities().find(entity=>entity.id===data.actor_semantic_id),dialogue=record.type==='dialogue';
  const scriptOwner=data.partition===2&&typeof data.owner_semantic_id==='string'?{id:data.owner_semantic_id,name:`Partition 2 script ${data.source_record?.record_index}`,partitionTwo:true}:actor;
  const status={decoded_supported_paths:'Supported paths decoded',partial:'Partial inspection',decoded_segment:'Decoded segment',unavailable:'Unavailable'}[data.status] ?? resourceLabel(data.status);
  scriptResourceDialog.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-script-resource" aria-label="Close script resource">×</button></div>${property('Stable ID',record.id)}${property(data.partition===2?'Script owner':'Actor',data.owner_semantic_id ?? data.actor_semantic_id)}${property('Source scene',record.source)}${property('Inspection',status)}${dialogue?`${property('Parent script status',data.script_status==='partial'?'Partial inspection':resourceLabel(data.script_status))}${property('Record offset',scriptOffset(data.pc))}${property('Source bytes',data.byte_length)}${property('Tokens',data.token_count)}${property('Text length',data.text_length)}<p>Catalog metadata contains no dialogue text. Open the verified script report to inspect this segment and any supported text runs.</p>`:`<div class="script-resource-counts">${property('Instructions',data.instruction_count)}${property('Dialogue segments',data.dialogue_count)}${property('Option menus',data.menu_count ?? 'Not cataloged')}${property('Opaque bytes',data.opaque_byte_count)}${property('Decoder stops',data.stop_count)}</div><p>Encoded references are read only. Runtime flag values, story-state reachability and actual scene transitions are not established by this catalog.</p><section id="resource-model-selections"><h3>Script model selectors</h3><p>Runtime pool bases and resolved assets are unknown.</p></section><section id="resource-movements"><h3>Movement target references</h3></section><section id="resource-menus"><h3>Dialogue option menus</h3></section><section id="resource-flags"><h3>Flag references</h3></section><section id="resource-transitions"><h3>Encoded transitions</h3></section>`}<div class="dialog-actions"><button id="select-script-resource-actor" ${actor?'':'disabled'}>Select actor</button><button id="inspect-script-resource" class="accent" ${scriptOwner&&state.capabilities?.actor_script_preview?'':'disabled'}>${dialogue?'Inspect dialogue segment':'Inspect script'}</button></div>${scriptOwner?'':'<p class="field-note">The script owner is not available in the active scene.</p>'}<details class="resource-provenance"><summary>Source records, encoded fields and limitations</summary><pre class="diagnostic-detail"></pre></details>`;
  $('close-script-resource').onclick=()=>scriptResourceDialog.close();scriptResourceDialog.querySelector('.resource-provenance pre').textContent=JSON.stringify(data,null,2);
  $('select-script-resource-actor').onclick=async()=>{if(actor&&!busy&&await api('/api/selection',{entity_id:actor.id})){scriptResourceDialog.close();frame(selected());document.querySelector('.workspace-tabs [data-panel="viewport"]').click();}};
  $('inspect-script-resource').onclick=()=>{if(scriptOwner&&!busy){scriptResourceDialog.close();openActorScript(scriptOwner,false,null,dialogue?{semantic_id:record.id,pc:data.pc}:null);}};
  if(dialogue){
    const script=resourceRecords.find(item=>item.asset_kind==='script'&&item.semantic_id===data.script_id);
    if(script){const button=document.createElement('button');button.className='parent-script-button';button.textContent='View parent script metadata';button.onclick=()=>openScriptResource({id:script.semantic_id,type:'script',label:script.name ?? script.semantic_id,source:script.source_record?.prot_entry_name ?? record.source,data:script});scriptResourceDialog.querySelector('.dialog-actions').before(button);}
  }else{
    const movementHost=$('resource-movements'),context=resourceStateKey();
    for(const target of data.movement_targets??[]){
      const button=document.createElement('button');button.textContent=`${target.mnemonic} at ${scriptOffset(target.pc)} · X ${target.target_position.x}, Z ${target.target_position.z} · Y unknown`;
      button.disabled=!scriptOwner||!state.capabilities?.actor_script_preview;
      button.onclick=()=>{if(busy||context!==resourceStateKey()||!scriptOwner)return;scriptResourceDialog.close();openActorScript(scriptOwner,false,null,null,target.pc);};movementHost.append(button);
    }
    if(!data.movement_targets?.length){const note=document.createElement('p');note.textContent=Array.isArray(data.movement_targets)?'No movement targets decoded in inspected paths.':'Refresh resources to discover movement targets.';movementHost.append(note);}
    const modelHost=$('resource-model-selections');
    for(const reference of data.model_selection_references??[]){
      const button=document.createElement('button');button.textContent=`Selector ${reference.model_selector_signed} · pool flag ${reference.high_pool_flag?'set':'clear'} · ${scriptOffset(reference.pc)}`;button.disabled=!scriptOwner||!state.capabilities?.actor_script_preview;
      button.onclick=()=>{if(busy||context!==resourceStateKey()||!scriptOwner)return;scriptResourceDialog.close();openActorScript(scriptOwner,false,null,null,reference.pc);};modelHost.append(button);
    }
    if(!data.model_selection_references?.length){const note=document.createElement('p');note.textContent=Array.isArray(data.model_selection_references)?'No model selectors decoded in inspected paths.':'Refresh resources to discover model selectors.';modelHost.append(note);}
    const menus=data.menus ?? [],menuHost=$('resource-menus');
    if(!menus.length){const note=document.createElement('p');note.textContent=Array.isArray(data.menus)?'No menus decoded in the inspected paths.':'Refresh the resource catalog to discover menus.';menuHost.append(note);}
    for(const menu of menus){
      const button=document.createElement('button');button.textContent=`Inspect ${menu.option_count}-option menu at ${scriptOffset(menu.pc)}`;
      button.disabled=!scriptOwner||!state.capabilities?.actor_script_preview;
      button.onclick=()=>{if(scriptOwner&&!busy){scriptResourceDialog.close();openActorScript(scriptOwner,false,null,null,menu.pc);}};
      menuHost.append(button);
    }
    const flags=data.flag_references ?? [],transitions=data.transitions ?? [];
    appendResourceTable($('resource-flags'),['Offset','Instruction','Bank / index','Operation','Scope / context','Interpretation'],flags.map(item=>[scriptOffset(item.pc),item.mnemonic,`${resourceLabel(item.bank)} / ${resourceValue(item.index)}`,resourceLabel(item.operation),`${resourceLabel(item.scope)}\n${item.context_resolution==='extended_target_unresolved'?`Extended target ${resourceValue(item.extended_target)} (unresolved)`:resourceLabel(item.context_resolution)}`,`${resourceLabel(item.status)}\n${resourceLabel(item.index_semantics)}`]),'No flag references were decoded in the inspected paths.');
    appendResourceTable($('resource-transitions'),['Offset','Instruction','Target scene label','Status','Encoded entry'],transitions.map(item=>[scriptOffset(item.pc),item.mnemonic,item.target_scene_name ?? 'Unresolved',`${resourceLabel(item.status)}\nReachability: ${resourceLabel(item.reachability)}`,`X ${resourceValue(item.entry_x_encoded)} / Z ${resourceValue(item.entry_z_encoded)} / direction ${resourceValue(item.direction_encoded)}`]),'No transitions were decoded in the inspected paths.');
  }
  if(!scriptResourceDialog.open)scriptResourceDialog.showModal();
}
function appendResourceTable(parent,headings,rows,empty){
  if(!rows.length){const note=document.createElement('p');note.className='field-note';note.textContent=empty;parent.append(note);return;}
  const wrap=document.createElement('div');wrap.className='script-table-wrap';const table=document.createElement('table'),header=document.createElement('thead'),labels=document.createElement('tr'),body=document.createElement('tbody');
  for(const heading of headings){const cell=document.createElement('th');cell.textContent=heading;labels.append(cell);}header.append(labels);
  for(const values of rows){const row=document.createElement('tr');for(const value of values){const cell=document.createElement('td');cell.textContent=resourceValue(value);row.append(cell);}body.append(row);}table.append(header,body);wrap.append(table);parent.append(wrap);
}
function property(label,value){return `<dl class="property"><dt>${escapeHTML(label)}</dt><dd>${escapeHTML(value ?? 'Unknown')}</dd></dl>`;}
function showTemplates(){renderTemplates();templateDialog.showModal();}
function renderTemplates(){
  const entity=selected(),position=entity?.components?.Transform?.authored?.position ?? {},templates=(state.actor_templates ?? []).filter(t=>t.scope!==NPC_PRESET_SCOPE);
  const appearance=entity?.components?.ActorAppearance?.authored?.donor_entity_id?entity.components.ActorAppearance.authored:null;
  const animation=entity?.components?.ActorAnimation?.authored?.animation_asset_id?entity.components.ActorAnimation.authored:null;
  const axes=Object.entries(position).map(([axis,value])=>`${axis.toUpperCase()} ${format(value)}`).join(' · ');
  templateDialog.innerHTML=`<div class="dialog-heading"><h2>Actor and NPC preset library</h2><button type="button" id="close-templates" aria-label="Close">×</button></div><p>Capture authored position, appearance and initial animation, then review the preset for an existing imported actor.</p><p class="field-note">Appearance and clips are reverified against the final proposed model. Initial MAN header only; scripts and gameplay remain unverified. Animation channel edits stay with their imported shared clip. Height stays project-only; Build requires representable X/Z values.</p><form id="create-template-form"><label>Template name<input id="template-name" required maxlength="80" placeholder="For example, courtyard actor" ${canEdit() && (axes||appearance||animation)?'':'disabled'}></label><p class="field-note">${entity?`Selected: ${escapeHTML(entity.name)} · ${axes?escapeHTML(axes):appearance?`Appearance donor: ${escapeHTML(appearance.donor_entity_id)}`:animation?`Initial clip: ${escapeHTML(animation.animation_asset_id)}`:'Author a position, appearance or initial animation override to capture a template.'}`:'Select an imported actor to capture or apply a template.'}</p><button type="submit" ${canEdit() && axes?'':'disabled'}>Capture authored position</button><button type="button" id="capture-appearance-template" ${canEditAppearance() && appearance?'':'disabled'}>Capture authored appearance</button><button type="button" id="capture-combined-template" ${canEditAppearance() && appearance && axes?'':'disabled'}>Capture position and appearance</button><button type="button" id="capture-animation-template" ${canEdit() && animation?'':'disabled'}>Capture authored initial animation</button><button type="button" id="capture-animated-template" ${canEdit() && animation?'':'disabled'}>Capture animation with authored position and appearance</button></form><div id="template-list" class="template-list"></div><p class="field-note">Template changes use Undo / Redo. Save the project to keep the library.</p>`;
  $('close-templates').onclick=()=>templateDialog.close();
  appendPresetImport({container:templateDialog,getState:()=>state,canEdit,isBusy:()=>busy,setBusy,api});
  npcPresetControls=mountNpcPresets({container:templateDialog,getState:()=>state,getSelection:()=>npcDraftSelection,canEdit,isBusy:()=>busy,setBusy,api,
    canChoosePosition:()=>!sceneRuler?.picking()&&!transitionArrivalOverlay&&!npcArrivalOverlay&&canMeasureScene(),
    choosePosition:(resume,current)=>{npcGroundPlacement.begin(resume,{current,returnLabel:'Return to NPC preset',note:'Choose a visible source-ground corner within 24 pixels. Only native X/Z will be copied into the preset form; height is not authored.'});document.querySelector('.workspace-tabs [data-panel="viewport"]').click();},
    captureCreation:report=>captureNpcPresetCreation(state,report),
    onCreated:capture=>{try{const id=createdNpcPresetSelection(state,capture);selectNpcDraft(id);frameNpcDraft();revealHierarchyButton.click();document.querySelector('.workspace-tabs [data-panel="inspector"]').click();}catch(error){notify(error.message,true);}},
    canInspectScene:()=>sceneModelsReady()&&scenePreviewCurrent()&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft&&!actorGroupInspection,getScenePreview:()=>scenePreview,
    inspectScene:(proposed,report,returnToReview,isCurrent)=>{
      cancelViewportGesture();const failures=sceneRenderer.load(structuredClone(proposed));if(failures.length){sceneRenderer.load(structuredClone(scenePreview));throw new Error(failures.join('; '));}
      scenePose={key:sceneKey,name:'Proposed NPC preset instance - not applied',returnToFile:returnToReview,isCurrent};scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent='Proposed NPC preset instance - not applied';configureSceneInspectionComparison(proposed);
      for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('[aria-label="Scene preview rate"]').parentElement])control.hidden=true;
      const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to NPC preset';frameShapeProposal({instance_scope:'all_model_instances',proposal_instances:[{entity_id:report.entity_id,proposed:report.draft.position}]},null);draw();
    }});
  const errorMessage=document.createElement('p');errorMessage.className='dialog-error';errorMessage.setAttribute('role','alert');templateDialog.append(errorMessage);
  const command=async body=>{const result=await api('/api/command',body);if(!result)errorMessage.textContent=$('status').textContent;return result;};
  $('create-template-form').onsubmit=async event=>{event.preventDefault();await command({type:'create_actor_template',entity_id:entity.id,name:$('template-name').value});};
  $('capture-appearance-template').onclick=()=>command({type:'create_actor_template',capture:'appearance',entity_id:entity.id,name:$('template-name').value});
  $('capture-combined-template').onclick=()=>command({type:'create_actor_template',capture:'combined',entity_id:entity.id,name:$('template-name').value});
  $('capture-animation-template').onclick=()=>command({type:'create_actor_template',capture:'animation',entity_id:entity.id,name:$('template-name').value});
  $('capture-animated-template').onclick=()=>command({type:'create_actor_template',capture:'animated',entity_id:entity.id,name:$('template-name').value});
  for(const template of templates){
    const card=document.createElement('section');card.className='template-card';
    const application=template.application??{available:false,reason:'Preset eligibility is unavailable.'};
    const values=[presetScopeLabel(template.scope),...(template.components.Transform?Object.entries(template.components.Transform.position).map(([axis,value])=>`${axis.toUpperCase()} ${format(value)}`):[]),...(template.components.ActorAppearance?[`Appearance donor: ${template.components.ActorAppearance.donor_entity_id}`]:[]),...(template.components.ActorAnimation?[`Initial clip: ${template.components.ActorAnimation.animation_asset_id}`,`Witness: ${template.components.ActorAnimation.donor_entity_id}`,`SHA-256: ${template.components.ActorAnimation.source_record_sha256}`]:[])].join(' · ');
    card.innerHTML=`<strong>${escapeHTML(template.name)}</strong><p>${escapeHTML(values)}</p><p class="field-note">${escapeHTML(application.reason)}</p><details><summary>Source provenance</summary><p>${escapeHTML(template.source.scene_id)}<br>${escapeHTML(template.source.entity_id)}</p><code>${escapeHTML(template.source.disc_identity)}</code></details><div class="template-actions"><button data-apply ${canEdit() && entity && application.available?'':'disabled'}>Apply to ${escapeHTML(entity?.name ?? 'selected actor')}</button><button data-delete ${canEdit()?'':'disabled'}>Delete</button></div>`;
    const reviewed=['authored-actor-preset-v1',ANIMATION_PRESET_SCOPE].includes(template.scope);
    card.querySelector('[data-apply]').textContent=reviewed?'Review actor preset':`Apply to ${entity?.name??'selected actor'}`;
    card.querySelector('[data-apply]').onclick=()=>reviewed?openActorPresetReview({template,entity,getState:()=>state,canEdit,isBusy:()=>busy,setBusy,api,
      canInspectScene:()=>sceneModelsReady()&&scenePreviewCurrent()&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft&&!actorGroupInspection,
      getScenePreview:()=>scenePreview,
      inspectScene:(proposed,report,returnToReview,isCurrent,onDiscard)=>{
        cancelViewportGesture();const failures=sceneRenderer.load(structuredClone(proposed));if(failures.length){sceneRenderer.load(structuredClone(scenePreview));throw new Error(failures.join('; '));}
        templateDialog.close();scenePose={key:sceneKey,name:'Proposed actor preset · not applied',returnToFile:returnToReview,isCurrent,onDiscard};
        scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=template.scope===ANIMATION_PRESET_SCOPE?'Proposed initial animation preset · not applied':'Proposed position and appearance · not applied';configureSceneInspectionComparison(proposed);
        for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('[aria-label="Scene preview rate"]').parentElement])control.hidden=true;
        const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to actor preset';draw();
      }
    }):command({type:'apply_actor_template',template_id:template.id,entity_id:entity.id});
    card.querySelector('[data-delete]').onclick=()=>command({type:'delete_actor_template',template_id:template.id});
    const rename=document.createElement('details');rename.innerHTML=`<summary>Rename preset</summary><form><label>New name for ${escapeHTML(template.name)}<input required maxlength="80" value="${escapeHTML(template.name)}" ${canEdit()?'':'disabled'}></label><button type="submit" ${canEdit()?'':'disabled'}>Save name</button></form>`;
    rename.querySelector('form').onsubmit=async event=>{event.preventDefault();await command({type:'rename_actor_template',template_id:template.id,name:rename.querySelector('input').value});};
    card.append(rename);
    card.append(presetExportButton({template,getState:()=>state,isBusy:()=>busy,setBusy,onError:message=>{if(templateDialog.open)errorMessage.textContent=message;}}));
    $('template-list').append(card);
  }
  if(!templates.length)$('template-list').innerHTML='<p class="field-note">No authored actor templates yet.</p>';
}
function coordinateComparisonRows(transform,observed){
  return ['x','y','z'].map(axis=>{
    const imported=transform?.imported?.position?.[axis],effective=transform?.effective?.position?.[axis],sample=observed?.[axis];
    return {axis,imported:numeric(imported)?imported:null,effective:numeric(effective)?effective:null,
      observed:numeric(sample)?sample:null,delta:numeric(effective)&&numeric(sample)?sample-effective:null};
  });
}
function coordinateComparisonMarkup(entityId,observed){
  const transform=entities().find(entity=>entity.id===entityId)?.components?.Transform;
  const cell=value=>value===null?'Unknown':escapeHTML(String(value));
  return '<table class="coordinate-comparison"><caption>Guest world coordinates - sampled candidate</caption><thead><tr><th>Axis</th><th>Imported</th><th>Effective</th><th>Sampled</th><th>Sample - effective</th></tr></thead><tbody>'+coordinateComparisonRows(transform,observed).map(row=>`<tr><th>${row.axis.toUpperCase()}</th><td>${cell(row.imported)}</td><td>${cell(row.effective)}</td><td>${cell(row.observed)}</td><td>${cell(row.delta)}</td></tr>`).join('')+'</tbody></table><p class="field-note">Values use guest coordinates; the viewport flips Y for display. Unknown height is not zero. Deltas compare current runtime position with authored-effective placement, not a coordinate calibration. Scripts may relocate actors; candidate identity remains unconfirmed.</p>';
}
function runtimeCandidateSummary(correlation,entityId){
  const candidates=correlation.candidates??[];
  if(!candidates.length)return `<p class="field-note">${escapeHTML(correlation.reason??'No accepted candidate observation.')}</p>`;
  return candidates.map(candidate=>{
    const layers=(candidate.appearance_layers??[]).map(layer=>({imported:'Imported',effective:'Effective'})[layer]).filter(Boolean);
    const donor=candidate.effective_donor_id;
    const position=candidate.observed_position??{};
    return `<div class="appearance-layer"><h4>Unconfirmed runtime candidate</h4>${property('Captured node',candidate.runtime_node_id)}${property('Appearance match',layers.join(' + ')||'Not classified')}${donor&&donor!==entityId?property('Effective donor',donor):''}${property('Binding capture frame',candidate.frame)}${property('Position capture frames',candidate.position_capture_frames?`${candidate.position_capture_frames.before}–${candidate.position_capture_frames.after}`:'Unknown')}${property('Placement header matches imported X/Z',candidate.placement_header_agrees_with_import===true?'Yes':candidate.placement_header_agrees_with_import===false?'No':'Unknown')}${property('Captured placement header',`X ${format(candidate.placement_position?.x)} · Z ${format(candidate.placement_position?.z)}`)}${property('Captured world position',`X ${format(position.x)} · Y ${format(position.y)} · Z ${format(position.z)}`)}${coordinateComparisonMarkup(entityId,position)}<p class="field-note">Captured evidence only. Structural compatibility does not establish actor identity.</p></div>`;
  }).join('');
}
async function exportNpcDrafts(entityId){
  if(busy||!canEdit())return;
  const dialog=document.createElement('dialog');dialog.id='draft-export-result';dialog.className='project-dialog';
  const title=document.createElement('h2');title.textContent='Experimental disc export';
  const message=document.createElement('p');message.textContent='Building a separate disc from supported authored changes across this project. This can take a minute.';
  const details=document.createElement('pre');details.style.whiteSpace='pre-wrap';details.style.overflowWrap='anywhere';
  let exporting=true;
  const close=document.createElement('button');close.textContent='Close';close.disabled=true;close.onclick=()=>dialog.close();
  dialog.addEventListener('cancel',event=>{if(exporting)event.preventDefault();});
  dialog.append(title,message,details,close);document.body.append(dialog);dialog.addEventListener('close',()=>dialog.remove(),{once:true});dialog.showModal();
  setBusy(true);
  try{
    if(liveFollow.pending)await liveFollow.pending;
    const response=await fetch(entityId?'/api/export/actor-drafts':'/api/export/project',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(entityId?{entity_id:entityId}:{})});
    const result=await response.json();
    if(!response.ok||result.error)throw new Error(result.error||'Draft export failed');
    if(!result.report_path||!result.disc_path||!result.output_sha256)throw new Error('Export service returned an incomplete report');
    message.textContent='Export complete. Gameplay remains unverified. The game has not been launched.';
    details.textContent=`Disc: ${result.disc_path}\nReport: ${result.report_path}\nSHA-256: ${result.output_sha256}`+(result.input_project_path?`\nSaved export inputs: ${result.input_project_path}`:'');
    notify('Experimental disc exported');
  }catch(error){message.textContent=error.message;notify(error.message,true);}
  finally{exporting=false;close.disabled=false;setBusy(false);}
}
const inspectorComponentFilterState={query:'',authoredOnly:false};
const inspectorSectionsState={project:null,collapsed:new Set()};
let inspectorSectionsScope=null;
function renderInspector(){
  const resource=selectedSceneResource();if(resource){renderSceneResourceInspector(resource);return;}
  const npc=selectedNpcDraft();
  if(npc){
    const id=npcDraftSelection,preview=activeScenePreview()?.entities.find(item=>item.entity_id===id),donor=entities().find(entity=>entity.id===npc.donor_entity_id);
    const draftPreviewState=!preview?'unavailable':!scenePreviewCurrent()?'pending':scenePose?'source-during-proposal':'current';
    $('selection-summary').textContent=`${npc.name} · Authored NPC draft`;
    const npcSnapshot={entity_id:id,draft:npc,donor,preview,scriptBinding:npcScriptBindingSnapshot(state,id)};
    $('inspector').innerHTML=renderNpcDraftInspector(state.inspector_schema,npcSnapshot,draftPreviewState)+`<section class="component"><h3>NPC draft authoring</h3><form id="draft-inspector-form"><label>X <input name="x" type="number" min="64" max="16384" step="64" required></label><label>Z <input name="z" type="number" min="64" max="16384" step="64" required></label><button type="submit">Apply draft position</button></form><button id="frame-npc-draft">Frame draft</button><button id="delete-npc-draft">Delete draft</button></section>`;
    const poseLabel={imported_scene_animation_frame0:'Imported animation · frame 0',authored_scene_animation_frame0:'Authored shared animation · frame 0',reference_party_idle:'Reference party idle · frame 0',reference_global_loop:'Reference shared clip · frame 0',single_object_static:'Static single-object model'}[preview?.pose_kind]??'Pose unavailable in this view';
    const poseNote=document.createElement('p');poseNote.className='field-note';poseNote.id='draft-pose-note';poseNote.textContent=`Preview pose: ${poseLabel}. A sampled frame does not establish an idle stance or runtime playback.`;$('draft-inspector-form').before(poseNote);
    const donorAnimation=scenePreviewCurrent()?npcDonorAnimationBinding(state,id,preview):null;
    if(donorAnimation){
      const inspectPose=document.createElement('button');inspectPose.id='inspect-draft-donor-animation';inspectPose.textContent=donorAnimation.representation==='authored'?'Inspect shared authored donor animation':'Inspect retail donor animation';
      const context=resourceStateKey();inspectPose.disabled=busy||!scenePreviewCurrent()||Boolean(scenePose);
      inspectPose.onclick=()=>{if(busy||context!==resourceStateKey()||!scenePreviewCurrent()||scenePose)return;try{const current=npcDonorAnimationBinding(state,id,activeScenePreview()?.entities.find(row=>row.entity_id===id));if(JSON.stringify(current)!==JSON.stringify(donorAnimation))throw new Error('NPC donor animation changed. Reselect the draft.');openModel(current.assetId,current.clipId,current.entityId,'imported',id);}catch(error){notify(error.message,true);}};poseNote.after(inspectPose);
    }
    const nameForm=document.createElement('form');nameForm.id='draft-name-form';
    const nameLabel=document.createElement('label');nameLabel.textContent='Name ';const nameInput=document.createElement('input');nameInput.name='name';nameInput.required=true;nameInput.maxLength=120;nameInput.value=npc.name;nameLabel.append(nameInput);
    const rename=document.createElement('button');rename.type='submit';rename.textContent='Rename';nameForm.append(nameLabel,rename);$('draft-inspector-form').before(nameForm);
    nameForm.onsubmit=event=>{event.preventDefault();api('/api/command',{type:'rename_actor_draft',entity_id:id,name:nameInput.value});};
    const presets=document.createElement('button');presets.id='npc-presets-button';presets.textContent='NPC presets...';presets.disabled=busy||!canEdit();presets.onclick=showTemplates;$('delete-npc-draft').before(presets);
    const npcAppearance=document.createElement('button');npcAppearance.id='npc-appearance-button';npcAppearance.textContent='Choose NPC initial appearance...';npcAppearance.disabled=busy||!canEdit();npcAppearance.onclick=()=>openNpcAppearanceInspector(id);$('delete-npc-draft').before(npcAppearance);
    const scriptOptions={entityId:id,getState:()=>state,isBusy:()=>busy,canEdit,api,onPreview:openNpcArrivalDestination,onPreviewArrival:openNpcArrivalDestination};
    mountNpcDraftScriptActions($('inspector').querySelector('[data-npc-draft-component="NpcDraftScriptBinding"]'),{
      schema:state.inspector_schema,snapshot:npcSnapshot,getState:()=>state,busy:()=>busy,editable:canEdit,
      current:()=>npcDraftSelection===id&&state.actor_drafts?.[id]?.scene_id===state.scene?.id,
      handlers:{'reset-npc-script':()=>openNpcScriptReset(scriptOptions),'edit-npc-dialogue':()=>openNpcDialogue(scriptOptions),'edit-npc-facing':()=>openNpcFacing(scriptOptions),
        'edit-npc-model-selectors':()=>openNpcModelSelectors(scriptOptions),'edit-npc-flags':()=>openNpcFlags(scriptOptions),'edit-npc-system-flags':()=>openNpcSystemFlags(scriptOptions),
        'edit-npc-animation-operands':()=>openNpcAnimationOperands(scriptOptions),'edit-npc-branches':()=>openNpcBranches(scriptOptions),'edit-npc-effect-colors':()=>openNpcEffectColors(scriptOptions),
        'edit-npc-transitions':()=>openNpcTransitions(scriptOptions),
        'edit-npc-waits':()=>openNpcWaits(scriptOptions),'edit-npc-movement':()=>openNpcMovement({...scriptOptions,showTargets:showNpcMovementTargets}),
        'inspect-npc-build-script':()=>openNpcBuildScript({...scriptOptions,renderInstructions:appendScriptInstructions}),
        'inspect-npc-current-script':()=>openNpcCurrentScript({...scriptOptions,renderInstructions:appendScriptInstructions,showTargets:showNpcMovementTargets}),
        'inspect-npc-donor-script':()=>openNpcDonorScript({...scriptOptions,renderInstructions:appendScriptInstructions})},
      onError:error=>notify(error.message,true)});
    const duplicate=document.createElement('button');duplicate.id='duplicate-npc-draft';duplicate.textContent='Duplicate draft';duplicate.title='Creates an independent draft at the same position, then selects it to move';$('delete-npc-draft').before(duplicate);
    duplicate.disabled=busy||!canEdit();duplicate.title+=' (Ctrl+D)';duplicate.onclick=()=>duplicateNpcDraft(id);
    const repeat=document.createElement('button');repeat.id='repeat-npc-draft';repeat.textContent='Repeat draft...';duplicate.after(repeat);repeat.onclick=()=>openDraftRepeat({entityId:id,entityIds:currentPlacementSelection(),onError:error=>notify(error.message,true),getState:()=>state,isBusy:()=>busy,canEdit,setBusy,api,
      canInspectScene:()=>sceneModelsReady()&&scenePreviewCurrent()&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft&&!actorGroupInspection,
      getScenePreview:()=>scenePreview,
      inspectScene:(proposed,report,returnToReview,isCurrent)=>{
        cancelViewportGesture();const failures=sceneRenderer.load(structuredClone(proposed));if(failures.length){sceneRenderer.load(structuredClone(scenePreview));throw new Error(failures.join('; '));}
        scenePose={key:sceneKey,name:'Proposed NPC copies - not applied',returnToFile:returnToReview,isCurrent};scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`${report.copies.length} proposed NPC copies - not applied`;
        configureSceneInspectionComparison(proposed);for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('[aria-label="Scene preview rate"]').parentElement])control.hidden=true;
        const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to draft copies';frameShapeProposal({instance_scope:'all_model_instances',proposal_instances:report.copies},null);draw();
      }
    });

    const draftGroup=document.createElement('button');draftGroup.id='draft-group-button';draftGroup.textContent='Move NPC draft group...';repeat.after(draftGroup);
    draftGroup.disabled=busy||!canEdit()||Object.values(state.actor_drafts??{}).filter(d=>d.scene_id===state.scene.id).length<2;
    draftGroup.onclick=()=>openDraftGroup({entityId:id,entityIds:currentPlacementSelection(),onError:error=>notify(error.message,true),getState:()=>state,isBusy:()=>busy,canEdit,setBusy,api,
      canInspectScene:()=>sceneModelsReady()&&scenePreviewCurrent()&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft&&!actorGroupInspection,
      getScenePreview:()=>scenePreview,
      inspectScene:(proposed,report,returnToReview,isCurrent)=>{
        cancelViewportGesture();const failures=sceneRenderer.load(structuredClone(proposed));if(failures.length){sceneRenderer.load(structuredClone(scenePreview));throw new Error(failures.join('; '));}
        scenePose={key:sceneKey,name:report.request.remove?'Proposed NPC draft removal - not applied':'Proposed NPC draft movement - not applied',returnToFile:returnToReview,isCurrent};scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`${report.targets.length} proposed NPC draft ${report.request.remove?'removals':'movements'} - not applied`;
        configureSceneInspectionComparison(proposed);for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('[aria-label="Scene preview rate"]').parentElement])control.hidden=true;
        const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to NPC draft group';if(!report.request.remove)frameShapeProposal({instance_scope:'all_model_instances',proposal_instances:report.targets},null);draw();
      }
    });
    const donorGroup=document.createElement('button');donorGroup.id='draft-donor-group-button';donorGroup.textContent='Assign NPC group donor...';draftGroup.after(donorGroup);
    donorGroup.disabled=busy||!canEdit()||!sceneModelsReady()||!scenePreviewCurrent()||sceneRepresentation!=='authored'||!!scenePose||!!shapeDraft||!!actorGroupInspection||Object.values(state.actor_drafts??{}).filter(d=>d.scene_id===state.scene.id).length<2;
    donorGroup.onclick=()=>openDonorGroup({entityId:id,entityIds:currentPlacementSelection(),getState:()=>state,isBusy:()=>busy,canEdit,api,getScenePreview:()=>scenePreview,onError:error=>notify(error.message,true),
      inspectScene:(proposed,report,returnToReview,isCurrent)=>{
        cancelViewportGesture();const failures=sceneRenderer.load(structuredClone(proposed));if(failures.length){sceneRenderer.load(structuredClone(scenePreview));throw new Error(failures.join('; '));}
        scenePose={key:sceneKey,name:'Proposed NPC donor group - not applied',returnToFile:returnToReview,isCurrent};scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`${report.targets.length} proposed NPC donors - not applied`;
        configureSceneInspectionComparison(proposed);for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('[aria-label="Scene preview rate"]').parentElement])control.hidden=true;
        const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to NPC donor group';frameShapeProposal({instance_scope:'all_model_instances',proposal_instances:report.targets.map(row=>({...row,proposed:row.proposed.position}))},null);draw();
      }
    });
    for(const control of [nameInput,rename,duplicate,repeat])control.disabled=busy||!canEdit();
    const donorForm=document.createElement('form');donorForm.id='draft-donor-form';
    const donorLabel=document.createElement('label');donorLabel.textContent='Script donor ';const donorSelect=document.createElement('select');donorSelect.name='donor';donorSelect.setAttribute('aria-label','Draft retail donor');
    for(const actor of entities()){const option=document.createElement('option');option.value=actor.id;option.textContent=actor.name??actor.id;donorSelect.append(option);}donorSelect.value=npc.donor_entity_id;donorLabel.append(donorSelect);
    const donorApply=document.createElement('button');donorApply.type='submit';donorApply.textContent='Change donor';const donorNote=document.createElement('p');donorNote.className='field-note';donorNote.textContent='Script donor controls cloned behavior and the default initial pair. Clear own appearance and every owned script edit family before changing it. Name, identity and position stay unchanged.';
    donorForm.append(donorLabel,donorApply,donorNote);nameForm.after(donorForm);donorSelect.disabled=donorApply.disabled=busy||!canEdit();
    donorForm.onsubmit=event=>{event.preventDefault();api('/api/command',{type:'set_actor_draft_donor',entity_id:id,donor_entity_id:donorSelect.value});};
    const form=$('draft-inspector-form');form.elements.x.value=npc.position.x;form.elements.z.value=npc.position.z;
    form.querySelectorAll('input,button').forEach(control=>control.disabled=busy||!canEdit());
    form.onsubmit=event=>{event.preventDefault();api('/api/command',{type:'set_actor_draft_position',entity_id:id,position:{x:Number(form.elements.x.value),z:Number(form.elements.z.value)}});};
    mountExistingGroundPosition(form,'npc',id);
    $('frame-npc-draft').textContent=sceneRepresentation==='retail'?'Show in authored scene':'Frame draft';
    $('frame-npc-draft').onclick=frameNpcDraft;
    const inspectDraft=document.createElement('button');inspectDraft.id='inspect-npc-draft';inspectDraft.textContent='Inspect donor append prototype';inspectDraft.disabled=busy;inspectDraft.onclick=()=>openActorCandidate({id,name:npc.name,components:{Transform:{effective:{position:{...npc.position,y:null}}}}});$('inspector').querySelector('section').append(inspectDraft);
    const exportDraft=document.createElement('button');exportDraft.id='export-npc-drafts';exportDraft.textContent='Export experimental disc';exportDraft.disabled=busy||!canEdit();exportDraft.onclick=()=>exportNpcDrafts(id);$('inspector').querySelector('section').append(exportDraft);
    $('delete-npc-draft').disabled=busy||!canEdit();$('delete-npc-draft').onclick=()=>api('/api/command',{type:'delete_actor_draft',entity_id:id});
    return;
  }
  const environment=selectedEnvironment();
  if(environment){
    $('selection-summary').textContent=environmentGroupSelection.length>1?`${environmentGroupSelection.length} scenery instances · focused ${environment.name}`:environment.name;
    const source=environment.source_record,transform=source.imported_transform;
    const sectionSnapshot=inspectorSectionSnapshot($('inspector'),inspectorSectionsScope);
    inspectorSectionsScope=JSON.stringify([state.project.path,state.scene?.id,environment.entity_id]);
    const layoutContext=JSON.stringify([resourceStateKey(),sceneRepresentation,sceneKey]);
    $('inspector').innerHTML=renderEnvironmentInspector(state.inspector_schema,environment,scenePreviewCurrent());
    $('frame-environment').onclick=frameEnvironment;
    if(source.record_offset&&source.source_record?.map_sha256){
      if(!environment.entity_id.includes('/decorations/')){
        const enable=document.createElement('button');enable.id='enable-shared-move';enable.textContent='Enable shared transform handles';
        enable.disabled=busy||!canEdit()||sceneRepresentation!=='authored'||!scenePreviewCurrent();
        enable.onclick=()=>{if(!canEdit()||!scenePreviewCurrent()||selectedEnvironment()?.entity_id!==environment.entity_id)return;sharedEnvironmentMove={id:environment.entity_id,key:resourceStateKey()};enable.textContent='Shared transform handles enabled';notify('X/Z and yaw handles affect every use of this placement record unless individually overridden. Undo restores the edit.');draw();};
        $('frame-environment').after(enable);
      }
      const scopes=environment.entity_id.includes('/decorations/')?['shared','instance']:['shared'];
      for(const scope of scopes){
      const individual=scope==='instance',cell=(source.source_record.grid_byte_offset-0x8000)/2;
      const section=document.createElement('section');section.className='component';
      const title=document.createElement('h3');title.textContent=individual?'Individual decoration override':'Shared transform override';section.append(title);
      const note=document.createElement('p');note.className='field-note';note.textContent=individual?'Changes affect this decoration only and take precedence over shared values. Builds allocate an unused MAP record. In-game behavior has not been verified.':'Changes affect every instance using this placement record unless individually overridden. Saved in the project and included in builds. In-game behavior has not been verified.';section.append(note);
      const binding=activeScenePreview()?.environment_authoring;
      const shared=binding?.edits?.find(e=>e.record_index===source.object_record_index);
      const current=individual?binding?.instances?.find(e=>e.cell_index===cell):shared;
      const inputs=[];
      for(const [field,label,retail] of [['offset','Placement offset',source.record_offset],['rotation_psx','Rotation (4096 units per turn)',transform.rotation_psx]]){
        const base=individual?{...retail,...shared?.[field]}:retail;
        const heading=document.createElement('h4');heading.textContent=label;section.append(heading);
        for(const axis of ['x','y','z']){
          const row=document.createElement('label');row.textContent=`${axis.toUpperCase()} · ${individual?'inherited':'imported'} ${base[axis]} `;
          const input=document.createElement('input');input.type='number';input.step='1';input.min=field==='offset'?'-32768':'0';input.max=field==='offset'?'32767':'4095';input.value=current?.[field]?.[axis]??base[axis];input.setAttribute('aria-label',`${individual?'Individual ':''}${label} ${axis.toUpperCase()}`);input.disabled=state.project?.mode==='live'||sceneRepresentation!=='authored'||!scenePreviewCurrent();row.append(input);section.append(row);inputs.push({field,axis,input,base:base[axis]});
        }
      }
      const effective=document.createElement('p');effective.textContent=`${scenePreviewCurrent()?'Effective position':'Previous preview position (refresh pending)'}: ${JSON.stringify(environment.effective_transform?.position??transform.position)}`;section.append(effective);
      const apply=document.createElement('button');apply.textContent=individual?'Apply individual transform':'Apply shared transform';apply.disabled=state.project?.mode==='live'||sceneRepresentation!=='authored'||!scenePreviewCurrent();
      const inspectorKey=sceneKey;
      apply.onclick=async()=>{
        if(sceneRepresentation!=='authored'||!scenePreviewCurrent()||sceneKey!==inspectorKey)return;
        const edit=individual?{cell_index:cell}:{record_index:source.object_record_index};
        for(const {field,axis,input,base} of inputs){if(!input.value.trim()||!input.checkValidity()){input.reportValidity();return;}const value=Number(input.value);if(value!==base)(edit[field]??={})[axis]=value;}
        const edits=(binding?.edits??[]).filter(e=>individual||e.record_index!==source.object_record_index);
        const instances=(binding?.instances??[]).filter(e=>!individual||e.cell_index!==cell);
        if(edit.offset||edit.rotation_psx)(individual?instances:edits).push(edit);
        await api('/api/command',edits.length||instances.length?{type:'set_environment_transforms',entity_id:state.scene.id,value:{source_sha256:source.source_record.map_sha256,edits,instances}}:{type:'clear_environment_transforms',entity_id:state.scene.id});
      };
      section.append(apply);$('inspector').insertBefore(section,$('inspector').lastElementChild);
      }
    }
    if(Number.isInteger(source.object_record_index)){
      const related=environmentEntities().filter(item=>item.source_record?.object_record_index===source.object_record_index);
      const section=document.createElement('section');section.className='component';
      const heading=document.createElement('h3');heading.textContent='Shared placement record';section.append(heading);
      const note=document.createElement('p');note.className='field-note';note.textContent=`${related.length} imported scene instance${related.length===1?'':'s'} use MAP record ${source.object_record_index}. Shared edits affect every grid use. Static decorations support individual overrides through a separately allocated record.`;section.append(note);
      if(Number.isInteger(source.source_record?.map_reference_count)){
        const count=document.createElement('p');count.className='field-note';count.textContent=`Total source grid references: ${source.source_record.map_reference_count}, including cells outside the preview visibility gates.`;section.append(count);
      }
      if(related.length>1){
        const select=document.createElement('select');select.setAttribute('aria-label','Instances sharing this placement record');
        for(const item of related){const option=document.createElement('option');option.value=item.entity_id;option.textContent=item.name;option.selected=item.entity_id===environment.entity_id;select.append(option);}
        select.onchange=()=>{selectEnvironment(select.value);frameEnvironment();};section.append(select);
      }
      $('inspector').insertBefore(section,$('inspector').lastElementChild);
    }
    mountInspectorSections($('inspector'),{state:inspectorSectionsState,project:state.project.path,scope:inspectorSectionsScope,snapshot:sectionSnapshot,current:()=>layoutContext===JSON.stringify([resourceStateKey(),sceneRepresentation,sceneKey])&&selectedEnvironment()?.entity_id===environment.entity_id});
    return;
  }
  const entity=selected();
  $('selection-summary').textContent=entity?entity.name ?? entity.id:'No entity selected';
  if(!entity){$('inspector').innerHTML='<div class="empty-panel">Select an entity in the scene<br>or hierarchy to inspect it.</div>';return;}
  const components=entity.components ?? {}, transform=components.Transform ?? {};
  const actorActionContext=resourceStateKey(),actorActions={
    'choose-appearance':{requiresEdit:true,canRun:canEditAppearance,run:()=>openAppearanceOptions(entity)},
    'choose-initial-animation':{requiresEdit:true,canRun:()=>state.capabilities?.actor_animation_assignment===true,
      run:()=>openActorAnimationAssignment({entity,getState:()=>state,busy:()=>busy,api,
        onPreview:review=>openModel(review.proposed.asset_semantic_id,'scene-header',review.proposed.actor_semantic_id,'imported',null,null,null,review.entity_id),
        onError:error=>notify(error.message,true)})},
    'clear-appearance':{requiresEdit:true,canRun:canEditAppearance,run:()=>api('/api/command',{type:'clear_actor_appearance',entity_id:entity.id})},
    'preview-appearance':{run:()=>openModel(components.ActorAppearance.effective.asset_id,'authored-appearance',entity.id)},
    'preview-initial-animation':{run:()=>openModel(components.ActorAppearance.effective.asset_id,'authored-initial-animation',entity.id)},
    'edit-actor-animation-glb':{requiresEdit:true,canRun:()=>Boolean(components.ActorAllocatedAnimation?.authored?.record_id)||components.Animation?.preview_support?.supported===true,run:()=>inspectAnimationGlb(entity)},
    'manage-allocated-clips':{requiresEdit:true,canRun:()=>state.capabilities?.actor_animation_assignment===true,run:()=>inspectSavedAnimationRecords(entity)},
    'duplicate-allocated-initial-animation':{requiresEdit:true,canRun:()=>Boolean(components.ActorAllocatedAnimation?.authored?.record_id),run:()=>inspectAssignedAnimationDuplicate(entity)},
    'preview-allocated-initial-animation':{canRun:()=>Boolean(components.ActorAllocatedAnimation?.authored?.record_id),run:()=>openModel(components.ActorAllocatedAnimation.authored.model_asset_id,'authored-initial-animation',entity.id)},
    'inspect-model':{run:()=>openModel(components.ModelRenderer.asset_id)},
    'inspect-script':{run:({componentId}={})=>openActorScript(entity,false,null,null,null,componentId)},
    'reset-script-component':{requiresEdit:true,run:({componentId})=>openScriptComponentReset({entity,component:componentId,getState:()=>state,current:()=>actorActionContext===resourceStateKey()&&selected()?.id===entity.id,editable:canEdit,busy:()=>busy,api,onError:error=>notify(error.message,true)})},
    'inspect-actor-candidate':{run:()=>openActorCandidate(entity)},
    'inspect-templates':{run:showTemplates},
    'preview-scene-animation':{canRun:()=>components.Animation?.preview_support?.supported===true,run:()=>openModel(components.ModelRenderer.asset_id,'scene-header',entity.id)},
    'author-animation-channels':{requiresEdit:true,canRun:()=>components.Animation?.preview_support?.supported===true&&state.capabilities?.actor_animation_authoring===true,run:()=>openAnimationChannels(entity)},
    'preview-reference-animation':{canRun:()=>components.ModelRenderer?.reference_animation?.supported===true&&typeof components.ModelRenderer.reference_animation.first_clip_id==='string',run:()=>openModel(components.ModelRenderer.asset_id,components.ModelRenderer.reference_animation.first_clip_id,null,'imported',entity.id)}
  };
  const componentActions=id=>renderComponentActions(state.inspector_schema,id,components[id],state.capabilities,actorActions,canEdit());

  let html=`<div class="entity-heading"><h2>${escapeHTML(entity.name ?? entity.id)}</h2><code>${escapeHTML(entity.id)}</code></div><section class="component"><h3>${escapeHTML(state.inspector_schema.components.Transform.label)} <small>${escapeHTML(state.inspector_schema.components.Transform.units)}</small></h3>${renderComponentProperties(state.inspector_schema,'Transform',transform,canEdit())}${(transform.build_issues??[]).map(issue=>`<p class="script-warning">Build: ${escapeHTML(issue)}</p>`).join('')}</section>`;
  const actorPreview=scenePreviewCurrent()?activeScenePreview()?.entities.find(item=>item.entity_id===entity.id):null;
  if(actorPreview?.preview_ground_sample){html+=`<section class="component"><h3>Preview elevation <small>Derived, not authored</small></h3>${property('Guest Y',actorPreview.preview_position.y)}${property('Terrain cell',actorPreview.preview_ground_sample.cell_index)}<p class="field-note">Interpolated from the displayed source terrain. Runtime collision, ramps and script elevation may differ.</p></section>`;}
  else if(actorPreview?.preview_height_status==='unresolved_no_source_surface'){html+='<section class="component"><h3>Preview elevation <small>Unresolved</small></h3><p class="field-note">No displayed source-ground cell exists at this placement. The mesh uses the preview ground plane; this is not a measured game height. Inspect a live sample to compare runtime placement.</p></section>';}


  if(state.capabilities?.actor_appearance && components.ActorAppearance){const appearance=components.ActorAppearance;html+=`<section class="component appearance-component"><h3>${escapeHTML(state.inspector_schema.components.ActorAppearance.label)} <small>${escapeHTML(state.inspector_schema.components.ActorAppearance.units)}</small></h3>${renderComponentProperties(state.inspector_schema,'ActorAppearance',appearance,false,true)}${componentActions('ActorAppearance')}<details><summary>Appearance evidence and limits</summary><pre>${escapeHTML(JSON.stringify(appearance,null,2))}</pre></details></section>`;}
  if(components.ActorAnimation)html+=`<section class="component"><h3>${escapeHTML(state.inspector_schema.components.ActorAnimation.label)}</h3>${renderComponentProperties(state.inspector_schema,'ActorAnimation',components.ActorAnimation,false,true)}${components.ActorAnimation.authored?.animation_asset_id?property('Authored source SHA-256',components.ActorAnimation.authored.source_record_sha256):''}<p class="field-note">Capture an authored assignment in Actor templates to reuse its observed clip witness. Initial MAN header only; animation channel ownership remains unchanged.</p>${componentActions('ActorAnimation')}</section>`;
  if(components.ActorAllocatedAnimation)html+=`<section class="component"><h3>${escapeHTML(state.inspector_schema.components.ActorAllocatedAnimation.label)} <small>${escapeHTML(state.inspector_schema.components.ActorAllocatedAnimation.units)}</small></h3>${renderComponentProperties(state.inspector_schema,'ActorAllocatedAnimation',components.ActorAllocatedAnimation,false,true)}${componentActions('ActorAllocatedAnimation')}${renderComponentDetails(state.inspector_schema,'ActorAllocatedAnimation',components.ActorAllocatedAnimation)}</section>`;
  if(state.capabilities.authored_transform_templates)html+=`<section class="component"><h3>${escapeHTML(state.inspector_schema.components.ActorPresets.label)} <small>${escapeHTML(state.inspector_schema.components.ActorPresets.units)}</small></h3>${renderComponentProperties(state.inspector_schema,'ActorPresets',{})}${componentActions('ActorPresets')}</section>`;
  if(components.ModelRenderer){const model=components.ModelRenderer;html+=`<section class="component"><h3>Model renderer <small>Imported reference</small></h3>${renderComponentProperties(state.inspector_schema,'ModelRenderer',model,false,true)}<p class="field-note">Scene meshes use supported SDK poses. Unresolved objects stay as placement markers; individual assets can be inspected separately.</p>${componentActions('ModelRenderer')}</section>`;}
  if(components.Animation)html+=`<section class="component"><h3>${escapeHTML(state.inspector_schema.components.Animation.label)}</h3>${renderComponentProperties(state.inspector_schema,'Animation',components.Animation)}<p class="field-note">${components.Animation.preview_support?.supported?'Imported association is eligible for decoding. Preview verifies the source; retail playback timing and live animation remain unknown.':escapeHTML(components.Animation.preview_support?.reason ?? 'No supported imported animation association is available for this actor.')}</p>${componentActions('Animation')}</section>`;
  if(components.RuntimeCorrelation){const correlation=components.RuntimeCorrelation;html+=`<section class="component"><h3>${escapeHTML(state.inspector_schema.components.RuntimeCorrelation.label)} <small>${escapeHTML(state.inspector_schema.components.RuntimeCorrelation.units)}</small></h3>${renderComponentProperties(state.inspector_schema,'RuntimeCorrelation',correlation)}${runtimeCandidateSummary(correlation,entity.id)}${renderComponentDetails(state.inspector_schema,'RuntimeCorrelation',correlation)}</section>`;}
  if(components.RetailMetadata){const retail=components.RetailMetadata;html+=`<section class="component"><h3>${escapeHTML(state.inspector_schema.components.RetailMetadata.label)} <small>${escapeHTML(state.inspector_schema.components.RetailMetadata.units)}</small></h3>${renderComponentProperties(state.inspector_schema,'RetailMetadata',retail)}${renderComponentDetails(state.inspector_schema,'RetailMetadata',retail)}</section>`;}
  if(components.Dialogue&&state.capabilities?.actor_script_preview)html+=`<section class="component"><h3>${escapeHTML(state.inspector_schema.components.Dialogue.label)} <small>${escapeHTML(state.inspector_schema.components.Dialogue.units)}</small></h3>${renderComponentProperties(state.inspector_schema,'Dialogue',components.Dialogue)}${componentActions('Dialogue')}</section>`;
  const renderedComponents=['Transform','ActorAppearance','ActorAnimation','ActorAllocatedAnimation','ModelRenderer','Animation','RuntimeCorrelation','RetailMetadata','Dialogue'];
  for(const [id,value] of Object.entries(components)){
    const definition=state.inspector_schema?.components?.[id];
    if(!definition||renderedComponents.includes(id))continue;
    html+=`<section class="component"><h3>${escapeHTML(definition.label??id)} <small>${escapeHTML(definition.units??'')}</small></h3>${renderComponentProperties(state.inspector_schema,id,value,false,true)}${componentActions(id)}${renderComponentDetails(state.inspector_schema,id,value)}</section>`;
    renderedComponents.push(id);
  }
  html+=renderUnregisteredComponents(state.inspector_schema,components,renderedComponents);
  const sectionSnapshot=inspectorSectionSnapshot($('inspector'),inspectorSectionsScope);
  inspectorSectionsScope=JSON.stringify([state.project.path,state.scene?.id,entity.id]);
  $('inspector').innerHTML=html;
  mountInspectorComponentFilter($('inspector'),{authored:entity.authored_components??[],state:inspectorComponentFilterState,current:()=>actorActionContext===resourceStateKey()&&selected()?.id===entity.id});
  mountInspectorSections($('inspector'),{state:inspectorSectionsState,project:state.project.path,scope:inspectorSectionsScope,snapshot:sectionSnapshot,current:()=>actorActionContext===resourceStateKey()&&selected()?.id===entity.id});
  bindComponentActions($('inspector'),actorActions,{current:()=>actorActionContext===resourceStateKey()&&selected()?.id===entity.id,editable:canEdit,busy:()=>busy,onError:error=>notify(error.message,true)});
  const transformHost=$('inspector').querySelector('[data-component-content="Transform"]')?.parentElement;if(transformHost)mountExistingGroundPosition(transformHost,'actor',entity.id);
  const inspectorContext=resourceStateKey();
  bindComponentReferences($('inspector'),{current:()=>inspectorContext===resourceStateKey()&&selected()?.id===entity.id,busy:()=>busy,records:()=>assetRecords(true),discover:()=>refreshResources(),open:record=>showAssetDetails(record,()=>assetRecords(true)),onError:error=>notify(error.message,true)});
  $('inspector').querySelectorAll('[data-component-property]').forEach(input=>input.addEventListener('change',async()=>{
    if(busy||!canEdit()||inspectorContext!==resourceStateKey()||selected()?.id!==entity.id)return;
    try{await api('/api/command',propertyCommand(state.inspector_schema,'Transform',input.dataset.componentProperty,entity.id,input.value));}
    catch(error){notify(error.message,true);renderInspector();}
  }));
}

let animationGlbEditor=null,animationGlbEntityId=null;
let animationAllocationEditor=null,animationAllocationEntityId=null;
let animationRecordLibrary=null,animationRecordEntityId=null,animationRecordAssetId=null;
let retainedAnimationEditor=null,retainedAnimationEntityId=null,retainedAnimationAssetId=null;
let retainedAnimationGlbEditor=null,retainedAnimationGlbEntityId=null,retainedAnimationGlbAssetId=null;
function refreshRetainedAssetAfterApply(assetId){
  if(assetId===null)return;
  const appliedContext=resourceStateKey();setTimeout(()=>{if(!busy&&state.project.mode==='edit'&&resourceStateKey()===appliedContext)void refreshResources();},0);
}
async function inspectRetainedAnimationGlb(entity,row,assetId=null){
  if(busy||state.project.mode!=='edit')return;
  retainedAnimationGlbEditor?.dispose();retainedAnimationGlbEntityId=entity.id;retainedAnimationGlbAssetId=assetId;
  retainedAnimationGlbEditor=await openRetainedAnimationGlbEditor({row,
    getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id??null,mode:state.project.mode,sourceKey:state.scene_preview_source_key}),
    busy:()=>busy,setBusy,onError:error=>notify(error.message??String(error),true),
    onApplied:next=>{state=next;render();notify('Retained GLB content and actor references updated. Save project to persist.');refreshRetainedAssetAfterApply(assetId);},
    onPosePreview:async(data,{returnToEditor})=>{setBusy(false);await openModel(data.semantic_id,data.animation.clip_id,entity.id,'imported',null,data,returnToEditor);
      if(model!==data||!$('model-dialog').open)throw new Error($('model-error').textContent||'Could not open proposed retained GLB content.');
      $('model-dialog').addEventListener('close',()=>{if(model===data&&scenePose?.preview!==data)returnToEditor();},{once:true});}
  });
}
async function inspectRetainedAnimationContent(entity,row,assetId=null,initialChannel=null){
  if(busy||state.project.mode!=='edit')return;
  retainedAnimationEditor?.dispose();retainedAnimationEntityId=entity.id;retainedAnimationAssetId=assetId;
  retainedAnimationEditor=await openRetainedAnimationEditor({row,initialChannel,
    getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id??null,mode:state.project.mode,sourceKey:state.scene_preview_source_key}),
    busy:()=>busy,setBusy,onError:error=>notify(error.message??String(error),true),
    onApplied:next=>{state=next;render();notify('Retained clip and actor references updated. Save project to persist.');
      refreshRetainedAssetAfterApply(assetId);},
    onPosePreview:async(data,{returnToEditor})=>{setBusy(false);await openModel(data.semantic_id,data.animation.clip_id,entity.id,'imported',null,data,returnToEditor);
      if(model!==data||!$('model-dialog').open)throw new Error($('model-error').textContent||'Could not open proposed retained content.');
      $('model-dialog').addEventListener('close',()=>{if(model===data&&scenePose?.preview!==data)returnToEditor();},{once:true});}
  });
}
async function inspectSavedAnimationRecords(entity,retainedRecord=null,assetId=null,assetAssignment=false){
  if(busy||state.project.mode!=='edit')return;
  animationRecordLibrary?.dispose();animationRecordEntityId=entity.id;animationRecordAssetId=assetId;
  animationRecordLibrary=await openAnimationRecordLibrary({entityId:entity.id,retainedRecord,assetAssignment,
    onEdit:assetAssignment?null:row=>inspectRetainedAnimationContent(entity,row,assetId),
    onGlb:assetAssignment?null:row=>inspectRetainedAnimationGlb(entity,row,assetId),
    assignment:entity.components?.ActorAllocatedAnimation?.authored??null,
    modelAssetId:entity.components?.ActorAppearance?.effective?.asset_id??null,
    getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id??null,mode:state.project.mode,sourceKey:state.scene_preview_source_key}),
    busy:()=>busy,setBusy,onError:error=>notify(error.message??String(error),true),
    onApplied:next=>{state=next;render();notify('Allocated clip settings updated. Save project to persist.');refreshRetainedAssetAfterApply(assetId);},
    onPosePreview:async(data,{returnToEditor})=>{
      setBusy(false);await openModel(data.semantic_id,data.animation.clip_id,entity.id,'imported',null,data,returnToEditor);
      if(model!==data||!$('model-dialog').open)throw new Error($('model-error').textContent||'Could not open saved allocated clip.');
      $('model-dialog').addEventListener('close',()=>{if(model===data&&scenePose?.preview!==data)returnToEditor();},{once:true});
    }});
}
async function inspectAssignedAnimationDuplicate(entity){
  if(busy||!canEdit())return;
  const getContext=()=>({projectPath:state.project.path,sceneId:state.scene?.id??null,mode:state.project.mode,sourceKey:selected()?.id===entity.id?state.scene_preview_source_key:null});
  let row;setBusy(true);
  try{row=await resolveActorAnimationGlbTarget({entityId:entity.id,getActor:()=>selected(),getContext});if(!row)throw Error('The actor has no assigned allocated clip.');}
  catch(error){notify(error.message,true);return;}finally{setBusy(false);}
  animationRecordLibrary?.dispose();animationRecordEntityId=entity.id;animationRecordAssetId=null;
  try{animationRecordLibrary=await openAnimationRecordLibrary({entityId:entity.id,retainedRecord:row,duplicateOnly:true,assignment:entity.components.ActorAllocatedAnimation.authored,getContext,busy:()=>busy,setBusy,onError:error=>notify(error.message,true),
    onApplied:next=>{state=next;render();notify('Assigned clip duplicated. Original assignment retained; the new clip is active and unassigned. Save project to persist.');}});}catch(error){notify(error.message,true);}
}
async function inspectAnimationAllocation(entity){
  if(busy||state.project.mode!=='edit')return;
  animationAllocationEditor?.dispose();animationAllocationEntityId=entity.id;
  animationAllocationEditor=await openAnimationAllocationEditor({entityId:entity.id,
    getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id??null,mode:state.project.mode,sourceKey:state.scene_preview_source_key}),
    busy:()=>busy,setBusy,onError:error=>notify(error.message??String(error),true),
    onApplied:next=>{state=next;render();notify('Animation clip allocated. Save project to persist. Gameplay assignment is pending.');},
    onPosePreview:async(data,{returnToEditor})=>{
      setBusy(false);
      await openModel(data.semantic_id,'allocation-preview',entity.id,'imported',null,data,returnToEditor);
      if(model!==data||!$('model-dialog').open)throw new Error($('model-error').textContent||'Could not open allocated clip preview.');
      $('model-dialog').addEventListener('close',()=>{if(model===data&&scenePose?.preview!==data)returnToEditor();},{once:true});
    }});
}
async function inspectAnimationGlb(entity){
  if(busy||state.project.mode!=='edit')return;
  let retainedRow;
  setBusy(true);
  try{retainedRow=await resolveActorAnimationGlbTarget({entityId:entity.id,getActor:()=>selected(),getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id??null,mode:state.project.mode,sourceKey:state.scene_preview_source_key})});}
  catch(error){notify(error.message,true);return;}
  finally{setBusy(false);}
  if(retainedRow){await inspectRetainedAnimationGlb(entity,retainedRow);return;}
  animationGlbEditor?.dispose();animationGlbEntityId=entity.id;
  animationGlbEditor=await openAnimationGlbEditor({entityId:entity.id,
    getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id??null,mode:state.project.mode,sourceKey:state.scene_preview_source_key}),
    busy:()=>busy,setBusy,onError:error=>notify(error.message??String(error),true),
    onApplied:next=>{state=next;render();notify('Animation GLB imported. Save project to persist.');},
    onPosePreview:async(data,{returnToEditor})=>{
      setBusy(false);
      await openModel(data.semantic_id,'file-preview',entity.id,'imported',null,data,returnToEditor);
      if(model!==data||!$('model-dialog').open)throw new Error($('model-error').textContent||'Could not open the reviewed animation preview.');
      $('model-dialog').addEventListener('close',()=>{
        if(model===data&&scenePose?.preview!==data)returnToEditor();
      },{once:true});
    }});
}
const animationEditDialog=document.createElement('dialog');animationEditDialog.className='project-dialog';document.body.append(animationEditDialog);
async function openAnimationChannels(entity,initialChannel=null){
  if(busy||state.project.mode!=='edit')return;
  const context=JSON.stringify([state.project.path,state.scene?.id,entity.id]);
  const loadedAuthoringState=JSON.stringify([state.scene_preview_source_key,state.authored_assets]);
  const current=()=>animationEditDialog.open&&state.project.mode==='edit'&&JSON.stringify([state.project.path,state.scene?.id,state.selection?.entity_id])===context;
  animationEditDialog.innerHTML='<h2>Edit imported animation channels</h2><p>Verifying source…</p><button type="button">Close</button>';
  animationEditDialog.querySelector('button').onclick=()=>animationEditDialog.close();animationEditDialog.showModal();setBusy(true);
  try{
    const response=await fetch('/api/animation-authoring-options',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entity.id})});
    const result=await response.json();if(!response.ok||result.error)throw new Error(result.error||'Could not load animation channels');if(!current())return;
    const binding=result.binding,edits=result.authored?.edits??[];validateImportedChannelHandoff(initialChannel,binding);
    animationEditDialog.innerHTML=`<h2>Edit imported animation channels</h2><p>${escapeHTML(binding.semantic_id)}</p><p>Imported actors sharing this clip: ${escapeHTML((result.shared_actor_ids??[]).join(", "))}</p><p>Edits apply to the imported clip. Blank axes remove this actor’s contribution; other shared-clip edits still apply. Build patches the shared scene clip within its original compressed capacity. Other actors using that clip are affected. Conflicting overrides or edits that need relocation are rejected. In-game playback has not yet been verified.</p><form><label>Frame (zero based)<input name="frame" type="number" min="0" max="${binding.frame_count-1}" step="1" value="0" required></label><label>Rigid object (zero based)<input name="object" type="number" min="0" max="${binding.bone_count-1}" step="1" value="0" required></label><div class="animation-channel-fields"></div><p class="dialog-error" role="alert"></p><button type="submit">Apply channel override</button><button type="button" class="clear-animation">Clear this actor’s channel edits</button><button type="button" class="close-animation">Close</button></form>`;
    const form=animationEditDialog.querySelector('form'),fields=form.querySelector('.animation-channel-fields'),error=form.querySelector('[role="alert"]');
    const glbEditorButton=document.createElement('button');glbEditorButton.type='button';glbEditorButton.textContent='Edit animation through GLB';glbEditorButton.dataset.animationEdit='true';
    glbEditorButton.onclick=async()=>{if(!current()||busy)return;if(channelDirty){error.textContent='Apply or discard the current channel draft before opening GLB authoring.';return;}animationEditDialog.close();await inspectAnimationGlb(entity);};
    form.querySelector('.close-animation').after(glbEditorButton);
    const allocateClipButton=document.createElement('button');allocateClipButton.type='button';allocateClipButton.textContent='Allocate independent animation clip';allocateClipButton.dataset.animationEdit='true';
    allocateClipButton.onclick=async()=>{if(!current()||busy)return;if(channelDirty){error.textContent='Apply or discard the current channel draft before allocating a clip.';return;}animationEditDialog.close();await inspectAnimationAllocation(entity);};
    glbEditorButton.after(allocateClipButton);
    const savedClipsButton=document.createElement('button');savedClipsButton.type='button';savedClipsButton.textContent='Manage allocated clips';savedClipsButton.dataset.animationEdit='true';
    savedClipsButton.onclick=async()=>{if(!current()||busy)return;if(channelDirty){error.textContent='Apply or discard the current channel draft before managing allocated clips.';return;}animationEditDialog.close();await inspectSavedAnimationRecords(entity);};
    allocateClipButton.after(savedClipsButton);
    if(initialChannel&&Number.isInteger(initialChannel.frame)&&Number.isInteger(initialChannel.object)&&initialChannel.frame>=0&&initialChannel.frame<binding.frame_count&&initialChannel.object>=0&&initialChannel.object<binding.bone_count){form.elements.frame.value=initialChannel.frame;form.elements.object.value=initialChannel.object;}
    const clearChannel=document.createElement('button');clearChannel.type='button';clearChannel.textContent='Clear selected channel contribution';clearChannel.className='clear-animation-channel';form.querySelector('.clear-animation').before(clearChannel);
    for(const group of ['translation','rotation_psx'])for(const axis of ['x','y','z']){const limits=result[group],label=document.createElement('label');label.textContent=`${group==='translation'?'Translation':'Rotation (PSX units)'} ${axis.toUpperCase()}`;const input=document.createElement('input');input.name=`${group}_${axis}`;input.type='number';input.min=limits.minimum;input.max=limits.maximum;input.step=limits.step;input.placeholder='Retail';label.append(input);fields.append(label);}
    let channelRequest=0,channelDirty=false,channelFrame=0,channelObject=0;
    const discardChannel=document.createElement('button');discardChannel.type='button';discardChannel.textContent='Discard unapplied channel changes';discardChannel.disabled=true;fields.after(discardChannel);
    fields.querySelectorAll('input').forEach(input=>input.oninput=()=>{channelDirty=true;discardChannel.disabled=false;});
    const retail=document.createElement('p');retail.className='field-note';fields.before(retail);
    let verifiedChannel=null,copiedChannel=null;
    const copyTools=document.createElement('div'),copyNote=document.createElement('p');copyNote.className='field-note';copyNote.textContent='Copy one object channel, select another frame of the same object, then paste into the draft. Apply is required.';
    for(const layer of ['retail','effective']){
      const button=document.createElement('button');button.type='button';button.textContent=`Copy ${layer} channel`;
      button.onclick=()=>{if(!current()||busy||!verifiedChannel)return;if(channelDirty){error.textContent='Apply or discard the draft before copying verified channel values.';return;}copiedChannel={object:channelObject,frame:channelFrame,layer,values:structuredClone(verifiedChannel[layer])};copyNote.textContent=`Copied ${layer} frame ${channelFrame}, object ${channelObject}. Paste into another frame of this object, then Apply.`;};copyTools.append(button);
    }
    const pasteChannel=document.createElement('button');pasteChannel.type='button';pasteChannel.textContent='Paste channel into draft';
    pasteChannel.onclick=()=>{if(!current()||busy||!verifiedChannel)return;if(!copiedChannel){error.textContent='Copy a verified channel first.';return;}if(channelDirty){error.textContent='Apply or discard the current draft before pasting.';return;}if(copiedChannel.object!==channelObject){error.textContent='Channel paste requires the same rigid object; no retargeting is inferred.';return;}for(const group of ['translation','rotation_psx'])for(const axis of ['x','y','z'])form.elements[`${group}_${axis}`].value=copiedChannel.values[group][axis];channelDirty=true;discardChannel.disabled=false;error.textContent='';};copyTools.append(pasteChannel);retail.after(copyTools,copyNote);
    const clipboardReady=value=>copyTools.querySelectorAll('button').forEach(button=>button.disabled=!value);clipboardReady(false);
    const refresh=async()=>{
      if(channelDirty){form.elements.frame.value=channelFrame;form.elements.object.value=channelObject;error.textContent='Apply or discard your channel changes before switching frames or objects.';return;}
      const request=++channelRequest,frame=Number(form.elements.frame.value),object=Number(form.elements.object.value);channelFrame=frame;channelObject=object;
      const edit=edits.find(e=>e.frame_index===frame&&e.object_index===object);
      clearChannel.disabled=!edit;
      for(const group of ['translation','rotation_psx'])for(const axis of ['x','y','z'])form.elements[`${group}_${axis}`].value=edit?.[group]?.[axis]??'';
      verifiedChannel=null;clipboardReady(false);retail.textContent='Loading retail channel…';
      if(!form.elements.frame.checkValidity()||!form.elements.object.checkValidity()){retail.textContent='Choose a valid frame and object.';return;}
      try{const response=await fetch('/api/animation-channel-values',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entity.id,frame_index:frame,object_index:object})});const values=await response.json();if(!current()||request!==channelRequest)return;if(!response.ok||values.error)throw new Error(values.error||'Channel inspection failed');if(values.source_record_sha256!==binding.source_record.record_sha256)throw new Error('Retail animation source changed; reopen the editor.');verifiedChannel=values;clipboardReady(true);retail.replaceChildren();for(const [layer,label] of [['retail','Retail'],['effective','Effective after applied shared edits']]){const row=document.createElement('div');row.textContent=`${label} · translation XYZ: ${['x','y','z'].map(a=>values[layer].translation[a]).join(' / ')} · rotation XYZ (PSX units): ${['x','y','z'].map(a=>values[layer].rotation_psx[a]).join(' / ')}`;retail.append(row);}const owners=document.createElement('div');owners.textContent=`Channel contributors: ${(values.contributors??[]).join(', ')||'None'}`;retail.append(owners);for(const group of ['translation','rotation_psx'])for(const axis of ['x','y','z']){const contributors=values.axis_contributors?.[group]?.[axis];if(!contributors?.length)continue;const row=document.createElement('div');row.className='animation-axis-contributors';row.textContent=`${group==='translation'?'Translation':'Rotation'} ${axis.toUpperCase()} contributors: ${contributors.join(', ')}`;retail.append(row);}}catch(error){if(current()&&request===channelRequest)retail.textContent=String(error.message);}
    };
    form.elements.frame.oninput=refresh;form.elements.object.oninput=refresh;refresh();
    discardChannel.onclick=()=>{if(!current()||busy)return;channelDirty=false;discardChannel.disabled=true;error.textContent='';refresh();};
    const editedLabel=document.createElement('label');editedLabel.textContent='This actor’s applied channel edits';
    const editedSelect=document.createElement('select');editedSelect.setAttribute('aria-label','Jump to applied animation channel');
    const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=edits.length?`Choose one of ${edits.length} edited channels…`:'No applied channel edits';editedSelect.append(placeholder);
    for(const edit of [...edits].sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index)){
      const option=document.createElement('option');option.value=JSON.stringify([edit.frame_index,edit.object_index]);
      const axes=['translation','rotation_psx'].flatMap(group=>Object.entries(edit[group]??{}).map(([axis,value])=>`${group==='translation'?'T':'R'}${axis.toUpperCase()}=${value}`));
      option.textContent=`Frame ${edit.frame_index} · object ${edit.object_index} · ${axes.join(', ')}`;editedSelect.append(option);
    }
    editedSelect.disabled=!edits.length;editedSelect.onchange=()=>{if(!editedSelect.value||!current())return;const [frame,object]=JSON.parse(editedSelect.value);form.elements.frame.value=frame;form.elements.object.value=object;refresh();};
    editedLabel.append(editedSelect);form.prepend(editedLabel);
    form.querySelector('.close-animation').onclick=()=>animationEditDialog.close();
    form.querySelector('.clear-animation').disabled=!edits.length;
    const apply=async command=>{
      if(busy||!current())return;
      const channel={frame:channelFrame,object:channelObject};
      if(!await api('/api/command',command,{dialog:animationEditDialog,success:'Animation override updated. Save project to persist.'})){error.textContent=$('status').textContent;return;}
      const actor=selected();if(actor?.id===entity.id&&state.project.mode==='edit')await openAnimationChannels(actor,channel);
    };
    const recordTools=document.createElement('section');recordTools.className='animation-record-tools';
    const recordNote=document.createElement('p');recordNote.className='field-note';recordNote.textContent='Animation record interchange preserves this clip’s frame/object counts and opaque bytes. Import replaces this actor’s channel contributions; other contributors remain and conflicting values reject. A retail-identical record clears this actor’s contribution. Save the project after importing.';
    const recordFormat=document.createElement('select');recordFormat.setAttribute('aria-label','Animation interchange format');
    for(const [value,label] of [['record','Raw animation record (.anm)'],['json','Editable channel JSON (.json)']]){const option=document.createElement('option');option.value=value;option.textContent=label;recordFormat.append(option);}
    recordTools.append(recordFormat);
    for(const recordLayer of ['retail','effective']){
    const downloadRecord=document.createElement('button');downloadRecord.type='button';downloadRecord.textContent=`Download ${recordLayer} animation record`;
    downloadRecord.onclick=async()=>{
      if(!current()||busy||!form.isConnected)return;const format=recordFormat.value;setBusy(true);
      try{const response=await fetch('/api/animation-record-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entity.id,layer:recordLayer,format})}),data=await response.json();if(!current()||!form.isConnected)return;if(!response.ok||data.error)throw new Error(data.error||'Animation source download failed');if(data.binding?.source_record?.record_sha256!==binding.source_record.record_sha256||typeof data.record_base64!=='string'||data.record_base64.length>5592408)throw new Error('Animation source identity or size changed; reopen the editor.');const bytes=Uint8Array.from(atob(data.record_base64),c=>c.charCodeAt(0));if(!bytes.length||bytes.length!==data.byte_length||bytes.length>4194304)throw new Error('Animation source length mismatch');const url=URL.createObjectURL(new Blob([bytes],{type:'application/octet-stream'})),link=document.createElement('a');link.href=url;link.download=recordLayer+'-animation-'+binding.semantic_id.split('/').pop()+(format==='json'?'.json':'.anm');link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(exc){if(current()&&form.isConnected)error.textContent=exc.message;}finally{setBusy(false);}
    };
    recordTools.append(downloadRecord);
    }
    const recordFile=document.createElement('input');recordFile.type='file';recordFile.accept='.anm,.bin,.json';recordFile.setAttribute('aria-label','Replacement animation record');
    const importRecord=document.createElement('button');importRecord.type='button';importRecord.textContent='Import animation record';
    const previewRecord=document.createElement('button');previewRecord.type='button';previewRecord.textContent='Preview animation file';
    const poseRecord=document.createElement('button');poseRecord.type='button';poseRecord.textContent='Inspect file animation';
    const recordPreview=document.createElement('div');recordPreview.setAttribute('aria-label','Animation file preview');
    let recordSelectionRevision=0;
    recordFile.onchange=recordFormat.onchange=()=>{recordSelectionRevision++;recordPreview.replaceChildren();error.textContent='';};
    const readRecord=async(previewOnly=false)=>{
      if(!current()||busy||!form.isConnected)return;
      if(channelDirty){error.textContent='Apply or discard the current channel draft before importing a record.';return;}
      const file=recordFile.files?.[0];if(!file||!file.size||file.size>4194304){error.textContent='Choose an animation record of at most 4 MiB.';return;}
      const format=recordFormat.value,selectionRevision=recordSelectionRevision;
      const recordCurrent=()=>current()&&form.isConnected&&recordSelectionRevision===selectionRevision&&recordFile.files?.[0]===file&&recordFormat.value===format;
      error.textContent='';let encoded;setBusy(true);
      try{encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('Could not read animation record'));reader.readAsDataURL(file);});}catch(exc){if(recordCurrent())error.textContent=exc.message;return;}finally{setBusy(false);}
      if(!recordCurrent())return;
      if(previewOnly==='pose'){
        setBusy(true);
        try{const response=await fetch('/api/animation-file-pose-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entity.id,record_base64:encoded,format})}),data=await response.json();if(!recordCurrent())return;if(!response.ok||data.error)throw new Error(data.error||'Animation pose preview failed');if(data.animation?.representation!=='file_preview'||data.animation?.entity_id!==entity.id)throw new Error('Animation file preview identity mismatch');setBusy(false);await openModel(binding.asset_semantic_id,'file-preview',entity.id,'imported',null,data,()=>{if(!form.isConnected||state.project.mode!=='edit'||JSON.stringify([state.project.path,state.scene?.id,state.selection?.entity_id])!==context||recordSelectionRevision!==selectionRevision)return false;if(!animationEditDialog.open)animationEditDialog.showModal();return true;});
        }catch(exc){if(recordCurrent())error.textContent=exc.message;}finally{setBusy(false);}return;
      }
      if(previewOnly){
        setBusy(true);recordPreview.replaceChildren();
        try{const response=await fetch('/api/animation-record-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entity.id,record_base64:encoded,format})}),data=await response.json();if(!recordCurrent())return;if(!response.ok||data.error)throw new Error(data.error||'Animation file preview failed');
          const summary=document.createElement('p');summary.textContent=`${data.changed_axes} axis changes from retail across ${data.changed_channels} channels. ${data.action==='clear_contribution'?'This would clear this actor’s contribution.':'This would replace this actor’s contribution.'} Shared-clip conflict check passed. Project unchanged; importing revalidates the file.`;recordPreview.append(summary);
          const rows=document.createElement('pre');rows.textContent=data.changes.slice(0,256).map(row=>`Frame ${row.frame_index}, object ${row.object_index} · ${row.field}: ${row.before_value} → ${row.after_value}`).join('\n');recordPreview.append(rows);
          if(data.changes.length>256){const more=document.createElement('p');more.textContent=`Showing the first 256 of ${data.changes.length} axis changes.`;recordPreview.append(more);}
        }catch(exc){if(recordCurrent())error.textContent=exc.message;}finally{setBusy(false);}return;
      }
      const channel={frame:channelFrame,object:channelObject};
      if(await api('/api/animation-record-replacement',{entity_id:entity.id,record_base64:encoded,format},{dialog:animationEditDialog,success:'Animation record imported. Save project to persist.'})){const actor=selected();if(actor?.id===entity.id)await openAnimationChannels(actor,channel);}
    };
    poseRecord.onclick=()=>readRecord('pose');previewRecord.onclick=()=>readRecord(true);importRecord.onclick=()=>readRecord();
    recordTools.prepend(recordNote);recordTools.append(recordFile,previewRecord,poseRecord,importRecord,recordPreview);form.querySelector('.close-animation').before(recordTools);
    const rangeControls=document.createElement('div');rangeControls.className='animation-copy-range';
    const rangeInputs={};
    for(const [name,label] of [['start','First target frame'],['end','Last target frame']]){
      const row=document.createElement('label');row.textContent=label;const input=document.createElement('input');input.type='number';input.min='0';input.max=String(binding.frame_count-1);input.step='1';input.value=String(channelFrame);input.required=true;input.setAttribute('aria-label',label);row.append(input);rangeControls.append(row);rangeInputs[name]=input;
    }
    const rangeNote=document.createElement('p');rangeNote.className='field-note';rangeNote.textContent='Repeat all six copied values on the same object for every frame in the inclusive range. Existing contributions for those channels are replaced. Other objects and frames remain unchanged. No interpolation is performed.';
    const applyRange=document.createElement('button');applyRange.type='button';applyRange.textContent='Apply copied channel to frame range';
    applyRange.onclick=async()=>{
      if(!current()||busy)return;
      if(channelDirty){error.textContent='Apply or discard the current draft before applying a frame range.';return;}
      if(!copiedChannel){error.textContent='Copy a verified channel first.';return;}
      if(copiedChannel.object!==channelObject){error.textContent='Frame range copy requires the same rigid object.';return;}
      if(!rangeInputs.start.reportValidity()||!rangeInputs.end.reportValidity())return;
      const start=Number(rangeInputs.start.value),end=Number(rangeInputs.end.value);
      if(start>end){error.textContent='First target frame must not exceed last target frame.';return;}
      const next=edits.filter(e=>e.object_index!==channelObject||e.frame_index<start||e.frame_index>end);
      for(let frame=start;frame<=end;frame++)next.push({frame_index:frame,object_index:channelObject,...structuredClone(copiedChannel.values)});
      await apply({type:'set_animation_channels',entity_id:entity.id,value:{animation_id:binding.semantic_id,source_record_sha256:binding.source_record.record_sha256,edits:next}});
    };
    rangeControls.append(rangeNote,applyRange);form.querySelector('.close-animation').before(rangeControls);
    const interpolate=document.createElement('button');interpolate.type='button';interpolate.textContent='Review interpolated frame range';
    const interpolationNote=document.createElement('p');interpolationNote.className='field-note';interpolationNote.textContent='Blend the copied pose into the selected effective pose across the target range. Translation rounds to integer units; rotation follows the shortest path on each PSX angle axis and rounds to 16 units. Half ties round upward; a half-turn follows the positive direction. This authors sampled poses, not playback timing or retargeting.';
    const interpolationReview=document.createElement('div');interpolationReview.dataset.animationInterpolation='review';
    const interpolationKey=()=>JSON.stringify([context,state.scene_preview_source_key,state.authored_assets,copiedChannel,verifiedChannel,channelFrame,channelObject,rangeInputs.start.value,rangeInputs.end.value,channelDirty]);
    interpolate.onclick=()=>{
      interpolationReview.replaceChildren();if(!current()||busy)return;
      try{
        if(loadedAuthoringState!==JSON.stringify([state.scene_preview_source_key,state.authored_assets]))throw new Error('Project changed since channel inspection. Reopen the animation editor.');
        if(channelDirty)throw new Error('Apply or discard the current channel draft before interpolating.');
        if(!copiedChannel||!verifiedChannel)throw new Error('Copy a verified channel and select the end pose first.');
        if(copiedChannel.object!==channelObject)throw new Error('Interpolation requires the same rigid object; no retargeting is inferred.');
        if(!rangeInputs.start.reportValidity()||!rangeInputs.end.reportValidity())return;
        const result=interpolateAnimationRange({first:copiedChannel.values,last:verifiedChannel.effective,start:Number(rangeInputs.start.value),end:Number(rangeInputs.end.value),object:channelObject,frameCount:binding.frame_count,objectCount:binding.bone_count,edits}),key=interpolationKey();error.textContent='';
        const summary=document.createElement('p');summary.textContent=`${result.proposed.length} proposed channels · copied ${copiedChannel.layer} frame ${copiedChannel.frame} to effective frame ${channelFrame} · project unchanged. Apply replaces this actor’s contributions in the target range; shared conflicts are checked on Apply.`;
        const preview=document.createElement('pre');preview.textContent=result.proposed.slice(0,256).map(row=>`Frame ${row.frame_index}, object ${row.object_index} · T ${Object.values(row.translation).join(' / ')} · R ${Object.values(row.rotation_psx).join(' / ')}`).join('\n');
        const accept=document.createElement('button');accept.type='button';accept.textContent='Apply reviewed interpolation';accept.dataset.applyInterpolation='';
        accept.onclick=async()=>{if(!current()||busy)return;if(key!==interpolationKey()){accept.disabled=true;error.textContent='Pose, range or project changed. Review interpolation again.';return;}await apply({type:'set_animation_channels',entity_id:entity.id,value:{animation_id:binding.semantic_id,source_record_sha256:binding.source_record.record_sha256,edits:result.edits}});};
        interpolationReview.append(summary,preview,accept);if(result.proposed.length>256){const limit=document.createElement('p');limit.textContent='Showing the first 256 channels; Apply uses the complete reviewed range.';interpolationReview.append(limit);}
      }catch(exc){error.textContent=exc.message;}
    };
    rangeControls.append(interpolationNote,interpolate,interpolationReview);
    clearChannel.onclick=()=>{
      if(channelDirty){error.textContent='Apply or discard unapplied channel changes before clearing the selected contribution.';return;}
      const next=edits.filter(edit=>edit.frame_index!==channelFrame||edit.object_index!==channelObject);
      apply(next.length?{type:'set_animation_channels',entity_id:entity.id,value:{animation_id:binding.semantic_id,source_record_sha256:binding.source_record.record_sha256,edits:next}}:{type:'clear_animation_channels',entity_id:entity.id});
    };
    form.querySelector('.clear-animation').onclick=()=>apply({type:'clear_animation_channels',entity_id:entity.id});
    form.onsubmit=async event=>{event.preventDefault();if(!form.reportValidity())return;if(Number(form.elements.frame.value)!==channelFrame||Number(form.elements.object.value)!==channelObject){error.textContent='Channel selection changed; discard the draft and select the channel again.';return;}const edit={frame_index:Number(form.elements.frame.value),object_index:Number(form.elements.object.value)};for(const group of ['translation','rotation_psx'])for(const axis of ['x','y','z']){const input=form.elements[`${group}_${axis}`];if(input.value!=='')(edit[group]??={})[axis]=Number(input.value);}const next=edits.filter(e=>e.frame_index!==edit.frame_index||e.object_index!==edit.object_index);if(edit.translation||edit.rotation_psx)next.push(edit);await apply(next.length?{type:'set_animation_channels',entity_id:entity.id,value:{animation_id:binding.semantic_id,source_record_sha256:binding.source_record.record_sha256,edits:next}}:{type:'clear_animation_channels',entity_id:entity.id});};
  }catch(error){if(animationEditDialog.open)animationEditDialog.querySelector('p').textContent=String(error.message);}finally{setBusy(false);}
}
const appearanceDialog=document.createElement('dialog');appearanceDialog.id='appearance-dialog';document.body.append(appearanceDialog);
async function openAppearanceOptions(entity,modelAssetId=null){
  if(busy||!canEditAppearance()||appearanceDialog.open||!entity)return;
  const key=resourceStateKey(),source=state.project_copy_source_key,fresh=()=>key===resourceStateKey()&&source===state.project_copy_source_key&&selected()?.id===entity.id&&canEditAppearance();
  if(!fresh())return;setBusy(true);
  appearanceDialog.innerHTML=`<div class="dialog-heading"><h2>Choose donor appearance</h2><button id="close-appearance" aria-label="Close donor appearance">×</button></div><p>Target: ${escapeHTML(entity.name)}. Assign a model and animation together from a verified imported donor.</p><p class="field-note">The existing actor keeps its placement and script. Structural pairing does not prove that the actor’s behavior will work with the new appearance.</p><div id="appearance-options"><p>Verifying available donor pairs…</p></div><p class="dialog-error" role="alert"></p>`;
  $('close-appearance').onclick=()=>appearanceDialog.close();
  if(modelAssetId){const filter=document.createElement('p');filter.className='field-note';filter.textContent='Model asset: '+modelAssetId+'. Only verified donor pairs using this model are listed; model and initial animation are assigned together.';$('appearance-options').before(filter);}
  appearanceDialog.showModal();
  const withdraw=()=>{if(!appearanceDialog.open||fresh())return;const host=$('appearance-options');if(host)host.textContent='Project, scene or selected actor changed. Reopen donor appearance selection.';};
  const timer=setInterval(withdraw,200);appearanceDialog.addEventListener('close',()=>clearInterval(timer),{once:true});
  try{
    const response=await fetch('/api/actor-appearance-options',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entity.id})});
    const result=await response.json();if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Could not verify donor appearances');if(!appearanceDialog.open)return;if(!fresh()){withdraw();return;}
    if(!Array.isArray(result.options)||result.options.some(option=>typeof option.donor_entity_id!=='string'||typeof option.asset_id!=='string'))throw new Error('Appearance service returned an invalid donor list.');
    const options=modelAssetId?result.options.filter(option=>option.asset_id===modelAssetId):result.options,available=result.supported&&options.length;
    $('appearance-options').innerHTML=available?'<form id="appearance-form"><label>Imported donor actor<select id="appearance-donor" required aria-label="Donor appearance"><option value="">Choose a verified donor…</option></select></label><div id="appearance-donor-details"></div><div class="dialog-actions"><button type="submit" id="apply-appearance" class="accent" data-appearance-edit data-unavailable="true" disabled>Apply donor appearance</button></div></form>':`<p>${escapeHTML(result.reason ?? (modelAssetId?'No verified donor pair uses this model for the selected actor.':'No supported donor appearances are available for this actor.'))}</p>`;
    const details=document.createElement('details');details.className='appearance-evidence';details.innerHTML='<summary>Verified options and limitations</summary><pre class="diagnostic-detail"></pre>';details.querySelector('pre').textContent=JSON.stringify(result,null,2);$('appearance-options').append(details);
    if(available){
      for(const option of options){const entry=document.createElement('option');entry.value=option.donor_entity_id;entry.textContent=`${option.label ?? option.donor_entity_id}${option.unchanged?' (same imported pair)':''}`;$('appearance-donor').append(entry);}
      const refresh=()=>{if(!fresh()){withdraw();return;}const option=options.find(item=>item.donor_entity_id===$('appearance-donor').value);$('apply-appearance').dataset.unavailable=String(!option);$('apply-appearance').disabled=busy||!canEditAppearance()||!option;$('appearance-donor-details').innerHTML=option?`${property('Donor ID',option.donor_entity_id)}${property('Model asset',option.asset_id)}${property('Animation ID',option.animation_id)}`:'';};
      $('appearance-donor').onchange=refresh;$('appearance-donor').value=entity.components.ActorAppearance?.authored?.donor_entity_id ?? '';refresh();
      $('appearance-form').onsubmit=async event=>{event.preventDefault();if(!fresh()){withdraw();return;}const donor=$('appearance-donor').value;if(options.some(option=>option.donor_entity_id===donor))await api('/api/command',{type:'set_actor_appearance',entity_id:entity.id,donor_entity_id:donor},{dialog:appearanceDialog,success:'Authored appearance assigned.'});};
    }
  }catch(error){if(appearanceDialog.open)appearanceDialog.querySelector('.dialog-error').textContent=error.message;}finally{setBusy(false);}
}

const scriptDialog=document.createElement('dialog');scriptDialog.id='script-dialog';document.body.append(scriptDialog);
let scriptEntity=null,scriptReport=null,scriptDrafts=new Map(),scriptFacingControls=null,scriptBranchControls=null,systemSelectorControls=null,sourceBuildScriptControls=null;
let animationOperandControls=null;
scriptDialog.addEventListener('close',()=>{scriptBookmarkControls?.dispose();scriptBookmarkControls=null;scriptFacingControls?.dispose();scriptFacingControls=null;scriptBranchControls?.dispose();scriptBranchControls=null;systemSelectorControls?.dispose();systemSelectorControls=null;sourceBuildScriptControls?.dispose();sourceBuildScriptControls=null;animationOperandControls?.dispose();animationOperandControls=null;});
function renderFacingAuthoring(){
  scriptFacingControls?.dispose();scriptFacingControls=null;
  if(!scriptReport?.facing_authoring)return;
  const owner=scriptEntity.id,key=resourceStateKey(),accepted=scriptReport;
  scriptFacingControls=mountScriptFacing($('script-report'),{
    report:accepted,owner,drafts:scriptDrafts,busy:()=>busy,setBusy,api,
    current:()=>scriptDialog.open&&scriptReport===accepted&&scriptEntity?.id===owner&&key===resourceStateKey()&&canEditDialogue(),
    reopen:()=>openActorScript(scriptEntity,true),onDraftChange:updateScriptActions,
    onError:error=>{if(scriptDialog.open)scriptDialog.querySelector('.dialog-error').textContent=error.message;}
  });
}
const scriptOffset=value=>Number.isInteger(value)?'0x'+value.toString(16).toUpperCase():'Unknown';
function openNpcDrafts(focusId=null){
  if(busy)return;
  const dialog=document.createElement('dialog');dialog.id='npc-drafts-dialog';
  dialog.innerHTML='<h2>NPC drafts</h2><p>Project-local new NPCs. Changes support Undo/Redo; Save persists them. Drafts appear in the viewport. Review Build assesses supported native serialization; spawning, scheduling and gameplay remain unverified.</p><p class="dialog-error" role="alert"></p><button type="button">Close</button>';
  dialog.querySelector('button').onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>dialog.remove(),{once:true});
  const drafts=Object.entries(state.actor_drafts??{});
  if(!drafts.length){const empty=document.createElement('p');empty.textContent='No drafts. Select an imported actor and use Inspect NPC creation candidate to create one.';dialog.append(empty);}
  for(const [id,draft] of drafts){
    if(focusId&&id!==focusId)continue;
    const form=document.createElement('form');
    form.innerHTML='<h3></h3><p class="field-note"></p><label>X <input name="x" type="number" min="64" max="16384" step="64" required></label><label>Z <input name="z" type="number" min="64" max="16384" step="64" required></label><button type="submit">Apply draft position</button><button type="button">Delete draft</button>';
    form.querySelector('h3').textContent=draft.name;
    form.querySelector('p').textContent=`${id} · Donor: ${draft.donor_entity_id}`;
    form.elements.x.value=draft.position.x;form.elements.z.value=draft.position.z;
    const editable=state.project?.mode==='edit';form.querySelectorAll('input,button').forEach(control=>control.disabled=!editable);
    form.onsubmit=async event=>{event.preventDefault();await api('/api/command',{type:'set_actor_draft_position',entity_id:id,position:{x:Number(form.elements.x.value),z:Number(form.elements.z.value)}},{dialog,success:'Draft position updated.'});};
    form.querySelector('button[type=button]').onclick=()=>api('/api/command',{type:'delete_actor_draft',entity_id:id},{dialog,success:'Draft deleted. Undo restores it.'});
    const focus=document.createElement('button');focus.type='button';focus.textContent='Frame draft';focus.disabled=draft.scene_id!==state.scene?.id;
    focus.onclick=()=>{dialog.close();frame({id,components:{Transform:{imported:{position:{...draft.position,y:null}}}}});};form.append(focus);
    dialog.append(form);
  }
  document.body.append(dialog);dialog.showModal();
}

function openModelNpcCreation(record,rowCurrent){
  if(busy||!canEdit())return;
  const key=resourceStateKey(),source=state.project_copy_source_key,ids=retailModelDonors(state,record.id,record.sceneId);
  if(!ids.length)return;
  let withdrawn=false;
  const fresh=()=>!withdrawn&&canEdit()&&rowCurrent()&&key===resourceStateKey()&&source===state.project_copy_source_key&&JSON.stringify(ids)===JSON.stringify(retailModelDonors(state,record.id,record.sceneId));
  const dialog=document.createElement('dialog');dialog.id='model-npc-donor-dialog';
  dialog.innerHTML='<h2>Create NPC from Model</h2><p>Choose a Retail actor donor. The new NPC inherits its native record, script and initial animation, even if that actor has authored overrides. Inspect the candidate and choose name and X/Z placement next. Runtime script behavior and gameplay remain unverified.</p><label>Retail NPC donor<select aria-label="Retail NPC donor"><option value="">Choose a donor…</option></select></label><p class="dialog-error" role="alert"></p><button type="button" data-review>Inspect NPC creation candidate</button><button type="button" data-close>Close NPC donor choice</button>';
  const select=dialog.querySelector('select'),review=dialog.querySelector('[data-review]'),error=dialog.querySelector('.dialog-error');
  for(const id of ids){const entity=entities().find(row=>row.id===id),option=document.createElement('option');option.value=id;option.textContent=`${entity.name} · ${id}`;select.append(option);}
  const refresh=()=>{let current=false;try{current=fresh();}catch{}if(!current){withdrawn=true;select.replaceChildren();select.disabled=true;error.textContent='Project, scene or Retail model donors changed. Reopen NPC creation.';}review.disabled=busy||!current||!ids.includes(select.value);};
  select.onchange=refresh;
  review.onclick=()=>{refresh();if(review.disabled)return;const entity=entities().find(row=>row.id===select.value);dialog.close();openActorCandidate(entity,record.id);};
  dialog.querySelector('[data-close]').onclick=()=>dialog.close();
  const timer=setInterval(refresh,250);dialog.addEventListener('close',()=>{clearInterval(timer);dialog.remove();},{once:true});document.body.append(dialog);refresh();dialog.showModal();
}
async function openActorCandidate(entity,modelAssetId=null){
  if(busy)return;
  const sceneId=state.scene?.id,key=resourceStateKey(),source=state.project_copy_source_key,controller=new AbortController();
  let withdrawn=false,placing=false,creationTool=null,creationBuildTool=null;
  const fresh=()=>!withdrawn&&state.scene?.id===sceneId&&key===resourceStateKey()&&source===state.project_copy_source_key&&(modelAssetId===null||canEdit()&&retailModelDonors(state,modelAssetId,sceneId).includes(entity.id));
  if(!fresh())return;
  const dialog=document.createElement('dialog');dialog.id='actor-candidate-dialog';
  const withdraw=()=>{withdrawn=true;creationBuildTool?.clear();creationTool?.clear();if(placing&&dialog.isConnected&&!dialog.open){placing=false;dialog.showModal();}controller.abort();dialog.querySelector('p').textContent='Project, scene or donor source changed. Reopen NPC creation.';dialog.querySelectorAll('input,button:not([data-close])').forEach(control=>control.disabled=true);};
  const timer=setInterval(()=>{try{if(!fresh())withdraw();}catch{withdraw();}},250);
  dialog.innerHTML='<h2>NPC creation candidate</h2><p>Inspecting the retail donor…</p><button data-close>Close</button>';
  dialog.querySelector('button').onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{if(placing)return;creationBuildTool?.dispose();creationTool?.dispose();clearInterval(timer);controller.abort();dialog.remove();});
  document.body.append(dialog);dialog.showModal();
  try{
    const response=await fetch('/api/actor-candidate-inspection',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entity.id}),signal:controller.signal});
    const report=await response.json();if(!response.ok||report.error)throw new Error(report.error||'Candidate inspection failed');
    if(!dialog.open)return;
    if(report.entity_id!==entity.id)throw new Error('Candidate identity mismatch');
    if(!fresh())throw new Error('Project, scene or donor source changed; inspect this donor again');
    if(modelAssetId!==null&&report.donor_dependencies?.model?.asset_semantic_id!==modelAssetId)throw new Error('Retail donor model differs from the selected model');
    const rows=report.actor.script_coverage.records;
    const containerStatus=report.container.supported===false?`unavailable (${report.container.reason})`:`${report.container.growth_bytes} bytes`;
    dialog.querySelector('p').textContent=`${entity.name}: ${report.includes_project_overrides ? "retail donor with authored X/Z placement" : "retail donor at imported placement"}; other project overrides are excluded. This inspection does not create an NPC. ${report.actor.reached_spawn_changes.length} decoded spawn references need updates; ${rows.filter(row=>row.coverage!=='decoded_supported_paths').length} scripts remain partial. Container growth: ${containerStatus}. Overlapping archive entries: ${report.archive.overlapping_entries.length}. This donor-only prototype does not assess complete project Build readiness. Use Review Build with proposed NPC below to assess proposed source serialization; spawning, scheduling and gameplay remain unverified.`;
    const placement=document.createElement('p');
    const included=Object.entries(report.included_overrides?.Transform?.position??{}).map(([axis,value])=>`${axis.toUpperCase()}=${value}`);
    const excluded=[...(report.excluded_override_components??[]),...(report.excluded_transform_axes??[]).map(axis=>`Position ${axis.toUpperCase()}`)];
    placement.textContent=`Candidate placement: ${included.length?included.join(', ')+'; remaining axes inherit the donor':'inherited from the retail donor'}.${excluded.length?' Excluded authored values: '+excluded.join(', ')+'.':''}`;
    dialog.append(placement);
    const form=document.createElement('form');
    form.innerHTML='<h3>New NPC draft</h3><label>Name <input name="name" maxlength="120" required></label><label>X <input name="x" type="number" min="64" max="16384" step="64" required></label><label>Z <input name="z" type="number" min="64" max="16384" step="64" required></label><p>Creates a saved-project draft through Undo/Redo. Use Save to persist it. Drafts appear in the viewport. Review Build assesses supported native candidates and the complete authored project; gameplay remains unverified.</p><p class="dialog-error" role="alert"></p><button type="submit">Create NPC draft</button>';
    form.elements.name.value=`${entity.name} draft`;
    const donorPosition=entity.components.Transform.effective.position;
    form.elements.x.value=donorPosition.x;form.elements.z.value=donorPosition.z;
    form.onsubmit=async event=>{
      event.preventDefault();if(busy)return;
      if(!fresh()||!canEdit()){withdraw();return;}
      const command={type:'create_actor_draft',donor_entity_id:entity.id,name:form.elements.name.value,position:{x:Number(form.elements.x.value),z:Number(form.elements.z.value)}},capture=captureNpcCreation(state,command);
      if(!await api('/api/command',command,{dialog,success:'NPC draft created. Save persists it; Review Build assesses native serialization.'}))return;
      try{const id=createdNpcSelection(state,capture);selectNpcDraft(id);frameNpcDraft();revealHierarchyButton.click();document.querySelector('.workspace-tabs [data-panel="inspector"]').click();}catch(error){notify(error.message,true);}
    };
    const choosePosition=document.createElement('button');choosePosition.type='button';choosePosition.textContent='Choose NPC position in scene';choosePosition.disabled=!canEdit();
    const pickedNote=document.createElement('p');pickedNote.className='field-note';
    choosePosition.onclick=()=>{if(busy||!fresh())return;try{npcGroundPlacement.begin(result=>{placing=false;if(!fresh())withdraw();else if(result){form.elements.x.value=result.position.x;form.elements.z.value=result.position.z;pickedNote.textContent=`Source-ground corner X ${result.position.x}, Z ${result.position.z}. Height is not authored; Create still requires confirmation.`;}if(dialog.isConnected&&!dialog.open)dialog.showModal();});placing=true;dialog.close();document.querySelector('.workspace-tabs [data-panel="viewport"]').click();}catch(error){form.querySelector('.dialog-error').textContent=error.message;}};
    form.querySelector('button[type="submit"]').before(choosePosition,pickedNote);
    if(!canEdit())form.querySelectorAll('input,button').forEach(control=>control.disabled=true);
    if(!state.actor_drafts?.[entity.id]){
      dialog.append(form);const previewOwner=Symbol('npc-creation');
      creationBuildTool=mountNpcCreationBuildReview({form,current:fresh,getRequest:()=>({donor_entity_id:entity.id,name:form.elements.name.value,position:nativePositionEntry({x:form.elements.x.value,z:form.elements.z.value}),project_source_key:source}),getContext:()=>({scene_id:state.scene?.id,source_key:state.scene_preview_source_key,existing_npc_draft_count:Object.keys(state.actor_drafts??{}).length}),available:()=>canEdit()&&state.capabilities?.npc_creation_build_review===true,isBusy:()=>busy||creationTool?.pending?.(),setBusy,onError:error=>{form.querySelector('.dialog-error').textContent=error.message;}});
      creationTool=mountNpcCreationPreview({form,current:fresh,available:npcCreationSceneAvailable,isBusy:()=>busy,getScene:activeScenePreview,
        getRequest:()=>({donor_entity_id:entity.id,name:form.elements.name.value,position:nativePositionEntry({x:form.elements.x.value,z:form.elements.z.value}),project_source_key:source}),
        suspend:()=>{placing=true;dialog.close();document.querySelector('.workspace-tabs [data-panel="viewport"]').click();},resume:()=>{placing=false;if(dialog.isConnected&&!dialog.open)dialog.showModal();},
        onShow:({report,document:proposed},current,resume)=>{cancelViewportGesture();const failures=sceneRenderer.load(proposed);if(failures.length){sceneRenderer.load(structuredClone(scenePreview));throw Error(failures.join('; '));}npcCreationInspection={owner:previewOwner,report,current,resume,key:sceneRequestKey()};updateNpcCreationInspection();frame({id:report.review.preview_entity_id});resize();},
        onClear:()=>clearNpcCreationInspection(previewOwner),onError:error=>{form.querySelector('.dialog-error').textContent=error.message;}});
    }

    const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Technical evidence';pre.textContent=JSON.stringify(report,null,2);details.append(summary,pre);dialog.append(details);
    const inspect=document.createElement('button');inspect.textContent='Inspect donor script';
    inspect.onclick=()=>{if(busy)return;if(!fresh()){withdraw();return;}dialog.close();openActorScript(entities().find(item=>item.id===(report.donor_entity_id??entity.id))??entity);};
    dialog.append(inspect);
    const dependencies=report.donor_dependencies;
    if(dependencies){
      const info=document.createElement('p');
      info.textContent=`Donor model: ${dependencies.model?.asset_semantic_id??'unresolved'}. Initial animations: ${(dependencies.animations??[]).map(a=>`${a.semantic_id} (${a.frame_count} frames, ${a.channel_count} channels)`).join(', ')||'unavailable'}. Scripts may select other assets at runtime.`;
      dialog.append(info);
      const assetId=dependencies.model?.asset_semantic_id;
      if(assetId){const model=document.createElement('button');model.textContent='Preview donor model';model.onclick=()=>{if(busy)return;if(!fresh()){withdraw();return;}dialog.close();openModel(assetId);};dialog.append(model);}
    }
  }catch(error){if(dialog.open)dialog.querySelector('p').textContent=String(error.message||error);}
}
let scriptBookmarkControls=null;
async function openActorScript(entity,refresh=false,focusRun=null,focusDialogue=null,focusInstruction=null,focusComponent=null,focusBookmark=null){
  if(busy||(refresh&&!scriptDialog.open))return;const scroll=refresh?scriptDialog.scrollTop:0;scriptBookmarkControls?.dispose();scriptBookmarkControls=null;scriptFacingControls?.dispose();scriptFacingControls=null;scriptBranchControls?.dispose();scriptBranchControls=null;systemSelectorControls?.dispose();systemSelectorControls=null;sourceBuildScriptControls?.dispose();sourceBuildScriptControls=null;animationOperandControls?.dispose();animationOperandControls=null;scriptReport=null;setBusy(true);
  if(!refresh){scriptEntity=entity;scriptDrafts.clear();
  scriptDialog.innerHTML=`<div class="dialog-heading"><h2>Script and dialogue</h2><button id="close-script" aria-label="Close script inspection">×</button></div><p>${escapeHTML(entity.name)} · Review source-qualified branch destinations below</p><div id="script-authoring-toolbar" class="script-authoring-toolbar" hidden><button id="script-undo">Undo</button><button id="script-redo">Redo</button><button id="script-save">Save project</button><span id="script-authoring-status"></span></div><div id="script-report"><p>Verifying the imported script record…</p></div><p class="dialog-error" role="alert"></p>`;
  $('close-script').onclick=()=>scriptDialog.close();scriptDialog.showModal();
  $('script-undo').onclick=()=>scriptProjectAction('/api/undo');$('script-redo').onclick=()=>scriptProjectAction('/api/redo');$('script-save').onclick=()=>scriptProjectAction('/api/project/save');
  }
  try{
    const response=await fetch(entity.triggerId?'/api/trigger-script':entity.partitionTwo?'/api/partition-two-script':'/api/actor-script',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(entity.triggerId?{asset_id:entity.triggerId}:{entity_id:entity.id})});
    let report=await response.json();if(!response.ok||report.error)throw new Error(typeof report.error==='string'?report.error:'Script inspection failed');
    if(entity.triggerId||entity.partitionTwo){if(report.script_id!==entity.id.replace(/^scene:\/\//,'script://')||report.scene_id!==state.scene?.id||report.source_key!==state.scene_preview_source_key)throw new Error('Script identity or source changed.');report={...report,...report.inspection};}
    if(!scriptDialog.open)return;
    if(report.read_only!==true||!Array.isArray(report.instructions)||!Array.isArray(report.dialogues))throw new Error('Script service returned an invalid inspection report.');
    if(focusBookmark){focusInstruction=qualifyScriptBookmark(focusBookmark,entity.id,report);}
    const instructions=report.instructions,dialogues=report.dialogues,opaque=report.opaque_regions ?? [],stops=report.stops ?? [];
    $('script-report').innerHTML=`<p class="script-summary">${instructions.length} decoded instructions · ${dialogues.length} dialogue segments · ${report.status==='partial'?'Partial inspection':'Supported paths decoded'}</p><p class="field-note">Record offsets are relative to the script record. Decoded paths do not establish which branch runs in the game. Name substitutions remain explicit placeholders.</p><div id="script-warnings"></div><section><h3>Decoded dialogue</h3><div id="script-dialogue"></div></section><details class="script-instructions" ${dialogues.length?'':'open'}><summary>Instruction paths (${instructions.length})</summary><div class="script-table-wrap"><table><thead><tr><th>Record offset</th><th>Instruction</th><th>Operands</th><th>Successors</th></tr></thead><tbody></tbody></table></div></details><details class="script-raw"><summary>Source, raw bytes and decoder limits</summary><pre class="diagnostic-detail"></pre></details>`;
    if(opaque.length||stops.length){const warning=document.createElement('div');warning.className='script-warning';warning.textContent=`${opaque.length} opaque regions · ${stops.length} decoder stops. Unvisited bytes and unsupported behavior remain unresolved.`;$('script-warnings').append(warning);for(const region of opaque){const line=document.createElement('p');line.className='field-note';line.textContent=`${scriptOffset(region.pc)} · ${region.length} opaque bytes: ${region.reason}`;$('script-warnings').append(line);}for(const stop of stops){const line=document.createElement('p');line.className='field-note';line.textContent=`${scriptOffset(stop.pc)}: ${stop.reason}`;$('script-warnings').append(line);}}
    if(!dialogues.length)$('script-dialogue').textContent='No dialogue was decoded in the inspected paths.';
    for(const dialogue of dialogues){const card=document.createElement('article');card.className='script-dialogue-card';card.dataset.dialogueId=dialogue.semantic_id;card.dataset.dialoguePc=dialogue.pc;card.innerHTML=`<small>Imported segment · ${escapeHTML(scriptOffset(dialogue.pc))} · ${escapeHTML(dialogue.length)} bytes</small><p></p><details><summary>Text tokens and source span</summary><pre class="diagnostic-detail"></pre></details>`;card.querySelector('p').textContent=dialogue.text ?? '';card.querySelector('pre').textContent=JSON.stringify(dialogue,null,2);$('script-dialogue').append(card);}
    const instructionNavigation=appendScriptInstructions($('script-report').querySelector('.script-instructions > div'),report,undefined,undefined,pc=>{scriptBranchControls?.select(pc);animationOperandControls?.select(pc);scriptBookmarkControls?.updateState();});

    $('script-report').querySelector('.script-raw pre').textContent=JSON.stringify(report,null,2);
    scriptReport=report;
    if(focusBookmark){const note=document.createElement('p');note.className='focused-script-bookmark';note.setAttribute('role','status');note.textContent=`Verified bookmark: ${focusBookmark.name} · ${scriptOffset(focusInstruction)} ${focusBookmark.mnemonic} · Original source boundary`; $('script-report').prepend(note);}
    if(state.capabilities?.saved_script_bookmarks){
      const owner=scriptEntity.id,key=resourceStateKey(),accepted=report;
      scriptBookmarkControls=mountScriptBookmarks($('script-report'),{owner,report,getRows:()=>state.script_bookmarks??[],getSelected:()=>instructionNavigation.selected(),select:instructionNavigation.select,
        current:()=>scriptDialog.open&&key===resourceStateKey()&&scriptEntity?.id===owner&&scriptReport===accepted,busy:()=>busy,editable:()=>!sceneAnimationController?.active()&&state.project?.mode==='edit',draftPending:()=>scriptDrafts.size>0,
        command:body=>api('/api/command',body),reopen:pc=>openActorScript(scriptEntity,true,null,null,pc),onError:error=>notify(error.message,true)});
    }
    if(state.capabilities?.system_selector_authoring){
      const owner=scriptEntity.id,accepted=report;
      systemSelectorControls=mountSystemSelectors($('script-report'),{owner,initialDrafts:new Map([...scriptDrafts].filter(([id])=>id.includes('/system-flag/'))),
        getContext:()=>({projectPath:state.project?.path,sceneId:state.scene?.id,mode:state.project?.mode,scriptKey:state.script_authoring_state_key}),busy:()=>busy,setBusy,api,
        reopen:pc=>openActorScript(scriptEntity,true,null,null,pc),
        onDraftChange:drafts=>{for(const id of scriptDrafts.keys())if(id.includes('/system-flag/'))scriptDrafts.delete(id);for(const [id,value] of drafts)scriptDrafts.set(id,value);updateScriptActions();},
        onError:error=>{if(scriptDialog.open&&scriptReport===accepted)scriptDialog.querySelector('.dialog-error').textContent=error.message;}});
    }
    if(state.capabilities?.script_branch_authoring){
      const owner=scriptEntity.id,accepted=report;
      scriptBranchControls=mountScriptBranches($('script-report'),{owner,initialDrafts:new Map([...scriptDrafts].filter(([id])=>id.includes('/branch/'))),
        getContext:()=>({projectPath:state.project?.path,sceneId:state.scene?.id,mode:state.project?.mode,scriptKey:state.script_authoring_state_key}),
        busy:()=>busy,setBusy,api,getProjectSourceKey:()=>state.project_copy_source_key,selectInstruction:(pc,reveal=true)=>instructionNavigation.select(pc,true,reveal),
        reopen:pc=>openActorScript(scriptEntity,true,null,null,pc),
        canEditAnimation:(snapshot,pc)=>{try{if(!scriptDialog.open||scriptReport!==accepted||sceneAnimationController?.active())return false;currentAnimationSelection(snapshot,accepted.animation_operand_authoring,pc,state);return true;}catch{return false;}},
        onEditAnimation:(snapshot,pc)=>{try{const selection=currentAnimationSelection(snapshot,accepted.animation_operand_authoring,pc,state);animationOperandControls?.select(selection.pc);scriptDialog.querySelector('.animation-operands-authoring')?.scrollIntoView({block:'start'});}catch(error){notify(error.message,true);}},
        onDraftChange:drafts=>{for(const id of scriptDrafts.keys())if(id.includes('/branch/'))scriptDrafts.delete(id);for(const [id,value] of drafts)scriptDrafts.set(id,value);updateScriptActions();},
        onError:error=>{if(scriptDialog.open&&scriptReport===accepted)scriptDialog.querySelector('.dialog-error').textContent=error.message;}});
      scriptBranchControls.ready.then(()=>{if(scriptDialog.open&&scriptReport===accepted){if(Number.isInteger(focusInstruction))scriptBranchControls?.select(focusInstruction);updateScriptActions();}});
    }
    scriptDialog.querySelector('[data-operand-files]')?.remove();
    if(state.capabilities?.script_operand_files&&canEditDialogue()){
      const owner=scriptEntity.id,key=resourceStateKey(),accepted=report,ownerContext=operandOwnerContext(state,owner);
      mountScriptOperandFiles($('script-report'),{owner,scene:state.scene.id,current:()=>scriptDialog.open&&key===resourceStateKey()&&scriptEntity?.id===owner&&scriptReport===accepted&&operandOwnerContext(state,owner)===ownerContext&&canEditDialogue(),busy:()=>busy,setBusy,api,reopen:()=>openActorScript(scriptEntity,true),onError:error=>notify(error.message,true)});
    }
    renderDialogueAuthoring();renderTransitionAuthoring();renderMovementAuthoring();renderFlagAuthoring();renderWaitAuthoring();renderScriptAnimationOperands();renderScriptEffectColors();renderModelSelectorAuthoring();renderFacingAuthoring();updateScriptActions();
    if(scriptEntity.id.includes('/scripts/man-p2/')){const owner=scriptEntity.id,key=resourceStateKey(),accepted=scriptReport;mountScriptOwnerInspector($('script-report'),{owner,getState:()=>state,current:()=>scriptDialog.open&&scriptEntity?.id===owner&&scriptReport===accepted&&key===resourceStateKey(),editable:canEditDialogue,busy:()=>busy,api,onReset:()=>openActorScript(scriptEntity,true),onError:error=>notify(error.message,true)});}
    {const owner=scriptEntity.id,key=resourceStateKey(),accepted=scriptReport;mountScriptFamilyNavigation($('script-report'),{current:()=>scriptDialog.open&&scriptEntity?.id===owner&&scriptReport===accepted&&key===resourceStateKey(),busy:()=>busy});}
    if(state.capabilities?.source_build_script_inspection){const owner=scriptEntity.id,key=resourceStateKey(),accepted=scriptReport;sourceBuildScriptControls=mountSourceBuildScript($('script-report'),{owner,getContext:()=>({projectPath:state.project?.path,sceneId:state.scene?.id,scriptKey:state.script_authoring_state_key}),current:()=>scriptDialog.open&&scriptEntity?.id===owner&&scriptReport===accepted&&key===resourceStateKey(),busy:()=>busy,setBusy});}
    scriptDialog.scrollTop=scroll;
    if(Number.isInteger(focusInstruction)){
      $('script-report').querySelector('.script-instructions').open=true;
      animationOperandControls?.select(focusInstruction);
      if(!instructionNavigation.select(focusInstruction))notify('The selected instruction was not found in the verified report.',true);
    }
  }catch(error){if(scriptDialog.open){scriptDialog.querySelector('.dialog-error').textContent=error.message;if(refresh){scriptReport=null;scriptDialog.querySelectorAll('.dialogue-run,.transition-entry,.transition-unresolved,.movement-authoring,.flag-authoring,.wait-authoring,.effectColor-authoring,.animation-operands-authoring,.modelSelector-authoring,.facing-authoring,[data-clear-unresolved]').forEach(item=>item.remove());}}}finally{setBusy(false);if(focusRun&&scriptDialog.open){const input=[...scriptDialog.querySelectorAll('[data-run-input]')].find(item=>item.dataset.runInput===focusRun);if(input){if(focusRun.includes('/transition/'))input.scrollIntoView({block:'center'});input.focus({preventScroll:true});}}else if(focusDialogue&&scriptDialog.open){const cards=[...scriptDialog.querySelectorAll('.script-dialogue-card')],card=cards.find(item=>item.dataset.dialogueId===focusDialogue.semantic_id) ?? cards.find(item=>Number.isInteger(focusDialogue.pc)&&Number(item.dataset.dialoguePc)===focusDialogue.pc);if(card){card.classList.add('dialogue-focus');card.tabIndex=-1;card.scrollIntoView({block:'start'});card.focus({preventScroll:true});}else notify('The selected dialogue segment was not found in the verified report.',true);}}
  if(focusComponent&&scriptDialog.open&&scriptEntity?.id===entity.id)focusScriptInspectorFamily(scriptDialog,focusComponent);
}

function renderMovementAuthoring(){
  const authoring=scriptReport?.movement_authoring;if(!authoring)return;
  const section=document.createElement('section');section.className='movement-authoring';
  section.innerHTML='<h3>Script movement operands</h3><p class="field-note">Edit decoded X/Z targets in exact 64-unit steps and NPC_RUN/EXEC_MOVE encoded move selectors (0–255). Selector meanings and upper depth bits remain unresolved. The low nibble is a separate facing operand where supported. Y, branch execution and runtime actor identity remain unresolved. These edits save to the project. Build supports descriptor MAN scenes; Export disc also supports streaming scenes and NPC drafts. Gameplay remains unverified. The instruction table shows retail coordinates; the target overlay offers retail and authored layers.</p>';
  $('script-report').append(section);
  const owner=scriptEntity.id,key=resourceStateKey(),current=()=>!busy&&canEditDialogue()&&key===resourceStateKey()&&scriptEntity?.id===owner;
  const send=async(id,type,values)=>{
    if(!current())return;
    if(await api('/api/command',{type,entity_id:owner,movement_id:id,...(type==='set_movement_target'?{values}:{})})){
      scriptDrafts.delete(id);await openActorScript(scriptEntity,true);
    }else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;
  };
  if(authoring.reason){const note=document.createElement('p');note.textContent=authoring.reason;section.append(note);}
  for(const id of authoring.unresolved_overrides??[]){
    const button=document.createElement('button');button.textContent=`Clear unresolved movement ${id}`;button.dataset.clearMovement=id;
    button.onclick=()=>send(id,'clear_movement_target');section.append(button);
  }
  for(const target of authoring.targets??[]){
    const form=document.createElement('form');form.className='movement-entry';form.dataset.movementId=target.semantic_id;
    const title=document.createElement('h4');title.textContent=`${target.mnemonic} at ${scriptOffset(target.pc)}`;
    const layers=document.createElement('p');layers.className='movement-layers';layers.textContent=target.mnemonic==='EXEC_MOVE'?`Retail encoded move selector ${target.values.move_id} · Authored ${Object.keys(target.authored_values).length?target.authored_values.move_id:'none'} · Effective ${target.effective_values.move_id} · No position operand · Selector meaning unresolved`:`Retail X ${target.values.x}, Z ${target.values.z} · Authored ${Object.keys(target.authored_values).length?Object.entries(target.authored_values).map(([a,v])=>`${a.toUpperCase()} ${v}`).join(', '):'none'} · Effective X ${target.effective_values.x}, Z ${target.effective_values.z}${target.mnemonic==='NPC_RUN'?` · Retail move selector ${target.values.move_id}, effective ${target.effective_values.move_id}`:''}${target.target_context!==null?` · actor context ${target.target_context} unresolved`:''}`;
    form.append(title,layers);const fields={};
    for(const axis of Object.keys(target.values)){
      const label=document.createElement('label'),input=document.createElement('input');label.textContent=axis==='move_id'?'Encoded move selector':`Target ${axis.toUpperCase()}`;
      input.type='number';input.required=true;input.min=axis==='move_id'?'0':'64';input.max=axis==='move_id'?'255':'16384';input.step=axis==='move_id'?'1':'64';input.value=scriptDrafts.get(target.semantic_id)?.[axis]??target.effective_values[axis];input.setAttribute('aria-label',`Movement ${axis.toUpperCase()} at ${scriptOffset(target.pc)}`);
      fields[axis]=input;label.append(input);form.append(label);
      input.oninput=()=>{scriptDrafts.set(target.semantic_id,Object.fromEntries(Object.entries(fields).map(([a,i])=>[a,i.value])));updateScriptActions();};
    }
    const apply=document.createElement('button'),clear=document.createElement('button'),discard=document.createElement('button');apply.type='submit';apply.textContent='Apply movement';clear.type=discard.type='button';clear.textContent='Clear movement override';discard.textContent='Discard movement draft';form.append(apply,clear,discard);
    form.updateState=()=>{const editable=current();for(const input of Object.values(fields))input.disabled=!editable;apply.disabled=!editable||!Object.values(fields).every(input=>input.value!==''&&input.checkValidity());clear.disabled=!editable||!Object.keys(target.authored_values).length;discard.disabled=busy;discard.hidden=!scriptDrafts.has(target.semantic_id);};
    form.onsubmit=event=>{event.preventDefault();if(!apply.disabled)send(target.semantic_id,'set_movement_target',Object.fromEntries(Object.entries(fields).map(([a,i])=>[a,Number(i.value)])));};
    clear.onclick=()=>send(target.semantic_id,'clear_movement_target');
    discard.onclick=()=>{scriptDrafts.delete(target.semantic_id);for(const [axis,input] of Object.entries(fields))input.value=target.effective_values[axis];updateScriptActions();};
    section.append(form);form.updateState();
  }
}
function renderFlagAuthoring(){
  const authoring=scriptReport?.flag_authoring;if(!authoring)return;
  const section=document.createElement('section');section.className='flag-authoring';
  const heading=document.createElement('h3'),note=document.createElement('p');heading.textContent='Script flag operands';note.className='field-note';
  note.textContent='Edit the encoded bit index in supported local, global and context SET/CLEAR/TEST instructions. Retail, authored and effective operands remain separate. Context SET bit 8 and CLEAR bit 10 have special behavior and cannot be authored here. Story meaning, current runtime values and execution are unresolved. Build and Export disc serialize these edits; gameplay remains unverified.';
  section.append(heading,note);$('script-report').append(section);
  const owner=scriptEntity.id,key=resourceStateKey(),current=()=>!busy&&canEditDialogue()&&key===resourceStateKey()&&scriptEntity?.id===owner;
  const send=async(id,type,values)=>{
    if(!current())return;
    if(await api('/api/command',{type,entity_id:owner,flag_id:id,...(type==='set_flag_bit'?{values}:{})})){
      scriptDrafts.delete(id);await openActorScript(scriptEntity,true);
    }else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;
  };
  if(authoring.reason){const reason=document.createElement('p');reason.textContent=authoring.reason;section.append(reason);}
  for(const item of authoring.unavailable??[]){const reason=document.createElement('p');reason.className='field-note';reason.textContent=`${item.mnemonic} at ${scriptOffset(item.pc)}: ${item.reason}`;section.append(reason);}
  for(const id of authoring.unresolved_overrides??[]){
    const button=document.createElement('button');button.textContent=`Clear unresolved flag ${id}`;button.dataset.clearFlag=id;button.onclick=()=>send(id,'clear_flag_bit');section.append(button);
  }
  for(const target of authoring.targets??[]){
    const form=document.createElement('form');form.className='flag-entry';form.dataset.flagId=target.semantic_id;
    const title=document.createElement('h4'),layers=document.createElement('p');title.textContent=`${target.mnemonic} at ${scriptOffset(target.pc)}`;
    layers.className='flag-layers';layers.textContent=`Retail bit ${target.values.bit} · Authored ${Object.keys(target.authored_values).length?target.authored_values.bit:'none'} · Effective bit ${target.effective_values.bit}${target.target_context!==null?` · Encoded actor context ${target.target_context}, runtime binding unresolved`:''}`;
    const label=document.createElement('label'),input=document.createElement('input');label.textContent='Encoded flag bit';input.type='number';input.required=true;input.min='0';input.max=String(target.maximum);input.step='1';input.value=scriptDrafts.get(target.semantic_id)?.bit??target.effective_values.bit;input.setAttribute('aria-label',`Flag bit at ${scriptOffset(target.pc)}`);label.append(input);
    const apply=document.createElement('button'),clear=document.createElement('button'),discard=document.createElement('button');apply.type='submit';apply.textContent='Apply flag bit';clear.type=discard.type='button';clear.textContent='Clear flag override';discard.textContent='Discard flag draft';form.append(title,layers,label,apply,clear,discard);
    const valid=()=>input.value!==''&&input.checkValidity()&&!(target.mnemonic==='CFLAG_SET'&&Number(input.value)===8)&&!(target.mnemonic==='CFLAG_CLEAR'&&Number(input.value)===10);
    form.updateState=()=>{const editable=current();input.disabled=!editable;apply.disabled=!editable||!valid();clear.disabled=!editable||!Object.keys(target.authored_values).length;discard.disabled=busy;discard.hidden=!scriptDrafts.has(target.semantic_id);};
    input.oninput=()=>{scriptDrafts.set(target.semantic_id,{bit:input.value});updateScriptActions();};
    form.onsubmit=event=>{event.preventDefault();if(!apply.disabled)send(target.semantic_id,'set_flag_bit',{bit:Number(input.value)});};
    clear.onclick=()=>send(target.semantic_id,'clear_flag_bit');discard.onclick=()=>{scriptDrafts.delete(target.semantic_id);input.value=target.effective_values.bit;updateScriptActions();};
    section.append(form);form.updateState();
  }
}
function renderWaitAuthoring(){
  const authoring=scriptReport?.wait_authoring;if(!authoring)return;
  const section=document.createElement('section');section.className='wait-authoring';
  const heading=document.createElement('h3'),note=document.createElement('p');heading.textContent='Script wait targets';note.className='field-note';
  note.textContent='Edit WAIT_FRAMES targets in host frame_delta ticks (0–32767). Retail, authored and effective targets remain separate. Seconds, frame rate and actual execution are unresolved. Build and Export disc serialize supported targets; gameplay timing remains unverified.';
  section.append(heading,note);$('script-report').append(section);
  const owner=scriptEntity.id,key=resourceStateKey(),current=()=>!busy&&canEditDialogue()&&key===resourceStateKey()&&scriptEntity?.id===owner;
  const send=async(id,type,values)=>{
    if(!current())return;
    if(await api('/api/command',{type,entity_id:owner,wait_id:id,...(type==='set_wait_target'?{values}:{})})){
      scriptDrafts.delete(id);await openActorScript(scriptEntity,true);
    }else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;
  };
  if(authoring.reason){const reason=document.createElement('p');reason.textContent=authoring.reason;section.append(reason);}
  for(const item of authoring.unavailable??[]){const reason=document.createElement('p');reason.className='field-note';reason.textContent=`WAIT_FRAMES at ${scriptOffset(item.pc)}: ${item.reason}`;section.append(reason);}
  for(const id of authoring.unresolved_overrides??[]){
    const button=document.createElement('button');button.textContent=`Clear unresolved wait ${id}`;button.dataset.clearWait=id;button.onclick=()=>send(id,'clear_wait_target');section.append(button);
  }
  for(const target of authoring.targets??[]){
    const form=document.createElement('form');form.className='wait-entry';form.dataset.waitId=target.semantic_id;
    const title=document.createElement('h4'),layers=document.createElement('p');title.textContent=`${target.mnemonic} at ${scriptOffset(target.pc)}`;
    layers.className='wait-layers';layers.textContent=`Retail ticks ${target.values.duration_ticks} · Authored ${Object.keys(target.authored_values).length?target.authored_values.duration_ticks:'none'} · Effective ticks ${target.effective_values.duration_ticks}${target.target_context!==null?` · Encoded actor context ${target.target_context}, runtime binding unresolved`:''}`;
    const label=document.createElement('label'),input=document.createElement('input');label.textContent='Duration in host ticks';input.type='number';input.required=true;input.min='0';input.max='32767';input.step='1';input.value=scriptDrafts.get(target.semantic_id)?.duration_ticks??target.effective_values.duration_ticks;input.setAttribute('aria-label',`Wait ticks at ${scriptOffset(target.pc)}`);label.append(input);
    const apply=document.createElement('button'),clear=document.createElement('button'),discard=document.createElement('button');apply.type='submit';apply.textContent='Apply wait target';clear.type=discard.type='button';clear.textContent='Clear wait override';discard.textContent='Discard wait draft';form.append(title,layers,label,apply,clear,discard);
    const valid=()=>input.value!==''&&input.checkValidity();
    form.updateState=()=>{const editable=current();input.disabled=!editable;apply.disabled=!editable||!valid();clear.disabled=!editable||!Object.keys(target.authored_values).length;discard.disabled=busy;discard.hidden=!scriptDrafts.has(target.semantic_id);};
    input.oninput=()=>{scriptDrafts.set(target.semantic_id,{duration_ticks:input.value});updateScriptActions();};
    form.onsubmit=event=>{event.preventDefault();if(!apply.disabled)send(target.semantic_id,'set_wait_target',{duration_ticks:Number(input.value)});};
    clear.onclick=()=>send(target.semantic_id,'clear_wait_target');discard.onclick=()=>{scriptDrafts.delete(target.semantic_id);input.value=target.effective_values.duration_ticks;updateScriptActions();};
    section.append(form);form.updateState();
  }
}
function renderScriptAnimationOperands(){
  animationOperandControls?.dispose();animationOperandControls=null;
  if(!scriptReport?.animation_operand_authoring||!state.capabilities?.script_animation_operand_authoring)return;
  const owner=scriptEntity.id,accepted=scriptReport,key=state.script_authoring_state_key;
  const current=()=>scriptDialog.open&&scriptEntity?.id===owner&&scriptReport===accepted&&state.script_authoring_state_key===key&&state.project?.mode==='edit'&&!sceneAnimationController?.active();
  animationOperandControls=mountAnimationOperands($('script-report'),{source:scriptReport.animation_operand_authoring,owner,stateKey:key,current,busy:()=>busy,drafts:scriptDrafts,onDraftChange:updateScriptActions,
    onReturn:pc=>{if(current()&&!busy){scriptBranchControls?.select(pc);scriptDialog.querySelector('.script-branch-authoring')?.scrollIntoView({block:'start'});}},
    requestUses:async body=>{if(!current()||busy)throw new Error('Animation usage source changed.');const response=await fetch('/api/animation-operand-uses',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),value=await response.json();if(!response.ok||value.error)throw new Error(value.error??'Animation usage inspection failed.');return value;},
    onInspectUse:row=>{if(!current()||busy)return;if(row.kind==='npc'){const draft=state.actor_drafts?.[row.entity_id];if(!draft||draft.scene_id!==state.scene?.id||draft.donor_entity_id!==row.donor_entity_id)return;scriptDialog.close();openNpcAnimationOperands({entityId:row.entity_id,getState:()=>state,isBusy:()=>busy,canEdit,api,focusPc:row.target.pc});}else{const entity=row.entity_id.includes('/scripts/man-p2/')?{id:row.entity_id,name:row.entity_id,partitionTwo:true}:entities().find(e=>e.id===row.entity_id);if(entity)openActorScript(entity,false,null,null,row.target.pc);}},
    requestReview:async body=>{if(!current()||busy)throw new Error('Animation source changed; reopen script inspection.');setBusy(true);try{const response=await fetch('/api/script-animation-operand-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await response.json();if(!response.ok||data.error)throw new Error(typeof data.error==='string'?data.error:'Animation Review failed.');return data;}finally{setBusy(false);}},
    command:async body=>{if(!await api('/api/command',body))throw new Error($('status').textContent);return true;},reopen:pc=>openActorScript(scriptEntity,true,null,null,pc),
    onError:error=>{if(scriptDialog.open&&scriptReport===accepted)scriptDialog.querySelector('.dialog-error').textContent=error.message;},
    selectInstruction:pc=>{const button=scriptDialog.querySelector(`[aria-label="Select instruction ${scriptOffset(pc)}"]`);button?.click();}});
}
function renderScriptEffectColors(){
  const owner=scriptEntity.id,key=resourceStateKey(),current=()=>!busy&&canEditDialogue()&&key===resourceStateKey()&&scriptEntity?.id===owner;
  renderEffectColorAuthoring({report:scriptReport,host:$('script-report'),owner,current,busy:()=>busy,drafts:scriptDrafts,onDraftChange:updateScriptActions,send:async(id,type,values)=>{if(!current())return;if(await api('/api/command',{type,entity_id:owner,effect_color_id:id,...(type==='set_effect_color_target'?{values}:{})})){scriptDrafts.delete(id);await openActorScript(scriptEntity,true);}else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;}});
}
function renderModelSelectorAuthoring(){
  const authoring=scriptReport?.model_selector_authoring;if(!authoring)return;
  const section=document.createElement('section');section.className='modelSelector-authoring';
  const heading=document.createElement('h3'),note=document.createElement('p');heading.textContent='Script model selectors';note.className='field-note';
  note.textContent='Edit a signed16 script selector (-32768 to32767), not a resolved model asset. Values >=240 request the high pool. Runtime pool bases and restaging are unresolved; the primitive resets move_id and clears draw flag0x1000. Build and Export disc preserve instruction layout; gameplay remains unverified.';
  section.append(heading,note);$('script-report').append(section);
  const owner=scriptEntity.id,key=resourceStateKey(),current=()=>scriptDialog.open&&!busy&&canEditDialogue()&&key===resourceStateKey()&&scriptEntity?.id===owner;
  const send=async(id,type,values)=>{
    if(!current())return;
    if(await api('/api/command',{type,entity_id:owner,model_selector_id:id,...(type==='set_model_selector_target'?{values}:{})})){
      scriptDrafts.delete(id);await openActorScript(scriptEntity,true,id);
    }else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;
  };
  if(authoring.reason){const reason=document.createElement('p');reason.textContent=authoring.reason;section.append(reason);}
  for(const item of authoring.unavailable??[]){const reason=document.createElement('p');reason.className='field-note';reason.textContent=`SET_ACTOR_MODEL at ${scriptOffset(item.pc)}: ${item.reason}`;section.append(reason);}
  for(const id of authoring.unresolved_overrides??[]){
    const button=document.createElement('button');button.textContent=`Clear unresolved model selector ${id}`;button.dataset.clearModelSelector=id;button.onclick=()=>send(id,'clear_model_selector_target');section.append(button);
  }
  for(const target of authoring.targets??[]){
    const form=document.createElement('form');form.className='modelSelector-entry';form.dataset.modelSelectorId=target.semantic_id;
    const title=document.createElement('h4'),layers=document.createElement('p');title.textContent=`${target.mnemonic} at ${scriptOffset(target.pc)}`;
    layers.className='modelSelector-layers';layers.textContent=`Retail selector ${target.values.model_selector_signed} · Authored ${Object.keys(target.authored_values).length?target.authored_values.model_selector_signed:'none'} · Effective selector ${target.effective_values.model_selector_signed}${target.target_context!==null?` · Encoded actor context ${target.target_context}, runtime binding unresolved`:''}`;
    const label=document.createElement('label'),input=document.createElement('input');label.textContent='Signed script model selector';input.type='number';input.required=true;input.min='-32768';input.max='32767';input.step='1';input.dataset.runInput=target.semantic_id;input.value=scriptDrafts.get(target.semantic_id)?.model_selector_signed??target.effective_values.model_selector_signed;input.setAttribute('aria-label',`Model selector at ${scriptOffset(target.pc)}`);label.append(input);
    const apply=document.createElement('button'),clear=document.createElement('button'),discard=document.createElement('button');apply.type='submit';apply.textContent='Apply model selector';clear.type=discard.type='button';clear.textContent='Clear model selector override';discard.textContent='Discard model selector draft';form.append(title,layers,label,apply,clear,discard);
    const dispatch=document.createElement('p');dispatch.className='field-note';form.append(dispatch);
    const valid=()=>input.value!==''&&input.checkValidity();
    form.updateState=()=>{dispatch.textContent=valid()?`Draft encoded u16 ${Number(input.value)&65535} · High-pool flag ${Number(input.value)>=240?'set':'clear'} · Asset binding unresolved`:'Invalid signed16 selector';const editable=current();input.disabled=!editable;apply.disabled=!editable||!valid();clear.disabled=!editable||!Object.keys(target.authored_values).length;discard.disabled=busy;discard.hidden=!scriptDrafts.has(target.semantic_id);};
    input.oninput=()=>{scriptDrafts.set(target.semantic_id,{model_selector_signed:input.value});updateScriptActions();};
    form.onsubmit=event=>{event.preventDefault();if(!apply.disabled)send(target.semantic_id,'set_model_selector_target',{model_selector_signed:Number(input.value)});};
    clear.onclick=()=>send(target.semantic_id,'clear_model_selector_target');discard.onclick=()=>{scriptDrafts.delete(target.semantic_id);input.value=target.effective_values.model_selector_signed;updateScriptActions();};
    section.append(form);form.updateState();
  }
}
function renderTransitionAuthoring(){
  const authoring=scriptReport?.transition_authoring;if(!authoring||(!authoring.transitions?.length&&!authoring.unresolved_overrides?.length))return;
  const section=document.createElement('section'),heading=document.createElement('h3'),note=document.createElement('p');
  section.className='transition-authoring';
  heading.textContent='Transition entries';note.className='field-note';
  note.textContent='Edit encoded entry bytes (0–255). The preview decodes the retail entry format. Destination names remain fixed.';
  section.append(heading,note);$('script-report').append(section);
  for(const identifier of authoring.unresolved_overrides ?? []){
    const row=document.createElement('div'),label=document.createElement('code'),button=document.createElement('button');
    row.className='transition-unresolved';label.textContent=identifier;button.type='button';button.textContent='Clear unresolved transition';button.dataset.clearTransition=identifier;
    button.disabled=busy||!canEditDialogue();button.onclick=async()=>{if(busy||!canEditDialogue())return;
      if(await api('/api/command',{type:'clear_transition_entry',entity_id:scriptEntity.id,transition_id:identifier})){scriptDrafts.delete(identifier);await openActorScript(scriptEntity,true);}else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;};
    row.append(label,button);section.append(row);
  }
  if(authoring.reason){const reason=document.createElement('p');reason.className='field-note';reason.textContent=authoring.reason;section.append(reason);}
  for(const entry of authoring.transitions ?? []){
    const form=document.createElement('form');form.className='transition-entry';
    const title=document.createElement('h4');title.textContent=`${entry.destination} at ${scriptOffset(entry.pc)}`;form.append(title);
    if(entry.effective_interpretation){const value=entry.effective_interpretation,preview=document.createElement('p');preview.className='field-note';preview.textContent=`Effective arrival: X ${value.x} / Z ${value.z} / facing ${value.facing_angle_12bit} (12-bit angle). Static retail interpretation; height and live arrival are not verified.`;form.append(preview);}
    const inputs={};
    for(const [field,label] of [['entry_x_encoded','Entry X'],['entry_z_encoded','Entry Z'],['direction_encoded','Direction']]){
      const row=document.createElement('label'),input=document.createElement('input');
      row.textContent=`${label} (imported ${entry.values[field]}) `;input.type='number';input.min='0';input.max='255';input.step='1';input.required=true;
      input.setAttribute('aria-label',`${label} at ${scriptOffset(entry.pc)}`);
      if(field==='entry_x_encoded')input.dataset.runInput=entry.semantic_id;
      input.value=scriptDrafts.get(entry.semantic_id)?.[field] ?? entry.effective_values[field];inputs[field]=input;row.append(input);form.append(row);
      input.oninput=()=>{scriptDrafts.set(entry.semantic_id,Object.fromEntries(Object.entries(inputs).map(([k,v])=>[k,v.value])));updateScriptActions();};
    }
    const apply=document.createElement('button'),clear=document.createElement('button'),discard=document.createElement('button');
    apply.type='submit';apply.textContent='Apply entry';clear.type=discard.type='button';clear.textContent='Clear entry override';discard.textContent='Discard draft';form.append(apply,clear,discard);
    form.updateState=()=>{const editable=!busy&&canEditDialogue()&&!scriptDrafts.has(entry.semantic_id+'/arrival');form.title=scriptDrafts.has(entry.semantic_id+'/arrival')?'Apply or discard the arrival draft before editing encoded bytes.':'';for(const input of Object.values(inputs))input.disabled=!editable;apply.disabled=!editable||!Object.values(inputs).every(i=>i.value!==''&&Number.isInteger(Number(i.value))&&Number(i.value)>=0&&Number(i.value)<=255);clear.disabled=!editable||!Object.keys(entry.authored_values).length;discard.disabled=busy;discard.hidden=!scriptDrafts.has(entry.semantic_id);};
    const send=async(type)=>{if(busy||!canEditDialogue()||scriptDrafts.has(entry.semantic_id+'/arrival'))return;const command={type,entity_id:scriptEntity.id,transition_id:entry.semantic_id};if(type==='set_transition_entry')command.values=Object.fromEntries(Object.entries(inputs).map(([k,v])=>[k,Number(v.value)]));
      if(await api('/api/command',command)){scriptDrafts.delete(entry.semantic_id);await openActorScript(scriptEntity,true);}else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;};
    form.onsubmit=e=>{e.preventDefault();if(!apply.disabled)send('set_transition_entry');};clear.onclick=()=>send('clear_transition_entry');discard.onclick=()=>{scriptDrafts.delete(entry.semantic_id);for(const [field,input] of Object.entries(inputs))input.value=entry.effective_values[field];updateScriptActions();};
    section.append(form);form.updateState();
    if(entry.effective_interpretation){
      const arrival=document.createElement('form');arrival.className='transition-entry';const title=document.createElement('h4');title.textContent='Arrival coordinates';arrival.append(title);
      const draftKey=entry.semantic_id+'/arrival',base={x:entry.effective_interpretation.x,z:entry.effective_interpretation.z,facing_sector:entry.effective_values.direction_encoded&7},fields={};
      for(const [key,label] of [['x','Arrival X'],['z','Arrival Z'],['facing_sector','Facing sector']]){
        const row=document.createElement('label'),input=document.createElement('input');row.textContent=label;input.type='number';input.required=true;input.min=key==='facing_sector'?'0':'64';input.max=key==='facing_sector'?'7':'16384';input.step=key==='facing_sector'?'1':'64';input.value=scriptDrafts.get(draftKey)?.[key] ?? base[key];input.setAttribute('aria-label',`${label} at ${scriptOffset(entry.pc)}`);fields[key]=input;row.append(input);arrival.append(row);
        input.oninput=()=>{scriptDrafts.set(draftKey,Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,v.value])));updateScriptActions();};
      }
      const apply=document.createElement('button'),discard=document.createElement('button'),note=document.createElement('p');apply.type='submit';apply.textContent='Apply arrival';discard.type='button';discard.textContent='Discard arrival draft';note.className='field-note';note.textContent='X/Z use exact 64-unit steps. Facing sectors 0–7 select 512-unit angle steps; other direction bits are preserved. Height is unchanged.';arrival.append(apply,discard,note);
      arrival.updateState=()=>{const editable=!busy&&canEditDialogue()&&!scriptDrafts.has(entry.semantic_id);arrival.title=scriptDrafts.has(entry.semantic_id)?'Apply or discard the encoded-byte draft before editing arrival coordinates.':'';for(const input of Object.values(fields))input.disabled=!editable;apply.disabled=!editable||!Object.values(fields).every(input=>input.value!==''&&input.checkValidity());discard.disabled=busy;discard.hidden=!scriptDrafts.has(draftKey);};
      discard.onclick=()=>{scriptDrafts.delete(draftKey);for(const [key,input] of Object.entries(fields))input.value=base[key];updateScriptActions();};
      arrival.onsubmit=async event=>{event.preventDefault();if(apply.disabled)return;const values=Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,Number(v.value)]));if(await api('/api/command',{type:'set_transition_arrival',entity_id:scriptEntity.id,transition_id:entry.semantic_id,arrival:values})){scriptDrafts.delete(draftKey);await openActorScript(scriptEntity,true,entry.semantic_id);}else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;};
      section.append(arrival);arrival.updateState();
    }
  }
}

function canEditDialogue(){return state.capabilities?.actor_dialogue_authoring===true && (state.project?.mode ?? 'edit').toLowerCase()==='edit';}
function updateScriptActions(){
  projectBookmarkNavigator?.updateState();
  scriptFacingControls?.updateState();scriptBranchControls?.updateState();systemSelectorControls?.updateState();sourceBuildScriptControls?.updateState();animationOperandControls?.updateState();scriptBookmarkControls?.updateState();
  const authoring=scriptReport?.dialogue_authoring;
  $('script-authoring-toolbar').hidden=!state.capabilities?.actor_dialogue_authoring||!(state.capabilities?.script_branch_authoring||authoring?.supported||authoring?.unresolved_overrides?.length||scriptReport?.transition_authoring?.supported||scriptReport?.movement_authoring?.supported||scriptReport?.movement_authoring?.unresolved_overrides?.length||scriptReport?.flag_authoring?.supported||scriptReport?.flag_authoring?.unresolved_overrides?.length||scriptReport?.animation_operand_authoring?.supported||scriptReport?.wait_authoring?.supported||scriptReport?.wait_authoring?.unresolved_overrides?.length||scriptReport?.model_selector_authoring?.supported||scriptReport?.model_selector_authoring?.unresolved_overrides?.length||scriptReport?.facing_authoring?.supported||scriptReport?.facing_authoring?.unresolved_overrides?.length);
  if(scriptBookmarkControls&&state.capabilities?.saved_script_bookmarks)$('script-authoring-toolbar').hidden=false;
  const bookmarkEdit=!!scriptBookmarkControls&&state.capabilities?.saved_script_bookmarks&&state.project?.mode==='edit'&&!sceneAnimationController?.active();
  const pending=scriptDrafts.size>0;
  $('script-undo').disabled=busy||pending||(!canEditDialogue()&&!bookmarkEdit)||!state.history?.can_undo;
  $('script-redo').disabled=busy||pending||(!canEditDialogue()&&!bookmarkEdit)||!state.history?.can_redo;
  $('script-save').disabled=busy||pending||!state.project?.dirty;
  $('script-authoring-status').textContent=pending?`${scriptDrafts.size} unapplied draft(s) · Apply or discard before project actions`:busy?'Verifying…':projectSaveStatus();
  for(const button of scriptDialog.querySelectorAll('[data-text-file]'))button.disabled=busy||pending||!canEditDialogue();
  for(const form of scriptDialog.querySelectorAll('.dialogue-run'))updateDialogueRun(form);
  for(const form of scriptDialog.querySelectorAll('.transition-entry'))form.updateState();
  for(const form of scriptDialog.querySelectorAll('.movement-entry,.flag-entry,.wait-entry,.effectColor-entry,.modelSelector-entry'))form.updateState();
  for(const button of scriptDialog.querySelectorAll('[data-clear-flag],[data-clear-wait],[data-clear-model-selector]'))button.disabled=busy||!canEditDialogue();
  for(const button of scriptDialog.querySelectorAll('[data-clear-movement]'))button.disabled=busy||!canEditDialogue();
  for(const button of scriptDialog.querySelectorAll('[data-clear-unresolved],[data-clear-transition]'))button.disabled=busy||!canEditDialogue();
}
function updateDialogueRun(form){
  const run=form.run,input=form.querySelector('textarea'),text=input.value,capacity=run.max_length;
  const validCapacity=Number.isInteger(capacity)&&capacity>=0&&capacity<=4096;
  const characters=/^[\x20-\x7e]*$/.test(text)&&!text.includes('^')&&!text.includes('|');
  const valid=validCapacity&&characters&&text.length<=capacity;
  const error=!validCapacity?'The source capacity is unavailable.':!characters?'Use printable ASCII only. Caret (^), pipe (the game newline), line breaks and control characters are unsupported.':text.length>capacity?`Too long: ${text.length} bytes exceeds ${capacity} source bytes.`:'';
  input.disabled=busy||!canEditDialogue();input.setAttribute('aria-invalid',String(!valid));
  form.querySelector('.run-counter').textContent=error||`${text.length} / ${capacity} bytes · ${capacity-text.length} space padding bytes after Apply`;
  form.querySelector('.run-counter').classList.toggle('invalid',!valid);
  form.querySelector('.run-apply').disabled=busy||!canEditDialogue()||!valid||text===run.authored_text;
  form.querySelector('.run-clear').disabled=busy||!canEditDialogue()||run.authored_text===null||run.authored_text===undefined;
  form.querySelector('.run-discard').hidden=!scriptDrafts.has(run.semantic_id);form.querySelector('.run-discard').disabled=busy;
  if(form.updateGlyphs)form.updateGlyphs();
}
async function scriptProjectAction(route){
  if(busy||scriptDrafts.size)return;
  scriptDialog.querySelector('.dialog-error').textContent='';
  if(await api(route,{}))await openActorScript(scriptEntity,true);
  else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;
}
async function dialogueCommand(run,type,text){
  if(busy||!canEditDialogue())return;
  const command={type,entity_id:scriptEntity.id,run_id:run.semantic_id,...(type==='set_dialogue_text'?{text}:{})};
  scriptDialog.querySelector('.dialog-error').textContent='';
  if(await api('/api/command',command)){scriptDrafts.delete(run.semantic_id);await openActorScript(scriptEntity,true,run.semantic_id);}
  else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;
}
async function loadTextGlyphPreviews(report,owner,key){
  const note=document.createElement('p');note.className='field-note';note.dataset.glyphStatus='true';note.textContent='Loading verified retail glyph stencil…';
  scriptDialog.querySelector('.dialogue-authoring-evidence').after(note);
  const current=()=>scriptDialog.open&&report===scriptReport&&owner===scriptEntity?.id&&key===resourceStateKey();
  try{
    const response=await fetch('/api/text-font',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:owner})}),data=await response.json();
    if(!current())return;if(!response.ok)throw new Error(data.error);
    const font=decodeTextFont(data,owner,report.dialogue_authoring.source.decoded_man_sha256),atlas=document.createElement('canvas');atlas.width=224;atlas.height=210;atlas.getContext('2d').putImageData(new ImageData(font.rgba,224,210),0,0);
    note.textContent='Source glyph stencil and advances · white fill/dark shadow. Each run starts at zero; controls, substitutions, line wrapping, boxes and runtime tint are not simulated.';
    const evidence=document.createElement('details');evidence.className='glyph-evidence';const summary=document.createElement('summary'),raw=document.createElement('pre');summary.textContent='Font source and preview limits';raw.className='diagnostic-detail';raw.textContent=JSON.stringify({source:data.source,limitations:data.limitations},null,2);evidence.append(summary,raw);note.after(evidence);
    for(const form of scriptDialog.querySelectorAll('.dialogue-run')){
      const run=form.run,group=document.createElement('section');group.className='run-glyph-preview';
      const paint=(label,text)=>{
        const row=document.createElement('div'),name=document.createElement('small'),canvas=document.createElement('canvas'),metrics=document.createElement('small');row.className='glyph-layer';name.textContent=label;row.append(name,canvas,metrics);
        const update=value=>{
          try{const layout=layoutGlyphRun(font,value);canvas.hidden=false;canvas.width=layout.canvas_width;canvas.height=15;const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;for(const glyph of layout.glyphs)ctx.drawImage(atlas,glyph.atlas_x,glyph.atlas_y,14,15,glyph.x,0,14,15);canvas.style.width=(canvas.width*2)+'px';canvas.style.height='30px';metrics.textContent=`${layout.advance} source pixels advance${layout.truncated?' · preview truncated':''}`;canvas.dataset.advance=layout.advance;}
          catch{canvas.width=1;canvas.height=15;canvas.hidden=true;delete canvas.dataset.advance;metrics.textContent='Unsupported or unavailable text · no glyph preview';}
        };update(text);group.append(row);return {row,update};
      };
      paint('Retail glyph run',run.text);paint('Effective glyph run',run.effective_text);
      const draft=paint('Draft after Apply · not applied',null);draft.row.hidden=true;form.append(group);
      form.updateGlyphs=()=>{if(!current()){group.remove();delete form.updateGlyphs;return;}const pending=scriptDrafts.has(run.semantic_id);draft.row.hidden=!pending;if(pending){const text=form.querySelector('textarea').value;draft.update(text.length<=run.max_length?text.padEnd(run.max_length,' '):null);}};form.updateGlyphs();
    }
  }catch(error){if(current())note.textContent='Glyph preview unavailable: '+error.message;}
}
async function downloadTextJSON(report,owner,key){
  if(busy||scriptDrafts.size||report!==scriptReport||key!==resourceStateKey())return;
  setBusy(true);
  try{
    const response=await fetch('/api/text-json-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:owner})}),data=await response.json();
    if(!response.ok)throw new Error(data.error);
    if(!scriptDialog.open||report!==scriptReport||key!==resourceStateKey())return;
    const text=JSON.stringify(data,null,2)+'\n';if(new TextEncoder().encode(text).length>1024*1024)throw new Error('Text JSON exceeds 1 MiB.');
    const url=URL.createObjectURL(new Blob([text],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='source-bound-text-runs.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    notify('Downloaded current text overrides. Edit only text; null inherits retail.');
  }catch(error){notify(error.message,true);}finally{setBusy(false);}
}
function openTextJSON(report,owner,key){
  if(busy||scriptDrafts.size||report!==scriptReport||key!==resourceStateKey())return;
  const dialog=document.createElement('dialog');dialog.className='project-dialog';dialog.id='text-json-dialog';
  dialog.innerHTML='<h2>Inspect text JSON</h2><p>Source-bound dialogue and menu label runs. Edit only text; null inherits retail. Inspect before Apply. Applying all file changes creates one Undo step.</p><label>Text JSON file <input type="file" accept=".json,application/json" aria-label="Text JSON file"></label><p data-file-status role="status">Choose a current exported file.</p><div data-file-changes></div><p class="dialog-error" role="alert"></p><button type="button" data-file-apply disabled>Apply text file</button><button type="button" data-file-close>Close</button>';
  document.body.append(dialog);let revision=0,encoded=null;
  const input=dialog.querySelector('input'),apply=dialog.querySelector('[data-file-apply]'),status=dialog.querySelector('[data-file-status]'),changes=dialog.querySelector('[data-file-changes]'),error=dialog.querySelector('.dialog-error');
  const current=()=>dialog.open&&scriptDialog.open&&report===scriptReport&&owner===scriptEntity?.id&&key===resourceStateKey()&&canEditDialogue()&&!scriptDrafts.size;
  dialog.addEventListener('close',()=>{revision++;dialog.remove();});dialog.querySelector('[data-file-close]').onclick=()=>dialog.close();
  input.onchange=async()=>{
    const ticket=++revision,file=input.files?.[0];encoded=null;apply.disabled=true;changes.replaceChildren();error.textContent='';status.textContent='';
    if(!file||!current())return;if(file.size>1024*1024){error.textContent='Text JSON exceeds 1 MiB.';return;}
    input.disabled=true;setBusy(true);
    try{
      const bytes=new Uint8Array(await file.arrayBuffer());if(ticket!==revision||!current())return;
      let binary='';for(let n=0;n<bytes.length;n+=8192)binary+=String.fromCharCode(...bytes.subarray(n,n+8192));const candidate=btoa(binary);
      const response=await fetch('/api/text-json-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:owner,json_base64:candidate})}),result=await response.json();
      if(ticket!==revision||!current())return;if(!response.ok)throw new Error(result.error);
      if(result.owner_id!==owner||!Array.isArray(result.changes)||result.changes.length>1024||result.change_count!==result.changes.length)throw new Error('Invalid text preview report.');
      status.textContent=`${result.change_count} proposed text override changes · not applied`;
      for(const change of result.changes){const row=document.createElement('article');row.className='script-dialogue-card';const title=document.createElement('code'),body=document.createElement('pre');title.textContent=change.run_id;row.style.minWidth='0';title.style.display='block';title.style.overflowWrap='anywhere';title.style.whiteSpace='normal';body.style.whiteSpace='pre-wrap';body.style.overflowWrap='anywhere';body.textContent=`Authored before: ${change.before===null?'inherit retail':JSON.stringify(change.before)}\nAuthored proposed: ${change.after===null?'inherit retail':JSON.stringify(change.after)}\nEffective proposed: ${JSON.stringify(change.effective)}`;row.append(title,body);changes.append(row);}
      encoded=candidate;apply.disabled=!result.change_count;
    }catch(exc){if(ticket===revision&&current())error.textContent=exc.message;}finally{input.disabled=false;setBusy(false);}
  };
  apply.onclick=async()=>{if(busy||!current()||!encoded||apply.disabled)return;
    if(await api('/api/text-json-import',{entity_id:owner,json_base64:encoded})){dialog.close();await openActorScript(scriptEntity,true);}else error.textContent=$('status').textContent;
  };
  dialog.showModal();
}
function renderDialogueAuthoring(){
  const authoring=scriptReport?.dialogue_authoring;
  if(!state.capabilities?.actor_dialogue_authoring||!authoring){updateScriptActions();return;}
  const note=document.createElement('div');note.className='dialogue-authoring-note';
  note.textContent=authoring.supported?'Supported plain-text runs can be replaced within their source byte capacity. Shorter text is padded with spaces; empty text becomes all spaces. Controls, substitutions, renderer newline bytes (|) and menu jump targets stay unchanged. Menu execution remains unresolved. Apply each draft before Save; unapplied drafts are discarded when this dialog is reopened.':authoring.reason ?? 'This actor has no supported text runs for authoring.';
  $('script-dialogue').before(note);
  const evidence=document.createElement('details');evidence.className='dialogue-authoring-evidence';evidence.innerHTML='<summary>Text authoring source and limits</summary><pre class="diagnostic-detail"></pre>';evidence.querySelector('pre').textContent=JSON.stringify({source:authoring.source,limitations:authoring.limitations,unresolved_overrides:authoring.unresolved_overrides},null,2);note.after(evidence);
  if(authoring.unresolved_overrides?.length){const warning=document.createElement('div');warning.className='unresolved-dialogue';const text=document.createElement('p');text.className='dialog-error';text.textContent=`${authoring.unresolved_overrides.length} stored text overrides could not be resolved. They can be cleared without changing the imported record.`;warning.append(text);for(const identifier of authoring.unresolved_overrides){const row=document.createElement('div'),label=document.createElement('code'),button=document.createElement('button');label.textContent=identifier;button.textContent='Clear unresolved override';button.dataset.clearUnresolved=identifier;button.onclick=()=>dialogueCommand({semantic_id:identifier},'clear_dialogue_text');row.append(label,button);warning.append(row);}evidence.after(warning);}
  if(!authoring.supported){updateScriptActions();return;}
  const files=document.createElement('div');files.className='dialog-actions';
  const download=document.createElement('button'),inspect=document.createElement('button'),owner=scriptEntity.id,key=resourceStateKey();
  download.textContent='Download text JSON';inspect.textContent='Inspect text JSON file';download.dataset.textFile=inspect.dataset.textFile='true';
  download.onclick=()=>downloadTextJSON(scriptReport,owner,key);inspect.onclick=()=>openTextJSON(scriptReport,owner,key);files.append(download,inspect);evidence.after(files);
  for(const run of authoring.runs ?? []){
    const parent=[...$('script-dialogue').querySelectorAll('.script-dialogue-card')].find(card=>card.dataset.dialogueId===run.dialogue_id) ?? $('script-dialogue');
    const form=document.createElement('form');form.className='dialogue-run';form.run=run;
    form.innerHTML=`<h4>${run.kind==='menu_label'?`Menu option ${escapeHTML(run.option_index+1)} of ${escapeHTML(run.option_count)} · picker ${escapeHTML(scriptOffset(run.menu_pc))} · label run`:'Text run'} ${escapeHTML(scriptOffset(run.pc))} <small>${escapeHTML(run.max_length)} source bytes</small></h4><div class="run-layer"><span>Imported</span><pre class="run-imported"></pre></div><label class="run-layer"><span>Authored replacement</span><textarea rows="2" spellcheck="false" aria-label="Authored text at ${escapeHTML(scriptOffset(run.pc))}" placeholder="No override. Empty text applied here becomes spaces."></textarea></label><div class="run-counter" role="status"></div><div class="run-actions"><button type="submit" class="run-apply accent">Apply text</button><button type="button" class="run-clear">Clear override</button><button type="button" class="run-discard" hidden>Discard draft</button></div><div class="run-layer"><span>Effective after Apply</span><pre class="run-effective"></pre></div><p class="run-effective-note field-note"></p>`;
    form.querySelector('.run-imported').textContent=run.text ?? '';
    const input=form.querySelector('textarea');input.dataset.runInput=run.semantic_id;input.value=scriptDrafts.has(run.semantic_id)?scriptDrafts.get(run.semantic_id):run.authored_text ?? '';
    form.querySelector('.run-effective').textContent=run.effective_text ?? 'Unavailable';
    form.querySelector('.run-effective-note').textContent=run.validation_error ?? (run.authored_text===null?'No authored override; effective text inherits the imported run.':`${Math.max(0,run.max_length-(run.authored_text?.length ?? 0))} trailing spaces are retained in the effective source bytes.`);
    input.oninput=()=>{if(input.value===(run.authored_text ?? ''))scriptDrafts.delete(run.semantic_id);else scriptDrafts.set(run.semantic_id,input.value);updateScriptActions();};
    form.onsubmit=event=>{event.preventDefault();if(!form.querySelector('.run-apply').disabled)dialogueCommand(run,'set_dialogue_text',input.value);};
    form.querySelector('.run-clear').onclick=()=>dialogueCommand(run,'clear_dialogue_text');
    form.querySelector('.run-discard').onclick=()=>{scriptDrafts.delete(run.semantic_id);input.value=run.authored_text ?? '';updateScriptActions();};
    if(run.kind==='menu_label'){
      const target=document.createElement('p');target.className='field-note';
      target.textContent=`Encoded choice target ${scriptOffset(run.encoded_target)} · jump entry ${scriptOffset(run.entry_pc)} · relative jump ${run.relative_jump}. Jump table and continuation stay unchanged; runtime choice and pager execution are unverified.`;
      form.prepend(target);
    }
    parent.append(form);
  }
  updateScriptActions();
  if(state.capabilities?.text_font_preview)loadTextGlyphPreviews(scriptReport,owner,key);
}

function frame(entity){
  pendingEntityFrame=null;
  if(entity&&modelsEnabled&&state.capabilities?.scene_preview&&state.scene_preview_source_key&&!scenePreviewCurrent()&&!sceneError){
    pendingEntityFrame={entity,key:sceneRequestKey(),scene:state.scene?.id,project:state.project?.path,projectSource:state.project_copy_source_key,selection:hierarchySelectedIdentity(),revision:cameraRevision};
    return;
  }
  const points=entity?[position(entity)]:(sceneLayers.actors?entities().filter(e=>!hiddenSceneEntities().has(e.id)).map(position):[]);
  const hasMesh=sceneModelsReady()&&(!entity||sceneRenderer.hasEntity(entity.id));
  if(hasMesh)points.push(...previewBounds(entity?.id,hiddenSceneEntities()));
  if(!points.length){camera.target={x:0,y:0,z:0};camera.distance=2000;draw();return;}
  const min={x:Infinity,y:Infinity,z:Infinity},max={x:-Infinity,y:-Infinity,z:-Infinity};
  for(const p of points)for(const axis of ['x','y','z']){min[axis]=Math.min(min[axis],p[axis]);max[axis]=Math.max(max[axis],p[axis]);}
  for(const axis of ['x','y','z'])camera.target[axis]=(min[axis]+max[axis])/2;
  const span=Math.hypot(max.x-min.x,max.y-min.y,max.z-min.z);
  camera.distance=entity?(hasMesh?Math.max(20,span*2.2):Math.max(100,camera.distance*.35)):Math.max(200,span*1.3);cameraRevision++;
  draw();
}
function basis(){return sceneCameraBasis(camera);}
function project(p){const b=basis(),d={x:p.x-camera.target.x,y:p.y-camera.target.y,z:p.z-camera.target.z},dot=v=>d.x*v.x+d.y*v.y+d.z*v.z,depth=camera.distance+dot(b.forward);if(depth<=camera.distance*.01)return null;const scale=Math.min(width,height)*.9/(camera.projection==='orthographic'?camera.distance:depth);return {x:width/2+dot(b.right)*scale,y:height/2-dot(b.up)*scale,depth,scale};}
function groundAt(x,y,planeY){
  const b=basis(),f=Math.min(width,height)*.9;
  const origin={x:camera.target.x-camera.distance*b.forward.x,y:camera.target.y-camera.distance*b.forward.y,z:camera.target.z-camera.distance*b.forward.z};
  const ray={};for(const axis of ['x','y','z']){const offset=(x-width/2)/f*b.right[axis]-(y-height/2)/f*b.up[axis];if(camera.projection==='orthographic'){origin[axis]+=offset*camera.distance;ray[axis]=b.forward[axis];}else ray[axis]=b.forward[axis]+offset;}
  if(Math.abs(ray.y)<.00001)return null;const t=(planeY-origin.y)/ray.y;if(t<0)return null;
  return {x:origin.x+t*ray.x,y:planeY,z:origin.z+t*ray.z};
}
function line(a,b,color,widthPx=1){const p=project(a),q=project(b);if(!p||!q)return;ctx.strokeStyle=color;ctx.lineWidth=widthPx;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.stroke();}
function observedCandidatePoints(){
  const epoch=acceptedEpoch(state.runtime),correlation=state.runtime_correlation;
  if(state.project?.mode!=='live'||!epoch||correlation?.available!==true||correlation.epoch_id!==epoch)return [];
  const candidates=selected()?.components?.RuntimeCorrelation?.candidates;
  if(!Array.isArray(candidates))return [];
  return candidates.slice(0,128).filter(candidate=>candidate?.epoch_id===epoch&&['x','y','z'].every(axis=>numeric(candidate.observed_position?.[axis]))).map(candidate=>displayPosition(candidate.observed_position));
}
function drawRuntimeNodeLayer(){
  runtimeNodeHits=[];
  if(!showObservedNodes)return;
  const epoch=acceptedEpoch(state.runtime),correlation=state.runtime_correlation;
  if(state.project?.mode!=='live'||!epoch||correlation?.available!==true||correlation.epoch_id!==epoch)return;
  const nodes=(correlation.runtime_nodes??[]).slice(0,128).filter(node=>node.epoch_id===epoch&&['x','y','z'].every(axis=>numeric(node.observed_position?.[axis])));
  ctx.save();ctx.strokeStyle='#79d5e8';ctx.fillStyle='#79d5e8';ctx.lineWidth=1.5;ctx.font='11px "Segoe UI",sans-serif';
  for(const node of nodes){const point=project(displayPosition(node.observed_position));if(!point||!numeric(point.x)||!numeric(point.y))continue;runtimeNodeHits.push({x:point.x,y:point.y,id:node.runtime_node_id,epoch});ctx.beginPath();ctx.moveTo(point.x,point.y-5);ctx.lineTo(point.x+5,point.y);ctx.lineTo(point.x,point.y+5);ctx.lineTo(point.x-5,point.y);ctx.closePath();ctx.stroke();}
  ctx.fillText(`${nodes.length} sampled runtime positions · Alt-click to inspect · includes occluded nodes`,12,78);ctx.restore();
}
function drawObservedCandidates(){
  const points=observedCandidatePoints();if(!points.length)return;
  ctx.save();ctx.strokeStyle='#cea9fa';ctx.fillStyle='#d7bcfa';ctx.lineWidth=1.5;ctx.font='11px "Segoe UI",sans-serif';
  for(const [index,world] of points.entries()){
    const p=project(world);if(!p||!numeric(p.x)||!numeric(p.y))continue;
    ctx.beginPath();ctx.arc(p.x,p.y,7,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.moveTo(p.x-10,p.y);ctx.lineTo(p.x+10,p.y);ctx.moveTo(p.x,p.y-10);ctx.lineTo(p.x,p.y+10);ctx.stroke();
    ctx.fillText(`Observed candidate${points.length>1?` ${index+1}/${points.length} · ambiguous`:''} · sampled`,p.x+13,p.y+13);
  }
  ctx.restore();
}
function drawEnvironmentSelection(){
  const item=selectedEnvironment();
  if(!item||!sceneModelsReady()||hiddenSceneEntities().has(item.entity_id))return;
  if(environmentGroupSelection.length>1){ctx.save();ctx.setLineDash([5,3]);for(const id of environmentGroupSelection){const bounds=previewBounds(id);if(hiddenSceneEntities().has(id)||bounds.length!==8)continue;for(let corner=0;corner<8;corner++)for(const bit of [1,2,4])if(!(corner&bit))line(bounds[corner],bounds[corner|bit],'#68f0ac',1.5);}ctx.restore();}
  const corners=previewBounds(item.entity_id);
  if(corners.length!==8)return;
  ctx.save();
  // A dashed bounds overlay identifies the selection without implying that
  // occluded edges are visible surfaces or that this is editable collision.
  ctx.setLineDash([5,3]);
  for(let corner=0;corner<8;corner++)for(const bit of [1,2,4]){
    if(!(corner&bit))line(corners[corner],corners[corner|bit],'#f4ce83',1.5);
  }
  ctx.setLineDash([]);
  const center=corners.reduce((p,c)=>({x:p.x+c.x/8,y:p.y+c.y/8,z:p.z+c.z/8}),{x:0,y:0,z:0});
  const label=project(center);
  if(label){ctx.font='11px "Segoe UI",sans-serif';ctx.fillStyle='#f4ce83';ctx.fillText(item.name,label.x+10,label.y-12);}
  ctx.restore();
}
function scenePlacementBoxCurrent(gesture){return !busy&&scenePlacementMode&&scenePlacementBoxMode&&canEdit()&&scenePreviewCurrent()&&sceneModelsReady()&&sceneRepresentation==='authored'&&!scenePose&&!shapeDraft&&!actorGroupInspection&&!environmentGroupInspection&&!scenePlacementInspection&&!wallSelectMode&&!wallInspection&&!pickScriptTargets&&!pickRuntimeNodes&&gesture.sourceKey===state.project_copy_source_key&&gesture.context===resourceStateKey()&&gesture.cameraRevision===cameraRevision&&gesture.width===width&&gesture.height===height;}
function draw(){
  updateNpcCreationInspection();
  updateGroundPositionInspection();
  sceneRuler?.update();
  sceneCameraInspector?.update();
  if(drag?.type==='environment-yaw'&&!transformGestureCurrent(drag)){cancelViewportGesture();return;}
  if(drag?.type==='scene-placement-box'&&!scenePlacementBoxCurrent(drag)){cancelViewportGesture();return;}
  if(drag?.type==='scene-placement-group-transform'&&!transformGestureCurrent(drag)){cancelViewportGesture();return;}
  updateScenePlacementSelection();
  if(scenePlacementInspection&&(!scenePreviewCurrent()||scenePlacementInspection.report.project_source_key!==state.project_copy_source_key||!canEdit()||sceneRepresentation!=='authored'||scenePose||shapeDraft||actorGroupInspection||environmentGroupInspection||wallInspection))scenePlacementTool.restore();
  updateFieldToggle();updateFieldSpatialTools();
  floorRectangleTool?.refresh();floorHeightTool?.refresh();
  if(wallRectangleTool){wallRectangleTool.refresh();if(wallInspection&&(!wallSourceCurrent()||wallInspection.report.project_source_key!==state.project_copy_source_key))wallRectangleTool.restore();if(wallSelectMode&&!wallSourceCurrent()){wallSelectMode=false;wallSelection=null;}if(drag?.type==='wall-rectangle'&&!wallGestureCurrent(drag)){cancelViewportGesture();return;}}
  updateEnvironmentGroupSelection();
  if(environmentGroupInspection&&(!scenePreviewCurrent()||environmentGroupInspection.report.project_source_key!==state.project_copy_source_key||sceneRepresentation!=='authored'||scenePose||shapeDraft||actorGroupInspection)){environmentGroupTool.restore();environmentLayoutTool?.restore();environmentRotationGroupTool?.restore();}
  updateActorGroupSelection();
  if(actorGroupInspection&&(!scenePreviewCurrent()||actorGroupInspection.key!==resourceStateKey()||sceneRepresentation!=='authored'||scenePose||shapeDraft))actorBatchTool.restore();
  if(scenePose&&(!scenePreviewCurrent()||scenePose.key!==sceneKey||state.project?.mode!=='edit'||(scenePose.isCurrent&&!scenePose.isCurrent())))clearScenePose();
  if(!ctx)return;ctx.clearRect(0,0,width,height);projected=[];handles=[];
  if(sceneModelsReady()){try{sceneRenderer.draw(sceneView());}catch(error){sceneError=error.message;}}
  updateSceneBadge();frameSamplesButton.disabled=observedCandidatePoints().length===0;
  const runtimeEpoch=acceptedEpoch(state.runtime),runtimeCorrelation=state.runtime_correlation;
  pickRuntimeButton.disabled=state.project?.mode!=='live'||!runtimeEpoch||runtimeCorrelation?.available!==true||runtimeCorrelation.epoch_id!==runtimeEpoch;
  if(pickRuntimeButton.disabled&&pickRuntimeNodes){pickRuntimeNodes=false;pickRuntimeButton.setAttribute('aria-pressed','false');}

  if(grid&&!sceneModelsReady()){const spacing=10**Math.floor(Math.log10(camera.distance/7)),half=spacing*12,cx=Math.round(camera.target.x/spacing)*spacing,cz=Math.round(camera.target.z/spacing)*spacing;for(let i=-12;i<=12;i++){line({x:cx+i*spacing,y:0,z:cz-half},{x:cx+i*spacing,y:0,z:cz+half},i===0?'#39504f88':'#33474c66');line({x:cx-half,y:0,z:cz+i*spacing},{x:cx+half,y:0,z:cz+i*spacing},i===0?'#39504f88':'#33474c66');}}
  drawFieldMap();if(fieldSpatialVisible&&fieldSpatialCurrent())drawFieldSpatial(ctx,fieldSpatialRows(),project,width,height,sceneResourceSelection,triggerGroupInspection?.key===resourceStateKey()?triggerGroupInspection.report.trigger_ids:[]);drawWallSelection();
  const items=entities().map(entity=>{const world=sceneView().positions.get(entity.id)??position(entity);return {entity,world,p:project(world)};}).filter(item=>item.p).sort((a,b)=>b.p.depth-a.p.depth);
  for(const {entity,world,p} of items){
    if(!sceneLayers.actors||hiddenSceneEntities().has(entity.id))continue;
    const active=!selectedSceneResource()&&!selectedEnvironment()&&!selectedNpcDraft()&&entity.id===state.selection?.entity_id,rendered=sceneModelsReady()&&sceneRenderer.hasEntity(entity.id),radius=active?7:4.5;
    const grouped=scenePlacementSelection.includes(entity.id)||!actorGroupInspection&&actorGroupSelection.includes(entity.id);if(rendered&&!active&&!grouped)continue;
    projected.push({id:entity.id,x:p.x,y:p.y});ctx.beginPath();ctx.ellipse(p.x,p.y+5,active?12:7,active?4:2.5,0,0,Math.PI*2);ctx.fillStyle='#02090966';ctx.fill();
    ctx.beginPath();ctx.moveTo(p.x,p.y-radius);ctx.lineTo(p.x+radius,p.y);ctx.lineTo(p.x,p.y+radius);ctx.lineTo(p.x-radius,p.y);ctx.closePath();ctx.fillStyle=active?'#c9edce':sceneRepresentation==='authored'&&authored(entity)?'#d2ae70':'#759d8d';ctx.fill();ctx.strokeStyle=active?'#f1fff0':'#a8c6b6';ctx.lineWidth=active?1.5:1;ctx.stroke();
    if(grouped){ctx.strokeStyle='#8bd7e8';ctx.lineWidth=2;ctx.strokeRect(p.x-8,p.y-8,16,16);}
    if(active){
      ctx.font='11px "Segoe UI", sans-serif';ctx.fillStyle='#c8ddd1';ctx.fillText(entity.name ?? entity.id,p.x+12,p.y-10);
      if(sceneRepresentation==='authored'&&(Object.keys(entity.components?.Transform?.authored?.position??{}).length||draft?.id===entity.id)){
        const original=displayPosition(entity.components?.Transform?.imported?.position),q=project(original);
        if(q&&Math.hypot(q.x-p.x,q.y-p.y)>3){ctx.save();ctx.setLineDash([4,4]);line(original,world,'#d6ad6c',1.5);ctx.setLineDash([]);ctx.strokeStyle='#d6ad6c';ctx.strokeRect(q.x-4,q.y-4,8,8);ctx.fillStyle='#e7c188';ctx.fillText('Imported',q.x+8,q.y+14);ctx.restore();}
      }
      if(!currentNpcCreationInspection()&&!currentGroundPositionInspection()&&canEdit()&&sceneRepresentation==='authored'&&!scenePlacementMode&&!scenePlacementInspection&&!actorGroupInspection&&!actorGroupSelection.length){const length=camera.distance*.085;for(const [axis,color] of [['x','#e0988a'],['z','#8bbbdc']]){const end={...world,[axis]:world[axis]+length},q=project(end);if(!q)continue;line(world,end,color,2);ctx.fillStyle=color;ctx.beginPath();ctx.arc(q.x,q.y,4,0,Math.PI*2);ctx.fill();ctx.font='bold 10px "Segoe UI",sans-serif';ctx.fillText(axis.toUpperCase(),q.x+7,q.y+3);handles.push({axis,x:q.x,y:q.y,start:p});}}
    }
  }
  if(sceneModelsReady()&&scenePlacementSelection.length){ctx.save();ctx.setLineDash([5,3]);for(const id of scenePlacementSelection){if(hiddenSceneEntities().has(id))continue;const actor=entities().some(e=>e.id===id);if(actor?!sceneLayers.actors:!sceneLayers.scenery)continue;const corners=previewBounds(id);if(corners.length!==8)continue;for(let corner=0;corner<8;corner++)for(const bit of [1,2,4])if(!(corner&bit))line(corners[corner],corners[corner|bit],'#8bd7e8',1.5);}ctx.restore();}
  drawEnvironmentSelection();drawCoordinateProbe();drawScriptTargets();drawArrivalComparison();drawNpcArrivalComparison();
  if(actorGroupInspection){
    for(const id of actorGroupInspection.positions.keys()){
      const proposed=groupProposalPosition(id);
      if(hiddenSceneEntities().has(id)||!sceneLayers.actors)continue;
      const original=activeScenePreview()?.entities.find(item=>item.entity_id===id)?.display_position;
      if(!original)continue;ctx.save();ctx.setLineDash([4,4]);line(original,proposed,'#e1bb76',1.5);ctx.setLineDash([]);
      const p=project(actorGroupInspection.layer==='proposed'?proposed:original);if(p){ctx.strokeStyle='#e1bb76';ctx.strokeRect(p.x-7,p.y-7,14,14);ctx.font='11px "Segoe UI",sans-serif';ctx.fillStyle='#e1bb76';ctx.fillText(`${id.split('/').at(-1)} · ${actorGroupInspection.layer}`,p.x+12,p.y+13);}ctx.restore();
    }
  }
  const groupCenter=groupProposalCenter();
  if(groupCenter&&canEdit()&&!busy){
    const start=project(groupCenter),length=camera.distance*.085;
    if(start)for(const [axis,color] of [['x','#e0988a'],['z','#8bbbdc']]){
      const end={...groupCenter,[axis]:groupCenter[axis]+length},q=project(end);if(!q)continue;line(groupCenter,end,color,3);ctx.fillStyle=color;ctx.beginPath();ctx.arc(q.x,q.y,6,0,Math.PI*2);ctx.fill();ctx.font='bold 11px "Segoe UI",sans-serif';ctx.fillText(`Group ${axis.toUpperCase()}`,q.x+9,q.y+4);handles.push({group:true,axis,x:q.x,y:q.y,start});
    }
  }
  const sceneryCenter=sceneryGroupCenter();
  if(sceneryCenter&&canEdit()&&!busy){
    const start=project(sceneryCenter),length=camera.distance*.085;
    if(start)for(const [axis,color] of [['x','#e0988a'],['z','#8bbbdc']]){
      const end={...sceneryCenter,[axis]:sceneryCenter[axis]+length},q=project(end);if(!q)continue;line(sceneryCenter,end,color,3);ctx.fillStyle=color;ctx.beginPath();ctx.arc(q.x,q.y,6,0,Math.PI*2);ctx.fill();ctx.font='bold 11px "Segoe UI",sans-serif';ctx.fillText(`Scenery ${axis.toUpperCase()}`,q.x+9,q.y+4);handles.push({sceneryGroup:true,axis,x:q.x,y:q.y,start});
    }
  }
  const placementCenter=scenePlacementCenter();
  if(placementCenter&&canEdit()&&!busy&&!scenePlacementInspection?.report?.operation){
    const start=project(placementCenter),length=camera.distance*.085;
    if(start)for(const [axis,color] of [['x','#e0988a'],['z','#8bbbdc']]){
      const end={...placementCenter,[axis]:placementCenter[axis]+length},q=project(end);if(!q)continue;line(placementCenter,end,color,3);ctx.fillStyle=color;ctx.beginPath();ctx.arc(q.x,q.y,6,0,Math.PI*2);ctx.fill();ctx.font='bold 11px "Segoe UI",sans-serif';ctx.fillText(`Placements ${axis.toUpperCase()}`,q.x+9,q.y+4);handles.push({scenePlacementGroup:true,axis,x:q.x,y:q.y,start});
    }
  }
  const scenery=selectedEnvironment(),movable=movableSelection();
  if(((scenery&&sceneryTool.value==='move')||selectedNpcDraft())&&movable&&canEdit()){
    const world=draft?.id===movable.id?draft.position:position(movable),p=project(world),length=camera.distance*.085;
    if(p)for(const [axis,color] of [['x','#e0988a'],['z','#8bbbdc']]){
      const end={...world,[axis]:world[axis]+length},q=project(end);if(!q)continue;
      line(world,end,color,2);ctx.fillStyle=color;ctx.beginPath();ctx.arc(q.x,q.y,4,0,Math.PI*2);ctx.fill();
      ctx.font='bold 10px "Segoe UI",sans-serif';ctx.fillText(axis.toUpperCase(),q.x+7,q.y+3);handles.push({axis,x:q.x,y:q.y,start:p});
    }
  }
  const rotating=rotationSelection();
  if(rotating){
    const pivot=rotating.display_position,radius=camera.distance*.085,points=[];ctx.save();ctx.strokeStyle='#8bd6a1';ctx.lineWidth=2;ctx.beginPath();
    for(let i=0;i<=64;i++){const a=i*Math.PI/32,q=project({x:pivot.x+Math.sin(a)*radius,y:pivot.y,z:pivot.z+Math.cos(a)*radius});if(!q){points.push(null);continue;}points.push(q);if(i===0||!points[i-1])ctx.moveTo(q.x,q.y);else ctx.lineTo(q.x,q.y);if(i<64)handles.push({sceneryYaw:true,axis:'y',x:q.x,y:q.y,start:project(pivot)});}ctx.stroke();
    const yaw=draft?.sceneryYaw?draft.yaw:rotating.effective_transform?.rotation_psx.y??rotating.source_record.imported_transform.rotation_psx.y,a=yaw*Math.PI*2/4096,tip={x:pivot.x+Math.sin(a)*radius,y:pivot.y,z:pivot.z+Math.cos(a)*radius};line(pivot,tip,'#f4ce83',2);const q=project(tip);if(q){ctx.fillStyle='#f4ce83';ctx.font='bold 11px "Segoe UI",sans-serif';ctx.fillText(`Yaw ${yaw} · ${rotating.entity_id.includes('/decorations/')?'individual':'shared'}`,q.x+8,q.y-8);}ctx.restore();
  }
  drawRuntimeNodeLayer();drawObservedCandidates();drawHistoricalPositions();
  if(['actor-box','scene-placement-box'].includes(drag?.type)&&drag.moved){ctx.save();ctx.fillStyle='#8bd7e820';ctx.strokeStyle='#8bd7e8';ctx.lineWidth=1.5;ctx.setLineDash([4,3]);ctx.fillRect(drag.start.x,drag.start.y,drag.last.x-drag.start.x,drag.last.y-drag.start.y);ctx.strokeRect(drag.start.x,drag.start.y,drag.last.x-drag.start.x,drag.last.y-drag.start.y);ctx.restore();}
  sceneRuler?.draw(ctx,project);
}
function resize(){const rect=canvas.getBoundingClientRect(),dpr=window.devicePixelRatio||1;width=rect.width;height=rect.height;canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);draw();}
new ResizeObserver(resize).observe(canvas);
function pointer(event){const r=canvas.getBoundingClientRect();return {x:event.clientX-r.left,y:event.clientY-r.top};}
canvas.addEventListener('contextmenu',event=>event.preventDefault());
function cancelViewportGesture(){
  if(!drag)return;
  const pointerId=drag.pointerId;drag=null;draft=null;canvas.classList.remove('dragging');
  if(canvas.hasPointerCapture(pointerId))canvas.releasePointerCapture(pointerId);
  wallSelection=null;$('transform-drag-status').textContent='Move cancelled';draw();
}
function transformGestureCurrent(gesture){
  if(gesture.type==='environment-yaw'){const rect=canvas.getBoundingClientRect();return !!rotationSelection()&&selectedEnvironment()?.entity_id===gesture.entity&&gesture.context===resourceStateKey()&&gesture.sourceKey===state.project_copy_source_key&&gesture.cameraRevision===cameraRevision&&gesture.width===width&&gesture.height===height&&gesture.rotationItem===selectedEnvironment()&&gesture.rotationBinding===activeScenePreview()?.environment_authoring&&gesture.yawSnap===(yawSnap.checked?Number(yawStep.value):1)&&gesture.width===rect.width&&gesture.height===rect.height;}
  if(gesture.type==='scene-placement-group-transform'){
    const center=scenePlacementCenter(false);
    return canEdit()&&scenePreviewCurrent()&&sceneModelsReady()&&sceneRepresentation==='authored'&&gesture.width===width&&gesture.height===height&&gesture.cameraRevision===cameraRevision&&scenePlacementInspection?.layer==='proposed'&&scenePlacementInspection.report===gesture.proposal&&gesture.sourceKey===state.project_copy_source_key&&gesture.context===resourceStateKey()&&center&&['x','y','z'].every(axis=>center[axis]===gesture.original[axis]);
  }
  if(gesture.type==='environment-group-transform'){
    const center=sceneryGroupCenter(false);
    return canEdit()&&sceneRepresentation==='authored'&&gesture.cameraRevision===cameraRevision&&environmentGroupInspection?.report===gesture.proposal&&gesture.sourceKey===state.project_copy_source_key&&gesture.context===resourceStateKey()&&center&&['x','y','z'].every(axis=>center[axis]===gesture.original[axis]);
  }
  if(gesture.type==='group-transform'){
    const center=groupProposalCenter(false);
    return canEdit()&&actorGroupInspection?.proposal===gesture.proposal&&gesture.context===resourceStateKey()&&center&&['x','y','z'].every(axis=>center[axis]===gesture.original[axis]);
  }
  const entity=movableSelection();
  return canEdit()&&entity?.id===gesture.entity&&gesture.context===resourceStateKey()&&
    ['x','y','z'].every(axis=>position(entity)[axis]===gesture.original[axis]);
}
window.addEventListener('blur',cancelViewportGesture);
window.addEventListener('resize',cancelViewportGesture);
document.addEventListener('visibilitychange',()=>{if(document.hidden)cancelViewportGesture();});
canvas.addEventListener('pointerdown',event=>{
  pendingEntityFrame=null;
  if(busy||drag)return;const p=pointer(event),entity=movableSelection();canvas.focus({preventScroll:true});canvas.setPointerCapture(event.pointerId);
  if(npcGroundPlacement.active()&&event.button===0&&!event.shiftKey){drag={pointerId:event.pointerId,type:'npc-create-position',key:npcGroundPlacement.key(),cameraRevision,width,height,start:p,last:p,moved:false};canvas.classList.add('dragging');return;}
  if(sceneRuler?.picking()&&event.button===0){drag={pointerId:event.pointerId,type:'scene-ruler',rulerContext:sceneRuler.contextKey(),cameraRevision,width,height,start:p,last:p,moved:false};canvas.classList.add('dragging');return;}
  if(pickHistoricalSamples&&currentHistoricalPositions()&&event.button===0){drag={pointerId:event.pointerId,type:'historical-sample',key:historicalPositionKey(),cameraRevision,width,height,start:p,last:p,moved:false};canvas.classList.add('dragging');return;}
  if(floorPickMode&&event.button===0){drag={pointerId:event.pointerId,type:'floor-selector',context:resourceStateKey(),sourceKey:state.scene_preview_source_key,projectKey:state.project_copy_source_key,cameraRevision,width,height,start:p,last:p,moved:false};canvas.classList.add('dragging');return;}
  if(sceneFacePickMode&&event.button===0){drag={pointerId:event.pointerId,type:'scene-face',context:resourceStateKey(),sourceKey:state.scene_preview_source_key,cameraRevision,width,height,start:p,last:p,moved:false};canvas.classList.add('dragging');return;}
  if(wallSelectMode&&event.button===0){const cell=wallCellAt(groundAt(p.x,p.y,0));if(!wallSourceCurrent()||wallInspection||!cell){canvas.releasePointerCapture(event.pointerId);notify('Point is outside the canonical source-wall reference plane.',true);return;}drag={pointerId:event.pointerId,type:'wall-rectangle',context:resourceStateKey(),sourceKey:state.project_copy_source_key,cameraRevision,width,height,wallStart:cell,start:p,last:p,moved:false};wallSelection=wallDragRectangle(cell,cell);canvas.classList.add('dragging');draw();return;}
  const placementBox=scenePlacementBoxMode&&!scenePlacementHost.querySelector('[data-mixed-box]').disabled&&event.button===0&&!event.shiftKey&&!event.altKey;
  const box=placementBox||actorBoxMode&&!actorBoxButton.disabled&&event.button===0&&!event.shiftKey&&!event.altKey;
  const handle=!box && event.button===0 && !event.ctrlKey && !event.metaKey && !pickScriptTargets && !fieldSpatialPick && (entity||groupProposalCenter()||sceneryGroupCenter()||scenePlacementCenter()) && canEdit()?handles.find(h=>Math.hypot(h.x-p.x,h.y-p.y)<12):null;
  drag={pointerId:event.pointerId,context:resourceStateKey(),start:p,last:p,moved:false,extendSelection:event.ctrlKey||event.metaKey,cameraRevision,representation:sceneRepresentation,type:box?(placementBox?'scene-placement-box':'actor-box'):handle?(handle.sceneryYaw?'environment-yaw':handle.scenePlacementGroup?'scene-placement-group-transform':handle.sceneryGroup?'environment-group-transform':handle.group?'group-transform':'transform'):event.button===2||event.button===1||event.shiftKey?'pan':'orbit',handle,entity:entity?.id,original:handle?.scenePlacementGroup?scenePlacementCenter(false):handle?.sceneryGroup?sceneryGroupCenter(false):handle?.group?groupProposalCenter(false):entity?position(entity):null,proposal:handle?.scenePlacementGroup?scenePlacementInspection.report:handle?.sceneryGroup?environmentGroupInspection.report:handle?.group?actorGroupInspection.proposal:null,sourceKey:state.project_copy_source_key,width,height,snapStep:handle?.scenePlacementGroup||handle?.group?64:$('transform-snap').checked?Number($('transform-snap-step').value):1};
  if(handle?.sceneryYaw){drag.rotationItem=selectedEnvironment();drag.rotationBinding=activeScenePreview().environment_authoring;drag.rotationShared=!drag.rotationItem.entity_id.includes('/decorations/');drag.originalYaw=drag.rotationItem.effective_transform?.rotation_psx.y??drag.rotationItem.source_record.imported_transform.rotation_psx.y;drag.yawSnap=yawSnap.checked?Number(yawStep.value):1;}
  if(handle)drag.ground=groundAt(p.x,p.y,drag.original.y);
  if(handle&&state.actor_drafts?.[entity?.id])drag.snapStep=64;
  canvas.classList.add('dragging');
});
canvas.addEventListener('pointermove',event=>{
  if(!drag||event.pointerId!==drag.pointerId)return;const p=pointer(event),dx=p.x-drag.last.x,dy=p.y-drag.last.y;
  if(Math.hypot(p.x-drag.start.x,p.y-drag.start.y)>3)drag.moved=true;
  if(drag.moved){
    if(drag.type==='environment-yaw'){if(!transformGestureCurrent(drag)){cancelViewportGesture();return;}const point=groundAt(p.x,p.y,drag.original.y);try{if(!point||!drag.ground)throw new Error('Yaw requires a stable X/Z plane.');const yaw=yawFromDrag(drag.ground,point,drag.original,drag.originalYaw,drag.yawSnap);draft={id:drag.entity,sceneryYaw:true,yaw,position:drag.original};$('transform-drag-status').textContent=`${drag.rotationShared?'Shared':'Individual'} yaw ${yaw} (${format(yaw*360/4096)}°) · ${drag.yawSnap>1?'Snap '+drag.yawSnap+' angle units':'Integer angle'} · Release to apply`;}catch(error){draft=null;$('transform-drag-status').textContent=error.message;}}
    else if(['transform','group-transform','environment-group-transform','scene-placement-group-transform'].includes(drag.type)){if(!transformGestureCurrent(drag)){cancelViewportGesture();return;}const point=groundAt(p.x,p.y,drag.original.y);if(point&&drag.ground){const axis=drag.handle.axis,group=['group-transform','environment-group-transform','scene-placement-group-transform'].includes(drag.type),amount=snappedTransformCoordinate(point[axis]-drag.ground[axis],drag.snapStep);draft={id:drag.entity,group,sceneryGroup:drag.type==='environment-group-transform',scenePlacementGroup:drag.type==='scene-placement-group-transform',groupAmount:amount,position:{...drag.original,[axis]:group?drag.original[axis]+amount:snappedTransformCoordinate(drag.original[axis]+point[axis]-drag.ground[axis],drag.snapStep)}};}}
    else if(drag.type==='wall-rectangle'){if(!wallGestureCurrent(drag)){cancelViewportGesture();return;}try{wallSelection=wallRectangleAt(drag,p);$('transform-drag-status').textContent=`Source wall rows ${wallSelection.row_start}–${wallSelection.row_end}, columns ${wallSelection.column_start}–${wallSelection.column_end} · Y=0 reference plane · Release to review`;}catch(error){wallSelection=null;$('transform-drag-status').textContent=error.message;}}
    else if(drag.type==='scene-placement-box'){if(!scenePlacementBoxCurrent(drag)){cancelViewportGesture();return;}drag.last=p;$('transform-drag-status').textContent='Visible placement pixels · Release to select; Ctrl/Command adds';}
    else if(drag.type==='actor-box'){drag.last=p;}
    else if(drag.type==='orbit'||drag.type==='scene-ruler'||drag.type==='scene-face'||drag.type==='floor-selector'||drag.type==='npc-create-position'){camera.yaw-=dx*.006;camera.pitch=Math.max(camera.projection==='orthographic'?0:.12,Math.min(Math.PI/2,camera.pitch+dy*.005));cameraRevision++;}
    else if(camera.projection==='orthographic'){const a=sceneCameraPlanePoint(camera,{width,height},0,0),b=sceneCameraPlanePoint(camera,{width,height},dx,dy);for(const axis of ['x','y','z'])camera.target[axis]+=a[axis]-b[axis];cameraRevision++;}
    else {const b=basis(),scale=camera.distance/Math.max(1,Math.min(width,height)*.9);camera.target.x-=dx*scale*b.right.x;camera.target.z-=dx*scale*b.right.z;camera.target.x-=dy*scale*Math.sin(camera.yaw)/Math.max(.15,Math.sin(camera.pitch));camera.target.z-=dy*scale*Math.cos(camera.yaw)/Math.max(.15,Math.sin(camera.pitch));cameraRevision++;}
    if(draft&&['transform','group-transform','environment-group-transform','scene-placement-group-transform'].includes(drag.type))$('transform-drag-status').textContent=['group-transform','environment-group-transform','scene-placement-group-transform'].includes(drag.type)?`${drag.type==='scene-placement-group-transform'?'Placement':drag.type==='environment-group-transform'?'Scenery':'Actor'} group ${drag.handle.axis.toUpperCase()} offset ${format(draft.groupAmount)} · ${drag.snapStep>1?`Snap ${drag.snapStep}`:'Integer move'} · Release to review; preview height held while dragging`:`${drag.handle.axis.toUpperCase()} ${format(draft.position[drag.handle.axis])} · ${drag.snapStep>1?`Snap ${drag.snapStep} units`:'Free move'} · Release to apply`;
    draw();
  }
  drag.last=p;
});
canvas.addEventListener('pointerup',async event=>{
  if(!drag||event.pointerId!==drag.pointerId)return;
  if(['environment-yaw','transform','group-transform','environment-group-transform','scene-placement-group-transform'].includes(drag.type)&&(busy||!transformGestureCurrent(drag))){cancelViewportGesture();return;}
  const finished=drag,p=pointer(event),edit=draft;drag=null;draft=null;canvas.classList.remove('dragging');$('transform-drag-status').textContent='X/Z moves · snap aligns to scene origin';
  if(finished.type==='historical-sample'){if(!finished.moved&&event.button===0&&!busy&&currentHistoricalPositions()&&finished.key===historicalPositionKey()&&finished.cameraRevision===cameraRevision&&finished.width===width&&finished.height===height){const ids=historicalSampleHits(historicalHits,p);if(ids.length===1){historicalSample.value=ids[0];openHistoricalSample(ids[0]);}else if(ids.length>1){notify('Several historical keys overlap here. Choose a node in Historical node sample.');historicalSample.focus();}else notify('No historical sample at this point.');}draw();return;}
  if(finished.type==='npc-create-position'){if(!finished.moved&&event.button===0&&finished.cameraRevision===cameraRevision&&finished.width===width&&finished.height===height)npcGroundPlacement.pick(p,finished.key);draw();return;}
  if(finished.type==='floor-selector'){floorPickMode=false;updateFieldToggle();if(!finished.moved&&event.button===0){try{pickFloorSelector(p,finished);}catch(error){notify(error.message,true);}}draw();return;}
  if(finished.type==='scene-ruler'){if(!finished.moved&&event.button===0&&finished.cameraRevision===cameraRevision&&finished.width===width&&finished.height===height&&canMeasureScene()){try{sceneRuler.pick(p,finished.rulerContext);}catch(error){notify(error.message,true);}}draw();return;}
  if(finished.type==='scene-face'){sceneFacePickMode=false;updateSceneFacePick();if(!finished.moved&&event.button===0){try{await inspectSceneFace(p,finished);}catch(error){notify(error.message,true);}}draw();return;}
  if(finished.type==='wall-rectangle'){wallSelection=null;wallSelectMode=false;updateFieldToggle();if(wallGestureCurrent(finished)){try{wallRectangleTool.open(wallRectangleAt(finished,p));}catch(error){notify(error.message,true);}}draw();return;}
  if(finished.type==='scene-placement-box'){
    if(finished.moved&&scenePlacementBoxCurrent(finished)){
      try{const eligible=scenePlacementEligible(),hits=sceneRenderer.pickRegion(finished.start,p,sceneView()).filter(id=>eligible.has(id)),next=mergeScenePlacementSelection(scenePlacementSelection,hits,eligible,!!finished.extendSelection);
        scenePlacementSelection=next;scenePlacementKey=resourceStateKey();const focus=next.includes(environmentSelection)?environmentSelection:next.includes(state.selection?.entity_id)?state.selection.entity_id:next[0];
        if(focus&&entities().some(e=>e.id===focus)){environmentSelection=null;npcDraftSelection=null;await api('/api/selection',{entity_id:focus});}else if(focus){environmentSelection=focus;npcDraftSelection=null;renderInspector();}
        renderHierarchy();notify(`${hits.length} placements in box · ${next.length} selected · visible mesh pixels`);
      }catch(error){notify(error.message,true);}
    }
  }
  else if(finished.type==='actor-box'){
    if(finished.moved&&!busy&&canEdit()&&!actorGroupInspection&&finished.context===resourceStateKey()&&finished.cameraRevision===cameraRevision&&finished.representation===sceneRepresentation&&scenePreviewCurrent()){
      try{const eligible=new Set(entities().map(e=>e.id)),hidden=hiddenSceneEntities(),hits=sceneModelsReady()?sceneRenderer.pickRegion(finished.start,p,sceneView()).filter(id=>eligible.has(id)):[...projected].filter(item=>eligible.has(item.id)&&!hidden.has(item.id)&&item.x>=Math.min(finished.start.x,p.x)&&item.x<=Math.max(finished.start.x,p.x)&&item.y>=Math.min(finished.start.y,p.y)&&item.y<=Math.max(finished.start.y,p.y)).map(item=>item.id);setActorGroupMembers(hits,finished.extendSelection);notify(`${hits.length} actor${hits.length===1?'':'s'} in box · ${sceneModelsReady()?'visible mesh pixels':'placement markers; occlusion unknown'}`);}
      catch(error){notify(error.message,true);}
    }
  }
  else if(finished.type==='scene-placement-group-transform'&&edit){draw();await scenePlacementTool.moveProposal(finished.handle.axis,edit.groupAmount,finished.proposal.review_key);}
  else if(finished.type==='environment-group-transform'&&edit){draw();await environmentGroupTool.moveProposal(finished.handle.axis,edit.groupAmount,finished.proposal.review_key);}
  else if(finished.type==='group-transform'&&edit){const axis=finished.handle.axis;await actorBatchTool.moveProposal(axis,edit.groupAmount,finished.proposal.review_key);}
  else if(finished.type==='environment-yaw'&&edit){draw();if(edit.yaw!==finished.originalYaw){try{await api('/api/command',environmentRotationCommand(state.scene.id,finished.rotationItem,finished.rotationBinding,edit.yaw,finished.rotationShared));}catch(error){notify(error.message,true);}}}
  else if(finished.type==='transform' && edit){const axis=finished.handle.axis;if(edit.position[axis]!==finished.original[axis]){if(state.actor_drafts?.[finished.entity])await api('/api/command',{type:'set_actor_draft_position',entity_id:finished.entity,position:{...state.actor_drafts[finished.entity].position,[axis]:edit.position[axis]}});else if(finished.entity.startsWith('environment://'))await moveDecoration(finished.entity,axis,edit.position[axis]);else await api('/api/command',{type:'set_transform',entity_id:finished.entity,position:{[axis]:edit.position[axis]}});}}
  else if(!finished.moved && event.button===0){
    if(fieldSpatialPick&&fieldSpatialVisible&&fieldSpatialCurrent()&&finished.context===resourceStateKey()){
      const id=hitFieldSpatial(fieldSpatialRows(),project,p.x,p.y,sceneResourceSelection),record=assetRecords().find(row=>row.id===id);
      if(record)selectSceneResource(record);else notify('No source cell at this point.');draw();return;
    }
    if(pickScriptTargets&&currentScriptTargets()&&finished.context===resourceStateKey()){
      const hits=scriptTargetHits.filter(hit=>Math.hypot(hit.x-p.x,hit.y-p.y)<10||(hit.label&&p.x>=hit.label.x&&p.x<=hit.label.x+hit.label.w&&p.y>=hit.label.y&&p.y<=hit.label.y+hit.label.h));
      if(hits.length===1){scriptTargetTools.querySelector('select').value=hits[0].pc;await inspectScriptTarget(hits[0].pc);}
      else if(hits.length>1){notify('Several script targets overlap here. Choose an instruction in the target selector.');scriptTargetTools.querySelector('select').focus();}
      else notify('No script target at this point');
      draw();return;
    }
    if((event.altKey||pickRuntimeNodes)&&showObservedNodes&&state.project?.mode==='live'){
      const epoch=acceptedEpoch(state.runtime),correlation=state.runtime_correlation;
      if(epoch&&correlation?.available===true&&correlation.epoch_id===epoch){
        const hits=runtimeNodeHits.filter(hit=>hit.epoch===epoch&&Math.hypot(hit.x-p.x,hit.y-p.y)<9);
        if(hits.length){renderObservedNodes('',hits.map(hit=>hit.id));draw();return;}
        if(pickRuntimeNodes){notify('No sampled runtime node at this point');draw();return;}
      }
    }

    // Resolve the frontmost visible mesh before overlay markers. Otherwise a
    // projected actor behind scenery steals a click on the scenery surface.
    let hit=null;
    if(sceneModelsReady()){try{hit=sceneRenderer.pick(p.x,p.y,sceneView());}catch(error){notify(error.message,true);}}
    if(hit&&currentNpcCreationInspection()?.report.review.preview_entity_id===hit){frame({id:hit});return;}
    if(!hit)hit=[...projected].reverse().find(item=>Math.hypot(item.x-p.x,item.y-p.y)<12)?.id;
    if(scenePlacementMode){if(hit)await toggleScenePlacement(hit);draw();return;}
    if(finished.extendSelection){if(hit){if(environmentEntities().some(e=>e.entity_id===hit))toggleEnvironmentSelection(hit);else toggleActorSelection(hit);}}
    else if(hit){if(state.actor_drafts?.[hit])selectNpcDraft(hit);else if(environmentEntities().some(e=>e.entity_id===hit))selectEnvironment(hit);else{environmentSelection=null;await api('/api/selection',{entity_id:hit});}}
    else if(environmentGroupSelection.length){clearEnvironmentGroupSelection();renderHierarchy();}else if(actorGroupSelection.length){clearActorGroupSelection();renderHierarchy();}
  }
  draw();
});
canvas.addEventListener('pointercancel',event=>{if(event.pointerId===drag?.pointerId)cancelViewportGesture();});
canvas.addEventListener('lostpointercapture',event=>{if(event.pointerId===drag?.pointerId)cancelViewportGesture();});
function zoomSceneAt(x,y,delta){
  const before=camera.projection==='orthographic'?sceneCameraPlanePoint(camera,{width,height},x,y):groundAt(x,y,camera.target.y);
  camera.distance=Math.max(20,Math.min(1e8,camera.distance*Math.exp(delta*.001)));
  const after=camera.projection==='orthographic'?sceneCameraPlanePoint(camera,{width,height},x,y):groundAt(x,y,camera.target.y);
  if(before&&after)for(const axis of ['x','y','z'])camera.target[axis]+=before[axis]-after[axis];
  cameraRevision++;
}
canvas.addEventListener('wheel',event=>{pendingEntityFrame=null;event.preventDefault();cancelViewportGesture();const p=pointer(event);zoomSceneAt(p.x,p.y,event.deltaY);draw();},{passive:false});

// Unposed assets stay object-local. Only decoder-provided frames assemble objects.
const modelCanvas=$('model-canvas');let modelRenderer=null,modelRenderSource=null,modelRenderObject=null,modelRenderFrame=null;
const exportDialog=document.createElement('dialog');document.body.append(exportDialog);
let model=null, modelDrag=null, modelRequest=0;
let modelTextures=new Map();
let modelAssetId=null, modelEntityId=null, modelSceneEntityId=null, animationFrame=0, animationTick=null, animationClock=null;
const modelView={yaw:.55,pitch:-.18,zoom:1,center:[0,0,0],radius:1};
let modelSceneContext=null,modelFileReturn=null,scenePoseTick=null,scenePoseClock=null;
const scenePoseBar=document.createElement('div');scenePoseBar.hidden=true;scenePoseBar.innerHTML='<span></span> <input type="range" min="0" value="0" aria-label="Scene pose frame"> <button type="button" data-play>Play scene preview</button> <label>Preview fps <select aria-label="Scene preview rate"><option>5</option><option selected>10</option><option>15</option><option>30</option><option>60</option></select></label> <button type="button" data-restore>Restore scene preview</button> <button type="button" data-return-file hidden>Return to animation file</button>';$('frame-selected').after(scenePoseBar);
const sceneInspectionLayer=document.createElement('label');sceneInspectionLayer.hidden=true;sceneInspectionLayer.innerHTML='Inspection layer <select aria-label="Scene inspection layer"><option value="proposed">Proposed · not applied</option><option value="current">Current authored scene</option></select>';scenePoseBar.querySelector('[data-restore]').before(sceneInspectionLayer);
sceneAnimationController=createSceneAnimationController({
  getContext:()=>({projectPath:state.project?.path,sceneId:state.scene?.id??null,mode:state.project?.mode,sourceKey:state.scene_preview_source_key,sceneSourceKey:scenePreview?.source_key??null,representation:sceneRepresentation,
    ready:!!(state.capabilities?.scene_animation_preview&&scenePreviewCurrent()&&sceneModelsReady()),
    canStart:!scenePose&&!shapeDraft&&!actorGroupInspection&&!scenePlacementInspection&&!environmentGroupInspection&&!document.querySelector('dialog[open]')}),
  busy:()=>busy,setBusy,onError:error=>notify(error.message??String(error),true),
  onNormalView:enabled=>{sceneNormalDiagnostic=enabled;draw();},
  onStatus:status=>{if(status.active!==sceneAnimationWriteGuard){sceneAnimationWriteGuard=status.active;renderInspector();updateSceneBadge();}},
  onLoad:async(report,{isCurrent,signal})=>{
    if(signal.aborted||!isCurrent()||!scenePreviewCurrent()||!sceneModelsReady()||scenePose||report.scene_source_key!==scenePreview.source_key||report.project_source_key!==state.scene_preview_source_key||report.representation!==sceneRepresentation)throw new Error('Scene animation no longer matches the loaded scene.');
    const byGeometry=new Map(scenePreview.assets.map(a=>[a.geometry_key,a])),byEntity=new Map(scenePreview.entities.map(e=>[e.entity_id,e]));
    for(const row of report.instances){const current=byEntity.get(row.entity_id);if(!current?.renderable||current.geometry_key!==row.geometry_key||current.asset_id!==row.asset_id||current.source_actor_id!==row.source_actor_id)throw new Error('Animation instance differs from the loaded source binding.');}
    for(const track of report.tracks){const current=byGeometry.get(track.geometry_key);if(current?.asset_id!==track.asset_id||JSON.stringify(current.preview.vertices)!==JSON.stringify(track.frames[0]))throw new Error('Animation baseline differs from the loaded source pose.');if(track.normal_pose){if(JSON.stringify(current.preview.triangles)!==JSON.stringify(track.normal_pose.source.triangles)||JSON.stringify((current.preview.normal_source??current.preview).triangle_normals)!==JSON.stringify(track.normal_pose.source.triangle_normals))throw new Error('Animation normals differ from the loaded source geometry.');}}
    cancelViewportGesture();scenePose={kind:'scene-animation',key:sceneKey,report};
    const failures=sceneRenderer.load(structuredClone(scenePreview));if(failures.length)throw new Error(failures.join('; '));
    draw();return true;
  },
  onSample:(samples,report)=>{
    if(scenePose?.kind!=='scene-animation'||scenePose.report!==report||scenePose.key!==sceneKey||!scenePreviewCurrent()||!sceneModelsReady()||report.project_source_key!==state.scene_preview_source_key||sceneRenderer.lost)return false;
    for(const row of samples){const mesh=sceneRenderer.meshes.get(row.geometry_key);if(!mesh||row.vertices.length!==mesh.vertexCount)return false;}
    for(const row of samples)if(!sceneRenderer.updateVertices(row.geometry_key,row.vertices,row.normal_preview))return false;
    draw();return true;
  },
  onRestore:report=>{
    if(scenePose?.kind!=='scene-animation'||scenePose.report!==report)return;
    scenePose=null;if(scenePreviewCurrent()&&sceneRenderer&&!sceneRenderer.lost){const failures=sceneRenderer.load(structuredClone(scenePreview));if(failures.length)sceneError=failures.join('; ');}
    renderInspector();draw();
  }
});
document.querySelector('.viewport-toolbar').after(sceneAnimationController.element);
document.addEventListener('beforetoggle',event=>{if(event.target instanceof HTMLDialogElement&&event.newState==='open'&&sceneAnimationController.active())sceneAnimationController.stop();},true);
document.addEventListener('close',event=>{if(event.target instanceof HTMLDialogElement)sceneAnimationController.updateState();},true);
const sceneInspectionIsolation=document.createElement('button');sceneInspectionIsolation.type='button';sceneInspectionIsolation.textContent='Isolate inspected instances';sceneInspectionIsolation.hidden=true;sceneInspectionIsolation.setAttribute('aria-pressed','false');sceneInspectionLayer.after(sceneInspectionIsolation);
sceneInspectionIsolation.onclick=()=>{if(busy||!scenePose?.inspectionEntityIds?.length||!scenePreviewCurrent()||scenePose.key!==sceneKey)return;scenePose.inspectionIsolated=!scenePose.inspectionIsolated;sceneInspectionIsolation.setAttribute('aria-pressed',String(scenePose.inspectionIsolated));draw();};
function configureSceneInspectionComparison(proposalDocument=null){
  sceneInspectionLayer.hidden=!proposalDocument;sceneInspectionLayer.querySelector('select').value='proposed';sceneInspectionIsolation.hidden=!proposalDocument||!scenePose?.inspectionEntityIds?.length;sceneInspectionIsolation.setAttribute('aria-pressed',String(!!scenePose?.inspectionIsolated));
  sceneInspectionLayer.querySelector('[value=current]').textContent=scenePose?.faceSelectionHighlight?'Current - face highlight (display only)':'Current authored scene';
  sceneInspectionLayer.querySelector('[value=proposed]').textContent=scenePose?.faceSelectionHighlight?'Proposed - face highlight (display only)':scenePose?.preview?.frames?'Inspected animation · not applied':'Proposed · not applied';
  for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('[aria-label="Scene preview rate"]')])control.disabled=false;
  if(scenePose){scenePose.inspectionLayer='proposed';scenePose.proposalDocument=proposalDocument?structuredClone(proposalDocument):null;scenePose.proposalLabel=scenePoseBar.querySelector('span').textContent;}
}
sceneInspectionLayer.querySelector('select').onchange=()=>{
  if(busy){sceneInspectionLayer.querySelector('select').value=scenePose?.inspectionLayer??'proposed';return;}
  if(!scenePose?.proposalDocument||!scenePreviewCurrent()||scenePose.key!==sceneKey||state.project.mode!=='edit'){clearScenePose();notify('Scene proposal is stale. Reopen the Inspector to preview it again.',true);draw();return;}
  try{
    stopScenePosePlayback();
    const current=sceneInspectionLayer.querySelector('select').value==='current',failures=sceneRenderer.load(structuredClone(current?(scenePose.currentDocument??scenePreview):scenePose.proposalDocument));
    if(failures.length)throw new Error(failures.join('; '));
    scenePose.inspectionLayer=current?'current':'proposed';
    const animated=!!scenePose.preview?.frames;if(animated)scenePoseBar.querySelector('input').value=scenePose.frame;
    for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('[aria-label="Scene preview rate"]')])control.disabled=current&&animated;
    scenePoseBar.querySelector('span').textContent=current?(scenePose.faceSelectionHighlight?'Current authored scene - GLB-selected faces highlighted yellow (display only)':animated?'Current authored scene · inspected animation retained, not applied':'Current authored scene · proposal retained, not applied'):scenePose.proposalLabel;
    draw();
  }catch(error){clearScenePose();notify(error.message,true);draw();}
};
const showScenePose=document.createElement('button');showScenePose.type='button';showScenePose.id='show-frame-in-scene';showScenePose.textContent='Inspect animation in scene';$('animation-frame-label').after(showScenePose);
function clearScenePose(restore=true,retainReview=false){
  if(scenePose?.kind==='scene-animation'&&sceneAnimationController?.active()){sceneAnimationController.stop();return;}
  stopScenePosePlayback();const previous=scenePose;scenePose=null;scenePoseBar.hidden=true;sceneInspectionLayer.hidden=true;sceneInspectionIsolation.hidden=true;
  if(!retainReview)previous?.onDiscard?.();
  if(restore&&previous&&scenePreviewCurrent()&&sceneRenderer){const failures=sceneRenderer.load(structuredClone(scenePreview));if(failures.length)sceneError=failures.join('; ');}
}
function scenePoseDocument(base,preview,entityId,frame){
  const target=base.entities.find(e=>e.entity_id===entityId);
  if(!target||!Array.isArray(frame===null?preview.vertices:preview.frames?.[frame]?.vertices))throw new Error('Choose a loaded inspection geometry.');
  const key='inspection-pose:'+entityId,geometry={...preview,vertices:frame===null?preview.vertices:preview.frames[frame].vertices};delete geometry.frames;
  const result=structuredClone(base);result.entities.find(e=>e.entity_id===entityId).geometry_key=key;result.entities.find(e=>e.entity_id===entityId).renderable=true;
  const used=new Set(result.entities.map(e=>e.geometry_key));result.assets=result.assets.filter(a=>used.has(a.geometry_key));
  if(result.assets.length>=128)throw new Error('Scene has no spare geometry capacity for isolated animation inspection.');
  result.assets.push({geometry_key:key,asset_id:preview.semantic_id,preview:geometry});
  return {document:result,geometryKey:key};
}
function sceneShapeProposalDocument(base,report,entityId){
  if(report.instance_scope!=='all_model_instances')return scenePoseDocument(base,report.preview,entityId,null);
  if(!Array.isArray(report.proposal_assets)||!Array.isArray(report.proposal_instances)||!report.proposal_instances.length||report.proposal_assets.length>128||report.proposal_instances.length>base.entities.length)throw new Error('Invalid shared model proposal');
  const result=structuredClone(base),seen=new Set(),assets=new Map(report.proposal_assets.map(a=>[a.geometry_key,a]));
  if(assets.size!==report.proposal_assets.length)throw new Error('Ambiguous proposed geometry');
  for(const row of report.proposal_instances){
    const target=result.entities.find(e=>e.entity_id===row.entity_id),geometry=assets.get(row.geometry_key);
    if(seen.has(row.entity_id)||!target?.renderable||target.asset_id!==report.asset_id||target.geometry_key!==row.source_geometry_key||geometry?.source_geometry_key!==row.source_geometry_key||geometry.asset_id!==report.asset_id)throw new Error('Shared proposal instance binding differs from the scene');
    seen.add(row.entity_id);target.geometry_key=row.geometry_key;
  }
  const used=new Set(result.entities.map(e=>e.geometry_key));result.assets=result.assets.filter(a=>used.has(a.geometry_key));
  if(result.assets.length+assets.size>128)throw new Error('Shared model proposal exceeds scene geometry capacity');
  for(const geometry of assets.values())result.assets.push(geometry);
  return {document:result,geometryKey:report.proposal_assets[0].geometry_key};
}
function frameShapeProposal(report,entityId){
  if(report.instance_scope!=='all_model_instances'){const target=scenePreview.entities.find(e=>e.entity_id===entityId);frame({id:entityId,components:{Transform:{imported:{position:target.position}}}});return;}
  const points=report.proposal_instances.flatMap(row=>previewBounds(row.entity_id,hiddenSceneEntities()));
  if(!points.length)return;
  const min={x:Infinity,y:Infinity,z:Infinity},max={x:-Infinity,y:-Infinity,z:-Infinity};
  for(const point of points)for(const axis of ['x','y','z']){min[axis]=Math.min(min[axis],point[axis]);max[axis]=Math.max(max[axis],point[axis]);}
  for(const axis of ['x','y','z'])camera.target[axis]=(min[axis]+max[axis])/2;
  camera.distance=Math.max(20,Math.hypot(max.x-min.x,max.y-min.y,max.z-min.z)*2.2);cameraRevision++;draw();
}
function sceneShapeProposalLabel(report,entityId){return report.instance_scope==='all_model_instances'?`${report.proposal_instances.length} supported instances · ${report.unavailable_instances.length} unavailable`:entityId;}
function updateScenePoseFrame(frame){
  if(!scenePose?.preview?.frames||scenePose.inspectionLayer==='current'||!scenePreviewCurrent()||scenePose.key!==sceneKey)return;
  if(!Number.isInteger(frame)||frame<0||frame>=scenePose.preview.frames.length)throw new Error('Scene inspection frame is outside the loaded animation.');
  if(sceneRenderer.updateVertices(scenePose.geometryKey,scenePose.preview.frames[frame].vertices)){
    scenePose.frame=frame;scenePose.proposalLabel=`Inspection only · ${scenePose.name} · frame ${frame+1}/${scenePose.preview.frames.length}`;scenePoseBar.querySelector('span').textContent=scenePose.proposalLabel;
    const retained=scenePose.proposalDocument?.assets.find(asset=>asset.geometry_key===scenePose.geometryKey);if(retained)retained.preview.vertices=structuredClone(scenePose.preview.frames[frame].vertices);
    scenePoseBar.querySelector('input').value=frame;draw();
  }
}
scenePoseBar.querySelector('[data-return-file]').onclick=()=>{if(busy)return;const returnToFile=scenePose?.returnToFile;clearScenePose(true,true);draw();if(!returnToFile?.())notify('The inspection context changed. Reopen the asset Inspector to review the proposal again.',true);};
scenePoseBar.querySelector('[data-restore]').onclick=()=>{const afterRestore=scenePose?.afterRestore;clearScenePose();draw();afterRestore?.();};
scenePoseBar.querySelector('input').oninput=event=>{stopScenePosePlayback();try{updateScenePoseFrame(Number(event.target.value));}catch(error){clearScenePose();notify(error.message,true);draw();}};
function stopScenePosePlayback(){
  if(scenePoseTick!==null)cancelAnimationFrame(scenePoseTick);
  scenePoseTick=null;scenePoseClock=null;scenePoseBar.querySelector('[data-play]').textContent='Play scene preview';
}
scenePoseBar.querySelector('select').onchange=()=>{scenePoseClock=null;};
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopScenePosePlayback();});
scenePoseBar.querySelector('[data-play]').onclick=()=>{
  if(scenePoseTick!==null){stopScenePosePlayback();return;}
  const session=scenePose;if(busy||!session?.preview?.frames||session.inspectionLayer==='current')return;
  scenePoseBar.querySelector('[data-play]').textContent='Pause scene preview';
  const tick=time=>{
    if(scenePose!==session||!scenePreviewCurrent()||session.key!==sceneKey||state.project?.mode!=='edit'||busy||document.hidden||!modelsEnabled||sceneRenderer.lost||$('model-dialog').open){stopScenePosePlayback();return;}
    if(scenePoseClock===null)scenePoseClock=time;
    const step=1000/Number(scenePoseBar.querySelector('select').value),advance=Math.floor((time-scenePoseClock)/step);
    try{if(advance){scenePoseClock+=advance*step;updateScenePoseFrame((session.frame+advance)%session.preview.frames.length);}}
    catch(error){stopScenePosePlayback();notify(error.message,true);return;}
    if(scenePose===session)scenePoseTick=requestAnimationFrame(tick);else stopScenePosePlayback();
  };
  scenePoseTick=requestAnimationFrame(tick);
};
showScenePose.onclick=()=>{
  if(busy||state.project?.mode!=='edit'||!scenePreviewCurrent()||modelSceneContext!==sceneRequestKey()||!modelSceneEntityId||!model?.frames?.length||$('shape-file').files?.length)return;
  try{
    stopScenePosePlayback();const isolated=scenePoseDocument(scenePreview,model,modelSceneEntityId,animationFrame);
    const failures=sceneRenderer.load(isolated.document);if(failures.length)throw new Error(failures.join('; '));
    scenePose={key:sceneKey,geometryKey:isolated.geometryKey,preview:model,frame:animationFrame,returnToFile:modelFileReturn,name:(model.animation?.representation==='allocated_record_edit_preview'?'Proposed retained edit · not applied · ':model.animation?.representation==='allocated_assignment_preview'?'Proposed initial assignment · not applied · ':model.animation?.representation==='allocated_initial_assignment'?'Assigned initial clip · ':model.animation?.representation==='allocated_record'?'Saved retained clip · ':model.animation?.representation==='allocation_preview'?'Proposed unassigned clip · ':model.animation?.representation==='file_preview'?'Proposed file · not applied · ':modelEntityId?'':'Reference clip · ')+(state.actor_drafts?.[modelSceneEntityId]?.name??entities().find(e=>e.id===modelSceneEntityId)?.name??modelSceneEntityId)};
    configureSceneInspectionComparison(isolated.document);
    for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('label')])control.hidden=false;scenePoseBar.querySelector('[data-return-file]').textContent=model.animation?.representation==='allocated_record_edit_preview'?'Return to retained editor':['allocated_record','allocated_assignment_preview'].includes(model.animation?.representation)?'Return to saved clips':model.animation?.representation==='allocation_preview'?'Return to clip allocation':'Return to animation file';
    scenePoseBar.hidden=false;scenePoseBar.querySelector('[data-return-file]').hidden=typeof modelFileReturn!=='function';scenePoseBar.querySelector('input').max=model.frames.length-1;
    if(model.animation?.representation==='file_preview')animationEditDialog.close();
    $('model-dialog').close();updateScenePoseFrame(animationFrame);if(state.actor_drafts?.[modelSceneEntityId]){selectNpcDraft(modelSceneEntityId);frameNpcDraft();}else{const actor=entities().find(e=>e.id===modelSceneEntityId);if(actor)frame(actor);}
  }catch(error){clearScenePose(false);const failures=sceneRenderer.load(structuredClone(scenePreview));if(failures.length)sceneError=failures.join('; ');notify(error.message,true);draw();}
};

const shapeControls=document.createElement('section');shapeControls.innerHTML='<h3>Model shape</h3><p>Edit object-local vertex and normal coordinates, existing face connections and normal references, texture UVs and stored RGB colors. Use the separate add/remove actions to change face counts. Source material bindings use a separate reviewed editor. Shape preview is unposed. OBJ preserves vertex order, oriented triangulation and integer source coordinates; normals remain unchanged. JSON contains complete ordered vertex and normal arrays bound to the retail source hash.</p><button id="shape-vectors">Edit model vectors</button><button id="shape-primitives">Edit faces, UVs and colors</button><button id="shape-source">Download source TMD</button><button id="shape-authored-tmd">Download authored TMD</button><button id="shape-source-obj">Download shape OBJ</button><button id="shape-download-authored">Download authored OBJ</button><button id="shape-source-json">Download source JSON</button><button id="shape-authored-json">Download authored JSON</button><label>Edited TMD, OBJ or JSON<input id="shape-file" type="file" accept=".tmd,.obj,.json"></label><button id="shape-file-preview">Preview shape file</button><button id="shape-upload">Apply shape</button><div id="shape-file-report"></div><button id="shape-retail">View retail shape</button><button id="shape-authored">View authored shape</button><button id="shape-clear">Clear shape override</button><p id="shape-status"></p>';$('model-description').after(shapeControls);
const vectorDialog=document.createElement('dialog');vectorDialog.id='model-vector-dialog';document.body.append(vectorDialog);
let modelFaceRemovalEditor=null;
let modelAllocationEditor=null;
let modelFaceAdditionEditor=null;
let modelVectorAllocationEditor=null,modelVertexMoveEditor=null;
let modelMeshAppendEditor=null;
let modelGroupAllocationEditor=null;
const groupAllocationButton=document.createElement('button');groupAllocationButton.id='shape-add-group';groupAllocationButton.type='button';groupAllocationButton.textContent='Create packet group';$('shape-primitives').after(groupAllocationButton);
groupAllocationButton.onclick=async()=>{
  if(busy||shapeDraft||!modelAssetId||state.project.mode!=='edit'||!state.capabilities?.model_group_allocation)return;
  modelGroupAllocationEditor?.dispose();const asset=modelAssetId,context=JSON.stringify([state.project.path,state.scene?.id,state.scene_preview_source_key]),module=await import('/model-group-allocation.js');
  if(busy||shapeDraft||!state.capabilities?.model_group_allocation||asset!==modelAssetId||state.project.mode!=='edit'||context!==JSON.stringify([state.project.path,state.scene?.id,state.scene_preview_source_key]))return;
  modelGroupAllocationEditor=await module.openModelGroupAllocation({assetId:asset,getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id,sourceKey:state.scene_preview_source_key,mode:state.project.mode,assetId:modelAssetId}),busy:()=>busy,setBusy,onError:error=>notify(error.message,true),onApplied:async next=>{state=next;render();setBusy(false);notify('Packet group created. Save project to persist.');await openModel(asset,null,null,'authored');}});
};

let modelObjectAllocationEditor=null;
const objectAllocationButton=document.createElement('button');objectAllocationButton.id='shape-add-object';objectAllocationButton.type='button';objectAllocationButton.textContent='Create native object';$('shape-primitives').after(objectAllocationButton);
objectAllocationButton.onclick=async()=>{
  if(busy||shapeDraft||!modelAssetId||state.project.mode!=='edit'||!state.capabilities?.model_object_allocation)return;
  modelObjectAllocationEditor?.dispose();const asset=modelAssetId,context=JSON.stringify([state.project.path,state.scene?.id,state.scene_preview_source_key]),module=await import('/model-object-allocation.js');
  if(busy||shapeDraft||!state.capabilities?.model_object_allocation||asset!==modelAssetId||state.project.mode!=='edit'||context!==JSON.stringify([state.project.path,state.scene?.id,state.scene_preview_source_key]))return;
  modelObjectAllocationEditor=await module.openModelObjectAllocation({assetId:asset,getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id,sourceKey:state.scene_preview_source_key,mode:state.project.mode,assetId:modelAssetId}),busy:()=>busy,setBusy,onError:error=>notify(error.message,true),onApplied:async next=>{state=next;render();setBusy(false);notify('Native object created. Save project to persist.');await openModel(asset,null,null,'authored');}});
};

const meshAppendButton=document.createElement('button');meshAppendButton.id='shape-append-mesh';meshAppendButton.type='button';meshAppendButton.textContent='Import GLB mesh';$('shape-primitives').after(meshAppendButton);
meshAppendButton.onclick=async()=>{
  if(busy||shapeDraft||!modelAssetId||state.project.mode!=='edit'||!state.capabilities?.model_mesh_append)return;
  modelMeshAppendEditor?.dispose();const asset=modelAssetId,context=JSON.stringify([state.project.path,state.scene?.id,state.scene_preview_source_key]),module=await import('/model-mesh-append.js');
  if(busy||asset!==modelAssetId||state.project.mode!=='edit'||context!==JSON.stringify([state.project.path,state.scene?.id,state.scene_preview_source_key]))return;
  modelMeshAppendEditor=await module.openModelMeshAppend({assetId:asset,getSceneInstances:()=>scenePreviewCurrent()&&sceneRepresentation==='authored'?(scenePreview.entities??[]).filter(e=>e.asset_id===asset&&e.renderable).map(e=>({entity_id:e.entity_id,name:e.name})):[],getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id,sourceKey:state.scene_preview_source_key,mode:state.project.mode,assetId:modelAssetId}),busy:()=>busy,setBusy,onError:error=>notify(error.message,true),onApplied:async next=>{state=next;render();setBusy(false);notify('Mesh imported. Save project to persist.');await openModel(asset,null,null,'authored');},onScenePreview:inspectMeshSceneProposal});
};

async function inspectMeshSceneProposal(request,report,{returnToEditor,isCurrent,signal}){
  if(!scenePreviewCurrent()||sceneRepresentation!=='authored'||scenePreview.project_source_key!==report.project_source_key)throw new Error('Load the current authored scene before inspecting the mesh import.');
  const instances=scenePreview.entities.filter(e=>e.asset_id===request.asset_id&&e.renderable);
  if(!instances.length)throw new Error('This model has no supported scene instances.');
  if(typeof request.all_instances!=='boolean'||!instances.some(e=>e.entity_id===request.entity_id))throw new Error('Choose a supported Current scene instance for mesh inspection.');
  const entityId=request.entity_id,loadedKey=sceneKey,context=sceneRequestKey();
  const response=await fetch(request.mappings?'/api/model-mesh-batch-scene-preview':'/api/model-mesh-append-scene-preview',{method:'POST',headers:{'Content-Type':'application/json'},signal,body:JSON.stringify(request)}),posed=await response.json();
  if(!response.ok||posed.error)throw new Error(posed.error||'Scene mesh proposal failed');
  if(signal.aborted||!isCurrent()||context!==sceneRequestKey()||loadedKey!==sceneKey||!scenePreviewCurrent()||posed.asset_id!==request.asset_id||posed.entity_id!==entityId||posed.project_source_key!==report.project_source_key||posed.proposed_sha256!==report.proposed_sha256||posed.review_key!==report.review_key||(posed.instance_scope==='all_model_instances')!==request.all_instances||!request.all_instances&&(posed.proposal_instances!==undefined||posed.proposal_assets!==undefined))throw new Error('Scene changed during mesh inspection.');
  stopScenePosePlayback();const isolated=sceneShapeProposalDocument(scenePreview,posed,entityId),failures=sceneRenderer.load(isolated.document);if(failures.length)throw new Error(failures.join('; '));
  const back=()=>{if(context!==sceneRequestKey()||loadedKey!==sceneKey||state.scene_preview_source_key!==report.project_source_key)return false;$('model-dialog').showModal();return returnToEditor();};
  const owned={key:sceneKey,geometryKey:isolated.geometryKey,preview:posed.preview,name:'Proposed mesh import · not applied',returnToFile:back,afterRestore:back,inspectionEntityIds:request.all_instances?posed.proposal_instances.map(row=>row.entity_id):[entityId],inspectionIsolated:true};scenePose=owned;
  scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`Proposed mesh import · not applied · ${sceneShapeProposalLabel(posed,entityId)}`;configureSceneInspectionComparison(isolated.document);
  for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('label')])control.hidden=true;
  const button=scenePoseBar.querySelector('[data-return-file]');button.hidden=false;button.textContent='Return to mesh import';
  $('model-dialog').close();frameShapeProposal(posed,entityId);draw();return {restore:()=>{if(scenePose===owned){clearScenePose();draw();}}};
}

const vectorAllocationButton=document.createElement('button');vectorAllocationButton.id='shape-add-vectors';vectorAllocationButton.type='button';vectorAllocationButton.textContent='Add vertices or normals';$('shape-primitives').after(vectorAllocationButton);
vectorAllocationButton.onclick=async()=>{
  if(busy||shapeDraft||!modelAssetId||state.project.mode!=='edit'||!state.capabilities?.model_vector_allocation)return;
  modelVectorAllocationEditor?.dispose();const asset=modelAssetId,context=JSON.stringify([state.project.path,state.scene?.id,state.scene_preview_source_key]),module=await import('/model-vector-allocation.js');
  if(busy||asset!==modelAssetId||state.project.mode!=='edit'||context!==JSON.stringify([state.project.path,state.scene?.id,state.scene_preview_source_key]))return;
  modelVectorAllocationEditor=await module.openModelVectorAllocation({assetId:asset,getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id,sourceKey:state.scene_preview_source_key,mode:state.project.mode,assetId:modelAssetId}),busy:()=>busy,setBusy,onError:error=>notify(error.message,true),onApplied:async next=>{state=next;render();setBusy(false);notify('Model vectors added. Save project to persist.');await openModel(asset,null,null,'authored');}});
};
const faceAdditionButton=document.createElement('button');faceAdditionButton.id='shape-add-face';faceAdditionButton.type='button';faceAdditionButton.textContent='Add model face';$('shape-primitives').after(faceAdditionButton);
faceAdditionButton.onclick=async()=>{
  if(busy||shapeDraft||!modelAssetId||state.project.mode!=='edit')return;
  modelFaceAdditionEditor?.dispose();const asset=modelAssetId,context=JSON.stringify([state.project.path,state.scene?.id,state.scene_preview_source_key]),module=await import('/model-face-addition.js');
  if(busy||asset!==modelAssetId||state.project.mode!=='edit'||context!==JSON.stringify([state.project.path,state.scene?.id,state.scene_preview_source_key]))return;
  modelFaceAdditionEditor=await module.openModelFaceAddition({assetId:asset,getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id,sourceKey:state.scene_preview_source_key,mode:state.project.mode,assetId:modelAssetId}),busy:()=>busy,setBusy,onError:error=>notify(error.message,true),onApplied:async next=>{state=next;render();setBusy(false);notify('Model face added. Save project to persist.');await openModel(asset,null,null,'authored');}});
};
const allocationButton=document.createElement('button');allocationButton.id='shape-allocation';allocationButton.type='button';allocationButton.textContent='Inspect native allocation';$('shape-primitives').after(allocationButton);
allocationButton.onclick=async()=>{if(busy||shapeDraft||!modelAssetId||state.project.mode!=='edit')return;modelAllocationEditor?.dispose();const asset=modelAssetId,module=await import('/model-allocation.js');if(busy||asset!==modelAssetId||state.project.mode!=='edit')return;modelAllocationEditor=await module.openModelAllocation({assetId:asset,getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id,sourceKey:state.scene_preview_source_key,mode:state.project.mode,assetId:modelAssetId}),busy:()=>busy,setBusy,onError:error=>notify(error.message,true)});};
const faceRemovalButton=document.createElement('button');faceRemovalButton.id='shape-remove-faces';faceRemovalButton.type='button';faceRemovalButton.textContent='Remove model faces';$('shape-primitives').after(faceRemovalButton);
faceRemovalButton.onclick=async()=>{if(busy||shapeDraft||!modelAssetId||state.project.mode!=='edit')return;modelFaceRemovalEditor?.dispose();const asset=modelAssetId,module=await import('/model-face-removal.js');modelFaceRemovalEditor=await module.openModelFaceRemoval({assetId:asset,getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id,sourceKey:state.scene_preview_source_key,mode:state.project.mode}),busy:()=>busy,setBusy,onError:error=>notify(error.message,true),onApplied:async next=>{state=next;render();setBusy(false);notify('Model topology updated. Save project to persist.');await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}});};
let modelGlbEditor=null;
let modelMaterialsEditor=null;
const modelMaterialsButton=document.createElement('button');modelMaterialsButton.id='shape-materials';modelMaterialsButton.type='button';modelMaterialsButton.textContent='Edit source material bindings';$('shape-primitives').after(modelMaterialsButton);
modelMaterialsButton.onclick=()=>inspectModelMaterials();
async function inspectModelMaterials(initial=null){
  if(busy||!modelAssetId||shapeDraft||state.project.mode!=='edit'||!state.capabilities?.model_material_authoring||modelSceneContext!==sceneRequestKey())return;
  const assetId=modelAssetId,context=sceneRequestKey();modelMaterialsEditor?.dispose();$('model-dialog').close();
  modelMaterialsEditor=await openModelMaterialsEditor({assetId,initial:initial?{object_index:initial.object_index,group_index:initial.group_index,...(initial.kind==='primitive'?{primitive_index:initial.primitive_index}:{})}:null,
    getContext:primitiveContext,busy:()=>busy,setBusy,onError:error=>notify(error.message??String(error),true),
    onApplied:next=>{state=next;render();notify('Model materials updated. Save project to persist.');},
    canPreviewScene:()=>scenePreviewCurrent()&&sceneRepresentation==='authored'&&scenePreview.entities.some(e=>e.asset_id===assetId&&e.renderable),
    onPreview:async(report,{returnToEditor,isCurrent,signal})=>{
      if(signal.aborted||!isCurrent()||context!==sceneRequestKey())throw new Error('Model source changed before inspection.');
      setBusy(false);await openModel(assetId,null,null,'imported',null,report.preview,returnToEditor);
      if(signal.aborted||!isCurrent()||model!==report.preview||!$('model-dialog').open)throw new Error($('model-error').textContent||'Could not inspect reviewed materials.');
      $('model-dialog').addEventListener('close',()=>{if(model===report.preview)returnToEditor();},{once:true});
    },
    onScenePreview:async(request,report,{returnToEditor,isCurrent,signal})=>{
      if(!scenePreviewCurrent()||sceneRepresentation!=='authored'||scenePreview.project_source_key!==report.project_source_key)throw new Error('Load the current authored scene before inspecting proposed materials.');
      const instances=scenePreview.entities.filter(e=>e.asset_id===assetId&&e.renderable);
      if(!instances.length)throw new Error('This model has no supported scene instances.');
      const entityId=instances.some(e=>e.entity_id===environmentSelection)?environmentSelection:instances[0].entity_id,loadedKey=sceneKey;
      const response=await fetch('/api/model-material-scene-preview',{method:'POST',headers:{'Content-Type':'application/json'},signal,body:JSON.stringify({...request,entity_id:entityId,all_instances:true})}),posed=await response.json();
      if(!response.ok||posed.error)throw new Error(posed.error||'Scene material proposal failed');
      if(signal.aborted||!isCurrent()||context!==sceneRequestKey()||loadedKey!==sceneKey||!scenePreviewCurrent()||posed.project_source_key!==report.project_source_key||posed.proposed_sha256!==report.proposed_sha256||posed.review_key!==report.review_key)throw new Error('Scene changed during material inspection.');
      stopScenePosePlayback();const isolated=sceneShapeProposalDocument(scenePreview,posed,entityId),failures=sceneRenderer.load(isolated.document);if(failures.length)throw new Error(failures.join('; '));
      const back=()=>{if(context!==sceneRequestKey()||loadedKey!==sceneKey||state.scene_preview_source_key!==report.project_source_key)return false;return returnToEditor();};
      scenePose={key:sceneKey,geometryKey:isolated.geometryKey,preview:posed.preview,name:'Proposed materials · not applied',returnToFile:back,afterRestore:back};
      scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`Proposed materials · not applied · ${sceneShapeProposalLabel(posed,entityId)}`;configureSceneInspectionComparison(isolated.document);
      for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('label')])control.hidden=true;
      const button=scenePoseBar.querySelector('[data-return-file]');button.hidden=false;button.textContent='Return to material editor';frameShapeProposal(posed,entityId);draw();return true;
    }});
}
const modelGlbButton=document.createElement('button');modelGlbButton.id='shape-glb';modelGlbButton.type='button';modelGlbButton.textContent='Edit model through GLB';$('shape-source-obj').before(modelGlbButton);
modelGlbButton.onclick=async()=>{
  if(busy||shapeDraft||state.project.mode!=='edit'||!state.capabilities?.model_glb_authoring||modelSceneContext!==sceneRequestKey())return;
  const assetId=modelAssetId;modelGlbEditor?.dispose();$('model-dialog').close();
  modelGlbEditor=await openModelGlbEditor({assetId,
    getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id??null,mode:state.project.mode,sourceKey:state.scene_preview_source_key}),
    busy:()=>busy,setBusy,onError:error=>notify(error.message??String(error),true),
    onApplied:next=>{state=next;render();notify('Model GLB imported. Save project to persist.');},
    onPreview:async(data,{returnToEditor})=>{
      setBusy(false);await openModel(assetId,null,null,'imported',null,data,returnToEditor);
      if(model!==data||!$('model-dialog').open)throw new Error($('model-error').textContent||'Could not open the reviewed model preview.');
      $('model-dialog').addEventListener('close',()=>{if(model===data)returnToEditor();},{once:true});
    }});
};
let objectProposalRenderer=null,objectProposalCanvas=null;
async function openVertexMovement(initial){
  if(busy||shapeDraft||state.project.mode!=='edit')return;const asset=modelAssetId;modelVertexMoveEditor?.dispose();vectorDialog.close();$('model-dialog').close();const module=await import('/model-vertex-move.js');
  modelVertexMoveEditor=await module.openModelVertexMove({assetId:asset,initial,getHistory:()=>state.history??{},getSavedGroups:()=>state.model_vertex_groups??[],getSceneInstances:()=>scenePreviewCurrent()&&sceneRepresentation==='authored'?(scenePreview.entities??[]).filter(e=>e.asset_id===asset&&e.renderable).map(e=>({entity_id:e.entity_id,name:e.name})):[],onScenePreview:inspectMovementSceneProposal,getContext:()=>({projectPath:state.project.path,sceneId:state.scene?.id,sourceKey:state.scene_preview_source_key,mode:state.project.mode,assetId:modelAssetId}),busy:()=>busy,setBusy,onError:error=>notify(error.message,true),onApplied:async(next,action)=>{state=next;render();notify(action==='selection'?'Saved model vertex group updated. Save project to persist.':action==='apply'?'Model geometry moved. Save project to persist.':action==='undo'?'Project change undone.':'Project change redone.');}});
}
async function inspectMovementSceneProposal(request,expected,{returnToEditor,isCurrent,signal}){
  if(!scenePreviewCurrent()||sceneRepresentation!=='authored'||scenePreview.project_source_key!==request.source_key)throw new Error('Load the current authored scene before inspecting movement.');
  const loadedKey=sceneKey,context=sceneRequestKey(),post=async(route,body)=>{const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},signal,body:JSON.stringify(body)}),value=await response.json();if(!response.ok||value.error)throw new Error(value.error||'Movement scene proposal failed');return value;};
  const vector=request.operation==='vector',base={asset_id:request.asset_id,object_index:request.object_index,values:request.values,expected_sha256:request.expected_sha256,...(vector?{kind:request.kind,vector_index:request.vector_index}:{operation:request.operation})},inspected=await post(vector?'/api/model-vector-preview':'/api/model-object-preview',base);
  const {qualifyObjectMoveReview}=await import('/model-vertex-move.js');qualifyObjectMoveReview(inspected,request,expected);if(!isCurrent()||signal.aborted)throw new Error('Movement draft changed during review.');
  const posed=await post(vector?'/api/model-vector-scene-preview':'/api/model-object-scene-preview',{...base,entity_id:request.entity_id,all_instances:request.all_instances,source_key:request.source_key});
  if(signal.aborted||!isCurrent()||context!==sceneRequestKey()||loadedKey!==sceneKey||!scenePreviewCurrent()||posed.asset_id!==request.asset_id||posed.entity_id!==request.entity_id||posed.project_source_key!==request.source_key||posed.proposed_sha256!==inspected.proposed_sha256||posed.source_sha256!==inspected.source_sha256||posed.effective_sha256!==request.expected_sha256||posed.object_index!==request.object_index||posed.operation!==request.operation||['vertex_translation','vertex_alignment','vertex_distribution','vertex_scaling','vertex_axis_scaling','vertex_rotation','vertex_rotation_angle','vertex_grid'].includes(request.operation)&&JSON.stringify(posed.values)!==JSON.stringify(request.values)||vector&&(posed.kind!==request.kind||posed.vector_index!==request.vector_index||JSON.stringify(posed.values)!==JSON.stringify(request.values))||(posed.instance_scope==='all_model_instances')!==request.all_instances||posed.project_changed!==false)throw new Error('Scene changed during movement inspection.');
  stopScenePosePlayback();const isolated=sceneShapeProposalDocument(scenePreview,posed,request.entity_id),failures=sceneRenderer.load(isolated.document);if(failures.length)throw new Error(failures.join('; '));
  const back=()=>{if(context!==sceneRequestKey()||loadedKey!==sceneKey||state.scene_preview_source_key!==request.source_key)return false;return returnToEditor();};
  const owned={key:sceneKey,geometryKey:isolated.geometryKey,preview:posed.preview,name:'Proposed model movement - not applied',returnToFile:back,afterRestore:back,isCurrent,inspectionEntityIds:posed.proposal_instances?.map(row=>row.entity_id)??[request.entity_id]};scenePose=owned;
  scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`Proposed ${vector?'vertex':['vertex_translation','vertex_alignment','vertex_distribution','vertex_scaling','vertex_axis_scaling','vertex_rotation','vertex_rotation_angle','vertex_grid'].includes(request.operation)?'vertex group':'object'} movement - not applied - ${sceneShapeProposalLabel(posed,request.entity_id)} - ${vector?'vertex '+request.vector_index+' XYZ '+request.values.join(', '):request.operation==='vertex_grid'?'grid '+request.values.spacing+' units on '+request.values.axes.map(axis=>axis.toUpperCase()).join(', '):request.operation==='vertex_rotation_angle'?'rotate '+request.values.axis.toUpperCase()+' '+(request.values.angle_units*360/4096)+' degrees about '+request.values.pivot:request.operation==='vertex_rotation'?'rotate '+request.values.axis.toUpperCase()+' '+(request.values.quarter_turns*90)+' degrees about '+request.values.pivot:request.operation==='vertex_axis_scaling'?'scale X/Y/Z '+request.values.percents.join('/')+'% about '+request.values.pivot:request.operation==='vertex_scaling'?'scale '+request.values.percent+'% about '+request.values.pivot:request.operation==='vertex_distribution'?'distribute '+request.values.axis.toUpperCase():request.operation==='vertex_alignment'?'align '+request.values.axis.toUpperCase()+' '+request.values.anchor:'offset '+request.values.offset.join(', ')}`;configureSceneInspectionComparison(isolated.document);
  for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('label')])control.hidden=true;
  const button=scenePoseBar.querySelector('[data-return-file]');button.hidden=false;button.textContent='Return to movement draft';frameShapeProposal(posed,request.entity_id);draw();return {restore:()=>{if(scenePose===owned){clearScenePose();draw();}}};
}
async function openModelVectors(initial=null){
  if(busy||shapeDraft||state.project.mode!=='edit')return;
  const asset=modelAssetId,context=JSON.stringify([state.project.path,state.scene.id]);setBusy(true);
  try{
    const response=await fetch('/api/model-shape-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:asset,format:'json',layer:state.model_overrides?.[asset]?'authored':'imported'})}),source=await response.json();
    if(!response.ok||source.error)throw new Error(source.error||'Model vectors unavailable');
    if(asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id])||!$('model-dialog').open)return;
    const document=JSON.parse(atob(source.json_base64));
    let retail=document;
    if(source.representation==='authored'){
      const response=await fetch('/api/model-shape-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:asset,format:'json',layer:'imported'})}),baseline=await response.json();
      if(!response.ok||baseline.error)throw new Error(baseline.error||'Retail vectors unavailable');
      if(baseline.semantic_id!==asset||baseline.source_sha256!==source.source_sha256)throw new Error('Retail vector source changed; reopen the editor');
      retail=JSON.parse(atob(baseline.json_base64));
      if(asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id])||!$('model-dialog').open)return;
    }
    vectorDialog.innerHTML='<h2>Edit model vectors</h2><p>Object-local Y-down source words. Layout and materials stay fixed. Source normal directions can be inspected separately; retail lighting is not reconstructed.</p><form><label>Object<select name="object" aria-label="Vector object"></select></label><label>Kind<select name="kind" aria-label="Vector kind"><option value="vertices">Vertices</option><option value="normals">Normals</option></select></label><label>Index<input name="index" aria-label="Vector index" type="number" min="0" step="1" value="0" required></label><div data-xyz></div><p data-original></p><p data-retail></p><button type="button" data-retail-vector>Use retail vector</button><button type="button" data-locate-vector>Locate inspected vertex</button><p data-error class="dialog-error" role="alert"></p><button type="submit">Apply vector</button><button type="button" data-discard>Discard vector draft</button><button type="button" data-close>Close vector editor</button></form>';
    const form=vectorDialog.querySelector('form'),object=form.elements.object,kind=form.elements.kind,index=form.elements.index,xyz=[];
    for(const row of document.objects){const option=window.document.createElement('option');option.value=row.object_index;option.textContent=`Object ${row.object_index} · ${row.vertices.length} vertices · ${row.normals.length} normals`;object.append(option);}
    for(const axis of ['X','Y','Z']){const label=window.document.createElement('label'),input=window.document.createElement('input');label.textContent=axis;input.type='number';input.step='1';input.min='-32768';input.max='32767';input.required=true;input.setAttribute('aria-label','Vector '+axis);label.append(input);form.querySelector('[data-xyz]').append(label);xyz.push(input);}
    const moveVertex=window.document.createElement('button');moveVertex.type='button';moveVertex.textContent='Move inspected vertex in 3D';form.querySelector('[data-locate-vector]').after(moveVertex);moveVertex.onclick=()=>{if(busy||!valid||object.disabled||kind.value!=='vertices')return;openVertexMovement({object_index:Number(object.value),vector_index:Number(index.value)});};
    let valid=false;
    const load=()=>{const values=document.objects[Number(object.value)]?.[kind.value]??[];index.max=String(Math.max(0,values.length-1));const i=Number(index.value);valid=Number.isInteger(i)&&i>=0&&i<values.length;xyz.forEach((input,a)=>{input.value=valid?values[i][a]:'';input.disabled=!valid;});form.querySelector('[type=submit]').disabled=!valid;form.querySelector('[data-retail-vector]').disabled=!valid||!retail.objects[Number(object.value)]?.[kind.value]?.[i];form.querySelector('[data-locate-vector]').disabled=!valid||kind.value!=='vertices';moveVertex.disabled=!valid||kind.value!=='vertices';form.querySelector('[data-retail]').textContent=valid?(retail.objects[Number(object.value)]?.[kind.value]?.[i]?'Retail XYZ: '+retail.objects[Number(object.value)][kind.value][i].join(', '):'Allocated vector · no Retail counterpart.'):'';form.querySelector('[data-original]').textContent=valid?'Inspected XYZ: '+values[i].join(', '):'No vector at this index.';object.disabled=kind.disabled=index.disabled=false;};
    object.onchange=kind.onchange=()=>{index.value='0';load();};index.oninput=load;
    xyz.forEach(input=>input.oninput=()=>{object.disabled=kind.disabled=index.disabled=true;form.querySelector('[data-locate-vector]').disabled=true;moveVertex.disabled=true;});
    form.querySelector('[data-retail-vector]').onclick=()=>{if(busy||!valid)return;const values=retail.objects[Number(object.value)]?.[kind.value]?.[Number(index.value)];if(!values)return;xyz.forEach((input,a)=>input.value=values[a]);object.disabled=kind.disabled=index.disabled=true;form.querySelector('[data-locate-vector]').disabled=true;moveVertex.disabled=true;};
    form.querySelector('[data-locate-vector]').onclick=async()=>{
      if(busy||!valid||kind.value!=='vertices'||object.disabled)return;
      if(asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id]))return;
      const objectIndex=Number(object.value),vectorIndex=Number(index.value),point=document.objects[objectIndex].vertices[vectorIndex].slice();
      vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');
      if(asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id])||!$('model-dialog').open)return;
      $('model-object').value=String(objectIndex);fitModelObject();modelView.center=point;drawModel();$('shape-status').textContent=`Located inspected object ${objectIndex}, vertex ${vectorIndex} · XYZ ${point.join(', ')} · camera only; project unchanged`;
    };
    const translation=window.document.createElement('details');translation.innerHTML='<summary>Translate all vertices in this object</summary><p>Offsets use object-local Y-down source units. Normals, other objects and topology stay unchanged. Apply creates one undoable model edit.</p><div data-offsets></div><p data-offset-report></p><button type="button" data-translate>Apply object translation</button>';
    form.querySelector('[data-xyz]').after(translation);const offsets=[];
    for(const axis of ['X','Y','Z']){const label=window.document.createElement('label'),input=window.document.createElement('input');label.textContent='Offset '+axis;input.type='number';input.step='1';input.min='-65535';input.max='65535';input.value='0';input.setAttribute('aria-label','Object offset '+axis);label.append(input);translation.querySelector('[data-offsets]').append(label);offsets.push(input);}
    const offsetValues=()=>offsets.map(input=>input.value.trim()===''?NaN:Number(input.value));
    const previewOffset=()=>{const values=offsetValues(),vertices=document.objects[Number(object.value)]?.vertices??[],validOffset=values.every(v=>Number.isInteger(v)&&Math.abs(v)<=65535),fits=validOffset&&vertices.every(vertex=>vertex.every((v,a)=>v+values[a]>=-32768&&v+values[a]<=32767));translation.querySelector('[data-offset-report]').textContent=!validOffset?'Enter three integer offsets.':!fits?'Offset exceeds signed16 coordinates; nothing will be applied.':`${vertices.length} vertices · offset ${values.join(', ')} · normals unchanged`;translation.querySelector('[data-translate]').disabled=!vertices.length||!fits||values.every(v=>v===0)||object.disabled;};
    offsets.forEach(input=>{input.oninput=previewOffset;input.onkeydown=event=>{if(event.key==='Enter')event.preventDefault();};});form.addEventListener('change',previewOffset);translation.ontoggle=previewOffset;
    translation.querySelector('[data-translate]').onclick=async()=>{if(busy||object.disabled)return;previewOffset();if(translation.querySelector('[data-translate]').disabled)return;if(asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id]))return;
      if(await api('/api/model-object-translation',{asset_id:asset,object_index:Number(object.value),offset:offsetValues(),expected_sha256:source.effective_sha256},{dialog:vectorDialog,success:'Model object translated. Save project to persist.'})){vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}
    };
    const rotation=window.document.createElement('details');rotation.innerHTML='<summary>Rotate whole object</summary><p>Rotate vertices and normals around the object-local origin. Source XYZ axes retain PSX Y-down coordinates; these are not scene transforms. Exact quarter turns preserve normal lengths and vector padding.</p><label>Source axis<select aria-label="Object rotation axis"><option value="x">X</option><option value="y">Y</option><option value="z">Z</option></select></label><label>Turn<select aria-label="Object rotation turn"><option value="1">+90°</option><option value="-1">−90°</option><option value="2">180°</option></select></label><p data-rotation-report></p><button type="button" data-rotate>Apply object rotation</button>';
    translation.after(rotation);const rotationAxis=rotation.querySelector('[aria-label="Object rotation axis"]');
    const turnControl=rotation.querySelector('[aria-label="Object rotation turn"]');
    const rotateVector=vector=>{let [x,y,z]=vector;for(let i=0;i<(Number(turnControl.value)+4)%4;i++)[x,y,z]=rotationAxis.value==='x'?[x,-z,y]:rotationAxis.value==='y'?[z,y,-x]:[-y,x,z];return [x,y,z];};
    const previewRotation=()=>{const obj=document.objects[Number(object.value)],vectors=[...(obj?.vertices??[]),...(obj?.normals??[])],fits=vectors.every(vector=>rotateVector(vector).every(value=>value>=-32768&&value<=32767));rotation.querySelector('[data-rotation-report]').textContent=object.disabled?'Apply or discard the vector draft first.':!fits?'Rotation exceeds signed16 vector values; nothing will be applied.':`${obj?.vertices.length??0} vertices · ${obj?.normals.length??0} normals · ${Number(turnControl.value)*90}° around source ${rotationAxis.value.toUpperCase()}`;rotation.querySelector('[data-rotate]').disabled=object.disabled||!obj?.vertices.length||!fits;};
    form.addEventListener('click',previewRotation);form.addEventListener('input',previewRotation);form.addEventListener('change',previewRotation);rotation.ontoggle=previewRotation;
    rotation.querySelector('[data-rotate]').onclick=async()=>{if(busy||object.disabled)return;previewRotation();if(rotation.querySelector('[data-rotate]').disabled)return;if(asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id]))return;if(await api('/api/model-object-rotation',{asset_id:asset,object_index:Number(object.value),axis:rotationAxis.value,quarter_turns:Number(turnControl.value),expected_sha256:source.effective_sha256},{dialog:vectorDialog,success:'Model object rotated. Save project to persist.'})){vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}};
    const objectAngleTool=window.document.createElement('details');objectAngleTool.innerHTML='<summary>Rotate whole object by angle</summary><p>Rotate all Current vertices and stored normals together around source X/Y/Z. Vertex pivot is local origin or Current vertex bounds center; normals rotate about zero. Source Y points down. Degrees round to 1/4096 turn and final signed16 words round halfway away from zero. Preview and compare before Apply.</p><label>Axis<select aria-label="Object angle axis"><option value="x">X</option><option value="y">Y</option><option value="z">Z</option></select></label><label>Degrees<input type="number" min="-360" max="360" step="0.01" value="45" aria-label="Object angle degrees"></label><label>Pivot<select aria-label="Object angle pivot"><option value="origin">Local origin</option><option value="center">Current bounds center</option></select></label><p data-object-angle-report></p><button type="button" data-object-angle>Apply reviewed object angle</button>';rotation.after(objectAngleTool);
    const objectAngleValues=()=>({axis:objectAngleTool.querySelector('[aria-label="Object angle axis"]').value,angle_units:normalAngleUnits(objectAngleTool.querySelector('input').value.trim()===''?NaN:Number(objectAngleTool.querySelector('input').value)),pivot:objectAngleTool.querySelector('[aria-label="Object angle pivot"]').value});
    let objectAngleValid=false;
    const refreshObjectAngle=()=>{let changed=0;objectAngleValid=false;try{const obj=document.objects[Number(object.value)],values=objectAngleValues(),rotated=rotateObjectWords(obj,values);changed=['vertices','normals'].reduce((n,kind)=>n+rotated[kind].filter((row,i)=>row.some((v,a)=>v!==obj[kind][i][a])).length,0);objectAngleValid=changed>0&&!object.disabled;}catch{}objectAngleTool.querySelector('[data-object-angle-report]').textContent=objectAngleValid?changed+' changed vector rows; preview before Apply.':'No eligible changed vectors; enter a bounded angle for this object.';objectAngleTool.querySelector('[data-object-angle]').disabled=!objectAngleValid||!proposalReport||proposalReport.operation!=='object_rotation_angle'||JSON.stringify(proposalReport.values)!==JSON.stringify(objectAngleValues());};
    objectAngleTool.ontoggle=()=>{if(vectorDialog.open)refreshObjectAngle();};
    objectAngleTool.querySelector('[data-object-angle]').onclick=async()=>{if(busy||!currentContext())return;refreshObjectAngle();if(objectAngleTool.querySelector('[data-object-angle]').disabled)return;const values=objectAngleValues();if(await api('/api/model-object-angle',{asset_id:asset,object_index:Number(object.value),...values,expected_sha256:source.effective_sha256,proposed_sha256:proposalReport.proposed_sha256},{dialog:vectorDialog,success:'Model object rotated with stored normals. Save project to persist.'})){vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}};
    const objectAxisScaleTool=window.document.createElement('details');objectAxisScaleTool.innerHTML='<summary>Scale whole object by axis</summary><p>Scale all Current vertices around local origin or Current bounds center. Stored normals use inverse transpose and retain their original length before signed16 rounding. Zero normals stay zero. Positive integer percents only; overflow rejects the proposal. Preview both geometry and normal directions before Apply.</p>'+['X','Y','Z'].map(axis=>`<label>${axis} percent<input type="number" min="1" max="1000" step="1" value="100" aria-label="Object scale ${axis} percent"></label>`).join('')+'<label>Pivot<select aria-label="Object axis scale pivot"><option value="origin">Local origin</option><option value="center">Current bounds center</option></select></label><p data-object-axis-scale-report></p><button type="button" data-object-axis-scale>Apply reviewed object axis scale</button>';objectAngleTool.after(objectAxisScaleTool);
    const objectAxisScaleValues=()=>({percents:[...objectAxisScaleTool.querySelectorAll('input')].map(input=>input.value.trim()===''?NaN:Number(input.value)),pivot:objectAxisScaleTool.querySelector('select').value});let objectAxisScaleValid=false;
    const refreshObjectAxisScale=()=>{let changed=0;objectAxisScaleValid=false;try{const obj=document.objects[Number(object.value)],scaled=scaleObjectWords(obj,objectAxisScaleValues());changed=['vertices','normals'].reduce((n,kind)=>n+scaled[kind].filter((row,i)=>row.some((v,a)=>v!==obj[kind][i][a])).length,0);objectAxisScaleValid=changed>0&&!object.disabled;}catch{}objectAxisScaleTool.querySelector('[data-object-axis-scale-report]').textContent=objectAxisScaleValid?changed+' changed vector rows; preview before Apply.':'No eligible changed vectors; enter three bounded scale percents.';objectAxisScaleTool.querySelector('[data-object-axis-scale]').disabled=!objectAxisScaleValid||!proposalReport||proposalReport.operation!=='object_axis_scaling'||JSON.stringify(proposalReport.values)!==JSON.stringify(objectAxisScaleValues());};
    objectAxisScaleTool.ontoggle=()=>{if(vectorDialog.open)refreshObjectAxisScale();};objectAxisScaleTool.querySelector('[data-object-axis-scale]').onclick=async()=>{if(busy||!currentContext())return;refreshObjectAxisScale();if(objectAxisScaleTool.querySelector('[data-object-axis-scale]').disabled)return;const values=objectAxisScaleValues();if(await api('/api/model-object-axis-scale',{asset_id:asset,object_index:Number(object.value),...values,expected_sha256:source.effective_sha256,proposed_sha256:proposalReport.proposed_sha256},{dialog:vectorDialog,success:'Model object scaled with corrected normal directions. Save project to persist.'})){vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}};
    const objectMirrorTool=window.document.createElement('details');objectMirrorTool.innerHTML='<summary>Mirror whole object</summary><p>Reflect all Current vertices around an origin or bounds-center axis plane. Reflect stored normals about zero and reverse native face winding with its UV, color and normal-reference corners. Quad diagonals and packet layout stay fixed. Preview before Apply.</p><label>Axis<select aria-label="Object mirror axis"><option value="x">X</option><option value="y">Y</option><option value="z">Z</option></select></label><label>Pivot<select aria-label="Object mirror pivot"><option value="origin">Local origin</option><option value="center">Current bounds center</option></select></label><p data-object-mirror-report></p><button type="button" data-object-mirror>Apply reviewed object mirror</button>';objectAxisScaleTool.after(objectMirrorTool);
    const objectMirrorValues=()=>({axis:objectMirrorTool.querySelector('[aria-label="Object mirror axis"]').value,pivot:objectMirrorTool.querySelector('[aria-label="Object mirror pivot"]').value});let objectMirrorValid=false;
    const refreshObjectMirror=()=>{objectMirrorValid=false;try{mirrorObjectWords(document.objects[Number(object.value)],objectMirrorValues());objectMirrorValid=!object.disabled;}catch{}objectMirrorTool.querySelector('[data-object-mirror-report]').textContent=objectMirrorValid?'Vector bounds eligible; preview qualifies coupled native corners.':'No eligible object vectors; reflection exceeds signed16 or the object is held.';objectMirrorTool.querySelector('[data-object-mirror]').disabled=!objectMirrorValid||!proposalReport||proposalReport.operation!=='object_mirror'||!proposalReport.changes_from_current.length||JSON.stringify(proposalReport.values)!==JSON.stringify(objectMirrorValues());};objectMirrorTool.ontoggle=()=>{if(vectorDialog.open)refreshObjectMirror();};
    objectMirrorTool.querySelector('[data-object-mirror]').onclick=async()=>{if(busy||!currentContext())return;refreshObjectMirror();if(objectMirrorTool.querySelector('[data-object-mirror]').disabled)return;if(await api('/api/model-object-mirror',{asset_id:asset,object_index:Number(object.value),...objectMirrorValues(),expected_sha256:source.effective_sha256,proposed_sha256:proposalReport.proposed_sha256},{dialog:vectorDialog,success:'Model object mirrored with coupled face corners. Save project to persist.'})){vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}};
    const scaling=window.document.createElement('details');scaling.innerHTML='<summary>Scale whole object</summary><p>Scale vertices uniformly around the source-local origin. Positive integer percent 1–1000; 100 keeps the size. Coordinates round to the nearest integer, with halves away from zero. Normals, padding and topology remain unchanged.</p><label>Scale percent<input type="number" min="1" max="1000" step="1" value="100" required aria-label="Object scale percent"></label><p data-scale-report></p><button type="button" data-scale>Apply object scale</button>';
    form.append(scaling);const scalePercent=scaling.querySelector('input');
    const scaleVertex=(value,percent)=>Math.floor((Math.abs(value)*percent+50)/100)*(value<0?-1:1);
    const previewScale=()=>{const obj=document.objects[Number(object.value)],percent=Number(scalePercent.value),valid=scalePercent.value!==''&&scalePercent.checkValidity(),fits=valid&&(obj?.vertices??[]).every(vector=>vector.every(value=>{const scaled=scaleVertex(value,percent);return scaled>=-32768&&scaled<=32767;}));scaling.querySelector('[data-scale-report]').textContent=object.disabled?'Apply or discard the vector draft first.':!valid?'Enter an integer percent from 1 to 1000.':!fits?'Scale exceeds signed16 vertex values; nothing will be applied.':`${obj?.vertices.length??0} vertices · ${percent}% around the source-local origin · Normals unchanged`;scaling.querySelector('[data-scale]').disabled=object.disabled||!obj?.vertices.length||!fits;};
    form.addEventListener('click',previewScale);form.addEventListener('input',previewScale);form.addEventListener('change',previewScale);scaling.ontoggle=previewScale;
    scaling.querySelector('[data-scale]').onclick=async()=>{if(busy||object.disabled)return;previewScale();if(scaling.querySelector('[data-scale]').disabled)return;if(asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id]))return;if(await api('/api/model-object-scale',{asset_id:asset,object_index:Number(object.value),percent:Number(scalePercent.value),expected_sha256:source.effective_sha256},{dialog:vectorDialog,success:'Model object scaled. Save project to persist.'})){vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}};
    const normalLengthTool=window.document.createElement('details');normalLengthTool.innerHTML='<summary>Rescale stored normals in this object</summary><p>Retain each nonzero direction, with nearest-integer signed source coordinates. Zero normals stay zero; geometry, normal references and other objects stay unchanged. Encoded length alone does not establish retail lighting.</p><label>Target encoded length<input type="number" min="1" max="32767" step="1" value="4096" aria-label="Object normal length"></label><p data-normal-length-report></p><button type="button" data-normal-length>Apply normal rescaling</button>';scaling.after(normalLengthTool);
    const normalRebuildTool=window.document.createElement('details');normalRebuildTool.innerHTML='<summary>Rebuild stored normals from faces</summary><p>Area-weighted native triangles, preserving existing sharing and unreferenced normals. Encoded length 4096. Source Y points down. Degenerate lit triangles and cancelling shared directions refuse the whole proposal. Preview directions before Apply; retail lighting remains unverified.</p><label>Normal direction<select aria-label="Rebuilt normal direction"><option value="winding">Source winding cross product</option><option value="reverse">Reverse source winding</option></select></label><p data-normal-rebuild-report></p><button type="button" data-normal-rebuild disabled>Apply reviewed normal rebuild</button>';normalLengthTool.after(normalRebuildTool);
    const normalRebuildValues=()=>({direction:normalRebuildTool.querySelector('select').value});
    const refreshNormalRebuild=()=>{const reviewed=!object.disabled&&proposalReport?.operation==='normal_rebuild'&&proposalReport.object_index===Number(object.value)&&JSON.stringify(proposalReport.values)===JSON.stringify(normalRebuildValues())&&proposalReport.changes_from_current.length>0;normalRebuildTool.querySelector('[data-normal-rebuild]').disabled=!reviewed;normalRebuildTool.querySelector('[data-normal-rebuild-report]').textContent=reviewed?proposalReport.changes_from_current.length+' changed normal words; reviewed.':'Preview the exact Current face references before Apply.';};
    normalRebuildTool.querySelector('[data-normal-rebuild]').onclick=async()=>{if(busy||!currentContext())return;refreshNormalRebuild();if(normalRebuildTool.querySelector('[data-normal-rebuild]').disabled)return;if(await api('/api/model-object-normal-rebuild',{asset_id:asset,object_index:Number(object.value),...normalRebuildValues(),expected_sha256:source.effective_sha256,proposed_sha256:proposalReport.proposed_sha256},{dialog:vectorDialog,success:'Stored normals rebuilt from faces. Save project to persist.'})){vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}};
    const normalRotationTool=window.document.createElement('details');normalRotationTool.innerHTML='<summary>Rotate stored normals in this object</summary><p>Rotate all Current stored normal directions around source X/Y/Z, independently of geometry. Degrees round to 1/4096 turn; nearest signed16 words, halfway away from zero. Zero vectors stay zero. Normals are not regenerated from faces; lighting remains a source-direction diagnostic. Preview and compare before Apply.</p><label>Axis<select aria-label="Object normal rotation axis"><option value="x">X</option><option value="y">Y</option><option value="z">Z</option></select></label><label>Degrees<input type="number" min="-360" max="360" step="0.01" value="45" aria-label="Object normal rotation degrees"></label><p data-normal-rotation-report></p><button type="button" data-normal-rotation>Apply reviewed normal rotation</button>';normalLengthTool.after(normalRotationTool);
    const normalRotationValues=()=>({axis:normalRotationTool.querySelector('select').value,angle_units:normalAngleUnits(normalRotationTool.querySelector('input').value.trim()===''?NaN:Number(normalRotationTool.querySelector('input').value))});
    let normalRotationValid=false;
    const refreshNormalRotation=()=>{let changed=0;normalRotationValid=false;try{const words=document.objects[Number(object.value)]?.normals??[],values=normalRotationValues(),rotated=rotateStoredNormals(words,values.axis,values.angle_units);changed=rotated.filter((row,i)=>row.some((v,a)=>v!==words[i][a])).length;normalRotationValid=changed>0&&!object.disabled;}catch{}normalRotationTool.querySelector('[data-normal-rotation-report]').textContent=normalRotationValid?changed+' changed stored normals; preview before Apply.':'No eligible changed normal words; enter a bounded angle for an object with normals.';normalRotationTool.querySelector('[data-normal-rotation]').disabled=!normalRotationValid||!proposalReport||proposalReport.operation!=='normal_rotation_angle'||JSON.stringify(proposalReport.values)!==JSON.stringify(normalRotationValues());};
    normalRotationTool.ontoggle=()=>{if(vectorDialog.open)refreshNormalRotation();};
    normalRotationTool.querySelector('[data-normal-rotation]').onclick=async()=>{if(busy||!currentContext())return;refreshNormalRotation();if(normalRotationTool.querySelector('[data-normal-rotation]').disabled)return;const values=normalRotationValues();if(await api('/api/model-object-normal-angle',{asset_id:asset,object_index:Number(object.value),...values,expected_sha256:source.effective_sha256,proposed_sha256:proposalReport.proposed_sha256},{dialog:vectorDialog,success:'Stored normal directions rotated. Save project to persist.'})){vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}};
    const normalLengthInput=normalLengthTool.querySelector('input');
    const previewNormalLength=()=>{const normals=document.objects[Number(object.value)]?.normals??[],length=Number(normalLengthInput.value);let changed=0,validLength=true;try{for(const vector of normals){const scaled=rescaleStoredNormal(vector,length);changed+=scaled.some((v,a)=>v!==vector[a]);}}catch{validLength=false;}normalLengthTool.querySelector('[data-normal-length-report]').textContent=object.disabled?'Apply or discard the vector draft first.':!validLength?'Enter an integer encoded length1–32767.':`${normals.length} stored normals · ${normals.filter(v=>v.every(a=>a===0)).length} zero vectors retained · ${changed} changed vectors`;normalLengthTool.querySelector('[data-normal-length]').disabled=object.disabled||!validLength||!changed;};
    for(const type of ['click','input','change'])form.addEventListener(type,previewNormalLength);normalLengthTool.ontoggle=previewNormalLength;
    normalLengthTool.querySelector('[data-normal-length]').onclick=async()=>{if(busy||object.disabled)return;previewNormalLength();if(normalLengthTool.querySelector('[data-normal-length]').disabled||!currentContext())return;if(await api('/api/model-object-normal-length',{asset_id:asset,object_index:Number(object.value),length:Number(normalLengthInput.value),expected_sha256:source.effective_sha256},{dialog:vectorDialog,success:'Stored model normals rescaled. Save project to persist.'})){vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}};
    const topologyLocked=state.model_overrides?.[asset]?.format==='tmd-face-removal-v1';
    const normalRetargetTool=window.document.createElement('details');normalRetargetTool.innerHTML='<summary>Retarget uses of this normal in this object</summary><p>Select Normals and the Current source normal index above. Replace every matching stored reference in this object with another existing normal. Flat operands affect every face corner; Gouraud operands affect their own corner. Coordinates, geometry and other references stay fixed. Preview must qualify the exact users before Apply.</p><label>Target normal index<input type="number" min="0" max="8191" step="1" value="0" aria-label="Retarget normal index"></label><p data-normal-retarget-report></p><button type="button" data-normal-retarget>Apply reviewed normal retargeting</button>';normalLengthTool.after(normalRetargetTool);
    const normalRetargetInput=normalRetargetTool.querySelector('input');
    const retargetValues=()=>({from_index:Number(index.value),to_index:Number(normalRetargetInput.value)});
    const retargetValid=()=>{const count=document.objects[Number(object.value)]?.normals.length??0,v=retargetValues();return kind.value==='normals'&&valid&&!object.disabled&&normalRetargetInput.value.trim()!==''&&[v.from_index,v.to_index].every(n=>Number.isInteger(n)&&n>=0&&n<Math.min(count,8192))&&v.from_index!==v.to_index;};
    const refreshNormalRetarget=()=>{const v=retargetValues(),reviewed=retargetValid()&&proposalReport?.operation==='normal_references'&&proposalReport.object_index===Number(object.value)&&JSON.stringify(proposalReport.values)===JSON.stringify(v)&&proposalReport.changes_from_current.length>0;normalRetargetTool.querySelector('[data-normal-retarget]').disabled=!reviewed;normalRetargetTool.querySelector('[data-normal-retarget-report]').textContent=!retargetValid()?'Select an inspected normal and a different existing target; apply or discard a vector draft first.':reviewed?`${proposalReport.changes_from_current.length} qualified reference words: normal ${v.from_index} → ${v.to_index}`:'Preview the exact Current users before Apply.';};
    for(const type of ['click','input','change'])form.addEventListener(type,refreshNormalRetarget);normalRetargetTool.ontoggle=refreshNormalRetarget;
    normalRetargetTool.querySelector('[data-normal-retarget]').onclick=async()=>{refreshNormalRetarget();if(busy||!currentContext()||normalRetargetTool.querySelector('[data-normal-retarget]').disabled)return;const v=retargetValues();if(await api('/api/model-object-normal-references',{asset_id:asset,object_index:Number(object.value),...v,expected_sha256:source.effective_sha256,proposed_sha256:proposalReport.proposed_sha256},{dialog:vectorDialog,success:'Normal references retargeted. Save project to persist.'})){vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}};
    const vertexRetargetTool=window.document.createElement('details');vertexRetargetTool.innerHTML='<summary>Retarget uses of this vertex in this object</summary><p>Select Vertices and the Current source vertex index above. Replace every matching stored reference in this object with another existing vertex. Coordinates and stored normals stay fixed; face corners move to the target vertex. Faces may collapse. Counts, packet layout and other objects stay fixed. Preview must qualify the exact users before Apply.</p><label>Target vertex index<input type="number" min="0" max="8191" step="1" value="0" aria-label="Retarget vertex index"></label><p data-vertex-retarget-report></p><button type="button" data-vertex-retarget>Apply reviewed vertex retargeting</button>';normalRetargetTool.after(vertexRetargetTool);
    const vertexRetargetInput=vertexRetargetTool.querySelector('input');
    const vertexRetargetValues=()=>({from_index:Number(index.value),to_index:Number(vertexRetargetInput.value)});
    const vertexRetargetValid=()=>{const count=document.objects[Number(object.value)]?.vertices.length??0,v=vertexRetargetValues();return kind.value==='vertices'&&valid&&!object.disabled&&vertexRetargetInput.value.trim()!==''&&[v.from_index,v.to_index].every(n=>Number.isInteger(n)&&n>=0&&n<Math.min(count,8192))&&v.from_index!==v.to_index;};
    const refreshVertexRetarget=()=>{const v=vertexRetargetValues(),reviewed=vertexRetargetValid()&&proposalReport?.operation==='vertex_references'&&proposalReport.object_index===Number(object.value)&&JSON.stringify(proposalReport.values)===JSON.stringify(v)&&proposalReport.changes_from_current.length>0;vertexRetargetTool.querySelector('[data-vertex-retarget]').disabled=!reviewed;vertexRetargetTool.querySelector('[data-vertex-retarget-report]').textContent=!vertexRetargetValid()?'Select an inspected vertex and a different existing target; apply or discard a vector draft first.':reviewed?`${proposalReport.changes_from_current.length} qualified reference words: vertex ${v.from_index} → ${v.to_index}`:'Preview the exact Current users before Apply.';};
    for(const type of ['click','input','change'])form.addEventListener(type,refreshVertexRetarget);vertexRetargetTool.ontoggle=refreshVertexRetarget;
    vertexRetargetTool.querySelector('[data-vertex-retarget]').onclick=async()=>{refreshVertexRetarget();if(busy||!currentContext()||vertexRetargetTool.querySelector('[data-vertex-retarget]').disabled)return;const v=vertexRetargetValues();if(await api('/api/model-object-vertex-references',{asset_id:asset,object_index:Number(object.value),...v,expected_sha256:source.effective_sha256,proposed_sha256:proposalReport.proposed_sha256},{dialog:vectorDialog,success:'Vertex references retargeted. Save project to persist.'})){vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}};
    if(topologyLocked){const note=window.document.createElement('p');note.textContent='Face removal is retained. Vertex and normal tables keep their Retail indices. Reference lookup shows exact Current-to-Retail face identities, including removed Retail faces. Retained faces can be inspected and edited using these mapped identities. Retargeting changes only qualified Current users and preserves removed-face identities.';form.append(note);}
    const proposal=window.document.createElement('section');proposal.hidden=true;proposal.innerHTML='<h3>Object preview · not applied</h3><p data-proposal-status></p><label>Preview layer<select aria-label="Object preview layer"><option value="proposed">Proposed</option><option value="current">Inspected current</option></select></label><p>Drag to orbit · Scroll to zoom · Object-local Y-down coordinates. Both layers share camera framing. Preview does not change history or saved assets; Apply remains explicit.</p>';
    if(!objectProposalCanvas){objectProposalCanvas=window.document.createElement('canvas');objectProposalCanvas.style.cssText='display:block;width:100%;height:300px;touch-action:none';objectProposalCanvas.setAttribute('aria-label','Object transform preview');}
    const normalDiagnosticInput=window.document.createElement('input');normalDiagnosticInput.type='checkbox';normalDiagnosticInput.setAttribute('aria-label','Object preview normal directions');const normalDiagnosticLabel=window.document.createElement('label');normalDiagnosticLabel.textContent='Source normal directions · not retail lighting';Object.assign(normalDiagnosticInput.style,{width:'auto',margin:'0'});Object.assign(normalDiagnosticLabel.style,{display:'inline-flex',flexDirection:'row',alignItems:'center',gap:'8px',margin:'10px 0'});normalDiagnosticLabel.prepend(normalDiagnosticInput);proposal.append(normalDiagnosticLabel,objectProposalCanvas);form.append(proposal);normalDiagnosticInput.onchange=()=>drawProposal();
    let proposalReport=null,proposalRequest=0,proposalView=null,proposalDrag=null;
    const sceneProposal=window.document.createElement('div');sceneProposal.innerHTML='<label>Scene instance<select aria-label="Proposed shape scene instance"></select></label><button type="button">Inspect proposed shape in scene</button><p>Choose one instance or all supported instances. Applying the model changes its shared asset. Source placement and supported pose are retained; gameplay visibility remains unverified.</p>';proposal.append(sceneProposal);
    const instanceSelect=sceneProposal.querySelector('select'),inspectSceneButton=sceneProposal.querySelector('button');
    const updateProposalInstances=()=>{
      instanceSelect.replaceChildren();
      const available=scenePreviewCurrent()&&sceneRepresentation==='authored'?(scenePreview.entities??[]).filter(e=>e.asset_id===asset&&e.renderable):[];
      for(const item of available){const option=window.document.createElement('option');option.value=item.entity_id;option.textContent=item.name??item.entity_id;instanceSelect.append(option);}
      if(available.length){const option=window.document.createElement('option');option.value='all-instances';option.textContent=`All supported model instances (${available.length})`;instanceSelect.append(option);}
      if(available.some(e=>e.entity_id===environmentSelection))instanceSelect.value=environmentSelection;
      inspectSceneButton.disabled=!available.length;sceneProposal.hidden=!available.length;
    };
    inspectSceneButton.onclick=async()=>{
      if(busy||!currentContext()||!proposalReport||!scenePreviewCurrent()||sceneRepresentation!=='authored')return;
      const inspected=proposalReport,request=proposalRequest,loadedKey=sceneKey,allInstances=instanceSelect.value==='all-instances',entityId=allInstances?instanceSelect.options[0].value:instanceSelect.value;
      setBusy(true);
      try{
        const response=await fetch('/api/model-object-scene-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:asset,object_index:inspected.object_index,operation:inspected.operation,values:inspected.values,expected_sha256:source.effective_sha256,entity_id:entityId,all_instances:allInstances,source_key:scenePreview.project_source_key})}),report=await response.json();
        if(request!==proposalRequest||proposalReport!==inspected||!currentContext()||!scenePreviewCurrent()||loadedKey!==sceneKey)return;
        if(!response.ok||report.error)throw new Error(report.error||'Scene proposal failed');
        if(report.entity_id!==entityId||report.asset_id!==asset||report.project_source_key!==scenePreview.project_source_key||report.proposed_sha256!==inspected.proposed_sha256)throw new Error('Scene proposal differs from inspected geometry');
        stopScenePosePlayback();const isolated=sceneShapeProposalDocument(scenePreview,report,entityId),failures=sceneRenderer.load(isolated.document);if(failures.length)throw new Error(failures.join('; '));
        const returnToVectors=()=>{if(asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id])||loadedKey!==sceneKey)return false;$('model-dialog').showModal();vectorDialog.showModal();normalUsers.refresh();vertexUsers.refresh();return true;};
        scenePose={key:sceneKey,geometryKey:isolated.geometryKey,preview:report.preview,returnToFile:returnToVectors,name:'Proposed shape · not applied'};
        scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`Proposed shape · not applied · ${sceneShapeProposalLabel(report,entityId)} · ${inspected.operation}`;
        configureSceneInspectionComparison(isolated.document);
        for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('label')])control.hidden=true;
        const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to model vectors';
        vectorDialog.close();$('model-dialog').close();frameShapeProposal(report,entityId);draw();
      }catch(error){if(currentContext()){clearScenePose();form.querySelector('[data-error]').textContent=error.message;draw();}}finally{setBusy(false);}
    };

    const normalUsersSourceKey=state.scene_preview_source_key;
    const normalUsers=mountNormalUsers({host:form,assetId:asset,expectedSha:source.effective_sha256,sourceKey:normalUsersSourceKey,getSelection:()=>kind.value==='normals'&&valid?{object_index:Number(object.value),normal_index:Number(index.value)}:null,isCurrent:()=>vectorDialog.open&&asset===modelAssetId&&context===JSON.stringify([state.project.path,state.scene.id])&&!object.disabled&&state.scene_preview_source_key===normalUsersSourceKey,onSelect:async row=>{vectorDialog.close();await inspectModelPrimitives(row);}});
    const vertexUsers=mountVertexUsers({host:form,assetId:asset,expectedSha:source.effective_sha256,sourceKey:normalUsersSourceKey,getSelection:()=>kind.value==='vertices'&&valid?{object_index:Number(object.value),vertex_index:Number(index.value)}:null,isCurrent:()=>vectorDialog.open&&asset===modelAssetId&&context===JSON.stringify([state.project.path,state.scene.id])&&!object.disabled&&state.scene_preview_source_key===normalUsersSourceKey,onSelect:async row=>{vectorDialog.close();await inspectModelPrimitives(row);}});
    for(const type of ['input','change','click'])form.addEventListener(type,()=>{normalUsers.refresh();vertexUsers.refresh();});
    const currentContext=()=>vectorDialog.open&&asset===modelAssetId&&context===JSON.stringify([state.project.path,state.scene.id])&&!object.disabled;
    const invalidateProposal=()=>{proposalRequest++;proposalReport=null;proposal.hidden=true;refreshNormalRetarget();refreshVertexRetarget();refreshNormalRotation();refreshNormalRebuild();refreshObjectAngle();refreshObjectAxisScale();refreshObjectMirror();};
    const drawProposal=()=>{
      if(!proposalReport||proposal.hidden||!currentContext()||!objectProposalRenderer)return;
      const rect=objectProposalCanvas.getBoundingClientRect(),c=Math.cos(proposalView.yaw),s=Math.sin(proposalView.yaw),cp=Math.cos(proposalView.pitch),sp=Math.sin(proposalView.pitch);
      objectProposalRenderer.draw({normalDiagnostic:normalDiagnosticInput.checked,width:rect.width,height:rect.height,positions:new Map(),grid:false,wireframe:true,camera:{target:{x:proposalView.center[0],y:-proposalView.center[1],z:proposalView.center[2]},distance:proposalView.radius*4/proposalView.zoom},basis:{right:{x:c,y:0,z:s},up:{x:sp*s,y:cp,z:-sp*c},forward:{x:-cp*s,y:sp,z:cp*c}}});
    };
    const loadProposal=()=>{
      if(!proposalReport||!currentContext())return;
      const data=proposalReport[proposal.querySelector('select').value==='current'?'current_preview':'preview'],obj=data.objects[proposalReport.object_index];
      const preview={...data,triangles:data.triangles.slice(obj.triangle_start,obj.triangle_start+obj.triangle_count),triangle_colors:data.triangle_colors?.slice(obj.triangle_start,obj.triangle_start+obj.triangle_count),triangle_uvs:data.triangle_uvs?.slice(obj.triangle_start,obj.triangle_start+obj.triangle_count),triangle_materials:data.triangle_materials?.slice(obj.triangle_start,obj.triangle_start+obj.triangle_count),triangle_normals:data.triangle_normals?.slice(obj.triangle_start,obj.triangle_start+obj.triangle_count)};
      const failures=objectProposalRenderer.load({assets:[{geometry_key:'object-proposal',preview}],entities:[{entity_id:'object-proposal',geometry_key:'object-proposal',renderable:true,model_to_scene:[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]}]});
      if(failures.length)throw new Error(failures.join('; '));drawProposal();
    };
    proposal.querySelector('select').onchange=()=>{try{loadProposal();}catch(error){form.querySelector('[data-error]').textContent=error.message;invalidateProposal();}};
    objectProposalCanvas.onpointerdown=event=>{objectProposalCanvas.setPointerCapture(event.pointerId);proposalDrag={x:event.clientX,y:event.clientY};};
    objectProposalCanvas.onpointermove=event=>{if(!proposalDrag||!proposalView)return;proposalView.yaw+=(event.clientX-proposalDrag.x)*.009;proposalView.pitch+=(event.clientY-proposalDrag.y)*.009;proposalDrag={x:event.clientX,y:event.clientY};drawProposal();};
    objectProposalCanvas.onpointerup=objectProposalCanvas.onpointercancel=()=>proposalDrag=null;
    objectProposalCanvas.onwheel=event=>{event.preventDefault();if(proposalView){proposalView.zoom=Math.max(.15,Math.min(2.5,proposalView.zoom*Math.exp(-event.deltaY*.001)));drawProposal();}};
    vectorDialog.onclose=()=>{invalidateProposal();normalUsers.close();vertexUsers.close();};
    // A proposal is tied to exact inputs. No old preview remains visible after a draft changes.
    for(const type of ['input','change'])form.addEventListener(type,event=>{if(event.target!==proposal.querySelector('select')&&event.target!==instanceSelect&&event.target!==normalDiagnosticInput)invalidateProposal();});
    form.querySelector('[data-retail-vector]').addEventListener('click',invalidateProposal);
    form.querySelector('[data-discard]').addEventListener('click',invalidateProposal);
    for(const [container,operation,applySelector,getValues,refresh] of [
      [translation,'translation','[data-translate]',()=>({offset:offsetValues()}),previewOffset],
      [rotation,'rotation','[data-rotate]',()=>({axis:rotationAxis.value,quarter_turns:Number(turnControl.value)}),previewRotation],
      [scaling,'scale','[data-scale]',()=>({percent:Number(scalePercent.value)}),previewScale],
      [objectMirrorTool,'object_mirror','[data-object-mirror]',objectMirrorValues,refreshObjectMirror],
      [objectAxisScaleTool,'object_axis_scaling','[data-object-axis-scale]',objectAxisScaleValues,refreshObjectAxisScale],
      [objectAngleTool,'object_rotation_angle','[data-object-angle]',objectAngleValues,refreshObjectAngle],
      [normalRebuildTool,'normal_rebuild','[data-normal-rebuild]',normalRebuildValues,refreshNormalRebuild],
      [normalRotationTool,'normal_rotation_angle','[data-normal-rotation]',normalRotationValues,refreshNormalRotation],
      [normalLengthTool,'normal_length','[data-normal-length]',()=>({length:Number(normalLengthInput.value)}),previewNormalLength],
      [normalRetargetTool,'normal_references','[data-normal-retarget]',retargetValues,refreshNormalRetarget],
      [vertexRetargetTool,'vertex_references','[data-vertex-retarget]',vertexRetargetValues,refreshVertexRetarget]]){
      const button=window.document.createElement('button');button.type='button';button.textContent=operation==='normal_rebuild'?'Preview normal rebuild':operation==='object_mirror'?'Preview whole object mirror':operation==='object_axis_scaling'?'Preview whole object axis scale':operation==='object_rotation_angle'?'Preview whole object angle':operation==='normal_rotation_angle'?'Preview normal rotation':operation==='normal_length'?'Preview normal rescaling':operation==='normal_references'?'Preview normal retargeting':operation==='vertex_references'?'Preview vertex retargeting':'Preview object '+operation;container.append(button);
      button.onclick=async()=>{
        refresh();if(busy||!currentContext()||(operation==='normal_rebuild'?object.disabled:operation==='object_mirror'?!objectMirrorValid:operation==='object_axis_scaling'?!objectAxisScaleValid:operation==='object_rotation_angle'?!objectAngleValid:operation==='normal_rotation_angle'?!normalRotationValid:operation==='normal_references'?!retargetValid():operation==='vertex_references'?!vertexRetargetValid():container.querySelector(applySelector).disabled))return;
        const request=++proposalRequest;proposalReport=null;proposal.hidden=true;form.querySelector('[data-error]').textContent='';setBusy(true);
        try{
          let users=null;
          if(operation==='normal_references'){const binding={asset_id:asset,object_index:Number(object.value),normal_index:getValues().from_index,expected_sha256:source.effective_sha256,source_key:normalUsersSourceKey};const response=await fetch('/api/model-normal-users',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(binding)}),value=await response.json();if(!response.ok||value.error)throw new Error(value.error||'Normal users unavailable');users=decodeNormalUsers(value,binding);}
          if(operation==='vertex_references'){const binding={asset_id:asset,object_index:Number(object.value),vertex_index:getValues().from_index,expected_sha256:source.effective_sha256,source_key:normalUsersSourceKey};const response=await fetch('/api/model-vertex-users',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(binding)}),value=await response.json();if(!response.ok||value.error)throw new Error(value.error||'Vertex users unavailable');users=decodeVertexUsers(value,binding);}
          const response=await fetch('/api/model-object-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:asset,object_index:Number(object.value),operation,values:getValues(),expected_sha256:source.effective_sha256})}),report=await response.json();
          if(request!==proposalRequest||!currentContext())return;
          if(!response.ok||report.error)throw new Error(report.error||'Object preview failed');
          if(report.asset_id!==asset||report.effective_sha256!==source.effective_sha256||report.object_index!==Number(object.value)||report.operation!==operation||report.project_changed!==false)throw new Error('Object preview context differs from inspection');
          if(operation==='object_mirror')qualifyObjectMirror(report,document.objects[Number(object.value)],getValues());
          if(operation==='object_axis_scaling')qualifyObjectAxisScale(report,document.objects[Number(object.value)],getValues());
          if(operation==='object_rotation_angle')qualifyObjectAngle(report,document.objects[Number(object.value)],getValues());
          if(operation==='normal_rebuild')qualifyNormalRebuild(report,document.objects[Number(object.value)],getValues());
          if(operation==='normal_rotation_angle')qualifyNormalRotation(report,document.objects[Number(object.value)].normals,getValues());
          if(operation==='normal_references')validateNormalRetarget(report,users,getValues().to_index);
          if(operation==='vertex_references')validateVertexRetarget(report,users,getValues().to_index);
          if(!objectProposalRenderer){const module=await import('/scene-renderer.js');if(request!==proposalRequest||!currentContext())return;objectProposalRenderer=new module.SceneRenderer(objectProposalCanvas,message=>{if(message&&vectorDialog.open)form.querySelector('[data-error]').textContent=message;});}
          objectProposalRenderer.onStatus=message=>{if(message&&vectorDialog.open)form.querySelector('[data-error]').textContent=message;else drawProposal();};
          const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
          for(const data of [report.preview,report.current_preview]){const obj=data.objects[report.object_index];for(const v of data.vertices.slice(obj.vertex_start,obj.vertex_start+obj.vertex_count))for(let a=0;a<3;a++){min[a]=Math.min(min[a],v[a]);max[a]=Math.max(max[a],v[a]);}}
          proposalView={center:min.map((v,a)=>(v+max[a])/2),radius:Math.max(1,Math.hypot(...max.map((v,a)=>v-min[a]))/2),yaw:.6,pitch:.4,zoom:1};
          report.values=getValues();proposalReport=report;normalDiagnosticInput.checked=operation==='normal_rebuild'||operation==='object_mirror'||operation==='object_axis_scaling'||operation==='normal_references'||operation==='normal_rotation_angle'||operation==='object_rotation_angle';refreshNormalRetarget();refreshVertexRetarget();refreshNormalRotation();refreshNormalRebuild();refreshObjectAngle();refreshObjectAxisScale();refreshObjectMirror();proposal.hidden=false;updateProposalInstances();proposal.querySelector('select').value='proposed';proposal.querySelector('[data-proposal-status]').textContent=`Object ${report.object_index} · ${operation==='normal_rebuild'?'Rebuilt normals':operation==='object_mirror'?'Object mirror':operation==='object_axis_scaling'?'Object axis scale':operation==='normal_rotation_angle'?'Normal rotation':operation==='normal_length'?'Normal rescaling':operation==='normal_references'?'Normal retargeting':operation==='vertex_references'?'Vertex retargeting':operation} · ${report.changes_from_current.length} scalar changes from inspected current · not applied`;
          proposal.scrollIntoView({block:'nearest'});loadProposal();
        }catch(error){if(request===proposalRequest&&currentContext()){form.querySelector('[data-error]').textContent=error.message;invalidateProposal();}}finally{setBusy(false);}
      };
    }
    form.querySelector('[data-discard]').onclick=()=>{load();previewOffset();previewRotation();previewScale();};form.querySelector('[data-close]').onclick=()=>vectorDialog.close();

    form.onsubmit=async event=>{event.preventDefault();if(busy||!valid||!form.reportValidity())return;if(asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id])){form.querySelector('[data-error]').textContent='Model context changed; reopen the editor.';return;}
      if(await api('/api/model-vector',{asset_id:asset,object_index:Number(object.value),kind:kind.value,vector_index:Number(index.value),values:xyz.map(input=>Number(input.value)),expected_sha256:source.effective_sha256},{dialog:vectorDialog,success:'Model vector updated. Save project to persist.'})){vectorDialog.close();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}
    };
    if(initial){const k=initial.kind==='vertex'?'vertices':initial.kind==='normal'?'normals':null;if(!k||!Number.isInteger(initial.object_index)||!Number.isInteger(initial.vector_index)||!document.objects[initial.object_index]?.[k]?.[initial.vector_index])throw new Error('The reported vector is unavailable in this model.');object.value=String(initial.object_index);kind.value=k;index.value=String(initial.vector_index);}
    load();previewOffset();previewRotation();previewScale();previewNormalLength();refreshNormalRetarget();refreshVertexRetarget();vectorDialog.showModal();normalUsers.refresh();vertexUsers.refresh();
  }catch(error){$('model-error').textContent=error.message;}finally{setBusy(false);}
}
$('shape-vectors').onclick=()=>openModelVectors();
const modelVertexMoveButton=document.createElement('button');modelVertexMoveButton.id='shape-vertex-move';modelVertexMoveButton.textContent='Move vertices in 3D';$('shape-vectors').after(modelVertexMoveButton);modelVertexMoveButton.onclick=()=>{if(busy||shapeDraft||state.project?.mode!=='edit')return;openVertexMovement({object_index:Number($('model-object').value),vector_index:0});};
let modelPrimitiveEditor=null;
const primitiveContext=()=>({projectPath:state.project.path,sceneId:state.scene?.id??null,mode:state.project.mode,sourceKey:state.scene_preview_source_key});
async function inspectModelPrimitives(initial=null){
  if(busy||!modelAssetId||shapeDraft||state.project.mode!=='edit')return;
  const asset=modelAssetId,context=JSON.stringify([state.project.path,state.scene.id]);let applied=false,normalNavigation=false;
  modelPrimitiveEditor?.dispose();
  modelPrimitiveEditor=await openModelPrimitiveEditor({assetId:asset,initial:initial?{object_index:initial.object_index,primitive_index:initial.primitive_index}:null,getContext:primitiveContext,busy:()=>busy,setBusy,
    onError:error=>notify(error.message??String(error),true),
    onApplied:next=>{applied=true;state=next;render();notify('Model faces updated. Save project to persist.');},
    onInspectNormal:async(target,source)=>{if(busy||asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id])||source.project_source_key!==state.scene_preview_source_key)return false;normalNavigation=true;modelPrimitiveEditor?.dispose();await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');if(asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id])||source.project_source_key!==state.scene_preview_source_key)return false;await openModelVectors(target);return true;},
    onScenePreview:async(report,edits,source,{returnToEditor,faceSelection=null,materialEdits=[]})=>{
      if(!scenePreviewCurrent()||sceneRepresentation!=='authored'||scenePreview.project_source_key!==source.project_source_key)throw new Error('Load the current authored scene before inspecting proposed faces.');
      const instances=scenePreview.entities.filter(e=>e.asset_id===asset&&e.renderable);
      if(!instances.length)throw new Error('This model has no supported scene instances.');
      const entityId=instances.some(e=>e.entity_id===environmentSelection)?environmentSelection:instances[0].entity_id,loadedKey=sceneKey;
      setBusy(true);try{
      const response=await fetch(materialEdits.length?'/api/model-texture-assignment-scene-preview':'/api/model-primitive-scene-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(materialEdits.length?{asset_id:asset,expected_sha256:source.effective_sha256,source_key:source.project_source_key,primitive_edits:edits,material_edits:materialEdits,review_key:report.review_key,entity_id:entityId,all_instances:true}:{asset_id:asset,expected_sha256:source.effective_sha256,source_key:source.project_source_key,edits,proposed_sha256:report.proposed_sha256,entity_id:entityId,all_instances:true})}),posed=await response.json();
      if(!response.ok||posed.error)throw new Error(posed.error||'Scene face proposal failed');
      if(!modelPrimitiveEditor?.dialog.open||context!==JSON.stringify([state.project.path,state.scene.id])||loadedKey!==sceneKey||!scenePreviewCurrent()||posed.project_source_key!==source.project_source_key||posed.proposed_sha256!==report.proposed_sha256)throw new Error('Scene changed during face proposal inspection.');
      if(materialEdits.length&&Object.entries(report).some(([key,value])=>!['current_preview','preview'].includes(key)&&JSON.stringify(posed[key])!==JSON.stringify(value)))throw new Error('Combined scene audit differs from the accepted face/material review.');
      stopScenePosePlayback();const displayed=faceSelection?highlightSceneFaceProposal(posed,source,faceSelection):posed,currentDocument=faceSelection?highlightSceneFaceDocument(scenePreview,source,faceSelection):null,isolated=sceneShapeProposalDocument(scenePreview,displayed,entityId),failures=sceneRenderer.load(isolated.document);if(failures.length)throw new Error(failures.join('; '));
      const back=()=>{if(context!==JSON.stringify([state.project.path,state.scene.id])||loadedKey!==sceneKey||state.scene_preview_source_key!==source.project_source_key)return false;$('model-dialog').showModal();return returnToEditor();};
      scenePose={currentDocument,faceSelectionHighlight:!!faceSelection,inspectionEntityIds:posed.proposal_instances.map(row=>row.entity_id),key:sceneKey,geometryKey:isolated.geometryKey,preview:displayed.preview,name:materialEdits.length?'Proposed faces and texture bindings - not applied':'Proposed faces · not applied',returnToFile:back,afterRestore:back};
      scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`${materialEdits.length?'Proposed faces and texture bindings':'Proposed faces'} · not applied · ${sceneShapeProposalLabel(posed,entityId)}${faceSelection?' - '+faceSelection.face_count+' native faces highlighted yellow (display only)':''}`;configureSceneInspectionComparison(isolated.document);
      for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('label')])control.hidden=true;
      const button=scenePoseBar.querySelector('[data-return-file]');button.hidden=false;button.textContent='Return to face editor';
      $('model-dialog').close();frameShapeProposal(posed,entityId);draw();return {restore:()=>{clearScenePose();draw();}};
      }finally{setBusy(false);}
    }});
  if(!modelPrimitiveEditor)return;
  const owned=modelPrimitiveEditor;
  owned.dialog.addEventListener('close',()=>{if(owned.dialog.dataset.sceneInspection==='true')return;if(!normalNavigation&&applied&&context===JSON.stringify([state.project.path,state.scene.id])&&modelAssetId===asset)setTimeout(()=>{if(!busy&&$('model-dialog').open)openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');},0);});
}
$('shape-primitives').onclick=()=>inspectModelPrimitives();

async function openModel(assetId,clipId=null,entityId=null,shapeLayer='imported',inspectionEntityId=null,preparedPreview=null,returnToFile=null,witnessTarget=null){
  if($('model-dialog').open&&$('shape-file').files?.length){$('model-error').textContent='Apply or discard the selected shape file before changing the model view.';$('animation-clip').value=model?.animation?.clip_id??'';return;}
  if(busy)return;stopAnimation();setBusy(true);$('model-error').textContent='';$('animation-clip').disabled=true;const request=++modelRequest,requestedSceneContext=sceneRequestKey();
  try{
    let data=preparedPreview;
    if(!data){
    const response=await fetch(shapeLayer==='authored'?'/api/model-shape-preview':entityId?(clipId==='authored-initial-animation'?'/api/actor-initial-animation-preview':clipId==='authored-appearance'?'/api/actor-appearance-preview':'/api/actor-animation-preview'):clipId?'/api/animation-preview':'/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(entityId?{entity_id:entityId,...(clipId==='authored-channels'?{representation:'authored'}:{})}:{asset_id:assetId,...(clipId?{clip_id:clipId}:{})})});
    data=await response.json();if(!response.ok||data.error)throw new Error(typeof data.error==='string'?data.error:JSON.stringify(data.error ?? data));
    }
    if(!Array.isArray(data.vertices)||!Array.isArray(data.triangles)||!Array.isArray(data.objects))throw new Error('Model service returned no decoded geometry.');
    if(request!==modelRequest)return;
    if(clipId && (!Array.isArray(data.frames) || !data.frames.length || data.frames.length*data.vertices.length>1000000 || data.frames.some(frame=>frame.coordinate_system!=='retail_psx_actor_local_y_down'||!Array.isArray(frame.vertices)||frame.vertices.length!==data.vertices.length||frame.vertices.some(v=>!Array.isArray(v)||v.length!==3||!v.every(numeric)))))throw new Error('Animation service returned an invalid or oversized posed vertex stream.');
    model=data;modelFileReturn=returnToFile;modelSceneContext=requestedSceneContext;modelAssetId=assetId;modelEntityId=entityId;modelSceneEntityId=witnessTarget?null:inspectionEntityId?.startsWith('authored-actor://')?npcAnimationSceneTarget(state,scenePreview,data,entityId,inspectionEntityId):entityId??inspectionEntityId;animationFrame=0;$('model-dialog').querySelector('h2').textContent=entityId?`${entities().find(entity=>entity.id===entityId)?.name ?? entityId} · ${clipId==='allocated-record-edit-preview'?'Proposed retained content · not applied':clipId==='allocated-assignment-preview'?'Proposed initial assignment · not applied':clipId==='authored-allocated-animation'?'Assigned allocated initial clip':clipId==='allocated-record'?'Saved retained clip':clipId==='allocation-preview'?'Proposed allocated clip · not applied':clipId==='file-preview'?'Proposed file animation · not applied':clipId==='authored-initial-animation'?'Assigned initial animation':clipId==='authored-appearance'?'Authored appearance':clipId==='authored-channels'?'Authored animation':'Imported animation'}`:assetId.split('/').slice(-2).join(' / ');
    modelTextures=new Map();$('model-textures').replaceChildren();
    for(const texture of model.textures ?? []){
      const card=document.createElement('div');card.className='texture-card';
      if(texture.status==='address_match' && texture.rgba_base64){
        const bytes=Uint8ClampedArray.from(atob(texture.rgba_base64),c=>c.charCodeAt(0));
        if(bytes.length!==texture.width*texture.height*4 || bytes.length>2*1024*1024)throw new Error('Invalid decoded texture size');
        const image=document.createElement('canvas');image.width=texture.width;image.height=texture.height;image.getContext('2d').putImageData(new ImageData(bytes,texture.width,texture.height),0,0);card.append(image);modelTextures.set(texture.material_index,{image,origin:texture.uv_origin});
      }
      const statusLabel={address_match:'Matched texture',missing:'Texture not found',ambiguous:'Multiple possible textures',unsupported:'Unsupported texture',untextured:'Vertex colors'}[texture.status] ?? 'Texture unavailable';
      const label=document.createElement('span');label.textContent=`Material ${texture.material_index} · ${statusLabel}${texture.width?' · '+texture.width+'×'+texture.height:''}`;card.append(label);card.title=texture.reason ?? 'Static texture addresses; runtime residency is not confirmed'; $('model-textures').append(card);
    }
    $('model-description').textContent=`Drag to orbit · Scroll to zoom · Wireframe + Shift-click to inspect an unposed vertex (includes hidden vertices) · ${clipId==='file-preview'?'Proposed file animation · not applied':clipId?'Decoded rigid animation pose':shapeLayer==='authored'?'Authored object-local shape · Unposed':'Retail object-local geometry · Unposed'} · ${modelTextures.size?(model.texture_scope==='field_party'?'Shared party texture bank':'Static texture address matches'):'Vertex colors'} · Approximate blends; no texture-window or animated palette reconstruction`;
    $('model-object').replaceChildren();
    if(model.frames?.length){const all=document.createElement('option');all.value='all';all.textContent='Animated assembly · supported objects';$('model-object').append(all);}
    for(let index=0;index<model.objects.length;index++){const object=model.objects[index],option=document.createElement('option');option.value=index;option.textContent=`Object ${object.object_index ?? index} · ${object.triangle_count} triangles`;$('model-object').append(option);}
    $('model-diagnostics').textContent=(model.diagnostics ?? []).map(d=>typeof d==='string'?d:d.message ?? (d.kind==='equipment_templates_excluded'?'Equipment template objects 10 and 11 are excluded from this pose.':JSON.stringify(d))).join(' · ');
    if(witnessTarget)$('model-dialog').querySelector('h2').textContent=`Verified witness ${entityId} · proposed target ${witnessTarget} · not applied`;
    configureAnimation(clipId);exportClipControls.hidden=!data.frames?.length;showScenePose.disabled=!modelSceneEntityId||!data.frames?.length||state.project?.mode!=='edit';
    shapeControls.hidden=clipId==='file-preview'||data.model_glb_proposal===true||data.representation==='model-material-proposal'||!state.capabilities?.model_shape_authoring;
    $('shape-file').value='';shapeDraft=null;const shape=state.model_overrides?.[assetId];
    for(const id of ['shape-upload','shape-clear','shape-file'])$(id).disabled=state.project.mode!=='edit';
    $('shape-clear').disabled=state.project.mode!=='edit'||!shape;$('shape-authored').disabled=!shape;
    $('shape-status').textContent=`Viewing ${clipId==='allocated-record-edit-preview'?'PROPOSED retained content · Current model geometry':clipId==='allocated-record'?'SAVED retained clip · Current model geometry':clipId==='allocation-preview'?'PROPOSED unassigned clip · Current model geometry':shapeLayer==='authored'?'AUTHORED object-local shape':clipId==='authored-channels'?'AUTHORED shared animation':clipId==='authored-initial-animation'?'AUTHORED initial animation':clipId==='authored-appearance'?'AUTHORED appearance animation':clipId?'RETAIL assigned animation':'RETAIL object-local shape'} · ${shape?'A persistent shape override exists.':'No shape override.'}`;
    updateShapeDraft();$('model-export').disabled=['file-preview','allocation-preview','allocated-record-edit-preview'].includes(clipId)||data.model_glb_proposal===true||data.representation==='model-material-proposal';exportClipControls.hidden=['file-preview','allocation-preview','allocated-record-edit-preview'].includes(clipId)||!data.frames?.length;
    if(data.model_glb_proposal===true){$('model-dialog').querySelector('h2').textContent='Proposed GLB model · not applied';$('model-description').textContent='Drag to orbit · Scroll to zoom · Proposed object-local positions and UVs · Not applied. Close to return to GLB review.';}
    if(!modelRenderer){const module=await import('/scene-renderer.js');modelRenderer=new module.SceneRenderer(modelCanvas,message=>{$('model-error').textContent=message??'';if(!message)requestAnimationFrame(drawModel);});}
    if(!$('model-dialog').open)$('model-dialog').showModal();
    fitModelObject();
  }catch(error){if($('model-dialog').open){$('model-error').textContent=error.message;$('animation-clip').value=model?.animation?.clip_id ?? '';}else notify(error.message,true);}finally{$('animation-clip').disabled=!!witnessTarget;setBusy(false);}
}
let shapeDraft=null;
const discardShape=document.createElement('button');discardShape.textContent='Discard selected shape file';discardShape.type='button';$('shape-upload').after(discardShape);
function updateShapeDraft(){
  $('shape-file-report').replaceChildren();
  const pending=!!$('shape-file').files?.length,shape=state.model_overrides?.[modelAssetId];
  discardShape.hidden=!pending;
  $('shape-upload').disabled=!pending||state.project?.mode!=='edit';$('shape-file-preview').disabled=!pending||state.project?.mode!=='edit';$('shape-vectors').disabled=pending||state.project?.mode!=='edit';modelVertexMoveButton.disabled=pending||state.project?.mode!=='edit';$('shape-primitives').disabled=pending||state.project?.mode!=='edit';$('shape-authored-tmd').disabled=!state.model_overrides?.[modelAssetId];
  $('shape-retail').disabled=pending;$('shape-authored').disabled=pending||!shape;
  $('shape-clear').disabled=pending||!shape||state.project?.mode!=='edit';$('shape-download-authored').disabled=pending||!shape;$('shape-authored-json').disabled=pending||!shape;
  $('model-export').disabled=pending;
  modelGlbButton.disabled=busy||pending||state.project?.mode!=='edit'||!state.capabilities?.model_glb_authoring;
  modelMaterialsButton.disabled=busy||pending||state.project?.mode!=='edit'||!state.capabilities?.model_material_authoring;
  faceRemovalButton.disabled=busy||pending||state.project?.mode!=='edit'||!state.capabilities?.model_face_removal;
  allocationButton.disabled=busy||pending||state.project?.mode!=='edit'||!state.capabilities?.model_allocation_inspection;
  vectorAllocationButton.disabled=busy||pending||state.project?.mode!=='edit'||!state.capabilities?.model_vector_allocation;
  groupAllocationButton.disabled=busy||pending||state.project?.mode!=='edit'||!state.capabilities?.model_group_allocation;
  objectAllocationButton.disabled=busy||pending||state.project?.mode!=='edit'||!state.capabilities?.model_object_allocation;
  meshAppendButton.disabled=busy||pending||state.project?.mode!=='edit'||!state.capabilities?.model_mesh_append;
  if(state.model_overrides?.[modelAssetId]?.format==='tmd-face-removal-v1'){$('shape-status').textContent='Count-changing face removal applied. Vector edits, object transforms and same-layout TMD/OBJ/JSON edits retain removals. Retained-face editing is available. Material editing is available. GLB export/import retains the qualified Current layout; downloads, further removals, Undo/Redo and Clear are available.';}
}
$('shape-file').onchange=()=>{const file=$('shape-file').files?.[0];shapeDraft=file?{file,asset:modelAssetId,context:JSON.stringify([state.project.path,state.scene.id])}:null;updateShapeDraft();if(file)$('shape-status').textContent=`Selected ${file.name} · not applied. Apply or discard before changing model views.`;};
discardShape.onclick=()=>{$('shape-file').value='';shapeDraft=null;updateShapeDraft();$('model-error').textContent='';$('shape-status').textContent='Selected file discarded; project unchanged.';};
$('model-dialog').addEventListener('close',()=>{if(shapeDraft?.sceneInspection)return;$('shape-file').value='';shapeDraft=null;});
$('shape-retail').onclick=()=>openModel(modelAssetId);
$('shape-authored').onclick=()=>openModel(modelAssetId,null,null,'authored');
$('shape-clear').onclick=async()=>{if(!busy&&!shapeDraft&&await api('/api/command',{type:'clear_model_replacement',asset_id:modelAssetId}))await openModel(modelAssetId);};
$('shape-source').onclick=()=>downloadShapeSource('tmd');
$('shape-authored-tmd').onclick=()=>downloadShapeSource('tmd','authored');
$('shape-source-obj').onclick=()=>downloadShapeSource('obj');
$('shape-source-json').onclick=()=>downloadShapeSource('json');
$('shape-authored-json').onclick=()=>downloadShapeSource('json','authored');
$('shape-download-authored').onclick=()=>downloadShapeSource('obj','authored');
async function downloadShapeSource(format,layer='imported'){
  if(busy||!modelAssetId)return;setBusy(true);
  try{const response=await fetch('/api/model-shape-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:modelAssetId,format,layer})}),data=await response.json();if(!response.ok)throw new Error(data.error);const encoded=data[format+'_base64'];if(typeof encoded!=='string'||encoded.length>(format!=='tmd'?22369624:5592408))throw new Error('Invalid model source size');const bytes=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));if(bytes.length!==data.byte_length)throw new Error('Model source length mismatch');const url=URL.createObjectURL(new Blob([bytes])),link=document.createElement('a');link.href=url;link.download=(layer==='authored'?'authored':'original')+'-model.'+format;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);$('shape-status').textContent=`Downloaded ${layer} ${format.toUpperCase()} · TMD SHA-256 ${data.effective_sha256}`;}catch(error){$('model-error').textContent=error.message;}finally{setBusy(false);}
};
async function readShapeFile(previewOnly=false){
  if(busy||state.project.mode!=='edit')return;const file=$('shape-file').files?.[0];if(!file||file.size<1||file.size>(/\.(obj|json)$/i.test(file.name)?16777216:4194304)){$('model-error').textContent='Choose a TMD up to 4 MiB or an OBJ/JSON up to 16 MiB.';return;}
  if(!shapeDraft||shapeDraft.file!==file||shapeDraft.asset!==modelAssetId||shapeDraft.context!==JSON.stringify([state.project.path,state.scene.id])){$('model-error').textContent='The selected shape file belongs to an earlier model context. Discard and select it again.';return;}
  const draft=shapeDraft;
  const asset=modelAssetId,context=JSON.stringify([state.project.path,state.scene.id]);
  const currentFile=()=>shapeDraft===draft&&asset===modelAssetId&&context===JSON.stringify([state.project.path,state.scene.id])&&$('model-dialog').open&&state.project.mode==='edit';
  $('model-error').textContent='';setBusy(true);let encoded;
  try{encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('Could not read model file'));reader.readAsDataURL(file);});}catch(error){if(currentFile())$('model-error').textContent=error.message;return;}finally{setBusy(false);}
  if(!encoded||shapeDraft!==draft||asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id])||!$('model-dialog').open)return;
  const obj=/\.obj$/i.test(file.name),json=/\.json$/i.test(file.name);
  if(previewOnly){
    setBusy(true);$('shape-file-report').replaceChildren();
    try{const response=await fetch('/api/model-file-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:asset,format:json?'json':obj?'obj':'tmd',content_base64:encoded})}),report=await response.json();if(!currentFile())return;if(!response.ok||report.error)throw new Error(report.error||'Model file preview failed');if(report.asset_id!==asset)throw new Error('Model proposal identity differs from the selected asset');
      const intro=document.createElement('p');intro.textContent='Proposed model file · project unchanged. Apply shape revalidates the file.';$('shape-file-report').append(intro);
      for(const [label,rows] of [['Changes from retail',report.coordinate_changes],['Changes from current authored model',report.changes_from_current]]){const details=document.createElement('details'),summary=document.createElement('summary'),text=document.createElement('pre');summary.textContent=`${label}: ${rows.length} source field changes`;text.textContent=rows.slice(0,256).map(row=>modelAuditLabel(row)).join('\n');details.append(summary,text);if(rows.length>256){const note=document.createElement('p');note.textContent='Showing the first 256 source field changes.';details.append(note);}$('shape-file-report').append(details);}
      const instances=scenePreviewCurrent()&&sceneRepresentation==='authored'?scenePreview.entities.filter(e=>e.asset_id===asset&&e.renderable):[];
      if(instances.length){
        const label=document.createElement('label'),select=document.createElement('select'),inspect=document.createElement('button');label.textContent='Scene instance';select.setAttribute('aria-label','Model file scene instance');label.append(select);
        for(const instance of instances){const option=document.createElement('option');option.value=instance.entity_id;option.textContent=instance.name??instance.entity_id;select.append(option);}
        const allOption=document.createElement('option');allOption.value='all-instances';allOption.textContent=`All supported model instances (${instances.length})`;select.append(allOption);
        if(instances.some(e=>e.entity_id===environmentSelection))select.value=environmentSelection;
        inspect.type='button';inspect.textContent='Inspect proposed model file in scene';$('shape-file-report').append(label,inspect);
        const loadedKey=sceneKey,sceneSource=scenePreview.project_source_key;
        inspect.onclick=async()=>{
          if(busy||!currentFile()||!scenePreviewCurrent()||loadedKey!==sceneKey||sceneRepresentation!=='authored')return;
          const allInstances=select.value==='all-instances',entityId=allInstances?select.options[0].value:select.value;setBusy(true);
          try{
            const response=await fetch('/api/model-file-scene-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:asset,format:json?'json':obj?'obj':'tmd',content_base64:encoded,entity_id:entityId,all_instances:allInstances,source_key:sceneSource,proposed_sha256:report.proposed_sha256})}),posed=await response.json();
            if(!currentFile()||!scenePreviewCurrent()||loadedKey!==sceneKey)return;
            if(!response.ok||posed.error)throw new Error(posed.error||'Model file scene inspection failed');
            if(posed.entity_id!==entityId||posed.asset_id!==asset||posed.project_source_key!==sceneSource||posed.proposed_sha256!==report.proposed_sha256)throw new Error('Scene file proposal differs from inspection');
            stopScenePosePlayback();const isolated=sceneShapeProposalDocument(scenePreview,posed,entityId),failures=sceneRenderer.load(isolated.document);if(failures.length)throw new Error(failures.join('; '));
            const returnToShapeFile=()=>{if(shapeDraft!==draft||asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id])||loadedKey!==sceneKey||state.project.mode!=='edit')return false;draft.sceneInspection=false;$('model-dialog').showModal();updateShapeDraft();$('shape-status').textContent=`Selected ${file.name} · not applied. Preview or Apply revalidates the file.`;return true;};
            scenePose={key:sceneKey,geometryKey:isolated.geometryKey,preview:posed.preview,name:'Proposed model file · not applied',returnToFile:returnToShapeFile,afterRestore:returnToShapeFile};
            scenePoseBar.hidden=false;scenePoseBar.querySelector('span').textContent=`Proposed model file · not applied · ${sceneShapeProposalLabel(posed,entityId)}`;
            configureSceneInspectionComparison(isolated.document);
            for(const control of [scenePoseBar.querySelector('input'),scenePoseBar.querySelector('[data-play]'),scenePoseBar.querySelector('label')])control.hidden=true;
            const back=scenePoseBar.querySelector('[data-return-file]');back.hidden=false;back.textContent='Return to model file';
            draft.sceneInspection=true;$('model-dialog').close();frameShapeProposal(posed,entityId);draw();
          }catch(error){if(currentFile()){clearScenePose();$('model-error').textContent=error.message;draw();}}finally{setBusy(false);}
        };
      }
    }catch(error){if(currentFile())$('model-error').textContent=error.message;}finally{setBusy(false);}return;
  }
  if(await api(json?'/api/model-json-replacement':obj?'/api/model-obj-replacement':'/api/model-shape-replacement',{asset_id:asset,[json?'json_base64':obj?'obj_base64':'tmd_base64']:encoded})){$('shape-file').value='';shapeDraft=null;await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}
};
$('shape-upload').onclick=()=>readShapeFile();
$('shape-file-preview').onclick=()=>readShapeFile(true);
function modelObject(){return $('model-object').value==='all' && model?.frames?.length?{vertex_start:0,vertex_count:model.vertices.length,triangle_start:0,triangle_count:model.triangles.length}:model?.objects[Number($('model-object').value)];}
function frameVertices(){return model?.frames?.[animationFrame]?.vertices ?? model?.vertices ?? [];}
function graphAuthoringTarget(channel){
  if(state.project?.mode!=='edit'||modelSceneContext!==sceneRequestKey()||!state.capabilities?.actor_animation_authoring||state.selection?.entity_id!==modelEntityId)throw new Error('Open the current selected actor in Edit mode before authoring channels.');
  return animationChannelAuthoringTarget(model,modelEntityId,channel.frame,channel.object);
}
const animationChannelGraph=createAnimationChannelGraph($('animation-controls'),{
  onFrame:index=>{stopAnimation();setAnimationFrame(index);},onObject:index=>{$('model-object').value=String(index);fitModelObject();},
  editAvailability:channel=>{try{graphAuthoringTarget(channel);return {available:true};}catch(e){return {available:false,reason:e.message};}},
  onEdit:async channel=>{
    if(busy)return;const target=graphAuthoringTarget(channel),preview=model,key=sceneRequestKey(),entity=entities().find(e=>e.id===modelEntityId);if(!entity)throw new Error('Source actor is no longer available.');
    if(target.kind==='retained'){
      setBusy(true);let library;try{const response=await fetch('/api/animation-record-library',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene_id:state.scene.id,expected_source_key:state.scene_preview_source_key})});library=await response.json();if(!response.ok||library.error)throw new Error(library.error||'Could not verify retained clip');}finally{setBusy(false);}
      if(model!==preview||key!==sceneRequestKey()||!$('model-dialog').open)throw new Error('Preview changed while verifying the saved clip.');graphAuthoringTarget(channel);
      const row=validateRetainedChannelHandoff(target,library,{sceneId:state.scene.id,sourceKey:state.scene_preview_source_key});
      animationRecordLibrary?.dispose();model=null;modelFileReturn=null;$('model-dialog').close();await inspectRetainedAnimationContent(entity,row,null,target.initial);
    }else{$('model-dialog').close();await openAnimationChannels(entity,target.initial);}
  }
});
function configureAnimation(clipId){
  animationChannelGraph.load(model);
  const support=model.animation_support ?? {},clips=support.clips ?? [],frames=model.frames ?? [];
  $('animation-controls').hidden=!support.supported && !frames.length;
  $('animation-clip').replaceChildren();const unposed=document.createElement('option');unposed.value='';unposed.textContent='Object-local geometry (unposed)';$('animation-clip').append(unposed);
  for(const clip of clips){const option=document.createElement('option');option.value=clip.id;option.textContent=clip.label;$('animation-clip').append(option);}
  $('animation-clip').value=clipId ?? '';
  const timing=model.animation?.timing ?? model.timing ?? {},fps=numeric(timing.fps)?timing.fps:10;
  $('animation-rate').value=fps;$('animation-rate').parentElement.querySelector('span').textContent=numeric(timing.fps)?`Reference rate: ${timing.fps} fps; not verified against a live trace.`:'Preview setting; retail timing is unresolved.';
  $('animation-evidence').textContent=JSON.stringify(model.animation?{...model.animation,geometry_diagnostics:model.diagnostics,texture_catalog:model.texture_catalog}:support,null,2);
  $('animation-error').textContent='';
  for(const id of ['animation-play','animation-previous','animation-next','animation-frame','animation-rate'])$(id).disabled=!frames.length;
  $('animation-frame').max=Math.max(0,frames.length-1);$('animation-frame').value=0;
  $('animation-frame-label').textContent=frames.length?`1 / ${frames.length}`:'No clip loaded';
}
function stopAnimation(){if(animationTick!==null)cancelAnimationFrame(animationTick);animationTick=null;animationClock=null;$('animation-play').textContent='Play';}
function setAnimationFrame(index){const count=model?.frames?.length ?? 0;if(!count)return;animationFrame=((index%count)+count)%count;$('animation-frame').value=animationFrame;$('animation-frame-label').textContent=`${animationFrame+1} / ${count}`;animationChannelGraph.frame(animationFrame);drawModel();}
$('animation-clip').onchange=()=>{const clip=$('animation-clip').value || null;openModel(modelAssetId,clip,['scene-header','authored-appearance','authored-initial-animation','authored-channels'].includes(clip)?modelEntityId:null,'imported',modelSceneEntityId);};
$('animation-frame').oninput=()=>{stopAnimation();setAnimationFrame(Number($('animation-frame').value));};
$('animation-previous').onclick=()=>{stopAnimation();setAnimationFrame(animationFrame-1);};
$('animation-next').onclick=()=>{stopAnimation();setAnimationFrame(animationFrame+1);};
$('animation-rate').onchange=()=>{const rate=Number($('animation-rate').value);$('animation-rate').value=Number.isFinite(rate)?Math.max(1,Math.min(60,rate)):10;animationClock=null;};
$('animation-play').onclick=()=>{
  if(animationTick!==null){stopAnimation();return;}if(!model?.frames?.length)return;
  $('animation-play').textContent='Pause';
  const tick=time=>{if(!$('model-dialog').open){stopAnimation();return;}if(animationClock===null)animationClock=time;const step=1000/Math.max(1,Math.min(60,Number($('animation-rate').value)||10)),advance=Math.floor((time-animationClock)/step);if(advance){animationClock+=advance*step;setAnimationFrame(animationFrame+advance);}animationTick=requestAnimationFrame(tick);};
  animationTick=requestAnimationFrame(tick);
};
$('model-dialog').addEventListener('close',()=>{stopAnimation();modelRequest++;});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopAnimation();});
const exportClipControls=document.createElement('span');exportClipControls.innerHTML='<label>Export fps <input id="clip-export-rate" type="number" min="1" max="120" step="1" value="10" style="width:4em"></label> <button id="model-export-clip" type="button">Export full clip GLB</button>';$('model-export').after(exportClipControls);
$('model-export').onclick=()=>exportModel(false);
$('model-export-clip').onclick=()=>exportModel(true);
async function exportModel(fullClip=false){
  if(modelSceneContext!==sceneRequestKey()){$('model-error').textContent='The scene or model source changed. Reopen the model preview before exporting.';return;}
  if(shapeDraft){$('model-error').textContent='Apply or discard the selected shape file before exporting.';return;}
  if(model?.animation?.representation==='allocation_preview'){$('model-error').textContent='Apply the allocated clip before exporting its retained identity.';return;}
  if(model?.animation?.representation==='allocated_record_edit_preview'){$('model-error').textContent='Apply the retained clip edit before exporting its new content.';return;}
  if(model?.animation?.representation==='file_preview'){$('model-error').textContent='Import the file before exporting an applied animation.';return;}
  if(model?.model_glb_proposal){$('model-error').textContent='Apply the reviewed GLB before exporting the current model.';return;}
  if(busy||!modelAssetId)return;const fps=Number($('clip-export-rate').value);if(fullClip&&(!model?.frames?.length||!Number.isFinite(fps)||fps<1||fps>120)){$('model-error').textContent='Load a clip and choose an export rate from 1 to 120 fps.';return;}stopAnimation();setBusy(true);$('model-export').disabled=true;$('model-error').textContent='';
  const clip=model.animation?.clip_id,payload=modelEntityId?{entity_id:modelEntityId,frame_index:animationFrame,...(clip==='authored-channels'?{representation:'authored'}:{})}:{asset_id:modelAssetId,...(clip?{clip_id:clip,frame_index:animationFrame}:{})};
  if(fullClip){delete payload.frame_index;payload.clip_fps=fps;}
  try{
    const allocated=['allocated_record','allocated_assignment_preview','allocated_initial_assignment'].includes(model.animation?.representation);
    const exportPayload=allocated?allocatedAnimationExportRequest(model.animation,{projectPath:state.project.path,sceneId:state.scene.id,mode:state.project.mode,sourceKey:state.scene_preview_source_key},animationFrame,fullClip?fps:null):payload;
    const response=await fetch(allocated?'/api/export/allocated-animation':model.representation==='authored-shape'?'/api/export/model-shape':modelEntityId?(clip==='authored-initial-animation'?'/api/export/actor-initial-animation':clip==='authored-appearance'?'/api/export/actor-appearance':'/api/export/actor-animation'):'/api/export/model',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(exportPayload)});
    const result=await response.json();if(!response.ok||result.error)throw new Error(result.error ?? 'Model export failed');
    exportDialog.innerHTML=`<div class="dialog-heading"><h2>${result.audit.full_clip?'Animation clip exported':result.audit.posed?'Static posed model exported':'Object-local model exported'}</h2><button id="close-export" aria-label="Close">×</button></div><p>${result.audit.object_count} objects · ${result.audit.triangle_count} triangles · ${result.audit.texture_count} embedded textures${result.audit.posed?' · Frame '+(result.audit.frame_index+1):''}</p><label>Private GLB file<input readonly value="${escapeHTML(result.path)}"></label><p>Full model export${result.audit.posed?' with the displayed animation frame baked into geometry':''}. Source units are retained; physical meter scale is unknown. ${result.audit.full_clip?`Rigid animation channels exported at ${result.audit.export_fps} selected fps; ${result.audit.frame_count} decoded frames. Retail timing is unverified; looping is controlled by the receiving application.`:'Animation channels and skin hierarchy are not exported.'}</p><details><summary>Export provenance and limitations</summary><pre class="diagnostic-detail">${escapeHTML(JSON.stringify(result.audit,null,2))}</pre></details>`;
    $('close-export').onclick=()=>exportDialog.close();exportDialog.showModal();
  }catch(error){$('model-error').textContent=error.message;}finally{$('model-export').disabled=false;setBusy(false);}
};
function fitModelObject(){
  const object=modelObject();if(!object)return;
  const streams=model.frames?.length?model.frames.map(frame=>frame.vertices):[model.vertices];
  const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
  for(const vertices of streams)for(let index=object.vertex_start;index<object.vertex_start+object.vertex_count;index++)for(let axis=0;axis<3;axis++){min[axis]=Math.min(min[axis],vertices[index][axis]);max[axis]=Math.max(max[axis],vertices[index][axis]);}
  modelView.center=object.vertex_count?min.map((v,i)=>(v+max[i])/2):[0,0,0];modelView.radius=object.vertex_count?Math.max(1,Math.hypot(...max.map((v,i)=>v-min[i]))/2):1;modelView.zoom=1;
  $('model-counts').textContent=`${object.vertex_count} vertices · ${object.triangle_count} triangles`;updateModelNormalView();
  drawModel();
}
$('model-object').onchange=()=>{animationChannelGraph.setObject(Number($('model-object').value));fitModelObject();};
$('model-wireframe').onchange=drawModel;
const modelShading=document.createElement('select');modelShading.id='model-shading-mode';modelShading.setAttribute('aria-label','Model shading');for(const [value,text] of [['surface','Textures and stored colors'],['source-normals','Source normal directions']]){const option=document.createElement('option');option.value=value;option.textContent=text;modelShading.append(option);}const modelShadingLabel=document.createElement('label');modelShadingLabel.textContent='View ';modelShadingLabel.append(modelShading);$('model-wireframe').closest('label').after(modelShadingLabel);const modelNormalNote=document.createElement('p');modelNormalNote.id='model-normal-note';modelNormalNote.setAttribute('role','status');$('model-description').after(modelNormalNote);modelShading.onchange=()=>{updateModelNormalView();drawModel();};
const modelNormalFrameCache=new WeakMap();
function modelNormalPreview(){
  if(!model)return null;
  if(!model.frames?.length){try{return qualifySourceNormals(model)?model:null;}catch{return null;}}
  const cached=modelNormalFrameCache.get(model);if(cached?.frame===animationFrame)return cached.preview;
  let preview=null;try{preview={...rigidFrameNormals(model,model.frames[animationFrame]),triangles:model.triangles};}catch{/* Unknown poses retain surface shading. */}
  modelNormalFrameCache.set(model,{frame:animationFrame,preview});return preview;
}
function updateModelNormalView(){
  const available=modelNormalPreview()!==null;
  modelShading.querySelector('[value="source-normals"]').disabled=!available;if(!available)modelShading.value='surface';
  if(!available){modelNormalNote.textContent=model?.frames?.length||model?.posed?'Source normal directions are unavailable for this pose; rigid object channels are not qualified.':'Source normal directions are unavailable for this preview.';return;}
  const object=modelObject(),rows=object?model.triangle_normals.slice(object.triangle_start,object.triangle_start+object.triangle_count):[],lit=rows.filter(row=>row!==null).length,zero=rows.reduce((sum,row)=>sum+(row?.filter(v=>v.every(n=>n===0)).length??0),0);
  modelNormalNote.textContent=`${lit}/${rows.length} triangles have source normal references · ${zero} zero-vector corners · ${model.normal_preview.invalid_triangles} invalid source triangles in full model · ${modelShading.value==='source-normals'?'Direction colors: red X, green display Y, blue Z. Gray means unlit, zero or unavailable.':'Source normal directions can be inspected separately from textures and stored colors.'}${model.frames?.length?' · Current frame uses analytic Rz × Ry × Rx rigid rotations; translation does not affect directions.':''} · Retail lighting is not reconstructed.`;
}

function modelRenderView(width,height){
  const c=Math.cos(modelView.yaw),s=Math.sin(modelView.yaw),cp=Math.cos(modelView.pitch),sp=Math.sin(modelView.pitch);
  return {normalDiagnostic:modelShading.value==='source-normals'&&modelNormalPreview()!==null,width,height,positions:new Map(),grid:false,wireframe:$('model-wireframe').checked,camera:{target:{x:modelView.center[0],y:-modelView.center[1],z:modelView.center[2]},distance:modelView.radius*4/modelView.zoom*.9/1.3},basis:{right:{x:c,y:0,z:s},up:{x:sp*s,y:cp,z:-sp*c},forward:{x:-cp*s,y:sp,z:cp*c}}};
}
function inspectModelVertex(event){
  if(!event.shiftKey||!$('model-wireframe').checked||busy||shapeDraft||model?.frames?.length||state.project.mode!=='edit'||!state.capabilities?.model_shape_authoring)return;
  const objectIndex=Number($('model-object').value),object=model.objects[objectIndex];if(!object)return;
  const rect=modelCanvas.getBoundingClientRect(),view=modelRenderView(rect.width,rect.height),x=event.clientX-rect.left,y=event.clientY-rect.top;
  let selected=null;
  for(let index=0;index<object.vertex_count;index++){
    const vertex=model.vertices[object.vertex_start+index],point=modelRenderer.projectPoint({x:vertex[0],y:-vertex[1],z:vertex[2]},view);if(!point)continue;
    const distance=Math.hypot(point.x-x,point.y-y);
    if(distance<=10&&(!selected||distance<selected.distance-.01||Math.abs(distance-selected.distance)<=.01&&point.depth<selected.depth))selected={index,distance,depth:point.depth};
  }
  if(selected)openModelVectors({object_index:objectIndex,kind:'vertex',vector_index:selected.index});
  else $('shape-status').textContent='No projected vertex within 10 pixels. Wireframe picking includes hidden vertices; orbit to separate overlaps.';
}
function drawModel(){
  if(!modelRenderer||!$('model-dialog').open)return;
  const rect=modelCanvas.getBoundingClientRect(),w=rect.width,h=rect.height;if(!w||!h)return;
  const object=modelObject();if(!object)return;
  try{
    updateModelNormalView();
    const choice=$('model-object').value,vertices=frameVertices(),start=object.triangle_start,end=start+object.triangle_count,changed=modelRenderSource!==model||modelRenderObject!==choice||modelRenderFrame!==animationFrame,normalPreview=changed?modelNormalPreview():null,normalSlice=normalPreview?{...normalPreview,triangles:model.triangles.slice(start,end),triangle_normals:normalPreview.triangle_normals.slice(start,end)}:undefined;
    if(modelRenderSource!==model||modelRenderObject!==choice){
      const preview={...model,...normalSlice,vertices,triangles:model.triangles.slice(start,end),triangle_colors:model.triangle_colors?.slice(start,end),triangle_uvs:model.triangle_uvs?.slice(start,end),triangle_materials:model.triangle_materials?.slice(start,end),triangle_normals:normalSlice?.triangle_normals??model.triangle_normals?.slice(start,end)};
      const failures=modelRenderer.load({assets:[{geometry_key:'model-view',preview}],entities:[{entity_id:'model-view',geometry_key:'model-view',renderable:true,model_to_scene:[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]}]});
      if(failures.length)throw new Error(failures.join('; '));
      modelRenderSource=model;modelRenderObject=choice;modelRenderFrame=animationFrame;
    }else if(modelRenderFrame!==animationFrame){if(modelRenderer.updateVertices('model-view',vertices,normalSlice))modelRenderFrame=animationFrame;}
    modelRenderer.draw(modelRenderView(w,h));
  }catch(error){$('model-error').textContent=String(error.message);}
}
new ResizeObserver(drawModel).observe(modelCanvas);
modelCanvas.addEventListener('pointerdown',event=>{modelCanvas.setPointerCapture(event.pointerId);modelDrag={x:event.clientX,y:event.clientY,startX:event.clientX,startY:event.clientY,moved:false};});
modelCanvas.addEventListener('pointermove',event=>{if(!modelDrag)return;modelView.yaw+=(event.clientX-modelDrag.x)*.009;modelView.pitch+=(event.clientY-modelDrag.y)*.009;modelDrag.moved ||= Math.hypot(event.clientX-modelDrag.startX,event.clientY-modelDrag.startY)>4;modelDrag.x=event.clientX;modelDrag.y=event.clientY;drawModel();});
modelCanvas.addEventListener('pointerup',event=>{const clicked=modelDrag&&!modelDrag.moved;modelDrag=null;if(clicked)inspectModelVertex(event);});
modelCanvas.addEventListener('pointercancel',()=>{modelDrag=null;});
modelCanvas.addEventListener('wheel',event=>{event.preventDefault();modelView.zoom=Math.max(.15,Math.min(2.5,modelView.zoom*Math.exp(-event.deltaY*.001)));drawModel();},{passive:false});

function arrivalMoveAllowed(){return !sceneRuler?.picking()&&!!transitionArrivalOverlay&&transitionArrivalCurrent(transitionArrivalOverlay,state)&&arrivalMove.checked&&!!arrivalLocalPreview()&&canEdit()&&scenePreviewCurrent()&&sceneModelsReady()&&sceneRepresentation==='authored'&&!busy&&!drag&&!scenePose&&!shapeDraft&&!actorGroupInspection&&!environmentGroupInspection&&!scenePlacementInspection&&!scenePlacementMode&&!actorBoxMode&&!wallSelectMode&&!wallInspection&&!sceneFacePickMode&&!floorPickMode&&!pickScriptTargets&&!pickRuntimeNodes&&!fieldSpatialPick;}
function arrivalMoveContext(){return JSON.stringify([resourceStateKey(),state.project_transition_state_key,state.scene_preview_source_key,cameraRevision,width,height,transitionArrivalHeight,arrivalMove.checked]);}
function arrivalMoveAxes(){if(!arrivalMoveAllowed())return {};const point=arrivalLocalPreview().proposed_arrival,origin={...point,y:transitionArrivalHeight},start=project(displayPosition(origin));if(!start)return {};const axes={};for(const axis of ['x','z']){const measure=project(displayPosition({...origin,[axis]:origin[axis]+64}));if(!measure)continue;const span=Math.hypot(measure.x-start.x,measure.y-start.y);if(span<.05)continue;const units=64*Math.max(1,Math.min(128,Math.round(70/span))),end=project(displayPosition({...origin,[axis]:origin[axis]+units}));if(end&&Math.hypot(end.x-start.x,end.y-start.y)>=4)axes[axis]={start,end,units};}return axes;}
function npcArrivalMoveAllowed(){return !sceneRuler?.picking()&&!!currentNpcArrivalPreview()&&npcArrivalAuthoring.move.checked&&canEdit()&&scenePreviewCurrent()&&sceneModelsReady()&&sceneRepresentation==='authored'&&!busy&&!drag&&!scenePose&&!shapeDraft&&!actorGroupInspection&&!environmentGroupInspection&&!scenePlacementInspection&&!scenePlacementMode&&!actorBoxMode&&!wallSelectMode&&!wallInspection&&!sceneFacePickMode&&!floorPickMode&&!pickScriptTargets&&!pickRuntimeNodes&&!fieldSpatialPick&&!arrivalMove.checked;}
function npcArrivalMoveContext(){return JSON.stringify([resourceStateKey(),state.npc_arrival_preview_state_key,state.scene_preview_source_key,cameraRevision,width,height,npcArrivalHeight,npcArrivalAuthoring.move.checked]);}
function npcArrivalMoveAxes(){if(!npcArrivalMoveAllowed())return {};const values=npcArrivalAuthoring.values();try{arrivalDraftPoint(values);}catch{return {};}const origin={x:values.x,y:npcArrivalHeight,z:values.z},start=project(displayPosition(origin));if(!start)return {};const axes={};for(const axis of ['x','z']){const measure=project(displayPosition({...origin,[axis]:origin[axis]+64}));if(!measure)continue;const span=Math.hypot(measure.x-start.x,measure.y-start.y);if(span<.05)continue;const units=64*Math.max(1,Math.min(128,Math.round(70/span))),end=project(displayPosition({...origin,[axis]:origin[axis]+units}));if(end&&Math.hypot(end.x-start.x,end.y-start.y)>=4)axes[axis]={start,end,units};}return axes;}
npcArrivalGizmo=mountPlacementGizmo({host:$('viewport-wrap'),idPrefix:'npc-arrival-placement',getAxes:npcArrivalMoveAxes,getContext:npcArrivalMoveContext,allowed:npcArrivalMoveAllowed,getStep:()=>64,
 getValues:()=>{const v=npcArrivalAuthoring.values();return {offset:{x:v.x,y:0,z:v.z},yaw_units:v.facing_sector*512};},
 onBegin:()=>{npcArrivalGesture={report:npcArrivalOverlay,snapshot:npcArrivalAuthoring.capture()};},
 onPreview:values=>npcArrivalAuthoring.setDraft(arrivalFromGizmo(values)),onEnd:()=>{npcArrivalGesture=null;},
 onCancel:()=>{const previous=npcArrivalGesture;npcArrivalGesture=null;if(previous&&currentNpcArrivalPreview()===previous.report)npcArrivalAuthoring.restore(previous.snapshot);else npcArrivalAuthoring.discard();},onError:message=>notify(message,true)
});
arrivalGizmo=mountPlacementGizmo({host:$('viewport-wrap'),idPrefix:'arrival-placement',getAxes:arrivalMoveAxes,getContext:arrivalMoveContext,allowed:arrivalMoveAllowed,getStep:()=>64,
  getValues:()=>{const v=arrivalValues();return {offset:{x:v.x,y:0,z:v.z},yaw_units:v.facing_sector*512};},
  onBegin:()=>{arrivalGesture={report:transitionArrivalOverlay,values:arrivalValues(),proposal:transitionArrivalProposal,draft:arrivalDraft,status:arrivalStatus.textContent,audit:arrivalForm.querySelector('pre').textContent};transitionArrivalProposal=null;transitionArrivalReviewGeneration++;draw();},
  onPreview:values=>{const next=arrivalFromGizmo(values);for(const [key,value] of Object.entries(next))arrivalForm.elements[key].value=value;arrivalChanged();},
  onEnd:()=>{arrivalGesture=null;arrivalStatus.textContent='Arrival draft moved. Review before Apply.';draw();},
  onCancel:reason=>{const previous=arrivalGesture;arrivalGesture=null;if(previous&&transitionArrivalOverlay===previous.report&&transitionArrivalCurrent(previous.report,state)){for(const [key,value] of Object.entries(previous.values))arrivalForm.elements[key].value=value;transitionArrivalProposal=previous.proposal;arrivalDraft=previous.draft;arrivalStatus.textContent=previous.status;arrivalForm.querySelector('pre').textContent=previous.audit;}else{transitionArrivalProposal=null;arrivalDraft=null;}draw();},
  onError:message=>{arrivalStatus.textContent=message;}
});

export async function initializeEditor({signal}={}){if(!await api('/api/state',undefined,{signal}))throw new Error($('status').textContent||'Initial project state could not be loaded.');return true;}

worldmapControls=mountWorldmapAuthoring({after:$('resource-refresh'),
  getContext:()=>state.capabilities?.worldmap_authoring?{projectPath:state.project?.path,mode:state.project?.mode,worldmapKey:state.worldmap_authoring_state_key}:null,
  busy:()=>busy,setBusy,api,onError:error=>notify(error.message,true),
  onDraftChange:pending=>{if(worldmapDraftPending===pending)return;worldmapDraftPending=pending;setBusy(busy);},
  onInspectDestination:label=>{if(busy||worldmapDraftPending)return;$('import-button').click();$('catalog-prefix').value=label;clearSceneCatalog();$('catalog-search').click();}});

worldmapGeometryControls=mountWorldmapGeometry({after:$('resource-refresh'),getState:()=>state,busy:()=>busy,setBusy,onError:error=>notify(error.message,true)});
worldPlacementControls=mountWorldPlacements({after:$('resource-refresh'),getState:()=>state,busy:()=>busy,setBusy,api,
  onDraftChange:pending=>{if(worldmapDraftPending===pending)return;worldmapDraftPending=pending;setBusy(busy);},onError:error=>notify(error.message,true)});

const projectAssetHost=document.createElement('div');projectAssetHost.style.gridColumn='1 / -1';assetTools.prepend(projectAssetHost);
projectAssetControls=mountProjectAssets({host:projectAssetHost,getContext:projectAssetContext,busy:()=>busy,setBusy,
  getUnavailableReason:()=>state.project_assets_unavailable_reason,
  onChange:()=>{assetPageSignature=null;renderAssets();},onError:error=>notify(error.message,true)});

mountSceneToolDrawer({toolbar:document.querySelector('.viewport-toolbar'),viewport:$('viewport-wrap'),keep:[sceneRuler.bar,npcGroundPlacement.bar,groundPositionBar,npcCreationBar,runRibbon,fieldNote,scenePoseBar,actorGroupTools,scriptTargetTools,transitionArrivalTools,npcArrivalTools,historicalTools],onToggle:()=>{cancelViewportGesture();resize();}});
