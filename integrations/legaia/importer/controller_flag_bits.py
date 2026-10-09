"""Native controller bit-index serialization; bank identity and gameplay remain unresolved."""
from .core import ImportError
from .controller_system_flags import ControllerRecordSource,load_controller_record_source
from .flag_authoring import FlagAuthoringContext,LIMITATIONS
from .script_inspection import inspect_record

class ControllerFlagBitAuthoringContext(FlagAuthoringContext):
    OWNER_PATTERN=r'[A-Za-z0-9_-]{1,128}/controllers/man-p1/0000'

    def __init__(self,source):
        if not isinstance(source,ControllerRecordSource):
            raise ImportError('Controller flag bits require a dedicated verified controller source')
        super().__init__(source)

    def provenance(self):
        return dict(self._source.provenance(),limitations=list(LIMITATIONS)+[
            'Controller record zero is separate from placed actors and partition-two scripts.',
            'Runtime flag values, story-state, scheduling and gameplay remain unverified.'])

    def options(self,owner):
        value=super().options(owner)
        offset,record,entry=self._source.verified_record(owner)
        value['inspection']=inspect_record(record,entry,semantic_id=owner.replace('scene://','script://',1),base_offset=offset)
        for target in value['targets']:
            target.update(bit_mask=31,preserved_bits=record[target['decoded_byte_offset']-offset]&0xe0)
        return value

    def patch(self,edits,*,original=None):
        result,audit=super().patch(edits,original=original)
        for row in audit:row.update(bit_mask=31,preserved_bits=row['before_byte']&0xe0)
        return result,audit

def load_controller_flag_bit_context(disc,scene):
    return ControllerFlagBitAuthoringContext(load_controller_record_source(disc,scene))
