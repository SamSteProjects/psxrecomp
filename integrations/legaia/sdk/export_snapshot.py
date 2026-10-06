"""Preserve exact editor inputs beside an export without saving the live project."""
from hashlib import sha256

from .build import authored_state_key
from .project import ProjectError, canonical, digest, atomic_write


def capture_export_inputs(project, *, max_bytes=None, max_files=None):
    key = authored_state_key(project)
    files = {}
    total = 0
    def store(relative,payload):
        nonlocal total
        old=files.get(relative)
        if old is not None:
            if old!=payload:raise ProjectError('Snapshot contains conflicting file identities')
            return
        if max_bytes is not None and (len(payload)>64*1024*1024 or total+len(payload)>max_bytes):
            raise ProjectError('Project input snapshot exceeds its byte limit')
        if max_files is not None and len(files)>=max_files:
            raise ProjectError('Project input snapshot exceeds its file limit')
        total+=len(payload);files[relative]=payload
    store('project.legaia.json',canonical(project._document()))
    for document in project.imports.values():
        store(f'Imported/{digest(document)}.json',canonical(document))
    from .texture_slots import validate_collection, read
    validate_collection(project)
    for identifier, binding in project.texture_additions.items():
        store(f"Authored/Textures/{binding['asset_sha256']}.tim",read(project,identifier,binding))
        if 'image_source' in binding:
            from .texture_slot_sources import read_sources
            png,stp,_=read_sources(project,binding)
            store(f"Authored/TextureSources/{binding['image_source']['png_sha256']}.png",png)
            if 'glb_source' in binding['image_source']:
                from .texture_slot_sources import read_glb_source
                store(f"Authored/TextureSources/{binding['image_source']['glb_source']['glb_sha256']}.glb",read_glb_source(project,binding,png))
            if stp is not None:store(f"Authored/TextureSources/{binding['image_source']['stp_png_sha256']}.png",stp)
    for binding in project.texture_overrides.values():
        payload = project.read_texture_replacement(binding)
        store(f"Authored/Textures/{binding['asset_sha256']}.tim",payload)
        if 'glb_byte_length' in binding.get('glb_source',{}):
            store(f"Authored/TextureSources/{binding['glb_source']['glb_sha256']}.glb",project.read_texture_glb_source(binding))
    for identifier, binding in project.model_overrides.items():
        payload = project.read_model_replacement(identifier, binding)
        store(f"Authored/Models/{binding['asset_sha256']}.tmd",payload)
        if binding.get('mesh_imports'):
            from .model_mesh_sources import read_source
            for receipt in binding['mesh_imports']:
                store(f"Authored/Models/Sources/{receipt['glb_sha256']}.glb",read_source(project,receipt))
        if binding['format'] == 'tmd-face-addition-v1' and binding['base_binding'] is not None:
            base = binding['base_binding']
            store(f"Authored/Models/{base['asset_sha256']}.tmd",
                  project.read_model_replacement(identifier, base))
    from .animation_sources import validate_files, read_source
    sources=getattr(project,'animation_sources',{})
    validate_files(project,sources)
    seen_sources=set()
    for record in sources.values():
        if record['glb_sha256'] not in seen_sources:
            store(f"Authored/Animations/Sources/{record['glb_sha256']}.glb",read_source(project,record))
            seen_sources.add(record['glb_sha256'])
    from .model_glb_sources import validate_files as validate_model_sources, read_source as read_model_source
    sources=getattr(project,'model_sources',{})
    validate_model_sources(project,sources)
    for record in sources.values():
        store(f"Authored/Models/GLBSources/{record['glb_sha256']}.glb",read_model_source(project,record))
    if authored_state_key(project) != key:
        raise ProjectError('Project changed while capturing export inputs')
    return key, files


def write_export_inputs(directory, key, files):
    """Only accept a fresh destination; report hashes after rereading every file."""
    root = (directory / 'Inputs').resolve()
    if not root.is_relative_to(directory.resolve()):
        raise ProjectError('Export input directory escapes output directory')
    root.mkdir(exist_ok=False)
    inventory = []
    for relative, payload in sorted(files.items()):
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ProjectError('Export input path escapes snapshot')
        atomic_write(path, payload)
        expected = sha256(payload).hexdigest()
        if sha256(path.read_bytes()).hexdigest() != expected:
            raise ProjectError('Export input snapshot failed readback')
        inventory.append(dict(path='Inputs/' + relative, byte_length=len(payload), sha256=expected))
    return dict(project_path='Inputs/project.legaia.json', source_authored_state_key=key,
                files=inventory, readback_verified=True,
                retail_disc_included=False)
