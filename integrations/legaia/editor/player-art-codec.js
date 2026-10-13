const fail = () => { throw Error('PLAYER art ME archive or channel codec source is malformed.'); };

export function decodeArtChannels(source) {
  if (!(source instanceof Uint8Array) || source.length < 7 || source.length > 0x7fff || (source[0] & 0xc0) !== 0x40) fail();
  const view = new DataView(source.buffer,source.byteOffset,source.byteLength), nibbleAt = 5+view.getUint16(1,true), byteAt = 5+view.getUint16(3,true);
  if (nibbleAt < 5 || byteAt < nibbleAt || byteAt+2 > source.length) fail();
  const parts = source[byteAt], frames = source[byteAt+1];
  if (parts < 1 || parts > 64 || frames < 1) fail();
  let bitCursor = 0, nibbleCursor = 0, byteCursor = byteAt+2;
  const bit = () => { const at = 5+(bitCursor>>3); if (at >= nibbleAt) fail(); const value = (source[at] >> (7-(bitCursor&7))) & 1; bitCursor++; return value; };
  const nibble = () => { const at = nibbleAt+(nibbleCursor>>1); if (at >= byteAt) fail(); const value = (source[at] >> ((nibbleCursor&1) ? 0 : 4)) & 15; nibbleCursor++; return value; };
  const low = () => { if (byteCursor >= source.length) fail(); return source[byteCursor++]; };
  const channels = parts*6, previous = new Uint16Array(channels), accumulated = new Uint16Array(channels), result = new Uint8Array(2+parts*frames*9);
  result[0] = parts; result[1] = frames;
  for (let frame=0;frame<frames;frame++) {
    for (let channel=0;channel<channels;channel++) {
      const parent = previous[(channel+channels-6)%channels]; let delta;
      if (bit()) delta = (nibble()<<8) | low();
      else if (bit()) delta = parent+nibble();
      else if (bit()) delta = parent+(nibble() | 0xff0);
      else if (bit()) delta = nibble();
      else delta = nibble() | 0xff0;
      previous[channel] = delta;
    }
    for (let channel=0;channel<channels;channel++) accumulated[channel] = previous[channel]+(frame ? accumulated[channel] : channel < 6 ? 0 : accumulated[channel-6]);
    for (let part=0;part<parts;part++) for (let pair=0;pair<3;pair++) {
      const a = accumulated[part*6+pair*2], b = accumulated[part*6+pair*2+1], at = 2+(frame*parts+part)*9+pair*3;
      result[at] = a; result[at+1] = b; result[at+2] = ((a>>8)&15) | ((b>>4)&0xf0);
    }
  }
  return result;
}

export function decodeArtArchive(source) {
  if (!(source instanceof Uint8Array) || source.length < 3 || source.length > 0x10800 || source[0] !== 77 || source[1] !== 69 || !source[2]) fail();
  const count = source[2], view = new DataView(source.buffer,source.byteOffset,source.byteLength), result = []; let at = 3+count*2;
  if (at > source.length) fail();
  for (let index=0;index<count;index++) {
    const word = view.getUint16(3+index*2,true), size = word & 0x7fff;
    if (!size || at+size > source.length) fail();
    const body = source.slice(at,at+size), decoded = (word & 0x8000) ? decodeArtChannels(body) : body;
    if (decoded.length < 2 || decoded[0] < 1 || decoded[0] > 64 || !decoded[1] || decoded.length !== 2+decoded[0]*decoded[1]*9) fail();
    result.push({entry_index:index,size_word:word,compressed:!!(word&0x8000),byte_offset:at,byte_length:size,decoded}); at += size;
  }
  return result;
}

export function encodeArtChannels(decoded,flags=0x40){
  if(!(decoded instanceof Uint8Array)||decoded.length<2||decoded[0]<1||decoded[0]>64||!decoded[1]||decoded.length!==2+decoded[0]*decoded[1]*9||!Number.isSafeInteger(flags)||flags<0x40||flags>0x7f)fail();
  const parts=decoded[0],frames=decoded[1],count=parts*6,delta=new Uint16Array(count),acc=new Uint16Array(count),bits=[],operands=[],lows=[];
  for(let f=0;f<frames;f++){
    const wanted=[];for(let p=0;p<parts;p++)for(let pair=0;pair<3;pair++){const at=2+(f*parts+p)*9+pair*3;wanted.push(decoded[at]|(decoded[at+2]&15)<<8,decoded[at+1]|(decoded[at+2]>>4)<<8);}
    for(let c=0;c<count;c++){
      const anchor=f?acc[c]:c<6?0:wanted[c-6],value=(wanted[c]-anchor)&4095,previous=delta[(c+count-6)%count],difference=(value-previous)&4095;let selector,operand,actual;
      if(difference<16){selector=[0,1];operand=difference;actual=previous+difference;}
      else if(difference>=4080){selector=[0,0,1];operand=difference&15;actual=previous+(operand|4080);}
      else if(value<16){selector=[0,0,0,1];operand=value;actual=value;}
      else if(value>=4080){selector=[0,0,0,0];operand=value&15;actual=value;}
      else{selector=[1];operand=value>>8;actual=value;lows.push(value&255);}
      bits.push(...selector);operands.push(operand);delta[c]=actual;
    }
    for(let c=0;c<count;c++)acc[c]=delta[c]+(f?acc[c]:c<6?0:acc[c-6]);
  }
  const bitSize=Math.ceil(bits.length/8),nibSize=Math.ceil(operands.length/2),result=new Uint8Array(7+bitSize+nibSize+lows.length);if(result.length>32767)fail();
  result[0]=flags;const view=new DataView(result.buffer);view.setUint16(1,bitSize,true);view.setUint16(3,bitSize+nibSize,true);
  bits.forEach((b,i)=>result[5+(i>>3)]|=b<<(7-(i&7)));operands.forEach((n,i)=>result[5+bitSize+(i>>1)]|=n<<((i&1)?0:4));result.set([parts,frames,...lows],5+bitSize+nibSize);
  const replay=decodeArtChannels(result);if(!replay.every((b,i)=>b===decoded[i]))fail();return result;
}

export function replaceArtEntry(source,index,decoded){
  const rows=decodeArtArchive(source),row=rows[index];if(!Number.isSafeInteger(index)||!row||!(decoded instanceof Uint8Array)||decoded.length!==row.decoded.length||decoded[0]!==row.decoded[0]||decoded[1]!==row.decoded[1])fail();
  const result=source.slice();if(decoded.every((b,i)=>b===row.decoded[i]))return result;
  const encoded=row.compressed?encodeArtChannels(decoded,source[row.byte_offset]):decoded;if(encoded.length>row.byte_length)fail();result.set(encoded,row.byte_offset);
  const replay=decodeArtArchive(result);for(let i=0;i<rows.length;i++)if(replay[i].size_word!==rows[i].size_word||replay[i].byte_offset!==rows[i].byte_offset||!replay[i].decoded.every((b,n)=>b===(i===index?decoded:rows[i].decoded)[n]))fail();return result;
}
