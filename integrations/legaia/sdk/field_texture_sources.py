"""Immutable PNG/mask/native preimage inputs for historical shared TIM imports."""
from hashlib import sha256
import re
from .project import ProjectError,atomic_write

KEYS = {
    'asset_id', 'schema_version', 'png_sha256', 'png_byte_length',
    'stp_sha256', 'stp_byte_length', 'tim_sha256', 'tim_byte_length',
    'palette_index', 'palette_mode', 'candidate_sha256',
}

def path(project,key,suffix):
    if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key) or suffix not in ('png','tim'):raise ProjectError('Invalid shared texture source identity')
    result=project.root/'Authored'/'FieldTextureInputs'/(key+'.'+suffix)
    if not result.resolve().is_relative_to(project.root.resolve()):raise ProjectError('Shared texture input escapes project root')
    return result

def retain(project,content,suffix):
    key = sha256(content).hexdigest()
    target = path(project,key,suffix)
    if target.exists():
        if target.read_bytes()!=content:raise ProjectError('Shared texture retained bytes changed')
    else:atomic_write(target,content)
    return key

def read(project,key,size,suffix):
    target=path(project,key,suffix)
    if type(size) is not int or not 1<=size<=(8*1024*1024 if suffix=='png' else 1024*1024) or not target.is_file() or target.stat().st_size!=size:raise ProjectError('Shared texture retained input missing or changed size')
    content=target.read_bytes()
    if sha256(content).hexdigest()!=key:raise ProjectError('Shared texture retained input hash changed')
    return content

def validate(project,receipt):
    from importer.texture_png import export_texture_png,import_texture_png
    from importer.core import ImportError as NativeError
    if not isinstance(receipt,dict) or set(receipt)!=KEYS or receipt['schema_version']!='legaia.field-texture-png-source.v1':raise ProjectError('Shared PNG source receipt changed')
    if type(receipt['palette_index']) is not int or not 0<=receipt['palette_index']<256 or receipt['palette_mode'] not in ('existing','rebuild'):
        raise ProjectError('Shared PNG source palette policy changed')
    if not isinstance(receipt['candidate_sha256'],str) or not re.fullmatch('[a-f0-9]{64}',receipt['candidate_sha256']):
        raise ProjectError('Shared PNG source candidate identity changed')
    from .field_texture_authoring import owns
    if not owns(receipt['asset_id']):raise ProjectError('Shared PNG source owner changed')
    from importer.field_texture_authoring import load_field_texture_authoring_context
    ctx=load_field_texture_authoring_context(project.disc_path)
    png=read(project,receipt['png_sha256'],receipt['png_byte_length'],'png')
    tim=read(project,receipt['tim_sha256'],receipt['tim_byte_length'],'tim')
    ctx.validate_replacement(receipt['asset_id'],tim)
    if (receipt['stp_sha256'] is None)!=(receipt['stp_byte_length'] is None):raise ProjectError('Shared STP source identity changed')
    stp=read(project,receipt['stp_sha256'],receipt['stp_byte_length'],'png') if receipt['stp_sha256'] is not None else None
    try:
        _,_,profile=export_texture_png(tim,receipt['palette_index'])
        candidate,_=import_texture_png(tim,png,profile,receipt['palette_mode'],stp)
    except (NativeError,KeyError,TypeError,ValueError) as e:raise ProjectError('Shared PNG source cannot replay its original import') from e
    if sha256(candidate).hexdigest()!=receipt['candidate_sha256']:raise ProjectError('Shared PNG source replay changed')
    return png,stp,tim,candidate
