const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
export function qualifyScriptBookmark(row,owner,report){
  if(!row||row.owner_id!==owner||!hash(row.source_record_sha256)||row.source_record_sha256!==report?.record?.sha256||report.read_only!==true||!Number.isInteger(row.pc)||row.pc<0||row.pc>65535)throw new Error('Bookmark differs from this verified Retail script record.');
  const matches=(report.instructions??[]).filter(item=>item.pc===row.pc).map(item=>item.mnemonic).concat((report.dialogues??[]).filter(item=>item.pc===row.pc).map(()=>'DIALOGUE_SEGMENT'));
  if(matches.length!==1||matches[0]!==row.mnemonic)throw new Error('Bookmark no longer identifies a unique decoded Retail boundary.');
  return row.pc;
}
