"""Reviewed whole PLAYER model-file restoration with Current actions preserved."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
import struct
from .project import ProjectError, digest
from .battle_character_resources import _fresh
from .player_model_authoring import current
from .player_model_store import effective, validate
from .player_action_store import effective as effective_actions
from importer.player_battle import DATA_BASE, _sources, table
from importer.core import ImportError as NativeError, decompress_lzs
from importer.model_authoring import replace_model_content


def _sha(data): return sha256(data).hexdigest()
def _b64(data): return b64encode(data).decode()


def _section(raw, row):
    at=row['byte_offset'];length=row['byte_length'];size=struct.unpack_from('<I',raw,at)[0]
    decoded,used=decompress_lzs(raw[at+4:at+length],size)
    if len(decoded)<20:raise NativeError('PLAYER changed equipment section has no qualified loader')
    frame,_,_,body,attach,_=struct.unpack_from('<4IhH',decoded)
    if not 0<=attach<=24 or frame!=20+4*attach or frame+24>len(decoded):raise NativeError('PLAYER changed section loader layout differs')
    data_size,magic,flags,count=struct.unpack_from('<4I',decoded,frame+8)
    pool=frame+24+count*28;pool_size=((data_size-count*28-9)//4)*4
    if magic!=0x80000002 or flags or not 1<=count<=24 or pool_size<0 or pool+pool_size>body or body>len(decoded):raise NativeError('PLAYER changed section native pool is unsupported')
    return decoded,used,pool,pool_size,frame


def _prepare(project,expected_current_sha256,expected_current_composed_sha256,**context):
    inspection=current(project,**context);record=inspection['record'];identifier=record['semantic_id']
    owner=project.player_model_overrides.get(identifier)
    if not owner:raise ProjectError('Selected PLAYER file has no authored model owner to restore')
    disc,sources=_sources(project.disc_path);retail=sources[record['player_index']][3]
    if disc!=record['source_record']['disc']['sha256'] or _sha(retail)!=record['source_record']['sha256']:raise ProjectError('PLAYER restoration Retail source changed')
    model=effective(project,record,retail);action,_=effective_actions(project,record,retail)
    if _sha(model)!=expected_current_sha256 or inspection['effective_file_sha256']!=expected_current_sha256:raise ProjectError('PLAYER Current model changed; inspect Current again')
    rows=table(retail);descriptor=rows[0]['descriptor_offset']
    if table(model)!=rows or model[:DATA_BASE]!=retail[:DATA_BASE] or action[:16]!=retail[:16] or action[descriptor:]!=retail[descriptor:]:raise ProjectError('PLAYER restoration changed protected record0, descriptors or source footprint')
    composed=model[:16]+action[16:descriptor]+model[descriptor:]
    candidate=retail[:16]+action[16:descriptor]+retail[descriptor:]
    if _sha(composed)!=expected_current_composed_sha256:raise ProjectError('PLAYER Current composed file changed; inspect Current again')
    if (model==retail)!=(composed==candidate):raise ProjectError('PLAYER ownership-only restoration differs from its complete composed file')
    if len(composed)!=len(retail) or composed[:DATA_BASE]!=candidate[:DATA_BASE]:raise ProjectError('PLAYER restoration changed the Current action span or descriptors')
    sections=[]
    try:
        for row in rows:
            at=row['byte_offset'];stop=at+row['byte_length']
            if model[at:stop]==retail[at:stop]:continue
            if model[at:at+4]!=retail[at:at+4]:raise NativeError('PLAYER restored section changed its decoded budget')
            before,used,pool,length,frame=_section(model,row);original,retail_used,rpool,rlength,rframe=_section(retail,row)
            if (len(before),pool,length,frame)!=(len(original),rpool,rlength,rframe) or before[:pool]!=original[:pool] or before[pool+length:]!=original[pool+length:]:raise NativeError('PLAYER model owner changed opaque loader or texture bytes')
            source_tmd=original[frame+12:pool+length];owned_tmd=before[frame+12:pool+length]
            replace_model_content(source_tmd,_sha(source_tmd),owned_tmd,allow_normal_references=True)
            sections.append(dict(descriptor=deepcopy(row),decoded_size=len(original),pool_offset=pool,pool_byte_length=length,
                retail_decoded_sha256=_sha(original),current_decoded_sha256=_sha(before),retail_compressed_bytes=retail_used,current_compressed_bytes=used,
                unchanged_decoded_neighbors_sha256=_sha(before[:pool]+before[pool+length:]),
                decoded_pool_byte_change_count=sum(a!=b for a,b in zip(original[pool:pool+length],before[pool:pool+length]))))
    except NativeError as e:raise ProjectError(str(e)) from e
    if not sections and model!=retail:raise ProjectError('PLAYER whole-model restoration has no qualified changed equipment sections')
    after=deepcopy(project.player_model_overrides);after.pop(identifier);validate(project,after)
    removed=[dict(import_index=i,sha256=r['sha256'],byte_length=r['byte_length']) for i,r in enumerate(owner['inputs'])]
    projection=dict(schema_version='legaia.player-model-restoration-projection.v1',asset_id=identifier,
        current_model_sha256=_sha(model),candidate_model_sha256=_sha(retail),current_composed_sha256=_sha(composed),candidate_composed_sha256=_sha(candidate),
        current_action_file_sha256=_sha(action),byte_length=len(retail),descriptor_offset=descriptor,
        unchanged_prefix_sha256=_sha(composed[:DATA_BASE]),unchanged_descriptors_sha256=_sha(composed[descriptor:DATA_BASE]),
        unchanged_action_span_sha256=_sha(composed[16:descriptor]),byte_change_count=sum(a!=b for a,b in zip(composed,candidate)),
        decoded_pool_byte_change_count=sum(s['decoded_pool_byte_change_count'] for s in sections),restored_sections=sections,removed_active_inputs=removed,
        native_content_changed=model!=retail,ownership_only=model==retail)
    value=dict(schema_version='legaia.player-model-restoration-review.v1',operation='restore_retail_player_model_file',
        project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],asset_id=identifier,
        equipped=deepcopy(context['equipped']),record=record,model_binding=deepcopy(owner),action_binding=deepcopy(inspection['action_binding']),
        current_model_file_base64=_b64(model),retail_file_base64=_b64(retail),current_composed_file_base64=_b64(composed),candidate_composed_file_base64=_b64(candidate),
        current_tmd_base64=inspection['tmd_base64'],retail_tmd_base64=inspection['retail_tmd_base64'],projection=projection,
        scope='whole_selected_PLAYER_file_model_owner_all_imported_equipment_sections',
        layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    value['review_key']=digest(value);_fresh(project,context['expected_project_path'],context['expected_source_key'])
    return value,after,inspection,candidate


def review(project,**args):return _prepare(project,**args)[0]


def apply(project,review_key,**args):
    value,after,_,_=_prepare(project,**args)
    if value['review_key']!=review_key:raise ProjectError('PLAYER restoration requires its exact fresh changed Review')
    before=deepcopy(project.player_model_overrides);project.player_model_overrides=after
    project.undo_stack.append(dict(target='player_model_overrides',before=before,after=deepcopy(after),label='Restore Retail PLAYER Model File'));project.redo_stack.clear()
    return dict(schema_version='legaia.player-model-restoration-apply.v1',asset_id=args['asset_id'],removed_active_inputs=value['projection']['removed_active_inputs'],history_steps=1,project_changed=True,gameplay_verified=False)


def proposed_preview(project,review_key,**args):
    from .player_battle import preview
    value,_,before,_=_prepare(project,**args)
    if value['review_key']!=review_key:raise ProjectError('PLAYER restoration preview requires its exact fresh Review')
    context={k:args[k] for k in ('expected_project_path','expected_source_key','asset_id','catalog_source_key','equipped')}
    retail=preview(project,**context);proposed=deepcopy(before)
    proposed.update(geometry=retail['geometry'],assembly=retail['assembly'],binding=None,tmd_base64=value['retail_tmd_base64'],effective_file_sha256=value['projection']['candidate_model_sha256'],current_composed_sha256=value['projection']['candidate_composed_sha256'],layer='proposed_native_model')
    before['current_composed_sha256']=value['projection']['current_composed_sha256']
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return dict(schema_version='legaia.player-model-restoration-preview.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],review_key=review_key,review=value,current_preview=before,proposed_preview=proposed,layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
