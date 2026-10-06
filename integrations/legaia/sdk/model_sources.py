"""Bounded immutable model derivations behind fresh retail disc verification."""
from collections import OrderedDict
from threading import RLock
from .project import ProjectError,digest

class ModelSourceService:
    MAX_SCENES=8
    MAX_MODELS=32
    MAX_BYTES=32*1024*1024

    def __init__(self):
        self.lock=RLock()
        self.scenes=OrderedDict();self.models=OrderedDict();self.byte_length=0
        self.scene_derivations=0;self.model_derivations=0;self.hits=0

    def __deepcopy__(self,memo):
        # Build review and import staging copy project authoring state. Locks and
        # derived caches belong to the service instance, not that saved state.
        result=type(self)();memo[id(self)]=result
        result.MAX_SCENES=self.MAX_SCENES;result.MAX_MODELS=self.MAX_MODELS;result.MAX_BYTES=self.MAX_BYTES
        return result

    def clear(self):
        with self.lock:
            self.scenes.clear();self.models.clear();self.byte_length=0

    def read(self,project,asset_id,scene_id):
        with self.lock:return self._read(project,asset_id,scene_id)

    def _read(self,project,asset_id,scene_id):
        from importer.pipeline import _disc_context,import_scene
        from importer.assets import load_model_source
        document=project.imports.get(scene_id);disc=project.disc_path
        if document is None or not disc:raise ProjectError('Model shape requires an imported scene and its disc')
        asset=next((a for a in document['assets']['models'] if a['semantic_id']==asset_id),None)
        if asset is None:raise ProjectError('Unknown imported model identity')
        document_key=digest(document)
        try:
            # The context hashes the complete disc for every new operation. Nested
            # readers share only their outer operation's verified handle/guard.
            with _disc_context(disc) as (_,disc_hash,_,_):
                scene_key=(scene_id,document_key,disc_hash)
                qualified=scene_key in self.scenes
                if not qualified:
                    self.scene_derivations+=1
                    if import_scene(disc,document['scene']['name'])!=document:raise ProjectError('Model source differs from imported evidence')
                model_key=(scene_key,asset_id)
                hit=model_key in self.models
                if hit:data=self.models[model_key]
                else:
                    self.model_derivations+=1;data=load_model_source(disc,asset)
                if not isinstance(data,bytes):raise ProjectError('Model source decoder did not return immutable bytes')
                if project.disc_path!=disc or digest(project.imports.get(scene_id))!=document_key:raise ProjectError('Model source context changed during its read')
            # Publish only after successful exit, including the disc-stamp check.
            self.scenes[scene_key]=True;self.scenes.move_to_end(scene_key)
            while len(self.scenes)>self.MAX_SCENES:self.scenes.popitem(last=False)
            if hit:self.hits+=1;self.models.move_to_end(model_key)
            elif len(data)<=self.MAX_BYTES:
                self.models[model_key]=data;self.byte_length+=len(data)
                while len(self.models)>self.MAX_MODELS or self.byte_length>self.MAX_BYTES:
                    _,old=self.models.popitem(last=False);self.byte_length-=len(old)
            return data
        except Exception:
            self.clear()
            raise

    def statistics(self):
        with self.lock:return dict(qualified_scenes=len(self.scenes),cached_models=len(self.models),
                    cached_bytes=self.byte_length,scene_derivations=self.scene_derivations,
                    model_derivations=self.model_derivations,cache_hits=self.hits)
