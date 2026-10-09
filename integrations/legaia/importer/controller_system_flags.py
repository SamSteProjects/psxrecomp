"""Native selector adapter with explicit controller-only MAN ownership.

This is serialization qualification, not runtime controller execution.
"""
from copy import deepcopy
import re
from .core import ImportError
from .scene_controller import controller_record
from .dialogue_authoring import DialogueAuthoringContext
from .system_flag_authoring import SystemFlagAuthoringContext
from .pipeline import _disc_context, _bounded_scene_range
from .man_source import read_man_source


class ControllerRecordSource:
    def __init__(self, scene, man, stream, provenance, *, compression='lzs'):
        if not isinstance(scene, str) or len(scene)>1024 or re.fullmatch(r'[A-Za-z0-9_-]+', scene) is None:
            raise ImportError('Controller source requires a bounded scene identity')
        # Reuse the established encoded/decoded MAN parity guard, without
        # registering controller record zero as an actor.
        source = DialogueAuthoringContext(scene, man, stream, provenance, compression=compression)
        self.scene, self._man = scene, source._man
        self._source = source
        self._record = controller_record(self._man, scene)
        self.owner_id = f'scene://{scene}/controllers/man-p1/0000'

    def verified_record(self, owner):
        if owner != self.owner_id:
            raise ImportError('Controller selector owner differs from its unique source record')
        return self._record

    def provenance(self):
        value = self._source.provenance()
        value.update(owner_id=self.owner_id, record_kind='man_partition_1_scene_controller',
                     runtime_execution='not_asserted', limitations=[
            'Controller record zero is separate from placed actors and partition-two scripts.',
            'Only independently qualified encoded operands are writable; native execution and bank capacity remain unknown.'])
        return deepcopy(value)


class ControllerSystemFlagAuthoringContext(SystemFlagAuthoringContext):
    OWNER_PATTERN = r'[A-Za-z0-9_-]+/controllers/man-p1/0000'

    def __init__(self, source):
        if not isinstance(source, ControllerRecordSource):
            raise ImportError('Controller selector adapter requires a dedicated verified source')
        super().__init__(source)


def load_controller_record_source(disc, scene):
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        carrier = read_man_source(archive, start, end, scene)
        raw = archive.read_entry(archive.entry(carrier.entry_index), extended=True)
        stream = raw[carrier.payload_offset:carrier.payload_offset + carrier.encoded_size]
        provenance = dict(disc_sha256=digest, iso_file='PROT.DAT',
                          prot_entry_index=carrier.entry_index, man=carrier.provenance())
        source = ControllerRecordSource(scene, carrier.payload, stream, provenance,
            compression='lzs' if carrier.kind == 'descriptor_man' else 'none')
        return source


def load_controller_system_flag_context(disc, scene):
    return ControllerSystemFlagAuthoringContext(load_controller_record_source(disc,scene))
