"""Source-qualified floor-selector rectangles; no ramp or gameplay inference."""
from copy import deepcopy
from hashlib import sha256
from importer.floor_authoring import patch_floor_tiers
from importer.environment import load_environment_placements
from .project import ProjectError,digest
from .project_copy import source_key

def review(project,scene,rectangle):
    if project.mode!='edit' or not isinstance(scene,str) or scene not in project.imports:
        raise ProjectError('Floor rectangle requires an imported scene in Edit mode')
    if not isinstance(rectangle,dict) or set(rectangle)!={'row_start','row_end','column_start','column_end','tier'}:
        raise ProjectError('Floor rectangle requires inclusive bounds and tier only')
    for key in ['row_start','row_end','column_start','column_end']:
        if type(rectangle[key]) is not int or not 0<=rectangle[key]<=127:raise ProjectError('Floor bounds escape the native grid')
    tier=rectangle['tier']
    if not (type(tier) is int and 0<=tier<=15 or tier=='retail'):raise ProjectError('Floor tier must be 0..15 or retail')
    if rectangle['row_start']>rectangle['row_end'] or rectangle['column_start']>rectangle['column_end']:raise ProjectError('Floor bounds must be ordered')
    count=(rectangle['row_end']-rectangle['row_start']+1)*(rectangle['column_end']-rectangle['column_start']+1)
    if count>4096:raise ProjectError('Floor rectangle exceeds 4096 selectors')
    before=source_key(project);original=project._environment_source(scene);source_hash=sha256(original).hexdigest()
    environment=load_environment_placements(project.disc_path,project.imports[scene]['scene']['name']);lut=environment['floor_height_lut']
    record=environment['source_record']
    if record.get('map_sha256')!=source_hash or 'sha256:'+record.get('disc_sha256','')!=project.imports[scene]['source']['disc_identity']:raise ProjectError('Floor MAP/MAN source differs from imported disc evidence')
    if not isinstance(lut,list) or len(lut)!=16 or any(type(v) is not int or not -32768<=v<=32767 for v in lut):raise ProjectError('Floor Review requires sixteen qualified MAN height values')
    authored=deepcopy(project.overrides.get(scene,{}).get('FloorTiers'))
    effective=patch_floor_tiers(original,authored['source_sha256'],authored['edits'])[0] if authored else original
    merged={(e['row'],e['column']):deepcopy(e) for e in (authored or {}).get('edits',[])};rows=[]
    for row in range(rectangle['row_start'],rectangle['row_end']+1):
        for column in range(rectangle['column_start'],rectangle['column_end']+1):
            offset=0x4000+row*128+column;retail=original[offset]&15;current=effective[offset]&15;proposed=retail if tier=='retail' else tier
            if proposed==retail:merged.pop((row,column),None)
            else:merged[(row,column)]=dict(row=row,column=column,tier=proposed)
            rows.append(dict(row=row,column=column,retail=retail,effective=current,proposed=proposed))
    edits=[merged[key] for key in sorted(merged)];_,audit=patch_floor_tiers(original,source_hash,edits)
    if source_key(project)!=before:raise ProjectError('Project changed while reviewing floor selectors')
    key=digest(dict(project_source_key=before,scene=scene,source_sha256=source_hash,rectangle=rectangle,floor_height_lut=lut,floor_source_record=record))
    value=dict(source_sha256=source_hash,edits=edits)
    return dict(schema_version='legaia.floor-rectangle-review.v1',project_source_key=before,scene_id=scene,source_sha256=source_hash,review_key=key,
                rectangle=deepcopy(rectangle),floor_height_lut=deepcopy(lut),floor_source_record=deepcopy(record),rows=rows,selector_count=count,effective_change_count=sum(r['effective']!=r['proposed'] for r in rows),
                authored_selector_count=len(edits),audited_selector_count=len(audit),project_change=authored!=(value if edits else None),value=value,
                scope='source-MAP-floor-selectors-only',gameplay_verified=False,
                limitations=['Selectors reference existing MAN heights; LUT values are not edited.',
                             'Floor grid row zero is supported; wall-biased row/Z coordinates do not apply.',
                             'Shared corner selectors affect adjacent tiles and some placed-object heights.',
                             'Ramp flags and kind-2 overrides remain unchanged; complete live floor heights are not inferred.'])

def apply(project,command):
    if set(command)!={'type','entity_id','rectangle','review_key'}:raise ProjectError('Floor Apply requires owner, rectangle and current Review key only')
    result=review(project,command['entity_id'],command['rectangle'])
    if result['review_key']!=command['review_key']:raise ProjectError('Floor inputs changed since Review')
    project.command(dict(type='set_floor_tiers',entity_id=command['entity_id'],value=result['value']) if result['value']['edits'] else dict(type='clear_floor_tiers',entity_id=command['entity_id']))
