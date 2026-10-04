"""Explicit TIM-local palette and page regions; no VRAM residency inference."""
from .core import ImportError
from .textures import parse_tim


def texture_material_pages(content,palette_index):
    tim=parse_tim(content)
    if tim.byte_length!=len(content) or tim.bpp not in (4,8,16):
        raise ImportError('Material assignment requires one complete 4, 8 or 16-bit TIM')
    if type(palette_index) is not int or palette_index<0:
        raise ImportError('Choose an existing integer TIM palette index')
    image=tim.image
    if image.x+image.width_words>1024 or image.y+image.height>512:
        raise ImportError('Texture image must fit native VRAM bounds')
    values=dict(texture_bpp=tim.bpp);palettes=0;origin=None
    if tim.bpp in (4,8):
        count=1<<tim.bpp
        palettes=len(tim.clut.data)//(count*2) if tim.clut else 0
        if palette_index>=palettes:
            raise ImportError('Texture has no complete requested TIM-local palette')
        clut=tim.clut;x=clut.x+palette_index*count
        if clut.x+clut.width_words*clut.height>1024 or x%16 or x+count>1024 or not 0<=clut.y<512:
            raise ImportError('Texture palette requires an aligned, unclipped native CLUT strip')
        origin=dict(x=x,y=clut.y);values.update(clut_column=x//16,clut_row=clut.y)
    elif palette_index:
        raise ImportError('Direct-color textures require palette index zero')
    pages=[];page_words=256*tim.bpp//16
    for py in range(image.y//256*256,image.y+image.height,256):
        for px in range(image.x//64*64,image.x+image.width_words,page_words):
            left=max(px,image.x);top=max(py,image.y);right=min(px+page_words,image.x+image.width_words);bottom=min(py+256,image.y+image.height)
            pages.append(dict(page_index=len(pages),values=dict(values,page_column=px//64,page_row=py//256),
                uv_rectangle=[(left-px)*16//tim.bpp,top-py,(right-px)*16//tim.bpp-1,bottom-py-1],
                image_rectangle=dict(x=left,y=top,width_words=right-left,height=bottom-top)))
    return dict(palette_count=palettes,palette_origin=origin,pages=pages)
