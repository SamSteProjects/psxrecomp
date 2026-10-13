"""Fresh known stored monster stats/rewards Inspect, Review and persistent Apply."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError,digest
from .battle_character_resources import _fresh
from .monster_model_authoring import snapshot as model_snapshot
from .monster_records import validate,compose
from importer.monster_record_authoring import FIELDS,patch,header_values
from importer.monster_archive import decode_catalog
from importer.serialization import serialize_lzs_decoded
from importer.core import ImportError as NativeError


def snapshot(project,**context):
    model,_,original,current,raw,used=model_snapshot(project,**context)
    catalog=decode_catalog(raw,model['source_record']['disc']['sha256'])
    record=next((r for r in catalog['records'] if r.get('model_asset_id')==model['semantic_id']),None)
    if record is None:raise ProjectError('Stored monster record belongs to another model/source')
    # Idempotent if the parent snapshot already composed the header last.
    current=compose(original,catalog,record['monster_id'],getattr(project,'monster_record_overrides',{}),current)
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return record,original,current,raw,used


def inspect(project,**context):
    record,original,current,_,_=snapshot(project,**context)
    return dict(schema_version='legaia.monster-record-inspection.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],
        catalog_source_key=context['catalog_source_key'],asset_id=context['asset_id'],record=record,fields=deepcopy(list(FIELDS)),
        retail_values=header_values(original),current_values=header_values(current),retail_header_base64=b64encode(original[:0x4c]).decode(),current_header_base64=b64encode(current[:0x4c]).decode(),
        binding=deepcopy(getattr(project,'monster_record_overrides',{}).get(record['semantic_id'])),current_block_sha256=sha256(current).hexdigest(),
        layer='current',read_only=True,project_changed=False,gameplay_verified=False)


def review(project,expected_current_block_sha256,values,**context):
    record,original,current,raw,used=snapshot(project,**context)
    if sha256(current).hexdigest()!=expected_current_block_sha256:raise ProjectError('Monster Current slot changed; inspect stored values again')
    try:candidate,changes=patch(original,current,record,values)
    except NativeError as e:raise ProjectError(str(e)) from e
    if not changes:raise ProjectError('Monster stored record Review has no native changes')
    retail=header_values(original);proposed=header_values(candidate)
    edits=[dict(field=field,value=value) for field,value in sorted(proposed.items()) if value!=retail[field]]
    binding=dict(schema_version='legaia.monster-record-override.v1',asset_id=record['semantic_id'],source_record=deepcopy(record['source_record']),edits=edits,current_header_sha256=sha256(candidate[:0x4c]).hexdigest()) if edits else None
    if binding:compose(original,dict(records=[record]),record['monster_id'],{record['semantic_id']:binding})
    start=record['source_record']['compressed_stream_offset']
    try:_,capacity=serialize_lzs_decoded(raw[start:start+used],len(original),candidate,'monster-stored-record')
    except NativeError as e:raise ProjectError(str(e)) from e
    result=dict(schema_version='legaia.monster-record-review.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],
        catalog_source_key=context['catalog_source_key'],asset_id=context['asset_id'],record=record,fields=deepcopy(list(FIELDS)),requested_values=deepcopy(values),
        retail_values=retail,current_values=header_values(current),proposed_values=proposed,
        retail_header_base64=b64encode(original[:0x4c]).decode(),current_header_base64=b64encode(current[:0x4c]).decode(),proposed_header_base64=b64encode(candidate[:0x4c]).decode(),
        binding=binding,current_block_sha256=sha256(current).hexdigest(),candidate_block_sha256=sha256(candidate).hexdigest(),changes=changes,
        changed_field_count=len(changes),byte_change_count=sum(row['byte_change_count'] for row in changes),capacity=capacity,
        layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    result['review_key']=digest(result);_fresh(project,context['expected_project_path'],context['expected_source_key'])
    return result


def apply(project,review_key,**args):
    result=review(project,**args)
    if result['review_key']!=review_key:raise ProjectError('Monster stored record Apply requires its exact fresh changed Review')
    before=deepcopy(getattr(project,'monster_record_overrides',{}));after=deepcopy(before);identifier=result['record']['semantic_id']
    if result['binding']:after[identifier]=result['binding']
    else:after.pop(identifier,None)
    validate(project,after);project.monster_record_overrides=after
    project.undo_stack.append(dict(target='monster_record_overrides',before=before,after=deepcopy(after),label='Monster Stored Record'));project.redo_stack.clear()
    return dict(schema_version='legaia.monster-record-apply.v1',record_asset_id=identifier,history_steps=1,project_changed=True,gameplay_verified=False)
