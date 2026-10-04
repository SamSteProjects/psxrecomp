"""Source-bound TIM image allocation, preserving mode, CLUT layout and VRAM origin."""
from hashlib import sha256
import struct

from .core import ImportError
from .textures import parse_tim

MAX_TIM_BYTES = 1024 * 1024


def _tim(content):
    if not isinstance(content,bytes) or not 1<=len(content)<=MAX_TIM_BYTES:
        raise ImportError('Texture allocation requires immutable TIM bytes of at most 1 MiB')
    tim=parse_tim(content)
    if tim.byte_length!=len(content):
        raise ImportError('Texture allocation requires exactly one TIM without trailing bytes')
    return tim


def validate_tim_allocation(source, candidate):
    """Qualify image dimensions/payload changes; no mode or placement inference."""
    old,new=_tim(source),_tim(candidate)
    if source[:8]!=candidate[:8] or (old.image.x,old.image.y)!=(new.image.x,new.image.y):
        raise ImportError('Texture allocation must preserve TIM flags and image VRAM origin')
    if old.clut is not None and source[8:20]!=candidate[8:20]:
        raise ImportError('Texture allocation must preserve CLUT headers and allocation')
    return dict(source_sha256=sha256(source).hexdigest(),proposed_sha256=sha256(candidate).hexdigest(),
                source_byte_length=len(source),proposed_byte_length=len(candidate),
                before=dict(width=old.width,height=old.image.height,width_words=old.image.width_words),
                after=dict(width=new.width,height=new.image.height,width_words=new.image.width_words),
                bpp=old.bpp,image_origin=dict(x=old.image.x,y=old.image.y),
                changed=source!=candidate,layout_changed=old.image.metadata()!=new.image.metadata(),
                scope='TIM-image-allocation-fixed-mode-and-VRAM-origin',gameplay_verified=False)


def resize_tim_image(source, expected_sha256, width, height, fill_value=0, resize_mode="crop-fill"):
    """Resize with top-left crop/fill or nearest encoded-pixel scaling.

    Indexed fill values are palette indices, 16-bpp values are raw PSX words,
    and 24-bpp values are raw RGB bytes in little-endian order. Nearest scaling
    copies encoded pixels; crop-fill retains the top-left overlap. Neither mode
    edits palettes, retargets UVs or assumes runtime upload order.
    Nearest maps destination pixel centers to source pixels using integer math.
    """
    old=_tim(source)
    if type(resize_mode) is not str or resize_mode not in ('crop-fill','nearest'):
        raise ImportError('Choose crop-fill or nearest texture resizing')
    if resize_mode=='nearest' and (type(fill_value) is not int or fill_value!=0):
        raise ImportError('Nearest resizing requires zero unused fill value')
    if sha256(source).hexdigest()!=expected_sha256:
        raise ImportError('Texture allocation source hash changed')
    if (type(width) is not int or type(height) is not int or width<1 or height<1 or
            width*old.bpp%16 or not 1<=width*old.bpp//16<=1024 or height>512 or
            old.image.x+width*old.bpp//16>1024 or old.image.y+height>512):
        raise ImportError('Texture dimensions must contain whole native words and remain within VRAM')
    if type(fill_value) is not int or not 0<=fill_value<(1<<old.bpp):
        raise ImportError('Choose an encoded fill value for the existing texture mode')
    words=width*old.bpp//16;stride=words*2;old_stride=old.image.width_words*2
    prefix=8+(12+len(old.clut.data) if old.clut else 0)
    if prefix+12+stride*height>MAX_TIM_BYTES:
        raise ImportError('Resized TIM exceeds the 1 MiB allocation budget')
    fill=(bytes([fill_value|(fill_value<<4)]) if old.bpp==4 else
          fill_value.to_bytes(old.bpp//8,'little'))
    data=bytearray(fill*(stride*height//len(fill)))
    for row in range(min(height,old.image.height)):
        count=min(stride,old_stride)
        data[row*stride:row*stride+count]=old.image.data[row*old_stride:row*old_stride+count]
    if resize_mode=='nearest':
        # Copy complete encoded pixels. Indexed values never pass through RGB,
        # and PSX16 STP bits and RGB24 channel bytes retain their exact values.
        data=bytearray(stride*height)
        for y in range(height):
            sy=min(old.image.height-1,(2*y+1)*old.image.height//(2*height))
            for x in range(width):
                sx=min(old.width-1,(2*x+1)*old.width//(2*width))
                if old.bpp==4:
                    value=(old.image.data[sy*old_stride+sx//2]>>(4*(sx%2)))&15
                    data[y*stride+x//2]|=value<<(4*(x%2))
                else:
                    count=old.bpp//8;start=sy*old_stride+sx*count;target=y*stride+x*count
                    data[target:target+count]=old.image.data[start:start+count]
    candidate=source[:prefix]+struct.pack('<I4H',12+len(data),old.image.x,old.image.y,words,height)+bytes(data)
    return candidate,validate_tim_allocation(source,candidate)
