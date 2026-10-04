"""Readonly source-qualified PNG construction for the authored TIM workflow."""
import base64

from importer.texture_image_conversion import convert_png
from .project import ProjectError
from .scene_preview import source_key


def convert(project, asset_id, expected_source_key, png_content, options, stp_content=None,*,glb_source=None):
    if not isinstance(asset_id,str) or not asset_id.startswith(('texture://','texture-new://')):
        raise ProjectError('Image conversion requires a selected texture asset')
    key = source_key(project)
    if project.mode != 'edit' or not key or key != expected_source_key:
        raise ProjectError('Image conversion requires the current Edit context')
    if isinstance(asset_id, str) and asset_id.startswith('texture-new://'):
        from .texture_slot_edit import source
        source(project, asset_id, key)
    else:
        from .texture_slots import native_pack
        context = project._texture_context(asset_id)
        with context._archive() as archive:
            native_pack(context, archive, asset_id)
    if glb_source is not None:
        from .texture_png import _glb_receipt
        _glb_receipt(glb_source,png_content)
    content, report = convert_png(png_content, options, stp_content)
    if source_key(project) != key:
        raise ProjectError('Project changed during image conversion')
    return dict(report=report, asset_id=asset_id, project_source_key=key,
                source_scene_id=project.active_scene, content_base64=base64.b64encode(content).decode('ascii'))
