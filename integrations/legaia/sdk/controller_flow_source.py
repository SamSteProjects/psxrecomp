"""Fresh read-only provenance for exact controller operand flow layers."""
from copy import deepcopy
from hashlib import sha256
from importlib import import_module
import json,re
from .project import ProjectError,digest
from .controller_snapshots import FAMILIES
from .controller_system_flags import state_key,scene_document

SCHEMA='legaia.controller-flow-source.v1'

def report_hash(report):
    # Same UTF-8 compact sorted representation as scriptFlowReportHash in the editor.
    return sha256(json.dumps(report,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest()

def qualify(project,owner,component,layer,expected_source_key,*,operand_id=None,value=None,review_key=None):
    modules=dict(FAMILIES)
    if not isinstance(component,str) or component not in modules or layer not in ('current','proposed'):
        raise ProjectError('Choose a supported controller component and flow layer')
    if not isinstance(expected_source_key,str) or expected_source_key!=state_key(project):
        raise ProjectError('Controller flow source changed; refresh before qualification')
    document=scene_document(project,owner)
    if project.mode!='edit' or project.active_scene!=document['scene']['semantic_id']:
        raise ProjectError('Controller flow qualification requires its active Edit scene')
    module=import_module('.'+modules[component],__package__)
    if layer=='current':
        if operand_id is not None or value is not None or review_key is not None:
            raise ProjectError('Current flow cannot include a Proposed operand binding')
        source=module.snapshot(project,owner);report=source['current_report'];effective=source['current_record_sha256']
    else:
        if not isinstance(review_key,str) or re.fullmatch('[a-f0-9]{64}',review_key) is None:
            raise ProjectError('Proposed flow requires a qualified Review key')
        source=module.review(project,owner,operand_id,value)
        if source['review_key']!=review_key:
            raise ProjectError('Controller flow Review or supplied operands changed')
        report=source['proposed_report'];effective=source['proposed_record_sha256']
    if (source['owner_id']!=owner or source['state_key']!=expected_source_key or source['gameplay_verified'] is not False
            or state_key(project)!=expected_source_key):
        raise ProjectError('Controller flow source changed during qualification')
    proof=dict(schema_version=SCHEMA,owner_id=owner,scene_id=project.active_scene,component=component,
        representation='authored_current' if layer=='current' else 'reviewed_proposed',state_key=expected_source_key,
        source_import_sha256=digest(document),source_record_sha256=source['source_record_sha256'],
        current_record_sha256=source['current_record_sha256'],effective_record_sha256=effective,
        operand_id=operand_id,value=deepcopy(value),review_key=review_key,report_sha256=report_hash(report),
        read_only=True,project_changed=False,runtime_execution='not_asserted',gameplay_verified=False)
    return dict(proof,source_key=digest(proof),report=deepcopy(report))
