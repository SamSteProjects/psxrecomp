"""Derived TIM adapter for native monster pool PNG interchange.

Synthetic zero origins are converter coordinates only, not retail TIM/VRAM
ownership. The original fifteen-palettes/page layout remains native-owned.
"""
import struct
from .core import ImportError
from .texture_authoring import _validate
from .texture_png import export_texture_png,import_texture_png


def to_tim(pool,width):
    if width not in (128,256) or len(pool)!=480+width*128:raise ImportError('Monster PNG adapter requires its exact native pool')
    return struct.pack('<III4H',16,8,492,0,0,16,15)+pool[:480]+struct.pack('<I4H',12+len(pool)-480,0,0,width//4,256)+pool[480:]


def export(pool,width,palette_index):return export_texture_png(to_tim(pool,width),palette_index)


def convert(pool,width,palette_index,png,mode,stp=None):
    original=to_tim(pool,width);_,_,profile=export_texture_png(original,palette_index)
    candidate,analysis=import_texture_png(original,png,profile,mode,stp);_validate(original,candidate)
    return candidate[20:500]+candidate[512:],analysis
