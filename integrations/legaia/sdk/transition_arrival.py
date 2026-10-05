"""Source-qualified destination arrival comparison; no source trigger or runtime pose."""
from copy import copy, deepcopy
from .project import ProjectError
from .scene_preview import source_key
from .resources import refresh_resource_catalog, _verify, project_transition_state_key
from .transition_assets import validate_transition_asset
from .project import digest
import re


def inspect(project, asset_id, expected_key):
    if project.mode != 'edit' or expected_key is None or expected_key != source_key(project):
        raise ProjectError('Transition arrival source changed or is outside Edit mode')
    key = project_transition_state_key(project)
    catalog = refresh_resource_catalog(project)
    records = [r for r in catalog['records'] if r['id'] == asset_id and r['kind'] == 'transition']
    if len(records) != 1:
        raise ProjectError('Transition arrival requires one verified source resource')
    record = validate_transition_asset(records[0])
    destination = record['target']
    if record['reference']['target_scene_name'] is None or destination not in project.imports:
        raise ProjectError('Import the named destination scene before inspecting arrival positions')
    _verify(project, project.imports[destination])
    view = copy(project)
    view.active_scene = destination
    destination_key = source_key(view)
    if destination_key is None:
        raise ProjectError('Destination scene preview is unavailable')
    if key != project_transition_state_key(project) or expected_key != source_key(project):
        raise ProjectError('Transition arrival project changed during inspection')
    return dict(schema_version='legaia.transition-arrival-preview.v1', read_only=True,
                asset_id=asset_id, source_scene_id=project.active_scene, source_key=expected_key,
                project_state_key=key, destination_scene_id=destination,
                destination_source_key=destination_key, resource=deepcopy(record),
                reference_y=0, height_known=False, runtime_verified=False,
                limitations=['Positions describe destination arrival operands, never source trigger locations.',
                             'Y is an explicit reference plane; source elevation and runtime pose are unknown.',
                             'Encoded scene changes do not establish execution or gameplay reachability.'])


def review(project, asset_id, expected_project_key, expected_destination_key, arrival):
    """Review one existing entry from its loaded destination without changing scenes."""
    if (project.mode != 'edit' or expected_project_key != project_transition_state_key(project) or
            expected_destination_key != source_key(project)):
        raise ProjectError('Arrival authoring project or destination changed')
    match=re.fullmatch(r'transition://([a-z0-9_]+)/(?:actors/man-p1|scripts/man-p2)/[0-9]{4}/[0-9a-f]{4}',asset_id) if isinstance(asset_id,str) else None
    if match is None:raise ProjectError('Arrival authoring requires a stable transition source identity')
    view=copy(project);view.active_scene='scene://'+match[1]
    if view.active_scene not in project.imports:raise ProjectError('Arrival source scene is not imported')
    preview=inspect(view,asset_id,source_key(view));resource=preview['resource']
    if project.active_scene!=preview['destination_scene_id'] or preview['destination_source_key']!=expected_destination_key:
        raise ProjectError('Arrival authoring requires the qualified destination scene')
    owner=resource['owner_id'];transition=resource['entry_layers']['transition_id']
    options=project.transition_options(owner)
    entry=next((row for row in options['transitions'] if row['semantic_id']==transition),None)
    if (entry is None or entry['source_record_sha256']!=resource['source_record']['sha256'] or
            entry['effective_values']!=resource['entry_layers']['effective']):
        raise ProjectError('Arrival entry differs from its verified authoring source')
    from importer.transition_authoring import encode_transition_arrival,reference_entry_interpretation
    encoded=encode_transition_arrival(arrival,entry['effective_values'])
    entries=deepcopy(project.overrides.get(owner,{}).get('Transitions',{}).get('entries',{}))
    authored_change=entries.get(transition)!=encoded;entries[transition]=encoded
    _,audit=project._transition_context(owner).patch(entries)
    audit=[row for row in audit if row['transition_id']==transition]
    from importer.transition_authoring import ENTRY_FIELDS
    imported=resource['entry_layers']['imported']
    changed_fields={field for field in ENTRY_FIELDS if encoded[field]!=imported[field]}
    if len(audit)!=len(changed_fields) or {row['field'] for row in audit}!=changed_fields:
        raise ProjectError('Arrival source byte audit differs from the proposed entry')
    for row in audit:
        offset=resource['reference']['pc']+(2 if resource['reference']['extended_target'] is not None else 1)+3+resource['reference']['name_byte_length']+ENTRY_FIELDS.index(row['field'])
        if (row['source_record_sha256']!=resource['source_record']['sha256'] or row['owner_id']!=owner or
                row['before_byte']!=imported[row['field']] or row['after_byte']!=encoded[row['field']] or
                row['record_relative_byte_offset']!=offset or row['decoded_byte_offset']!=resource['source_record']['byte_offset']+offset):
            raise ProjectError('Arrival source byte audit failed independent qualification')
    report=dict(schema_version='legaia.transition-arrival-review.v1',read_only=True,
                preview=preview,arrival=deepcopy(arrival),proposed_encoded=encoded,
                proposed_arrival=reference_entry_interpretation(encoded),source_byte_audit=audit,
                authored_change=authored_change,
                current_change_count=sum(encoded[key]!=entry['effective_values'][key] for key in encoded))
    if expected_project_key!=project_transition_state_key(project) or expected_destination_key!=source_key(project):
        raise ProjectError('Arrival authoring source changed during Review')
    report['review_key']=digest(report)
    return report


def apply(project, body):
    if not isinstance(body,dict) or set(body)!={'asset_id','project_state_key','destination_source_key','arrival','review_key'}:
        raise ProjectError('Arrival Apply requires the exact reviewed request')
    report=review(project,body['asset_id'],body['project_state_key'],body['destination_source_key'],body['arrival'])
    if body['review_key']!=report['review_key']:raise ProjectError('Arrival Review changed; review again before Apply')
    resource=report['preview']['resource']
    project.command(dict(type='set_transition_arrival',entity_id=resource['owner_id'],
                         transition_id=resource['entry_layers']['transition_id'],arrival=report['arrival']))
    return report
