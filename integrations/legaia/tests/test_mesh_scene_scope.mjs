import assert from 'node:assert/strict';
import {meshSceneScopeChoice} from '../editor/mesh-scene-scope.js';
const rows=[{entity_id:'wall-left',name:'Left wall'},{entity_id:'wall-right',name:'Right wall'}];
assert.deepEqual(meshSceneScopeChoice(rows,'all-model-instances'),{entity_id:'wall-left',all_instances:true});
assert.deepEqual(meshSceneScopeChoice(rows,'wall-right'),{entity_id:'wall-right',all_instances:false});
assert.equal(meshSceneScopeChoice(rows,'gone'),null);assert.equal(meshSceneScopeChoice([],'all-model-instances'),null);
for(const changed of [null,[{entity_id:''}],[{entity_id:'x'.repeat(513)}],[rows[0],rows[0]],Array(4097).fill(rows[0])])assert.throws(()=>meshSceneScopeChoice(changed,'all-model-instances'));
assert.deepEqual(rows,[{entity_id:'wall-left',name:'Left wall'},{entity_id:'wall-right',name:'Right wall'}]);
console.log('Exact one/all mesh inspection choices; missing, duplicate and bounded instance inventories fail closed.');
