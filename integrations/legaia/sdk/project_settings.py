"""Project metadata commands, separate from imported content and runtime configuration."""
from .project import ProjectError,digest

def view(project):
    return dict(name=project.name,path=str(project.root),disc_path=project.disc_path,
                disc_identity=next(iter(project.imports.values()))['source']['disc_identity'] if project.imports else None,
                imported_scene_count=len(project.imports),active_scene=project.active_scene,mode=project.mode,
                review_key=digest(dict(project_root=str(project.root),name=project.name)))

def rename(project,command):
    if set(command)!={'type','name','review_key'}:raise ProjectError('Project rename accepts name and current review identity only')
    name=command['name']
    if not isinstance(name,str) or not 1<=len(name.strip())<=120 or any(ord(char)<32 or ord(char)==127 or 0xD800<=ord(char)<=0xDFFF for char in name):raise ProjectError('Project name requires 1–120 valid Unicode characters without controls')
    if command['review_key']!=view(project)['review_key']:raise ProjectError('Project name changed since inspection; reopen settings')
    name=name.strip()
    if name==project.name:return
    project.undo_stack.append(dict(target='project_name',before=project.name,after=name));project.name=name;project.redo_stack.clear()
