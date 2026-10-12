"""Qualified shared field-party TIM authoring in the original section span.

Pinned eight-member bank: PROT874 section2. This context does not substitute
scene uploads or infer live VRAM residency. Growing section relocation remains
separate from the bounded fixed-span write supplied here.
"""
from .core import ImportError,parse_lzs_sections,decompress_lzs
from .pipeline import _disc_context
from .textures import _field_party_catalog,_pack_members,MAX_ENTRY_BYTES
from .texture_authoring import TextureAuthoringContext


LIMITATIONS=[
    'Shared field-party eight-TIM bank only; source scene membership and live VRAM residency are not inferred.',
    'Exact TIM headers, dimensions, VRAM/CLUT placement and member lengths; only existing image/palette payloads may differ.',
    'Original compressed section span only; growing section relocation is not qualified by this context.',
    'CLUT words retain native storage; field upload flattens CLUT blocks to a strip. Native palette animation, lighting and gameplay remain unverified.',
]


class FieldTextureAuthoringContext(TextureAuthoringContext):
    def options(self,identifier):
        result=super().options(identifier);result['limitations']=list(LIMITATIONS);result['scope']='shared_field_party_TIM';return result

    def validate_replacement(self,identifier,replacement):
        result=super().validate_replacement(identifier,replacement);result['limitations']=list(LIMITATIONS);return result

    def _carrier(self,archive,source):
        if source.get('prot_entry_index')!=874 or source.get('container_section')!=2 or source.get('byte_coordinate_space')!='decoded_lzs_section':
            raise ImportError('Shared field TIM source is outside the pinned bank')
        entry=archive.entry(874);raw=archive.read_entry(entry,extended=True)
        if len(raw)>MAX_ENTRY_BYTES:raise ImportError('Shared field texture carrier exceeds its byte budget')
        sections=parse_lzs_sections(raw)
        if len(sections)!=3:raise ImportError('Shared field texture container layout changed')
        section=sections[2];decoded,consumed=decompress_lzs(raw[section.stream_offset:],section.decoded_size)
        if section.stream_offset!=source['compressed_stream_offset'] or consumed!=source['compressed_bytes_consumed'] or len(decoded)!=source['containing_size']:
            raise ImportError('Shared field texture section differs from its source locator')
        ranges=_pack_members(decoded,False)
        if len(ranges)!=8:raise ImportError('Shared field texture member count changed')
        return dict(kind='lzs_shared_field_texture_pack',decoded=decoded,stream=raw[section.stream_offset:section.stream_offset+consumed],offset=(archive.node.extent_lba+entry.start_lba)*2048+section.stream_offset,ranges=ranges,stream_offset=section.stream_offset,source=dict(prot_entry_index=874,container_section=2,compressed_stream_offset=section.stream_offset,compressed_bytes_consumed=consumed))

    def build_patch(self,edits):
        # Parent growth requests name scene-descriptor carriers, which are a
        # different format. Never manufacture such a request for this bank.
        overlays,audit=self.patch(edits)
        return overlays,audit,[]


def load_field_texture_authoring_context(disc):
    with _disc_context(disc) as (_,digest,_,archive):
        catalog=_field_party_catalog(archive.read_entry(archive.entry(874),extended=True),digest)
        return FieldTextureAuthoringContext(disc,'global-field-party',catalog)
