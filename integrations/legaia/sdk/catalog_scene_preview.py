"""Isolated Retail scene browsing; no import or authored mutation of the user Project."""
from pathlib import Path
from tempfile import TemporaryDirectory
from .project import ProjectService,ProjectError,digest,canonical
from .project_copy import source_key
from .scene_preview import ScenePreviewService
from .terrain_preview import terrain_preview
from importer.pipeline import import_scene,_disc_context
from importer.scene_animation import load_scene_actor_animation_catalog
from importer.environment import load_environment_preview_catalog

def preview(project,disc,scene,expected_project_key,model_loader):
    if project.mode!='edit' or source_key(project)!=expected_project_key:
        raise ProjectError('Project changed; reopen the scene catalog preview')
    with _disc_context(disc):
        metadata=import_scene(disc,scene)
        with TemporaryDirectory(prefix='legaia-scene-preview-') as directory:
            view=ProjectService(Path(directory));view.import_metadata(metadata,str(disc))
            service=ScenePreviewService()
            try:
                graph=service.preview(view,lambda asset,*args,**kwargs:model_loader(view,asset,*args,**kwargs),load_scene_actor_animation_catalog,load_environment_preview_catalog,terrain_preview)
            finally:service.clear()
    if source_key(project)!=expected_project_key:raise ProjectError('Project changed during scene catalog preview')
    result=dict(schema_version='legaia.catalog-scene-preview.v1',scene_id=metadata['scene']['semantic_id'],project_source_key=expected_project_key,disc_identity=metadata['source']['disc_identity'],source_import_sha256=digest(metadata),read_only=True,representation='isolated_retail',project_imported=False,runtime_binding='not_asserted',gameplay_verified=False,preview=graph)
    if len(canonical(result))>64*1024*1024:raise ProjectError('Scene catalog preview exceeds response byte bound')
    return result
