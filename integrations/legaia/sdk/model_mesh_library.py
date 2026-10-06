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
