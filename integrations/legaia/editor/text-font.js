/** Bounded source-glyph runs; no controls, boxes, pager or wrapping simulation. */
export function decodeTextFont(data,owner,manHash){
  if(data?.schema!=='legaia.dialogue-font.v1'||data.owner_id!==owner||data.decoded_man_sha256!==manHash||
     data.representation!=='source-glyph-stencil'||data.atlas_width!==224||data.atlas_height!==210||
     data.glyph_width!==14||data.glyph_height!==15||data.columns!==16||data.first_byte!==32||data.inter_glyph_pad!==1||
     !Array.isArray(data.widths)||data.widths.length!==256||data.widths.some(v=>!Number.isInteger(v)||v<0||v>255)||
     typeof data.rgba_base64!=='string'||data.rgba_base64.length!==250880||!/^[A-Za-z0-9+/]+$/.test(data.rgba_base64))throw new Error('Font preview source, dimensions or payload are invalid/stale.');
  const bytes=Uint8ClampedArray.from(atob(data.rgba_base64),c=>c.charCodeAt(0));
  if(bytes.length!==188160)throw new Error('Font stencil byte length mismatch.');
  return {widths:[...data.widths],rgba:bytes};
}
export function layoutGlyphRun(font,text){
  if(!font||!Array.isArray(font.widths)||font.widths.length!==256||font.widths.some(v=>!Number.isInteger(v)||v<0||v>255)||
     typeof text!=='string'||text.length>4096||!/^[\x20-\x7e]*$/.test(text)||text.includes('^')||text.includes('|'))throw new Error('Glyph preview requires supported plain text.');
  const glyphs=[];let advance=0,right=0,shown=0;
  for(let i=0;i<text.length;i++){
    const code=text.charCodeAt(i);
    if(i<128&&advance<4096){
      if(code!==32){glyphs.push({code,x:advance,atlas_x:(code&15)*14,atlas_y:((code-32)>>4)*15});right=Math.max(right,Math.min(4096,advance+14));}
      shown++;
    }
    advance+=font.widths[code]+1;
  }
  return {advance,glyphs,canvas_width:Math.max(1,Math.min(4096,Math.max(right,advance))),shown_characters:shown,text_length:text.length,truncated:shown<text.length};
}
