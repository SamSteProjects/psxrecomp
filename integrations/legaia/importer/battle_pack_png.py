"""Bounded PNG interchange for real complete pack TIMs; fixed native VRAM layout."""
from hashlib import sha256
from copy import deepcopy
from .core import ImportError
from .battle_pack_palettes import source
from .texture_authoring import _validate
from .texture_png import export_texture_png,import_texture_png


def _current(original,catalog,record,current=None):
    retail=source(original,catalog,record)
    current=retail if current is None else current
    if not isinstance(current,bytes) or len(current)!=33312:raise ImportError('Pack PNG conversion requires the complete fixed TIM span')
    _validate(retail,current)
    if current[:20]!=retail[:20] or current[532:544]!=retail[532:544]:raise ImportError('Pack PNG conversion changed native headers or VRAM placement')
    return current


def export(original,catalog,record,palette_index,current=None):
    body=_current(original,catalog,record,current)
    if type(palette_index) is not int or not 0<=palette_index<16:raise ImportError('Choose an existing whole pack palette')
    return export_texture_png(body,palette_index)


def convert(original,catalog,record,palette_index,png,palette_mode,stp=None,current=None):
    before=_current(original,catalog,record,current)
    _,_,profile=export(original,catalog,record,palette_index,before)
    if palette_mode not in ('existing','rebuild'):raise ImportError('Choose existing or rebuilt pack palette mapping')
    candidate,analysis=import_texture_png(before,png,profile,palette_mode,stp)
    _current(original,catalog,record,candidate)
    at=20+palette_index*32;end=at+32
    if candidate[20:at]!=before[20:at] or candidate[end:532]!=before[end:532]:raise ImportError('Pack PNG conversion changed another local palette')
    return candidate,dict(schema_version='legaia.battle-pack-png-projection.v1',asset_id=record['semantic_id'],source_record=deepcopy(record['source_record']),
        palette_index=palette_index,palette_mode=palette_mode,current_tim_sha256=sha256(before).hexdigest(),candidate_tim_sha256=sha256(candidate).hexdigest(),
        png_sha256=sha256(png).hexdigest(),png_byte_length=len(png),stp_sha256=sha256(stp).hexdigest() if stp is not None else None,
        stp_byte_length=len(stp) if stp is not None else None,index_image_sha256=sha256(candidate[544:]).hexdigest(),index_byte_length=32768,
        byte_change_count=sum(a!=b for a,b in zip(before,candidate)),quantization=analysis['quantization'],
        unchanged_layout_sha256=sha256(before[:20]+before[532:544]).hexdigest(),
        shared_indices=True,read_only=True,project_changed=False,gameplay_verified=False)
