"""Source-bound scene floor height component and reviewed normal authoring commands."""
from copy import deepcopy
from hashlib import sha256
import struct
from importer.pipeline import import_scene,_disc_context,_bounded_scene_range
from importer.man_source import read_man_source
from importer.floor_height_authoring import patch_floor_heights
from .project import ProjectError,digest
from .project_copy import source_key

def context(project,scene):
    if not isinstance(scene,str) or scene not in project.imports or not project.disc_path:raise ProjectError('Floor heights require an imported source scene and disc')
    document=project.imports[scene];name=document['scene']['name']
    if import_scene(project.disc_path,name)!=document:raise ProjectError('Floor height imported evidence differs from the source disc')
    with _disc_context(project.disc_path) as (_,disc,mapping,archive):
        if document['source']['disc_identity']!='sha256:'+disc:raise ProjectError('Floor height disc identity differs from imported evidence')
        start,end=_bounded_scene_range(archive,mapping,name);carrier=read_man_source(archive,start,end,name)
    return carrier.payload,dict(disc_sha256=disc,**carrier.provenance())

def validate(project,scene,value):
    if not isinstance(value,dict) or set(value)!={'source_sha256','edits'}:raise ProjectError('Floor heights require source SHA256 and tier edits only')
    source,_=context(project,scene);patch_floor_heights(source,value['source_sha256'],project.imports[scene]['scene']['name'],value['edits']);return value

def effective_lut(project,scene,retail,source_hash):
    value=project.overrides.get(scene,{}).get('FloorHeights');result=list(retail)
    if value:
        validate(project,scene,value)
        if value['source_sha256']!=source_hash:raise ProjectError('Floor preview MAN differs from authored height binding')
        for e in value['edits']:result[e['tier']]=e['height']
    return result

def compose(project,scene,source,candidate):
    value=project.overrides.get(scene,{}).get('FloorHeights')
    if not value:return candidate,[]
    if candidate[2:0x22]!=source[2:0x22]:raise ProjectError('Floor height edit overlaps another authored MAN header change')
    changed,audit=patch_floor_heights(source,value['source_sha256'],project.imports[scene]['scene']['name'],value['edits'])
    return candidate[:2]+changed[2:0x22]+candidate[0x22:],audit

def review(project,scene,heights):
    if project.mode!='edit':raise ProjectError('Floor height Review requires Edit mode')
    if not isinstance(heights,list) or len(heights)!=16 or any(type(v) is not int or not -32768<=v<=32767 for v in heights):raise ProjectError('Floor height Review requires sixteen signed height values')
    before=source_key(project);source,record=context(project,scene);h=sha256(source).hexdigest();retail=list(struct.unpack_from('<16h',source,2));authored=project.overrides.get(scene,{}).get('FloorHeights');current=retail[:]
    if authored:
        patch_floor_heights(source,authored['source_sha256'],project.imports[scene]['scene']['name'],authored['edits'])
        for e in authored['edits']:current[e['tier']]=e['height']
    edits=[dict(tier=i,height=v) for i,v in enumerate(heights) if v!=retail[i]];value=dict(source_sha256=h,edits=edits);_,audit=patch_floor_heights(source,h,project.imports[scene]['scene']['name'],edits)
    if source_key(project)!=before:raise ProjectError('Project changed during floor height Review')
    canonical=dict(authored,edits=sorted(authored['edits'],key=lambda e:e['tier'])) if authored else None
    return dict(schema_version='legaia.floor-height-review.v1',scene_id=scene,project_source_key=before,source_sha256=h,source_record=record,retail=retail,current=current,proposed=deepcopy(heights),value=value,audit=audit,
        review_key=digest(dict(project_source_key=before,scene=scene,source_record=record,heights=heights)),project_change=canonical!=(value if edits else None),effective_change_count=sum(a!=b for a,b in zip(current,heights)),scope='MAN-floor-height-table-only',gameplay_verified=False,
        limitations=['Shared tier heights affect all source consumers in the scene.','MAP selectors and native ramp/override records remain unchanged.','Reference heights are not proof of live collision or movement behavior.'])

def apply(project,command):
    if set(command)!={'type','entity_id','heights','review_key'}:raise ProjectError('Floor height Apply requires exact reviewed fields')
    result=review(project,command['entity_id'],command['heights'])
    if command['review_key']!=result['review_key']:raise ProjectError('Floor height inputs changed since Review')
    if not result['project_change']:return
    project.command(dict(type='set_floor_heights',entity_id=command['entity_id'],value=result['value']) if result['value']['edits'] else dict(type='clear_floor_heights',entity_id=command['entity_id']))
