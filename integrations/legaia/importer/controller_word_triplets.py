"""Encoded D8 source operands; the first-word runtime offset is not authored."""
from .controller_triplets import ControllerTripletAuthoringContext, validate_triplet_values
from .controller_system_flags import load_controller_record_source

LIMITATIONS = [
    'Only reached FIELD_WORD_TRIPLET_REQUEST operands in fully decoded controller paths are candidates.',
    'Selector/word meanings, runtime binding and visible effects remain unresolved.',
    'The first encoded word is unadjusted; its runtime offset remains unknown and is never authored here.',
    'Sub-op, dispatch context, instruction layout, successors, dialogue and MAN pointers remain unchanged.',
    'Native serialization does not establish gameplay execution or project/editor Build support.',
]


def validate_word_triplet_values(values):
    return validate_triplet_values(values, 'Word-triplet')


class ControllerWordTripletAuthoringContext(ControllerTripletAuthoringContext):
    MNEMONIC = 'FIELD_WORD_TRIPLET_REQUEST'
    SUB_OPS = (0xD8,)
    IDENTITY_SEGMENT = 'word-triplet'
    AUDIT_ID = 'word_triplet_id'
    LABEL = 'Word-triplet'
    LIMITATIONS = LIMITATIONS


def load_controller_word_triplet_context(disc, scene):
    return ControllerWordTripletAuthoringContext(load_controller_record_source(disc, scene))
