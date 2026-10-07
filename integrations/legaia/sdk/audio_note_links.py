"""Current encoded note/program/tone/sample evidence; no runtime instrument claim."""
from copy import deepcopy
from hashlib import sha256
from importer.audio_bank import read_audio_bank,bank_from_entry,inspect_bank
from .project import ProjectError
from .audio_authoring import options,source_key,_current
from .audio_composition import read_entry


def inspect(project,asset_id,expected_entry_sha256,expected_source_key,expected_authoring_key,note_index):
    if expected_authoring_key!=source_key(project):
        raise ProjectError('Audio inputs changed; inspect the Current sequence again')
    if type(note_index) is not int or not 0<=note_index<32768:
        raise ProjectError('Choose a reached encoded note start')
    report=options(project,asset_id,expected_entry_sha256,expected_source_key)
    events=report['current']['events']
    if note_index>=len(events) or events[note_index]['kind']!='note_on' or not events[note_index]['values'][1]:
        raise ProjectError('Choose a positive-velocity encoded note start')
    note=events[note_index]
    program_event=next((e for e in reversed(events[:note_index]) if e['channel']==note['channel'] and e['kind']=='program_change'),None)
    bank=None
    allocated=report['schema_version']=='legaia.audio-sequence-authoring.v2'
    if report['source_record']['sequence_offset']!=0:
        bank=read_audio_bank(project.disc_path,asset_id,expected_entry_sha256)
        _,current,_,_,_=_current(project,asset_id,expected_entry_sha256)
        if sha256(current).hexdigest()!=report['current_entry_sha256']:
            raise ProjectError('Current audio changed during bank inspection')
        body,pieces,carrier=bank_from_entry(current)
        if carrier!=bank['source_record']['carrier'] or not allocated and pieces!=bank['source_record']['pieces']:
            raise ProjectError('Current bank carrier changed source ownership')
        bank.update(inspect_bank(body),schema_version='legaia.audio-current-bank-inspection.v1' if allocated else 'legaia.audio-bank-inspection.v1',asset_id=asset_id,
                    scene_id=project.active_scene,source_key=expected_source_key,read_only=True,
                    project_changed=False,runtime_state='not_observed')
        if allocated:bank['current_layout']=dict(entry_sha256=report['current_entry_sha256'],entry_size_bytes=len(current),bank_size_bytes=len(body),carrier=carrier,pieces=pieces)
    if expected_authoring_key!=source_key(project):
        raise ProjectError('Audio inputs changed during note link inspection')
    return dict(schema_version='legaia.audio-note-links.v2' if allocated else 'legaia.audio-note-links.v1',asset_id=asset_id,
        authoring_key=expected_authoring_key,current_entry_sha256=report['current_entry_sha256'],
        current_sequence_sha256=report['current_sequence_sha256'],note=deepcopy(note),
        program_event=deepcopy(program_event),bank=bank,project_changed=False,runtime_state='not_observed')
