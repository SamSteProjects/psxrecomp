import assert from 'node:assert/strict';
import {createAssetResourceDiscovery,resourceAssetCategories} from '../editor/asset-resource-discovery.js';
let context={key:'scene-a',eligible:true,busy:false,loaded:false,pending:false},tasks=[],calls=0,errors=[];
const controller=createAssetResourceDiscovery({getContext:()=>context,schedule:work=>tasks.push(work),load:async()=>{calls++;},onError:e=>errors.push(e)});
assert(resourceAssetCategories.has('animation'));assert(!resourceAssetCategories.has('model'));assert(!resourceAssetCategories.has('all'));
assert(controller.request());assert.equal(controller.request(),false);await tasks.shift()();assert.equal(calls,1);assert.equal(controller.request(),false);
assert(controller.request(true));await tasks.shift()();assert.equal(calls,2);
context={...context,key:'scene-b'};assert(controller.request());context={...context,key:'scene-c'};assert(controller.request());await tasks.shift()();assert.equal(calls,2);await tasks.shift()();assert.equal(calls,3);
for(const field of ['busy','loaded','pending']){context={...context,key:field,[field]:true};assert.equal(controller.request(),false);context[field]=false;}
context={...context,key:'scope',eligible:true};assert(controller.request());context.eligible=false;await tasks.shift()();assert.equal(calls,3);context.eligible=true;assert(controller.request());context.busy=true;await tasks.shift()();assert.equal(calls,3);context.busy=false;assert(controller.request());await tasks.shift()();assert.equal(calls,4);
context={...context,key:'disposed'};assert(controller.request());controller.dispose();await tasks.shift()();assert.equal(calls,4);assert.equal(controller.request(true),false);
let failed=0;tasks=[];const failure=createAssetResourceDiscovery({getContext:()=>({key:'error',eligible:true}),schedule:work=>tasks.push(work),load:async()=>{failed++;throw Error('source failure');},onError:e=>errors.push(e.message)});assert(failure.request());await tasks.shift()();assert.equal(failed,1);assert.equal(failure.request(),false);assert(failure.request(true));await tasks.shift()();assert.equal(failed,2);assert.deepEqual(errors,['source failure','source failure']);
console.log('Asset resource discovery: once per source, explicit retry, busy/pending/cache guards, queued scene/scope rejection, disposal and no error retry loops passed.');
