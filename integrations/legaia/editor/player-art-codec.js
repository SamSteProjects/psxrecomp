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
