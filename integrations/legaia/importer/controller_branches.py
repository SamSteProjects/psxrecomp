"""Source-bound controller branch words; record zero is never an actor."""
from .core import ImportError
from .branch_authoring import BranchAuthoringContext
from .controller_system_flags import (ControllerRecordSource,ControllerSystemFlagAuthoringContext,
                                      load_controller_record_source)


class ControllerBranchAuthoringContext(BranchAuthoringContext):
    OWNER_PATTERN = r'[A-Za-z0-9_-]+/controllers/man-p1/0000'

    def __init__(self,source,*,system_selectors=None):
        if not isinstance(source,ControllerRecordSource):
            raise ImportError('Controller branches require a dedicated verified controller source')
        super().__init__(source,system_selectors=system_selectors)

    @staticmethod
    def _selector_context(source):
        return ControllerSystemFlagAuthoringContext(source)

    def provenance(self):
        value=super().provenance()
        value['limitations']+=['Controller branch ownership is separate from actor and partition-two script ownership.',
                              'Encoded controller branch serialization does not establish scheduling, story activation or runtime execution.']
        return value


def load_controller_branch_context(disc,scene,*,system_selectors=None):
    return ControllerBranchAuthoringContext(load_controller_record_source(disc,scene),system_selectors=system_selectors)
