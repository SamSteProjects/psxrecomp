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
    for binding in project.texture_overrides.values():
        payload = project.read_texture_replacement(binding)
        store(f"Authored/Textures/{binding['asset_sha256']}.tim",payload)
    for identifier, binding in project.model_overrides.items():
        payload = project.read_model_replacement(identifier, binding)
        store(f"Authored/Models/{binding['asset_sha256']}.tmd",payload)
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
