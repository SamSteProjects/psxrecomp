// VAB tone words at +16/+18; bit layout checked against pinned Andrew
// d6e64c68, crates/engine-audio/src/spu/adsr.rs and runtime/src/spu.c.
// These are register fields, not a synthesized envelope or runtime assignment.
const definitions={
 adsr1:[['attack_mode','Attack mode',15,1,['Linear','Exponential']],['attack_shift','Attack shift',10,31],['attack_step','Attack step code',8,3],['decay_shift','Decay shift',4,15],['sustain_level','Sustain level code',0,15]],
 adsr2:[['sustain_mode','Sustain mode',15,1,['Linear','Exponential']],['sustain_direction','Sustain direction',14,1,['Increase','Decrease']],['sustain_shift','Sustain shift',8,31],['sustain_step','Sustain step code',6,3],['release_mode','Release mode',5,1,['Linear','Exponential']],['release_shift','Release shift',0,31]]
};
const integer=(value,max)=>Number.isSafeInteger(value)&&value>=0&&value<=max;
export function decodeAdsrWord(field,word){
 if(!Object.hasOwn(definitions,field)||!integer(word,65535))throw Error('ADSR requires an exact native word and unsigned sixteen-bit value.');
 return definitions[field].map(([key,label,shift,max,choices])=>({key,label,shift,max,value:(word>>>shift)&max,...(choices?{choices:[...choices]}:{})}));
}
export function editAdsrWord(field,word,key,value){
 const row=decodeAdsrWord(field,word).find(row=>row.key===key);
 if(!row||!integer(value,row.max))throw Error('ADSR field is outside its encoded integer range.');
 const mask=row.max<<row.shift;
 return (word&~mask)|(value<<row.shift);
}
export function describeAdsrWord(field,word){
 const rows=decodeAdsrWord(field,word),text=rows.map(row=>row.label+': '+(row.choices?.[row.value]??row.value)).join(' · ');
 return text+(field==='adsr2'?' · Held reserved bit 13: '+((word>>>13)&1):' · Encoded sustain target: '+(((word&15)+1)*2048));
}
