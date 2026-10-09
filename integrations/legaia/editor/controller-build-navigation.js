import {controllerOwnerComponents} from './controller-owner-inspector.js';
export const CONTROLLER_BUILD_TARGETS={
 'controller-flag-bit-only':['ControllerFlagBits','flag-bit','script.flag_bit'],
 'script-system-selector-only':['ControllerSystemFlags','system-flag','system_flag.index'],
 'script-branch-target-only':['ControllerBranches','branch','script.branch_target'],
 'controller-tile-rect-operands-only':['ControllerTileRects','tile-rect','script.tile_rect_operands'],
 'controller-fade-operands-only':['ControllerFades','fade','script.fade_operands'],
 'controller-table-copy-operands-only':['ControllerTableCopies','table-copy','script.table_copy_operands'],
 'controller-word-triplet-operands-only':['ControllerWordTriplets','word-triplet','script.word_triplet_operands'],
 'controller-three-word-operands-only':['ControllerThreeWords','three-word','script.three_word_operands'],
 'controller-bgm-operand-only':['ControllerBgm','bgm','script.bgm_operand'],
 'controller-scene-byte-operand-only':['ControllerSceneBytes','scene-byte','script.scene_byte_operand'],
 'controller-five-word-operands-only':['ControllerFiveWords','five-word','script.five_word_operands'],
 'controller-global-byte-operands-only':['ControllerGlobalBytes','global-byte','script.global_byte_operands'],
 'controller-party-selector-only':['ControllerPartySelectors','party-selector','script.party_selector'],
};
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
export function controllerBuildTarget(change,scenes,authoredAssets){
 if(typeof change?.owner_id!=='string'||!change.owner_id.includes('/controllers/'))return null;
 const match=/^(scene:\/\/[A-Za-z0-9_-]{1,128})\/controllers\/man-p1\/0000$/.exec(change.owner_id),target=CONTROLLER_BUILD_TARGETS[change.scope];
 if(!match||!Object.hasOwn(CONTROLLER_BUILD_TARGETS,change.scope)||change.field!==target[2])throw Error('Controller Build change has no supported source target.');
 const [component,kind]=target,sceneId=match[1],scene=scenes.find(row=>row.id===sceneId&&row.name===change.scene),assetId=change.owner_id.replace('scene://','script://'),prefix=assetId+'/'+kind+'/';
 if(!scene||typeof change.asset_id!=='string'||!change.asset_id.startsWith(prefix)||!/^[a-f0-9]{4}$/.test(change.asset_id.slice(prefix.length)))throw Error('Controller Build change source ownership is invalid.');
 const record=authoredAssets.find(row=>row.kind==='controller'&&row.id===assetId&&row.scene_id===sceneId),value=record?controllerOwnerComponents(record,sceneId)[component]?.entries?.[change.asset_id]:null;
 const expected=component==='ControllerSystemFlags'?{index:change.after}:component==='ControllerBranches'?{target_pc:change.after}:change.after;
 if(!value||JSON.stringify(canonical(value))!==JSON.stringify(canonical(expected)))throw Error('Controller operands differ from this Build report. Rebuild to inspect current changes.');
 return {sceneId,assetId,ownerId:change.owner_id,component,pc:parseInt(change.asset_id.slice(-4),16)};
}
