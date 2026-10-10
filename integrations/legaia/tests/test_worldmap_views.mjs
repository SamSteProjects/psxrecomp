import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeWorldViewReview} from '../editor/worldmap-views.js';
const out=process.argv[2];assert(out,'Pass the private native workflow evidence directory');
for(const scene of ['map01','map02','map03']){
 const read=name=>JSON.parse(fs.readFileSync(`${out}/${scene}-${name}.json`));
 const saved=read('saved'),report=read('geometry'),review=read('review'),held=structuredClone([saved,report,review]);
 assert.deepEqual(decodeWorldViewReview(review,saved,report),saved.display);
 const detached=decodeWorldViewReview(review,saved,report);detached.camera.target.x++;assert.deepEqual([saved,report,review],held);
 const mutations=[v=>v.source_key='0'.repeat(64),v=>v.review_key='0'.repeat(64),v=>v.read_only=false,v=>v.extra=true,v=>v.view.source_record.map_sha256='0'.repeat(64),v=>v.view.binding.source_instance_ids.pop(),v=>v.view.display.selected_id=`scene://map01/worldmap/ground`,v=>v.view.display.camera.distance=Infinity,v=>v.view.display.scope='foreign',v=>v.view.display.models=1];
 for(const mutate of mutations){const bad=structuredClone(review);mutate(bad);assert.throws(()=>decodeWorldViewReview(bad,saved,report));}
 // A self-consistent forged saved/review pair still must match loaded native ownership.
 for(const mutate of [v=>v.binding.source_instance_ids.pop(),v=>v.source_record.map_sha256='0'.repeat(64),v=>v.binding.asset_id='asset://foreign',v=>v.display.camera.distance=Infinity,v=>v.display.models=1,v=>v.binding.entity_sha256='invalid']){
  const bad=structuredClone(saved);mutate(bad);const {review_key,...entry}=bad;assert.throws(()=>decodeWorldViewReview({...review,view:entry},bad,report));
 }
}
console.log('Three native saved World view reviews: detached exact recall and sixteen forged variants each refused.');
