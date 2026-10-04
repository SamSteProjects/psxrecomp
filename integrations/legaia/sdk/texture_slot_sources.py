"""Retained, reproducible PNG/STP inputs for an immutable authored TIM slot."""
from copy import deepcopy
from hashlib import sha256
import base64

from importer.texture_image_conversion import convert_png
from .project import ProjectError, atomic_write, digest
from .scene_preview import source_key


def validate_receipt(binding):
    receipt=binding.get('image_source')
    fields={'format','png_sha256','png_byte_length','stp_png_sha256','stp_png_byte_length','options','conversion_report'}
    if not isinstance(receipt,dict) or set(receipt)!=fields or receipt['format']!='png-tim-source-v1':
        raise ProjectError('Invalid authored slot image-source receipt')
    for prefix in ('png','stp_png'):
        key=receipt[prefix+'_sha256'];size=receipt[prefix+'_byte_length']
        if prefix=='stp_png' and key is None and size is None:continue
        if (not isinstance(key,str) or len(key)!=64 or any(c not in '0123456789abcdef' for c in key) or
                type(size) is not int or not 8<=size<=8*1024*1024):
            raise ProjectError('Retained PNG source hash or length is malformed')
    report=receipt['conversion_report']
    if (not isinstance(report,dict) or report.get('schema_version')!='legaia.texture-image-conversion.v1' or
            report.get('proposed_sha256')!=binding['asset_sha256'] or report.get('byte_length')!=binding['byte_length'] or
            report.get('png_sha256')!=receipt['png_sha256'] or report.get('png_byte_length')!=receipt['png_byte_length'] or
            report.get('stp_png_sha256')!=receipt['stp_png_sha256'] or report.get('options')!=receipt['options']):
        raise ProjectError('Retained image recipe differs from Current TIM or source identities')
    return receipt


def read_sources(project,binding,native=None):
    receipt=validate_receipt(binding)
    def read(prefix):
        key=receipt[prefix+'_sha256']
        if key is None:return None
        path=project.root/'Authored'/'TextureSources'/(key+'.png')
        if not path.resolve().is_relative_to(project.root) or not path.is_file() or path.stat().st_size!=receipt[prefix+'_byte_length']:
            raise ProjectError('Retained PNG source is missing or changed size')
        content=path.read_bytes()
        if sha256(content).hexdigest()!=key:raise ProjectError('Retained PNG source hash changed')
        return content
    png,stp=read('png'),read('stp_png')
    candidate,report=convert_png(png,receipt['options'],stp)
    if (sha256(candidate).hexdigest()!=binding['asset_sha256'] or len(candidate)!=binding['byte_length'] or
            report!=receipt['conversion_report'] or native is not None and candidate!=native):
        raise ProjectError('Retained image recipe does not reproduce Current TIM exactly')
    return png,stp,report


def review(project,asset_id,expected_sha256,expected_source_key,png,options,stp=None):
    from .texture_slot_edit import source
    native,original=source(project,asset_id,expected_source_key)
    if original['current_sha256']!=expected_sha256:
        raise ProjectError('Current TIM changed; review image-source retention again')
    candidate,conversion=convert_png(png,options,stp)
    if candidate!=native:raise ProjectError('Supplied PNG recipe must reproduce Current TIM exactly')
    receipt=dict(format='png-tim-source-v1',png_sha256=sha256(png).hexdigest(),png_byte_length=len(png),
        stp_png_sha256=sha256(stp).hexdigest() if stp is not None else None,
        stp_png_byte_length=len(stp) if stp is not None else None,options=deepcopy(options),conversion_report=conversion)
    total=sum(b['image_source']['png_byte_length']+(b['image_source']['stp_png_byte_length'] or 0)
        for i,b in project.texture_additions.items() if i!=asset_id and 'image_source' in b)
    if total+len(png)+len(stp or b'')>32*1024*1024:
        raise ProjectError('Retained slot image sources exceed their 32 MiB project budget')
    changed=project.texture_additions[asset_id].get('image_source')!=receipt
    result=dict(schema_version='legaia.texture-slot-source-retention.v1',asset_id=asset_id,
        project_source_key=expected_source_key,effective_sha256=expected_sha256,source=receipt,
        native_bytes_changed=False,changed=changed,can_apply=changed,project_changed=False,gameplay_verified=False)
    result['review_key']=digest(result)
    if source_key(project)!=expected_source_key:raise ProjectError('Project changed during source retention review')
    return result


def apply(project,asset_id,expected_sha256,expected_source_key,png,options,stp,review_key):
    report=review(project,asset_id,expected_sha256,expected_source_key,png,options,stp)
    if report['review_key']!=review_key or not report['can_apply']:
        raise ProjectError('Image-source retention requires the applicable current review')
    before=deepcopy(project.texture_additions[asset_id]);after=deepcopy(before);after['image_source']=deepcopy(report['source'])
    for prefix,content in (('png',png),('stp_png',stp)):
        if content is None:continue
        path=project.root/'Authored'/'TextureSources'/(report['source'][prefix+'_sha256']+'.png')
        if not path.resolve().is_relative_to(project.root):raise ProjectError('PNG source path escapes the project')
        if path.exists():
            if path.stat().st_size!=len(content) or path.read_bytes()!=content:raise ProjectError('Existing retained PNG content changed')
        else:atomic_write(path,content)
    read_sources(project,after)
    project.texture_additions[asset_id]=after
    project.undo_stack.append(dict(target='texture_additions',asset_id=asset_id,before=before,after=deepcopy(after)))
    project.redo_stack.clear()
    return dict(report,project_changed=True)


def download(project,asset_id,expected_sha256,expected_source_key):
    from .texture_slot_edit import source
    native,original=source(project,asset_id,expected_source_key)
    if original['current_sha256']!=expected_sha256:raise ProjectError('Current TIM changed before source download')
    binding=project.texture_additions[asset_id];png,stp,report=read_sources(project,binding,native)
    if source_key(project)!=expected_source_key:raise ProjectError('Project changed during source download')
    return dict(asset_id=asset_id,project_source_key=expected_source_key,effective_sha256=expected_sha256,
        source=deepcopy(binding['image_source']),png_base64=base64.b64encode(png).decode('ascii'),
        stp_png_base64=base64.b64encode(stp).decode('ascii') if stp is not None else None,
        read_only=True,project_changed=False)
