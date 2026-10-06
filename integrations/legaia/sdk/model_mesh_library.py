"""Project-wide retained mesh inputs; read-only, ledger-reconstructed recovery."""
from copy import copy,deepcopy
from .project import ProjectError,digest
from . import model_mesh_sources
MAX_RECEIPTS=128
MAX_BYTES=64*1024*1024

def _key(project):
    return digest(dict(project_path=str(project.root),mode=project.mode,imports=project.imports,native=project.model_overrides))

def library(project,expected_project_path):
    if not isinstance(expected_project_path,str) or expected_project_path!=str(project.root):raise ProjectError('Mesh input library project changed')
    key=_key(project);rows=[];sizes={}
    for asset,binding in sorted(project.model_overrides.items()):
        if not binding.get('mesh_imports'):continue
        scene=binding.get('source_scene_id')
        if scene not in project.imports:raise ProjectError('Mesh input source scene is not imported')
        for receipt in model_mesh_sources._metadata(asset,binding):
            rows.append(dict(scene_id=scene,receipt=deepcopy(receipt)))
            if receipt['glb_sha256'] in sizes and sizes[receipt['glb_sha256']]!=receipt['byte_length']:raise ProjectError('Mesh input library has conflicting lengths')
            sizes[receipt['glb_sha256']]=receipt['byte_length']
    if len(rows)>MAX_RECEIPTS or sum(sizes.values())>MAX_BYTES:raise ProjectError('Mesh input library exceeds 128 receipts or 64 MiB of distinct inputs')
    if len({r['receipt']['receipt_key'] for r in rows})!=len(rows):raise ProjectError('Mesh input library has duplicate receipts')
    if rows:
        from importer.pipeline import _disc_context
        from .scene_preview import source_key
        with _disc_context(project.disc_path):
            for asset in sorted({row['receipt']['asset_id'] for row in rows}):
                binding=project.model_overrides[asset];view=copy(project);view.active_scene=binding['source_scene_id']
                value=model_mesh_sources.catalog(view,asset,source_key(view))
                if value['imports']!=[row['receipt'] for row in rows if row['receipt']['asset_id']==asset]:raise ProjectError('Mesh input receipts changed during verification')
    if key!=_key(project):raise ProjectError('Mesh input library changed during verification')
    return dict(schema_version='legaia.mesh-source-library.v1',project_path=str(project.root),mode=project.mode,library_key=key,imports=rows,receipt_count=len(rows),distinct_glb_count=len(sizes),registered_byte_length=sum(sizes.values()),project_changed=False,historical_inputs=True)

def download(project,receipt_key,expected_project_path,expected_library_key):
    import base64
    value=library(project,expected_project_path)
    if value['library_key']!=expected_library_key:raise ProjectError('Mesh input library changed; refresh it')
    selected=next((row for row in value['imports'] if row['receipt']['receipt_key']==receipt_key),None)
    if selected is None:raise ProjectError('Mesh input receipt is absent from Current')
    raw=model_mesh_sources.read_source(project,selected['receipt'])
    if value['library_key']!=_key(project):raise ProjectError('Mesh input library changed during download')
    return dict(value,selected=deepcopy(selected),content_base64=base64.b64encode(raw).decode('ascii'))


def compare_native(project,receipt_key,expected_project_path,expected_library_key):
    """Compare complete model bytes and import face lifetime, without replaying writes."""
    value=library(project,expected_project_path)
    if value['library_key']!=expected_library_key:raise ProjectError('Mesh input library changed; refresh it')
    row=next((row for row in value['imports'] if row['receipt']['receipt_key']==receipt_key),None)
    if row is None:raise ProjectError('Mesh input receipt is absent from Current')
    from hashlib import sha256
    from importer.pipeline import _disc_context
    from importer.model_face_ledger import replay_face_ledger
    from .model_face_addition import base_content
    receipt=row['receipt'];asset=receipt['asset_id'];scene=row['scene_id'];disc=project.disc_path
    if not disc:raise ProjectError('Mesh native comparison requires the matching retail disc')
    with _disc_context(disc):
        original=project._model_source(asset,scene);binding=project.model_overrides.get(asset)
        if not binding or binding.get('format')!='tmd-face-addition-v1':raise ProjectError('Mesh comparison requires the retained native ledger')
        current=project.read_model_replacement(asset,binding)
        if not isinstance(current,bytes) or not 1<=len(current)<=4*1024*1024:raise ProjectError('Mesh native comparison requires bounded immutable model bytes')
        base=base_content(project,asset,original,binding)
        operations=model_mesh_sources.operations(binding)
        def prefix(length):
            return dict(schema_version=binding['ledger']['schema_version'],source_sha256=binding['ledger']['source_sha256'],source_byte_length=binding['ledger']['source_byte_length'],operations=deepcopy(operations[:length]))
        start=receipt['first_operation'];end=start+receipt['operation_count']
        _,before=replay_face_ledger(base,prefix(start));historical,after=replay_face_ledger(base,prefix(end));replayed,active=replay_face_ledger(base,binding['ledger'])
        if replayed!=current or sha256(historical).hexdigest()!=receipt['proposed_sha256']:raise ProjectError('Mesh comparison native ledger differs from the retained input')
        previous={face['face_id'] for face in before['faces']};created={face['face_id'] for face in after['faces']}-previous;current_faces={face['face_id'] for face in active['faces']}
        if not created:raise ProjectError('Mesh comparison requires imported face identities')
        current_hash=sha256(current).hexdigest()
        report=dict(schema_version='legaia.mesh-source-native-comparison.v1',project_path=value['project_path'],library_key=value['library_key'],receipt_key=receipt_key,scene_id=scene,asset_id=asset,historical_candidate_sha256=receipt['proposed_sha256'],current_sha256=current_hash,current_byte_length=len(current),matches_current=current_hash==receipt['proposed_sha256'],imported_face_count=len(created),active_imported_face_count=len(created&current_faces),retired_imported_face_count=len(created-current_faces),comparison_scope='complete_native_model_and_imported_face_lifetime',face_content_match_asserted=False,project_changed=False,native_content_changed=False,gameplay_verified=False)
        if project.disc_path!=disc or value['library_key']!=_key(project):raise ProjectError('Mesh native comparison context changed')
    if project.disc_path!=disc or value['library_key']!=_key(project):raise ProjectError('Mesh native comparison context changed')
    return report
