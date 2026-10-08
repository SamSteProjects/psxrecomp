"""Request-local retained audio dependency proofs shared by reference scene adapters.

Native composition runs once per request. Publication still rechecks saved
project identity, retained WAV/MIDI bytes and qualified native ownership.
This snapshot is private assembly state, never a persisted or HTTP input.
"""
from copy import deepcopy
from hashlib import sha256

from .project import ProjectError


class AudioReferenceSnapshot:
    def __init__(self, project):
        from .project_assets import source_key
        from .audio_input_assets import inventory
        from .audio_input_bindings import current
        self._key = source_key(project)
        self._inputs = inventory(project)
        from .midi_input_assets import inventory as midi_inventory
        self._midi_inputs = midi_inventory(project)
        self._bindings = current(project, self._inputs)
        self._sources = {}
        for proof in self._bindings:
            native = proof['native_asset_id']
            binding = project.audio_sample_overrides[native]
            self._sources[native] = deepcopy(binding)
        self.check_owner(project)

    def check_owner(self, project):
        from .project_assets import source_key
        if source_key(project) != self._key:
            raise ProjectError('Audio reference project changed during assembly')

    def inputs(self):
        return deepcopy(self._inputs)

    def midi_inputs(self):
        return deepcopy(self._midi_inputs)

    def bindings(self):
        return deepcopy(self._bindings)

    def verify(self, project):
        from .audio_input_assets import inventory
        from .audio_bank_authoring import _source
        self.check_owner(project)
        if inventory(project) != self._inputs:
            raise ProjectError('Retained WAV reference inputs changed during assembly')
        from .midi_input_assets import inventory as midi_inventory
        if midi_inventory(project) != self._midi_inputs:
            raise ProjectError('Retained MIDI reference inputs changed during assembly')
        for native, binding in self._sources.items():
            record = binding['source_record']
            body, bank, actual = _source(project, native, record['entry_sha256'], binding['source_scene_id'])
            if (actual != record or sha256(body).hexdigest() != record['entry_sha256']
                    or sha256(bank).hexdigest() != binding['bank_sha256']):
                raise ProjectError('Current WAV reference native ownership changed during assembly')
        self.check_owner(project)
