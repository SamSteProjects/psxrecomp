"""Native PLAYER section projection prerequisite for persistent model authoring.

Fixed source layouts only. No disc mutation, new equipment allocation or runtime
registration. Every reconstructed compressed section stays in its own footprint.
"""
from hashlib import sha256
from copy import deepcopy
import struct
from .core import ImportError,decompress_lzs
from .player_battle import assemble_tmd,table
from .serialization import compress_lzs
from .model_glb import export_model_glb,import_model_glb
from .model_authoring import replace_model_content


def export_player_model(raw,expected_sha256,equipped,preview=None):
    if sha256(raw).hexdigest()!=expected_sha256:raise ImportError('PLAYER authoring source changed')
    geometry,assembly,tmd=assemble_tmd(raw,equipped)
    if preview is not None:
        for field in ('vertices','triangles','triangle_uvs','triangle_colors','triangle_materials','materials'):
            if preview.get(field)!=geometry[field]:raise ImportError('PLAYER authoring preview differs from assembled source')
        geometry=deepcopy(preview)
    glb,profile=export_model_glb(tmd,geometry)
    return glb,dict(schema_version='legaia.player-model-glb-binding.v1',source_sha256=expected_sha256,equipped=equipped.copy(),assembly=assembly,profile=profile)


def project_tmd(raw,expected_sha256,equipped,candidate):
    """Map typed assembled-TMD changes into original compressed data pools."""
    if sha256(raw).hexdigest()!=expected_sha256:raise ImportError('PLAYER authoring source changed')
    geometry,assembly,tmd=assemble_tmd(raw,equipped)
    candidate,changes=replace_model_content(tmd,assembly['tmd_sha256'],candidate,allow_normal_references=True)
    if len(candidate)!=len(tmd) or candidate[:12+24*28]!=tmd[:12+24*28]:raise ImportError('PLAYER authoring cannot change the reserved object table or header')
    allowed=bytearray(len(tmd));result=bytearray(raw);sections=[]
    for selected in assembly['sections']:
        start=selected['merged_pool_offset'];length=selected['pool_byte_length'];allowed[start:start+length]=b'\1'*length
        replacement=candidate[start:start+length]
        if replacement==tmd[start:start+length]:continue
        at=selected['byte_offset'];limit=at+selected['byte_length'];size=struct.unpack_from('<I',raw,at)[0];decoded,consumed=decompress_lzs(raw[at+4:limit],size);source=selected['decoded_pool_offset']
        if sha256(decoded).hexdigest()!=selected['decoded_sha256'] or source+length>selected['tmd_body_end']:raise ImportError('PLAYER pool source differs from its selected allocation')
        changed=bytearray(decoded);changed[source:source+length]=replacement;stream=compress_lzs(bytes(changed))
        if len(stream)+4>selected['byte_length']:raise ImportError('Edited PLAYER section exceeds its original compressed allocation')
        check,used=decompress_lzs(stream,size)
        if check!=bytes(changed) or used!=len(stream):raise ImportError('PLAYER recompression does not reproduce the edited section')
        result[at+4:at+4+len(stream)]=stream
        # Old unused tokens/padding remain byte-exact; decoding stops at budget.
        sections.append(dict(section_index=selected['section_index'],record_index=selected['record_index'],item_id=selected['item_id'],byte_offset=at,byte_length=selected['byte_length'],decoded_pool_offset=source,pool_byte_length=length,before_decoded_sha256=sha256(decoded).hexdigest(),after_decoded_sha256=sha256(changed).hexdigest(),old_compressed_bytes=consumed,new_compressed_bytes=len(stream),byte_change_count=sum(a!=b for a,b in zip(decoded,changed))))
    if any(a!=b and not allowed[i] for i,(a,b) in enumerate(zip(tmd,candidate))):raise ImportError('PLAYER candidate changed an unmapped assembled byte')
    proposed=bytes(result);table(proposed);_,_,reassembled=assemble_tmd(proposed,equipped)
    if reassembled!=candidate:raise ImportError('PLAYER projected sections do not reproduce the complete candidate TMD')
    return proposed,dict(schema_version='legaia.player-model-projection.v1',source_sha256=expected_sha256,proposed_sha256=sha256(proposed).hexdigest(),source_byte_length=len(raw),proposed_byte_length=len(proposed),equipped=equipped.copy(),source_tmd_sha256=sha256(tmd).hexdigest(),proposed_tmd_sha256=sha256(candidate).hexdigest(),sections=sections,changes=changes,project_changed=False,gameplay_verified=False)


def import_player_model(raw,binding,content):
    if not isinstance(binding,dict) or binding.get('schema_version')!='legaia.player-model-glb-binding.v1':raise ImportError('PLAYER GLB import requires its source-qualified native binding')
    _,assembly,tmd=assemble_tmd(raw,binding.get('equipped'))
    if sha256(raw).hexdigest()!=binding.get('source_sha256') or assembly!=binding.get('assembly'):raise ImportError('PLAYER GLB source or selected assembly changed')
    candidate,analysis=import_model_glb(tmd,content,binding['profile']);proposed,report=project_tmd(raw,binding['source_sha256'],binding['equipped'],candidate)
    report['glb_analysis']=analysis
    return proposed,report
