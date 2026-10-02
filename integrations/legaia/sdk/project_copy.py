"""Capture current editable inputs into a fresh project without saving the source."""
from hashlib import sha256
import json
from uuid import uuid4
from .build import _guard_output, _write_exact
from .export_snapshot import capture_export_inputs
from .project import ProjectError, ProjectService, canonical, digest

MAX_BYTES=256*1024*1024
MAX_FILES=512


def source_key(project):
    return digest(dict(root=str(project.root),mode=project.mode,document=project._document()))


def _capture(project):
    if project.mode!='edit':raise ProjectError('Project copy requires Edit mode')
    if len(project.imports)>64:raise ProjectError('Project copy supports at most 64 imported scenes')
    before=digest(project._document())
    authored_key,files=capture_export_inputs(project,max_bytes=MAX_BYTES,max_files=MAX_FILES)
    if digest(project._document())!=before:raise ProjectError('Project metadata changed while capturing inputs')
    inventory=[dict(path=relative,sha256=sha256(payload).hexdigest(),byte_length=len(payload)) for relative,payload in sorted(files.items())]
    key=digest(dict(root=str(project.root),mode=project.mode,document=before,files=inventory))
    return key,authored_key,files,inventory


def review(project):
    key,authored_key,files,inventory=_capture(project)
    return dict(schema_version='legaia.project-copy-review.v1',review_key=key,
                project_source_key=source_key(project),
                source_project=str(project.root),source_name=project.name,source_dirty=project.dirty,
                source_authored_state_key=authored_key,imported_scene_count=len(project.imports),
                file_count=len(inventory),byte_length=sum(row['byte_length'] for row in inventory),
                files=inventory,includes_unsaved_metadata=True,retail_disc_included=False,
                undo_history_included=False,generated_outputs_included=False,live_state_included=False)


def create_copy(project,name,review_key):
    from .project_settings import normalize_name
    name=normalize_name(name)
    key,authored_key,files,inventory=_capture(project)
    if key!=review_key:raise ProjectError('Project inputs changed since copy review; review again')
    document=json.loads(files['project.legaia.json']);document['name']=name
    files['project.legaia.json']=canonical(document)
    if len(files['project.legaia.json'])>64*1024*1024 or sum(map(len,files.values()))>MAX_BYTES:
        raise ProjectError('Named project copy exceeds its byte limit')
    destination=project.root/'ProjectCopies'/('project-'+uuid4().hex)
    _guard_output(destination,project.root)
    destination.mkdir(parents=True,exist_ok=False)
    _write_exact(destination/'.gitignore',b'*\n',project.root)
    copied=[]
    for relative,payload in sorted(files.items()):
        target=destination/relative
        _write_exact(target,payload,project.root)
        if sha256(target.read_bytes()).hexdigest()!=sha256(payload).hexdigest():
            raise ProjectError('Copied input changed during readback')
        copied.append(dict(path=relative,sha256=sha256(payload).hexdigest(),byte_length=len(payload)))
    reopened=ProjectService.open(destination)
    if reopened._document()!=document:raise ProjectError('Reopened copy differs from captured metadata')
    # Repeat the full input review, including templates/views and file hashes.
    if _capture(project)[0]!=key:raise ProjectError('Source inputs changed while copying; no completion report saved')
    report=dict(schema_version='legaia.project-copy.v1',source_project=str(project.root),
                source_review_key=key,source_authored_state_key=authored_key,
                project_source_key=source_key(project),
                source_dirty=project.dirty,copied_project=str(destination),name=name,
                files=copied,readback_verified=True,reopened_metadata_verified=True,
                retail_disc_included=False,undo_history_included=False,
                generated_outputs_included=False,live_state_included=False)
    _write_exact(destination/'copy-report.json',canonical(report),project.root)
    return report
