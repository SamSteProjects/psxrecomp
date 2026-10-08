"""Content-addressed retained MIDI assets; capture targets are historical."""
import base64,re
from copy import deepcopy
from .audio_midi_sources import validate_collection,read_source
from .project import ProjectError,digest
from importer.audio_sequence_midi import decode_midi

PREFIX='audio-input://legaia/midi/'


def inventory(project):
    rows=deepcopy(project.audio_midi_sources);validate_collection(rows)
    assets,receipts,memberships={},{},{}
    for key,r in sorted(rows.items()):
        raw=read_source(project,r);track=decode_midi(raw);h=r['midi_sha256'];identifier=PREFIX+h
        record=dict(id=identifier,semantic_id=identifier,kind='audio',asset_kind='audio',
            name='MIDI Input '+h[:12],layer='authored_input',source_kind='retained_midi_input',format='smf0',
            source_record=dict(kind='project_midi_input',sha256=h,byte_length=len(raw),relative_path='Authored/Audio/MidiSources/'+h+'.mid'),
            midi_input=dict(schema_version='legaia.midi-input-asset.v1',midi_sha256=h,byte_length=len(raw),
                midi_format=0,ppqn=track['ppqn'],event_count=len(track['events']),decoded_ticks=track['decoded_ticks']))
        if identifier in assets and assets[identifier]!=record:raise ProjectError('Shared MIDI content has conflicting file metadata')
        assets[identifier]=record;receipts.setdefault(identifier,[]).append(deepcopy(r))
        memberships.setdefault(r['source_scene_id'],set()).add(identifier)
    if digest(rows)!=digest(project.audio_midi_sources):raise ProjectError('MIDI assets changed during qualification')
    return dict(records_by_scene={scene:[deepcopy(assets[k]) for k in sorted(keys)] for scene,keys in sorted(memberships.items())},assets=deepcopy(assets),receipts=deepcopy(receipts))


def inspect(project,asset_id,expected_source_key,*,include_midi=False):
    from .project_assets import source_key
    if not isinstance(asset_id,str) or re.fullmatch(re.escape(PREFIX)+'[a-f0-9]{64}',asset_id) is None or type(include_midi) is not bool:raise ProjectError('Choose a retained MIDI asset identity')
    if source_key(project)!=expected_source_key:raise ProjectError('Project MIDI asset sources changed')
    snapshot=inventory(project)
    if asset_id not in snapshot['assets']:raise ProjectError('MIDI asset has no registered Current receipt')
    from .midi_current_matches import compare
    comparisons=compare(project,snapshot['receipts'][asset_id])
    result=dict(schema_version='legaia.midi-input-inspection.v2',asset_id=asset_id,source_key=expected_source_key,
        project_path=str(project.root),record=snapshot['assets'][asset_id],receipts=snapshot['receipts'][asset_id],
        current_comparisons=comparisons,historical_inputs=True,read_only=True,project_changed=False,current_binding='not_asserted',runtime_binding='not_asserted',gameplay_verified=False)
    if include_midi:result['midi_base64']=base64.b64encode(read_source(project,result['receipts'][0])).decode('ascii')
    if inventory(project)!=snapshot or source_key(project)!=expected_source_key:raise ProjectError('MIDI sources changed during asset inspection')
    return deepcopy(result)
