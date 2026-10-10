"""Compose qualified authored World TMD geometry without changing Retail seeds."""
from copy import deepcopy
from hashlib import sha256
from importer.model_authoring import preview_model_shape
from importer.worldmap_model_authoring import model_identity
from .worldmap_model_binding import source,validate
from .project import ProjectError


def compose(project,geometry):
    scene=geometry['scene'];disc=geometry['source_record']['disc_sha256']
    assets={a['asset_id']:a for a in geometry['scene_graph']['assets']}
    edits=[];prepared=[]
    for identifier,binding in sorted(project.model_overrides.items()):
        identity=model_identity(identifier)
        if not identity or identity[0]!=scene:continue
        validate(identifier,binding)
        original,native=source(project,identifier)
        asset=assets.get(identifier)
        if asset is None or asset['source_record']!=native or native['disc_sha256']!=disc:
            raise ProjectError('Current World model lost its native scene-graph source ownership')
        if binding['source_sha256']!=sha256(original).hexdigest():
            raise ProjectError('Current World model differs from its immutable Retail source')
        replacement=project.read_model_replacement(identifier,binding)
        preview=preview_model_shape(asset['preview'],replacement,binding)
        prepared.append((asset,preview))
        if replacement!=original:
            edits.append(dict(asset_id=identifier,source_tmd_sha256=sha256(original).hexdigest(),
                effective_tmd_sha256=sha256(replacement).hexdigest(),byte_length=len(replacement)))
    # Qualify every binding before changing any geometry, including failure paths.
    graph=geometry['scene_graph']
    previews={a['asset_id']:a['preview'] for a in graph['assets']}
    previews.update({asset['asset_id']:preview for asset,preview in prepared})
    if any(entity.get('asset_id') not in previews for entity in graph['entities']):
        raise ProjectError('Current World entity lost its native model ownership')
    stored=sum(len(preview['triangles']) for preview in previews.values())
    drawn=sum(len(previews[entity['asset_id']]['triangles']) for entity in graph['entities'])
    if stored>200000 or drawn>200000:
        raise ProjectError('Current World topology exceeds its scene triangle budget')
    for asset,preview in prepared:asset['preview']=preview
    graph['metrics'].update(stored_triangle_count=stored,drawn_triangle_count=drawn)
    extended=any(binding['format']!='tmd-shape' for identifier,binding in project.model_overrides.items() if (model_identity(identifier) or [None])[0]==scene)
    allocated=any(binding['format'] in ('world-tmd-vector-allocation-v1','world-tmd-vector-content-v1','world-tmd-face-addition-v1','world-tmd-group-allocation-v1','world-tmd-object-allocation-v1') for identifier,binding in project.model_overrides.items() if (model_identity(identifier) or [None])[0]==scene)
    face_growth=any(binding['format']=='world-tmd-face-addition-v1' for identifier,binding in project.model_overrides.items() if (model_identity(identifier) or [None])[0]==scene)
    group_growth=any(binding['format']=='world-tmd-group-allocation-v1' for identifier,binding in project.model_overrides.items() if (model_identity(identifier) or [None])[0]==scene)
    object_growth=any(binding['format']=='world-tmd-object-allocation-v1' for identifier,binding in project.model_overrides.items() if (model_identity(identifier) or [None])[0]==scene)
    geometry['model_layer']='current'
    geometry['model_authoring']=dict(schema_version='legaia.worldmap-current-models.v6' if object_growth else 'legaia.worldmap-current-models.v5' if group_growth else 'legaia.worldmap-current-models.v4' if face_growth else 'legaia.worldmap-current-models.v3' if allocated else 'legaia.worldmap-current-models.v2' if extended else 'legaia.worldmap-current-models.v1',scene=scene,
        disc_sha256=disc,edits=edits,scope='qualified-TMD-object-allocation' if object_growth else 'qualified-TMD-group-allocation' if group_growth else 'qualified-TMD-face-addition' if face_growth else 'qualified-TMD-vector-allocation' if allocated else 'existing-TMD-layout-content' if extended else 'existing-TMD-vertex-normal-XYZ-only',gameplay_verified=False)
    return geometry
