"""Read-only recovery of exact GLBs in the active, freshly replayed pack owner."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError
from .battle_pack_model_authoring import snapshot
from .battle_pack_models import read
from .battle_character_resources import _fresh


def receipt_key(asset,index,receipt):
    fields=(asset,str(index),receipt['glb_sha256'],str(receipt['glb_byte_length']),
            receipt['base_tmd_sha256'],receipt['candidate_tmd_sha256'],receipt['review_key'])
    return sha256('|'.join(fields).encode('utf-8')).hexdigest()


def library(project,expected_current_tmd_sha256,expected_current_entry_sha256,**context):
    _,_,record,tmd,entry=snapshot(project,**context)
    tmd_hash,entry_hash=sha256(tmd).hexdigest(),sha256(entry).hexdigest()
    if tmd_hash!=expected_current_tmd_sha256 or entry_hash!=expected_current_entry_sha256:
        raise ProjectError('Current pack owner changed; inspect its model again')
    owner=deepcopy(project.battle_pack_model_overrides.get(record['semantic_id']))
    receipts=owner['inputs'] if owner else []
    rows=[dict(import_index=i,receipt_key=receipt_key(record['semantic_id'],i,r),receipt=r) for i,r in enumerate(receipts)]
    sizes={r['glb_sha256']:r['glb_byte_length'] for r in receipts}
    identity=[str(project.root),context['expected_source_key'],context['catalog_source_key'],record['semantic_id'],tmd_hash,entry_hash]
    key=sha256('\n'.join(identity+[r['receipt_key'] for r in rows]).encode('utf-8')).hexdigest()
    value=dict(schema_version='legaia.battle-pack-model-inputs.v1',project_path=str(project.root),
        project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],
        record=record,model_binding=owner,current_tmd_sha256=tmd_hash,current_entry_sha256=entry_hash,
        library_key=key,imports=rows,receipt_count=len(rows),distinct_glb_count=len(sizes),registered_byte_length=sum(sizes.values()),
        layer='active_retained_inputs',historical_inputs=True,read_only=True,project_changed=False,gameplay_verified=False)
    _fresh(project,context['expected_project_path'],context['expected_source_key']);return value


def download(project,expected_library_key,selected_receipt_key,**context):
    value=library(project,**context)
    if value['library_key']!=expected_library_key:raise ProjectError('Pack input library changed; inspect it again')
    selected=next((r for r in value['imports'] if r['receipt_key']==selected_receipt_key),None)
    if selected is None:raise ProjectError('Choose an active retained pack input receipt')
    receipt=selected['receipt'];content=read(project,receipt['glb_sha256'],receipt['glb_byte_length'],'glb')
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return dict(value,selected=deepcopy(selected),content_base64=b64encode(content).decode('ascii'),
        filename=f'battle-pack-{value["record"]["pool_index"]}-import-{selected["import_index"]+1:02d}-{receipt["glb_sha256"][:12]}.glb')
