"""Scene-scoped source-qualified controller inspection service."""
from .project import ProjectError
from .asset_references import source_key
from .resources import _verify
from importer.pipeline import _disc_context
from importer.scene_controller import inspect_scene_controller


def inspect(project, scene_id, expected_source_key):
    key = source_key(project)
    if key != expected_source_key or scene_id != project.active_scene or scene_id not in project.imports:
        raise ProjectError('Scene controller sources changed; reopen inspection')
    document = project.imports[scene_id]
    with _disc_context(project.disc_path):
        _verify(project, document)
        report = inspect_scene_controller(project.disc_path, document['scene']['name'])
    if source_key(project) != key:
        raise ProjectError('Scene controller sources changed during inspection')
    return dict(report, source_key=key)
