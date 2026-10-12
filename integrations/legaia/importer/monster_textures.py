"""Native monster pool palettes and source-local material crops.

Pinned monster_archive/mesh.rs: fifteen BGR555 CLUTs then a 256-row 4bpp
page. Exact tail sizes qualify 128/256 widths; unknown layouts remain explicit.
No runtime VRAM placement, texture window or neighbor-page bytes are inferred.
"""
from hashlib import sha256
import struct
from .core import ImportError

CLUT_BYTES=480
HEIGHT=256


def layout(data,offset):
    if type(offset) is not int or offset<0x4c or offset>=len(data):raise ImportError('Monster texture pool pointer is unqualified')
    pool=data[offset:]
    if len(pool) not in (CLUT_BYTES+64*HEIGHT,CLUT_BYTES+128*HEIGHT):raise ImportError('Monster pool tail does not match a qualified fifteen-palette 4bpp page')
    return pool,(len(pool)-CLUT_BYTES)//HEIGHT*2


def pixels(pool,width,palette_index,bounds=None):
    if width not in (128,256) or len(pool)!=CLUT_BYTES+width//2*HEIGHT or type(palette_index) is not int or not 0<=palette_index<15:raise ImportError('Monster palette/page selection is unqualified')
    bounds=(0,0,width-1,255) if bounds is None else bounds
    if len(bounds)!=4 or any(type(n) is not int for n in bounds):raise ImportError('Monster source crop requires whole UV bounds')
    u0,v0,u1,v1=bounds
    if not 0<=u0<=u1<width or not 0<=v0<=v1<HEIGHT:raise ImportError('Monster UV crop exceeds its own source page')
    words=struct.unpack_from('<16H',pool,palette_index*32);rgba=bytearray();stp=bytearray()
    for y in range(v0,v1+1):
        for x in range(u0,u1+1):
            nibble=pool[CLUT_BYTES+y*(width//2)+x//2]>>((x&1)*4)&15;word=words[nibble]
            rgba.extend([((word>>(c*5))&31)*8+(((word>>(c*5))&31)>>2) for c in range(3)]+[0 if word==0 else 255]);stp.append(word>>15)
    return dict(width=u1-u0+1,height=v1-v0+1,uv_origin=[u0,v0],palette_index=palette_index,words=list(words),rgba=bytes(rgba),stp=bytes(stp))


def material_crops(geometry,pool,width,source_id):
    out=[]
    for index,material in enumerate(geometry['materials']):
        if not material.get('textured'):
            out.append(dict(material_index=index,status='untextured',reason='Material uses native vertex colors'));continue
        palette=material['clut']&63;uvs=[uv for i,face in enumerate(geometry['triangle_uvs']) if geometry['triangle_materials'][i]==index for uv in (face or [])]
        if not uvs or palette>=15 or (material['tpage']>>7)&3:
            out.append(dict(material_index=index,status='unsupported',reason='Material palette, depth or UV source is unqualified'));continue
        bounds=(min(v[0] for v in uvs),min(v[1] for v in uvs),max(v[0] for v in uvs),max(v[1] for v in uvs))
        try:value=pixels(pool,width,palette,bounds)
        except ImportError as e:
            out.append(dict(material_index=index,status='unsupported',reason=str(e),palette_index=palette,uv_bounds=list(bounds)));continue
        value.pop('words');out.append(dict(value,material_index=index,status='source_pool_match',source_ids=[source_id],association='page_local_uv_and_source_clut_low6',pool_sha256=sha256(pool).hexdigest()))
    return out
