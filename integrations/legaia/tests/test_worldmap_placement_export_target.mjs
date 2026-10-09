import assert from 'node:assert/strict';
import {worldPlacementExportTarget} from '../editor/worldmap-placement-state.js';
const entity='scene://map02/worldmap/placements/1234',report={scene:'map02',source_key:'a'.repeat(64),records:[{record_id:'0461',placements:[{entity_id:entity}]}]};
for(const scope of ['source-scene','ground'])assert.deepEqual(worldPlacementExportTarget(report,'0461',entity,scope),{scope,entityId:null});
assert.deepEqual(worldPlacementExportTarget(report,'0461',entity,'selected'),{scope:'selected',entityId:entity});
for(const args of [[report,'0461',entity,'unknown'],[report,'0460',entity,'selected'],[report,'0461','scene://map01/worldmap/placements/1234','selected'],[report,'0461','scene://map02/worldmap/placements/4000','selected'],[{...report,source_key:'bad'},'0461',entity,'selected'],[{...report,records:[...report.records,...report.records]},'0461',entity,'selected']])assert.throws(()=>worldPlacementExportTarget(...args));
console.log('Placement export scopes and exact affected-anchor ownership qualified.');
