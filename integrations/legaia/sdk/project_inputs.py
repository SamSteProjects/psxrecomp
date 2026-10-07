"""Navigation-independent persistent identity, separate from catalog availability."""
from pathlib import Path
from .project import ProjectError,digest


def identity(project):
    try:
        document=project._document()
        document.pop('active_scene',None)
        disc_path=str(Path(project.disc_path).resolve()) if project.disc_path else None
        stamp=None
        if disc_path is not None:
            try:
                stat=Path(disc_path).stat()
                stamp=[stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns]
            except OSError:
                pass
        return dict(project_path=str(project.root),disc_path=disc_path,disc_stat=stamp,
                    imports={scene:digest(imported) for scene,imported in sorted(project.imports.items())},
                    project_document=document)
    except (TypeError,ValueError,AttributeError,RecursionError) as exc:
        raise ProjectError('Persistent project inputs cannot be inspected') from exc
