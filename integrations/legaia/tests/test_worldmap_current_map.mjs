import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {qualifyCurrentWorldMap as qualify,composeWorldMapCoauthors as compose} from '../editor/worldmap-current-map.js';
import {qualifyCurrentWorldMan} from '../editor/worldmap-current-man.js';
const pairs=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),bytes=s=>new Uint8Array(Buffer.from(s,'base64'));
const hash=b=>createHash('sha256').update(b).digest('hex');let refusals=0;
function matching(a,b,key=''){
  if(key==='source_to_world'){a.forEach((v,i)=>assert.ok(Math.abs(v-b[i])<=1e-12));return;}
  if(Array.isArray(b)){assert.equal(a.length,b.length);b.forEach((v,i)=>matching(a[i],v));return;}
  if(b&&typeof b==='object'){assert.deepEqual(Object.keys(a).sort(),Object.keys(b).sort());Object.keys(b).forEach(k=>matching(a[k],b[k],k));return;}
  assert.deepEqual(a,b);
}
for(const c of pairs.synthetic){
  const raw=bytes(c.raw),normal=bytes(c.normal),man=bytes(c.man),held=JSON.stringify(c);
  assert.deepEqual(await compose(raw,normal,'map01',c.components,man),bytes(c.expected));
  const expected=bytes(c.expected),at=expected.findIndex((v,i)=>v!==raw[i]);
  if(at>=0){const conflict=normal.slice();conflict[at]=raw[at]===1||expected[at]===1?2:1;
    const name=Object.keys(c.components)[0];
    // A wall bit has only two states; its independent bit merge cannot have
    // a third conflicting value. Test full fields and the floor nibble.
    if(name!=='Collision'){
      await assert.rejects(()=>compose(raw,conflict,'map01',c.components,man));refusals++;
    }
  }
  for(const name of Object.keys(c.components)){
    for(const kind of ['hash','duplicate','extra','domain']){
      const bad=structuredClone(c.components),b=bad[name];
      if(kind==='hash')b.source_sha256='0'.repeat(64);
      if(kind==='duplicate')b.edits.push(structuredClone(b.edits[0]));
      if(kind==='extra')b.extra=true;
      if(kind==='domain'){
        const e=b.edits[0];if(name==='Environment')e.offset.z=true;else if(name==='Collision')e.blocked=1;else if(name==='FloorTiers')e.tier=16;else if(name==='RegionBounds')e.x0=256;else if(name==='TriggerCells')e.tile_x=-1;else e.script_sha256='0'.repeat(64);
      }
      await assert.rejects(()=>compose(raw,normal,'map01',bad,man));refusals++;
    }
  }
  assert.deepEqual(raw,bytes(c.raw));assert.deepEqual(normal,bytes(c.normal));assert.equal(JSON.stringify(c),held);
  console.log(c.name,'native MAP coauthors match');
}
for(const c of pairs.cases){
  const held=JSON.stringify(c),man=await qualifyCurrentWorldMan(c.man,c.retail,c.options),result=await qualify(c.value,c.retail,man,c.options);
  assert.deepEqual(result.current,bytes(c.value.current_map_base64));assert.deepEqual(result.normal,bytes(c.value.normal_map_base64));
  matching(result.scripted,c.placement.authored_scripted_placements);matching(result.decorations,c.placement.authored_decorations);
  for(const key of ['source_key','project_path','normal_map_sha256','current_man_sha256','scene']){
    const bad=structuredClone(c.value);bad[key]='wrong';await assert.rejects(()=>qualify(bad,c.retail,man,c.options));refusals++;
  }
  for(const key of ['normal_map_base64','current_map_base64']){
    const bad=structuredClone(c.value),data=bytes(bad[key]);data[0]^=1;bad[key]=Buffer.from(data).toString('base64');bad[key==='normal_map_base64'?'normal_map_sha256':'current_map_sha256']=hash(data);
    await assert.rejects(()=>qualify(bad,c.retail,man,c.options));refusals++;
  }
  const ledger=structuredClone(c.value),options=structuredClone(c.options);
  ledger.scripted_binding.operations[0].proposed_map_sha256='0'.repeat(64);options.overrides[`worldmap://${c.value.scene}/scripted-placement-allocations`].WorldMapScriptedPlacementAllocations=structuredClone(ledger.scripted_binding);
  await assert.rejects(()=>qualify(ledger,c.retail,man,options));refusals++;
  const extra=structuredClone(c.value);extra.scene_components.Unsupported={};await assert.rejects(()=>qualify(extra,c.retail,man,c.options));refusals++;
  const badFloor=structuredClone(man);badFloor.floor[0]++;
  await assert.rejects(()=>qualify(c.value,c.retail,badFloor,c.options));refusals++;
  assert.equal(JSON.stringify(c),held);console.log(c.name,'complete Current MAP and authored audits match');
}
const proof={synthetic_cases:pairs.synthetic.length,native_cases:pairs.cases.length,refusals,complete_maps_and_authored_audits_match:true,inputs_unchanged:true,browser_rendered:false,gameplay_verified:false};
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
