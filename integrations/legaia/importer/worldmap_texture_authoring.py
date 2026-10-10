"""Pinned kingdom TIM catalog for the existing exact-layout texture serializer.

This adapter supplies native entry-head descriptor coordinates. It does not
write disc data, infer runtime palettes, or introduce another compression path.
"""
from hashlib import sha256
from .core import ImportError
from .pipeline import _bounded_scene_range, _disc_context
from .textures import MAX_CATALOG_BYTES,MAX_TEXTURES,TextureCatalog,_pack_members,parse_tim
from .texture_authoring import TextureAuthoringContext
from .worldmap_geometry import KINGDOM_BASES,_scene,_kingdom_table,_slot


def load_worldmap_texture_authoring_context(disc,scene):
    _scene(scene)
    base=KINGDOM_BASES[scene]
    with _disc_context(disc) as (_,digest,mapping,archive):
        start,end=_bounded_scene_range(archive,mapping,scene)
        if start!=base-2 or not start<=base<base+1<end:
            raise ImportError('World texture authoring differs from the pinned kingdom range')
        _,index,offset,bundle,raw=_kingdom_table(archive,base)
        if offset!=0 or bundle.table_offset!=0:
            raise ImportError('World texture authoring requires a verified entry-head kingdom table')
        pack,carrier=_slot(bundle,raw,0)
        catalog=TextureCatalog(scene,digest);total=0
        for slot,(at,stop) in enumerate(_pack_members(pack,False)):
            if pack[at:at+4]!=b'\x10\0\0\0':
                catalog.diagnostics.append(f'Kingdom member {slot}: opaque non-TIM payload retained')
                continue
            try:tim=parse_tim(pack[at:stop])
            except ImportError as exc:
                catalog.diagnostics.append(f'Kingdom member {slot}: unsupported TIM retained: {exc}')
                continue
            total+=tim.byte_length
            if total>MAX_CATALOG_BYTES or len(catalog.textures)>=MAX_TEXTURES:
                raise ImportError('World texture authoring catalog exceeds its byte/count budget')
            catalog.textures.append((tim,dict(semantic_id=f'texture://{scene}/kingdom/{slot:04d}',
                prot_entry_index=index,descriptor_index=0,pack_slot=slot,byte_offset=at,
                byte_length=tim.byte_length,decoded_member_sha256=sha256(pack[at:at+tim.byte_length]).hexdigest(),
                byte_coordinate_space='decoded_lzs_descriptor',
                compressed_stream_offset=carrier['compressed_stream_offset'])))
        catalog.diagnostics.append('Only existing kingdom TIM image/palette payloads are supported; opaque CLUT strips, runtime uploads and palette animation remain unmodified and unverified.')
        return TextureAuthoringContext(disc,scene,catalog)
