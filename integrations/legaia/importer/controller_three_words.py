"""E6 encoded signed-word operands; helper state and effects remain unresolved."""
from .controller_triplets import ControllerTripletAuthoringContext, validate_triplet_values
from .controller_system_flags import load_controller_record_source

LIMITATIONS = [
    'Only reached FIELD_THREE_WORD_REQUEST operands in fully decoded controller paths are candidates.',
    'Signed word meanings, helper-owned runtime state and visible effects remain unresolved.',
    'Sub-op, dispatch context, instruction layout, successors, dialogue and MAN pointers remain unchanged.',
    'Native serialization does not establish gameplay execution or project/editor Build support.',
]


def validate_three_word_values(values):
    return validate_triplet_values(values, 'Three-word', selector=False)


class ControllerThreeWordAuthoringContext(ControllerTripletAuthoringContext):
    HAS_SELECTOR = False
    MNEMONIC = 'FIELD_THREE_WORD_REQUEST'
    SUB_OPS = (0xE6,)
    IDENTITY_SEGMENT = 'three-word'
    AUDIT_ID = 'three_word_id'
    LABEL = 'Three-word'
    LIMITATIONS = LIMITATIONS


def load_controller_three_word_context(disc, scene):
    return ControllerThreeWordAuthoringContext(load_controller_record_source(disc, scene))
