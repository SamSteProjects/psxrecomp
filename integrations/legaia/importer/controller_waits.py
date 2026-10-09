"""Dedicated controller WAIT_FRAMES serialization; no scheduling claims."""
from .core import ImportError
from .controller_system_flags import ControllerRecordSource,load_controller_record_source
from .wait_authoring import WaitAuthoringContext,LIMITATIONS


class ControllerWaitAuthoringContext(WaitAuthoringContext):
    OWNER_PATTERN = r'[A-Za-z0-9_-]+/controllers/man-p1/0000'
    LIMITATIONS = [*LIMITATIONS[:-1],
        'Only native controller wait serialization is qualified; project/editor/Build integration remains pending.',
        'Controller scheduling, seconds, story activation and gameplay timing are not asserted.']

    def __init__(self,source):
        if not isinstance(source,ControllerRecordSource):
            raise ImportError('Controller waits require a dedicated verified controller source')
        super().__init__(source)


def load_controller_wait_context(disc,scene):
    return ControllerWaitAuthoringContext(load_controller_record_source(disc,scene))
