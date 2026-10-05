import assert from 'node:assert/strict';
import {scriptComponentResetReview} from '../editor/script-component-reset.js';
const owner='scene://fixture/actors/man-p1/0001',entry='script://fixture/actors/man-p1/0001/wait/0000';
const authored={entries:{[entry]:{duration_ticks:17}}},entity={id:owner,components:{ScriptWaits:authored}};
const state={project:{mode:'edit'},scene:{entities:[entity]},authored_assets:[{id:owner,component_reviews:[{component:'ScriptWaits',authored,review_key:'a'.repeat(64)}]}]};
const before=JSON.stringify(state),review=scriptComponentResetReview(state,entity,'ScriptWaits');
assert.equal(review.owner,owner);assert.equal(review.component,'ScriptWaits');assert.equal(review.entries[entry].duration_ticks,17);
review.entries[entry].duration_ticks=99;assert.equal(JSON.stringify(state),before);
for(const component of ['Transform','__proto__','constructor',null])assert.throws(()=>scriptComponentResetReview(state,entity,component));
for(const mutate of [s=>s.project.mode='live',s=>s.scene.entities=[],s=>s.authored_assets=[],s=>s.authored_assets[0].component_reviews[0].review_key='bad',s=>s.authored_assets[0].component_reviews[0].authored={entries:{[entry]:{duration_ticks:18}}}]){
  const copy=JSON.parse(before);mutate(copy);assert.throws(()=>scriptComponentResetReview(copy,entity,'ScriptWaits'));
}
console.log('Script reset review is detached, family-bounded and rejects missing/stale witnesses.');
for(const component of ['ScriptFacing','ScriptBranches']){
  const copy=JSON.parse(before),entries={[entry]:{fixture:1}};
  copy.scene.entities[0].components={[component]:{entries}};
  copy.authored_assets[0].component_reviews=[{component,authored:{entries},review_key:'b'.repeat(64)}];
  assert.equal(scriptComponentResetReview(copy,entity,component).component,component);
}
