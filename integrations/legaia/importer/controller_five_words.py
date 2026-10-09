"""ACTOR_CTRL11 encoded operands; helper state and effects remain unresolved."""
from .controller_triplets import ControllerWordOperandAuthoringContext, validate_triplet_values
from .controller_system_flags import load_controller_record_source

LIMITATIONS = [
    'Only reached FIVE_WORD_HELPER_REQUEST operands with no decoder stops are candidates.',
    'Signed word meanings, helper-owned runtime state and visible effects remain unresolved.',
    'Sub-op, dispatch context, instruction layout, successors, dialogue and MAN pointers remain unchanged.',
    'Native serialization alone does not establish project/editor Build support or gameplay execution.',
]


def validate_five_word_values(values):
    return validate_triplet_values(values, 'Five-word', selector=False, word_count=5)


class ControllerFiveWordAuthoringContext(ControllerWordOperandAuthoringContext):
    HAS_SELECTOR = False
    WORD_COUNT = 5
    OPCODE = 0x43
    MNEMONIC = 'FIVE_WORD_HELPER_REQUEST'
    SUB_OPS = (0x11,)
    IDENTITY_SEGMENT = 'five-word'
    AUDIT_ID = 'five_word_id'
    LABEL = 'Five-word'
    LIMITATIONS = LIMITATIONS


def load_controller_five_word_context(disc, scene):
    return ControllerFiveWordAuthoringContext(load_controller_record_source(disc, scene))
