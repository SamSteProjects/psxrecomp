"""Content-addressed MIDI assets with separate historical and active source bindings."""
import base64,re
from hashlib import sha256
from copy import deepcopy
from .audio_midi_sources import validate_collection,read_source
from .project import ProjectError,digest
from importer.audio_sequence_midi import decode_midi

PREFIX='audio-input://legaia/midi/'


def inventory(project):
    rows=deepcopy(project.audio_midi_sources);validate_collection(rows)
    replacements=deepcopy(project.audio_sequence_replacements)
    from .sequence_replacement_authoring import validate_collection as validate_replacements,read as read_replacement
    validate_replacements(project)
    assets,receipts,memberships,bindings={},{},{},{}
    def register(raw,path,scene):
        track=decode_midi(raw)
        h=sha256(raw).hexdigest();identifier=PREFIX+h
        record=dict(id=identifier,semantic_id=identifier,kind='audio',asset_kind='audio',
            name='MIDI Input '+h[:12],layer='authored_input',source_kind='retained_midi_input',format='smf0',
            source_record=dict(kind='project_midi_input',sha256=h,byte_length=len(raw),relative_path=path),
            midi_input=dict(schema_version='legaia.midi-input-asset.v1',midi_sha256=h,byte_length=len(raw),
                midi_format=0,ppqn=track['ppqn'],event_count=len(track['events']),decoded_ticks=track['decoded_ticks']))
        if identifier in assets:
            previous=assets[identifier]
            if previous['midi_input']!=record['midi_input']:raise ProjectError('Shared MIDI content has conflicting file metadata')
            record['source_record']['relative_path']=min(path,previous['source_record']['relative_path'])
        assets[identifier]=record;receipts.setdefault(identifier,[]);bindings.setdefault(identifier,[])
        memberships.setdefault(scene,set()).add(identifier)
        return identifier
    for key,r in sorted(rows.items()):
        raw=read_source(project,r);identifier=register(raw,'Authored/Audio/MidiSources/'+r['midi_sha256']+'.mid',r['source_scene_id'])
        receipts[identifier].append(deepcopy(r))
    for native,b in sorted(replacements.items()):
        _,_,raw=read_replacement(project,native,b)
        identifier=register(raw,'Authored/Audio/SequenceReplacements/'+b['midi_sha256']+'.mid',b['source_scene_id'])
        bindings[identifier].append(dict(native_asset_id=native,binding=deepcopy(b)))
    if digest(rows)!=digest(project.audio_midi_sources) or digest(replacements)!=digest(project.audio_sequence_replacements):raise ProjectError('MIDI assets changed during qualification')
    return dict(records_by_scene={scene:[deepcopy(assets[k]) for k in sorted(keys)] for scene,keys in sorted(memberships.items())},assets=deepcopy(assets),receipts=deepcopy(receipts),replacement_bindings=deepcopy(bindings))


def inspect(project,asset_id,expected_source_key,*,include_midi=False):
    from .project_assets import source_key
    if not isinstance(asset_id,str) or re.fullmatch(re.escape(PREFIX)+'[a-f0-9]{64}',asset_id) is None or type(include_midi) is not bool:raise ProjectError('Choose a retained MIDI asset identity')
    if source_key(project)!=expected_source_key:raise ProjectError('Project MIDI asset sources changed')
    snapshot=inventory(project)
    if asset_id not in snapshot['assets']:raise ProjectError('MIDI asset has no registered receipt or replacement binding')
    from .midi_current_matches import compare
    from .midi_replacement_bindings import current
    receipts=snapshot['receipts'][asset_id]
    comparisons=compare(project,receipts) if receipts else []
    proofs=current(project,snapshot,asset_id)
    result=dict(schema_version='legaia.midi-input-inspection.v3',asset_id=asset_id,source_key=expected_source_key,
        project_path=str(project.root),record=snapshot['assets'][asset_id],receipts=receipts,
        current_comparisons=comparisons,current_replacement_bindings=proofs,historical_inputs=bool(receipts),read_only=True,project_changed=False,
        current_binding='verified_authored_sequence_replacement' if proofs else 'not_asserted',runtime_binding='not_asserted',gameplay_verified=False)
    if include_midi:
        if receipts:raw=read_source(project,receipts[0])
        else:
            from .sequence_replacement_authoring import read
            row=snapshot['replacement_bindings'][asset_id][0];raw=read(project,row['native_asset_id'],row['binding'])[2]
        result['midi_base64']=base64.b64encode(raw).decode('ascii')
    if inventory(project)!=snapshot or source_key(project)!=expected_source_key:raise ProjectError('MIDI sources changed during asset inspection')
    return deepcopy(result)
