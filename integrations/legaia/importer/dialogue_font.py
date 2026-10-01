"""Private retail font stencil and advances, not dialogue/pager simulation.

Independent implementation from pinned font/lib.rs and dialog-font.md.
"""
import base64
import hashlib
import struct
from .core import ImportError
from .pipeline import REFERENCE_COMMIT, _disc_context
from .textures import parse_tim

FONT_OFFSET=0x7f40
FONT_READ=0x8100
WIDTH_RAM=0x80073f1c
ATLAS_WIDTH,ATLAS_HEIGHT=224,210


def decode_dialogue_font(font_tim: bytes, executable: bytes) -> dict:
    if not isinstance(font_tim,bytes) or not 0<len(font_tim)<=FONT_READ:
        raise ImportError('Font requires the bounded retail TIM slice')
    tim=parse_tim(font_tim)
    if (tim.bpp!=4 or (tim.image.x,tim.image.y,tim.image.width_words,tim.image.height)!=(896,0,64,256) or
        tim.clut is None or (tim.clut.x,tim.clut.y,tim.clut.width_words,tim.clut.height)!=(0,510,16,1)):
        raise ImportError('Font TIM does not match the pinned page and CLUT layout')
    if not isinstance(executable,bytes) or not 0x800<=len(executable)<=2*1024*1024 or executable[:8]!=b'PS-X EXE':
        raise ImportError('Font widths require a bounded PS-X executable')
    load=struct.unpack_from('<I',executable,0x18)[0]
    offset=0x800+WIDTH_RAM-load
    if WIDTH_RAM<load or not 0x800<=offset<=len(executable)-256:
        raise ImportError('Font width table is outside the executable')
    widths=list(executable[offset:offset+256])
    atlas=bytearray(ATLAS_WIDTH*ATLAS_HEIGHT*4)
    pixels=tim.image.data
    for code in range(0x20,0x100):
        sx,sy=(code&15)*16,(code&0xf0)-0x20
        dx,dy=(code&15)*14,((code-0x20)>>4)*15
        for y in range(15):
            for x in range(14):
                px=sx+x;value=pixels[(sy+y)*128+px//2]
                index=(value>>(4*(px&1)))&15
                rgba=(0,0,0,0) if index==0 else (32,32,32,255) if index==14 else (255,255,255,255)
                target=((dy+y)*ATLAS_WIDTH+dx+x)*4
                atlas[target:target+4]=bytes(rgba)
    return dict(schema='legaia.dialogue-font.v1',asset_id='asset://legaia/fonts/dialogue',
                representation='source-glyph-stencil',atlas_width=ATLAS_WIDTH,atlas_height=ATLAS_HEIGHT,
                glyph_width=14,glyph_height=15,columns=16,first_byte=32,
                inter_glyph_pad=1,widths=widths,rgba_base64=base64.b64encode(atlas).decode('ascii'),
                source=dict(reference_commit=REFERENCE_COMMIT,reference_paths=['crates/font/src/lib.rs','docs/formats/dialog-font.md'],
                            tim=dict(iso_file='PROT.DAT',file_offset=FONT_OFFSET,byte_length=tim.byte_length,
                                     sha256=hashlib.sha256(font_tim[:tim.byte_length]).hexdigest()),
                            widths=dict(iso_file='SCUS_942.54',ram_address=WIDTH_RAM,file_offset=offset,byte_length=256,
                                        sha256=hashlib.sha256(bytes(widths)).hexdigest(),executable_sha256=hashlib.sha256(executable).hexdigest())),
                limitations=['Only source-supported plain glyph runs are previewed; controls, substitutions, boxes and pager behavior are not simulated.',
                             'Index0 is transparent, index14 is dark shadow, other indices are white fill; runtime tint and palette selection are not observed.',
                             'Advances use the retail width table plus one pixel; preceding controls, run origin, wrapping and scene scale are not evaluated.'])


def load_dialogue_font(disc) -> dict:
    with _disc_context(disc) as (image,digest,_,archive):
        node=image.find('SCUS_942.54')
        if node.size>2*1024*1024:
            raise ImportError('Font executable exceeds read budget')
        raw=image.read_user(archive.node.extent_lba,FONT_OFFSET,FONT_READ,archive.node.size)
        result=decode_dialogue_font(raw,image.read_file(node))
        result['source']['disc_sha256']=digest
        return result
