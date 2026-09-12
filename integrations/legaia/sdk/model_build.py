"""Existing-layout model shapes prepared for archive relocation."""
from importer.model_authoring import model_shape_overlays
from importer.pipeline import import_scene
from .project import ProjectError, digest
from .texture_build import archive_overlay_patches


def prepare_model_patches(project,scene_id,bindings,archive):
    document=project.imports[scene_id]
    if digest(import_scene(project.disc_path,document['scene']['name']))!=digest(document):
        raise ProjectError('Model export source metadata differs from retail')
    imported={asset['semantic_id']:asset for asset in document['assets']['models']}
    assets,payloads={},{}
    for identifier,binding in bindings.items():
        if not isinstance(binding,dict) or binding.get('source_scene_id')!=scene_id or identifier not in imported:
            raise ProjectError('Model export requires an imported model from its source scene')
        assets[identifier]=imported[identifier]
        payloads[identifier]=project.read_model_replacement(identifier,binding)
    overlays,changes=model_shape_overlays(archive,assets,payloads)
    patches,carriers=archive_overlay_patches(archive,overlays)
    return patches,dict(changes=changes,carriers=carriers)
