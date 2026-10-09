"""One request-scoped source preparation for the complete controller workspace."""
from contextvars import ContextVar
from copy import deepcopy
from hashlib import sha256
from importlib import import_module
from .project import ProjectError
from .controller_components import CONTROLLER_COMPONENTS
from importer.core import ImportError as RetailImportError

_request_preparation = ContextVar('legaia_controller_snapshot_preparation', default=None)
FAMILIES = (
    ('ControllerSystemFlags', 'controller_system_flags'),
    ('ControllerBranches', 'controller_branches'),
    ('ControllerTileRects', 'controller_tile_rects'),
    ('ControllerFades', 'controller_fades'),
    ('ControllerTableCopies', 'controller_tables'),
    ('ControllerWordTriplets', 'controller_word_triplets'),
    ('ControllerThreeWords', 'controller_three_words'),
    ('ControllerSceneBytes', 'controller_scene_bytes'),
    ('ControllerFiveWords', 'controller_five_words'),
    ('ControllerGlobalBytes', 'controller_global_bytes'),
    ('ControllerPartySelectors', 'controller_party_selectors'),
    ('ControllerFlagBits', 'controller_flag_bits'),
)


def snapshot(project, owner, expected_source_key):
    from .controller_system_flags import prepare, state_key
    from importer.pipeline import _disc_context
    if not isinstance(expected_source_key, str) or expected_source_key != state_key(project):
        raise ProjectError('Controller workspace source changed; refresh before inspection')
    if {family for family, _ in FAMILIES} != CONTROLLER_COMPONENTS:
        raise ProjectError('Controller workspace family registry is incomplete')
    if _request_preparation.get() is not None:
        raise ProjectError('Controller workspace snapshot cannot nest preparation scopes')
    try:
        with _disc_context(project.disc_path):
            prepared = prepare(project, owner)
            key, _, offset, record, _, _, current, _ = prepared
            if key != expected_source_key:
                raise ProjectError('Controller workspace source changed during preparation')
            source_hash = sha256(record).hexdigest()
            current_hash = sha256(current[offset:offset+len(record)]).hexdigest()
            token = _request_preparation.set((project, owner, prepared))
            try:
                families = {}
                for family, module in FAMILIES:
                    value = import_module('.'+module, __package__).snapshot(project, owner)
                    if (value.get('owner_id') != owner or value.get('state_key') != key or
                            value.get('source_record_sha256') != source_hash or
                            value.get('current_record_sha256') != current_hash or
                            value.get('gameplay_verified') is not False):
                        raise ProjectError('Controller workspace family lost its source binding')
                    families[family] = deepcopy(value)
                if key != state_key(project):
                    raise ProjectError('Controller workspace source changed during inspection')
            finally:
                _request_preparation.reset(token)
    except RetailImportError as exc:
        raise ProjectError(str(exc)) from exc
    return dict(schema_version='legaia.controller-workspace-snapshot.v1', owner_id=owner,
                state_key=key, source_record_sha256=source_hash, current_record_sha256=current_hash,
                families=families, read_only=True, project_changed=False, gameplay_verified=False)
