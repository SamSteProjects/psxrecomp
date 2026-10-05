import assert from 'node:assert/strict';
import {qualifyScriptBookmark} from '../editor/script-bookmarks.js';
const owner='scene://town01/actors/man-p1/0044',sha='a'.repeat(64),report={read_only:true,record:{sha256:sha},instructions:[{pc:5,mnemonic:'WAIT_FRAMES'}],dialogues:[{pc:12}]};
const row={owner_id:owner,source_record_sha256:sha,pc:5,mnemonic:'WAIT_FRAMES'};
assert.equal(qualifyScriptBookmark(row,owner,report),5);
assert.equal(qualifyScriptBookmark({...row,pc:12,mnemonic:'DIALOGUE_SEGMENT'},owner,report),12);
for(const changed of [{owner_id:'other'},{source_record_sha256:'b'.repeat(64)},{pc:true},{pc:6},{pc:-1},{pc:65536},{mnemonic:'RETURN'}])assert.throws(()=>qualifyScriptBookmark({...row,...changed},owner,report));
assert.throws(()=>qualifyScriptBookmark(row,owner,{...report,read_only:false}));
assert.throws(()=>qualifyScriptBookmark(row,owner,{...report,dialogues:[{pc:5}]}));
assert.deepEqual(row,{owner_id:owner,source_record_sha256:sha,pc:5,mnemonic:'WAIT_FRAMES'});
console.log('Script bookmark recall requires exact original source, owner and unique decoded boundary.');

assert.equal(qualifyScriptBookmark({...row,pc:65535},owner,{...report,instructions:[{pc:65535,mnemonic:row.mnemonic}]}),65535);
