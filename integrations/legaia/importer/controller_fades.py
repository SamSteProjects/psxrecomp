"""Controller fade authoring; shared triplet geometry, separate source ownership."""
from .controller_triplets import ControllerTripletAuthoringContext, validate_triplet_values
from .controller_system_flags import load_controller_record_source

LIMITATIONS = [
    'Only reached FIELD_FADE_REQUEST operands in fully decoded controller paths are candidates.',
    'Selector and signed word meanings, runtime ownership and visible fade effects remain unresolved.',
    'Sub-op, dispatch context, instruction layout, successors, dialogue and MAN pointers remain unchanged.',
    'Native serialization does not establish gameplay execution or project/editor Build support.',
]


def validate_fade_values(values):
    return validate_triplet_values(values, 'Fade')


class ControllerFadeAuthoringContext(ControllerTripletAuthoringContext):
    MNEMONIC = 'FIELD_FADE_REQUEST'
    SUB_OPS = (0x90, 0x91, 0x92)
    IDENTITY_SEGMENT = 'fade'
    AUDIT_ID = 'fade_id'
    LABEL = 'Fade'
    LIMITATIONS = LIMITATIONS


def load_controller_fade_context(disc, scene):
    return ControllerFadeAuthoringContext(load_controller_record_source(disc, scene))
