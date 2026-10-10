"""Global verified kingdom geometry/texture identities; no field memberships or payloads."""
from copy import copy,deepcopy
import math,re
from .project import AssetDatabase,ProjectError
from .project_assets import _metadata,_budget
from .worldmap_authoring import state_key
from .worldmap_placements import SCENES
from importer.worldmap_geometry import load_worldmap_geometry


def inspect(project,key):
    if project.mode!='edit' or not project.disc_path or key!=state_key(project):raise ProjectError('World resource discovery requires the current Edit project and disc inputs')
    view=copy(project)
    for name,value in vars(project).items():
        if name!='assets':setattr(view,name,deepcopy(value))
    view.assets=AssetDatabase()
    if state_key(view)!=key:raise ProjectError('World resources changed while capturing inputs')
    assets=[];references=[];roots=[];identities=set()
    def add(row):
        if row['id'] in identities:raise ProjectError('World resource identities conflict')
        identities.add(row['id']);row.update(semantic_id=row['id'],scene_id=None,scope='global-worldmap-resources',runtime_state='not_observed');assets.append(row)
    for scene in SCENES:
        geometry=load_worldmap_geometry(view.disc_path,scene);source=geometry['source_record'];graph=geometry['scene_graph'];root='worldmap://'+scene+'/resources';roots.append(root)
        if geometry.get('scene')!=scene or any(not isinstance(source.get(k),str) or not re.fullmatch('[0-9a-f]{64}',source[k]) for k in ('disc_sha256','map_sha256','floor_lut_sha256','bundle_sha256')):raise ProjectError('World resource kingdom provenance is incomplete')
        if not 1<=len(graph['assets'])<=129 or not 1<=len(graph['entities'])<=513:raise ProjectError('World resource scene exceeds its bounded geometry inventory')
        catalog=geometry['preview']['texture_catalog'];textures=catalog['textures'];texture_ids=set()
        if len(textures)>512:raise ProjectError('World resource texture catalog exceeds 512 native TIMs')
        for texture in textures:
            id=texture['semantic_id'];slot=texture['pack_slot'];offset=texture['byte_offset'];length=texture['byte_length']
            if type(slot) is not int or not 0<=slot<65536 or id!=f'texture://{scene}/kingdom/{slot:04d}' or id in texture_ids or any(type(n) is not int or n<0 for n in (offset,length)) or length<20 or offset+length>source['texture_slot']['decoded_byte_length'] or texture['prot_entry_index']!=source['bundle_entry_index'] or texture['descriptor_index']!=source['texture_slot']['slot_index'] or not re.fullmatch('[0-9a-f]{64}',texture['decoded_member_sha256']):raise ProjectError('World texture source is outside its native kingdom pack')
            texture_ids.add(id);add(dict(id=id,name=f'{scene} native TIM {slot:04d}',kind='texture',resource_role='native_tim',source_scene=scene,source_record=deepcopy(texture)))
            references.append(dict(source_id=root,target_id=id,kind='owns_native_tim',layer='derived'))
        mesh_ids=[]
        for asset in graph['assets']:
            id=asset['asset_id'];preview=asset['preview'];record=asset['source_record'];ground=id==geometry['semantic_id'];members=sorted(e['entity_id'] for e in graph['entities'] if e['asset_id']==id)
            if not members or len(members)>512 or len(members)!=len(set(members)):raise ProjectError('World model lacks unique qualified source instances')
            if ground:
                if id!=f'asset://{scene}/worldmap/walk-ground' or record!=source or members!=[f'scene://{scene}/worldmap/ground']:raise ProjectError('World ground resource differs from native source')
            else:
                slot=record.get('pack_slot');a=record.get('decoded_member_offset');b=record.get('decoded_member_span_end')
                if type(slot) is not int or not 0<=slot<240 or id!=f'asset://{scene}/worldmap/models/{slot:04d}' or any(type(n) is not int or n<0 for n in (a,b)) or not a<b<=record.get('decoded_byte_length',0) or record.get('disc_sha256')!=source['disc_sha256'] or record.get('prot_entry_index')!=source['bundle_entry_index'] or not re.fullmatch('[0-9a-f]{64}',record.get('decoded_member_sha256','')):raise ProjectError('World model source differs from its native TMD pack')
            bounds=preview['bounds']
            if set(bounds)!={'min','max'} or any(not isinstance(v,list) or len(v)!=3 or any(type(n) not in (int,float) or not math.isfinite(n) for n in v) for v in bounds.values()) or any(bounds['min'][i]>bounds['max'][i] for i in range(3)):raise ProjectError('World resource has invalid native bounds')
            materials=preview.get('materials',[]);matches=preview.get('textures',[])
            if len(materials)>256 or len(matches)!=len(materials):raise ProjectError('World resource material coverage is incomplete')
            associations=[]
            for i,(material,match) in enumerate(zip(materials,matches)):
                ids=match.get('source_ids',[])
                if not isinstance(ids,list) or len(ids)>512 or len(set(ids))!=len(ids) or any(id not in texture_ids for id in ids):raise ProjectError('World material references an unknown native TIM')
                if match.get('material_index')!=i or match.get('status')=='address_match' and not ids:raise ProjectError('World material address evidence is incomplete')
                associations.append(dict(material_index=i,status=match['status'],texture_ids=sorted(ids),material=deepcopy(material)))
                for target in sorted(ids):references.append(dict(source_id=id,target_id=target,kind='uses_native_tim',layer='derived',material_index=i))
            add(dict(id=id,name=f'{scene} walk ground' if ground else f'{scene} placed model {slot:04d}',kind='model',resource_role='derived_ground' if ground else 'native_placed_model',source_scene=scene,source_record=deepcopy(record),bounds=deepcopy(bounds),vertex_count=len(preview['vertices']),triangle_count=len(preview['triangles']),object_count=len(preview['objects']),material_associations=associations,source_instance_ids=members))
            mesh_ids.append(id);references.append(dict(source_id=root,target_id=id,kind='owns_geometry_asset',layer='derived'))
        add(dict(id=root,name=f'{scene} source resources',kind='worldmap',resource_role='kingdom_resources',source_scene=scene,source_record=deepcopy(source),geometry_asset_ids=sorted(mesh_ids),texture_asset_ids=sorted(texture_ids),texture_diagnostics=deepcopy(catalog['diagnostics']),placement_coverage=deepcopy(graph['coverage'])))
    result=dict(schema_version='legaia.worldmap-resources.v1',source_key=key,project_path=str(project.root),metadata_only=True,read_only=True,project_changed=False,gameplay_verified=False,roots=roots,assets=sorted(assets,key=lambda a:a['id']),references=sorted(references,key=lambda e:(e['source_id'],e['target_id'],e.get('material_index',-1))),coverage=dict(kingdom_count=3,asset_count=len(assets),reference_count=len(references),geometry_asset_count=sum(a['kind']=='model' for a in assets),texture_asset_count=sum(a['kind']=='texture' for a in assets)),limitations=['Only verified drawable assets referenced by source walk placements are enumerated; unplaced TMD inventory is not claimed.','Native TIM catalog coverage is bounded; CLUT strips, runtime uploads, residency and animated palette semantics remain unknown.','Material relationships are static address evidence; source seeds are not observed runtime actors.','Ground meshes are derived MAP/floor surfaces, not native primitive pools.'])
    _metadata(result);_budget(result)
    if project.mode!='edit' or state_key(project)!=key or state_key(view)!=key:raise ProjectError('World resources changed during discovery')
    return result
