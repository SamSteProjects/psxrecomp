import {controllerAssetSourceHash} from './controller-owner-inspector.js';
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
export function controllerNavigationTarget(record,context,pc=null){
 if(record?.type!=='controller'||!/^scene:\/\/[A-Za-z0-9_-]{1,128}$/.test(record.sceneId??'')||record.id!==record.sceneId.replace('scene://','script://')+'/controllers/man-p1/0000'||typeof context?.projectPath!=='string'||!context.projectPath||!hash(context.sourceKey)||pc!==null&&(!Number.isInteger(pc)||pc<0||pc>65535))throw Error('Controller navigation requires a qualified project, scene and operand location.');
 return {id:record.id,sceneId:record.sceneId,projectPath:context.projectPath,sourceKey:context.sourceKey,sourceHash:controllerAssetSourceHash(record),pc};
}
export function qualifyControllerNavigation(target,record,context){
 if(context?.activeSceneId!==target.sceneId||context.projectPath!==target.projectPath||context.sourceKey!==target.sourceKey)throw Error('Controller project inputs or source scene changed during navigation. Reopen the controller.');
 const fresh=controllerNavigationTarget(record,context,target.pc);
 if(fresh.id!==target.id||fresh.sceneId!==target.sceneId||fresh.sourceHash!==target.sourceHash)throw Error('Controller source record changed during navigation. Refresh resources.');
 return fresh;
}
