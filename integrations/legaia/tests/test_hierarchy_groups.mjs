import assert from 'node:assert/strict';
import {hierarchyGroupExpanded} from '../editor/hierarchy-groups.js';
const state={collapsed:new Set(['actors','script'])};
assert.equal(hierarchyGroupExpanded('actors',state),false);assert.equal(hierarchyGroupExpanded('environment',state),true);
assert.equal(hierarchyGroupExpanded('actors',state,'actor 0002'),true);assert.equal(hierarchyGroupExpanded('actors',state,'  '),false);
assert.deepEqual([...state.collapsed],['actors','script']);
for(const id of ['Unknown','__proto__','constructor',null])assert.throws(()=>hierarchyGroupExpanded(id,state));
assert.throws(()=>hierarchyGroupExpanded('actors',{collapsed:[]}));
console.log('Hierarchy folds use explicit UI groups; search expands presentation without changing saved folds.');
