"""Verified resource discovery shared by the asset browser and inspectors."""
from __future__ import annotations

import base64
from copy import deepcopy
from importer.core import ImportError as RetailImportError
from importer.pipeline import _disc_context, import_scene
from .project import ProjectError
from .scene_preview import source_key


def _scene(project):
    document = project.imports.get(project.active_scene)
    if not project.disc_path or document is None:
        raise ProjectError("Resource discovery requires an imported scene and its user-owned disc")
    return document, source_key(project)


def _verify(project, document):
    if import_scene(project.disc_path, document["scene"]["name"]) != document:
        raise ProjectError("Resource source differs from freshly verified imported evidence")


def model_shape_source(project, asset_id: str, format: str = 'tmd', layer: str = 'imported') -> dict:
    """Private source download for editing an existing model's local shape."""
    from hashlib import sha256
    from importer.assets import decode_tmd
    if format not in ('tmd', 'obj', 'json'):
        raise ProjectError('Choose TMD, OBJ or JSON model source')
    if layer not in ('imported', 'authored'):
        raise ProjectError('Choose imported or authored model shape')
    document, key = _scene(project)
    asset = next((a for a in document['assets']['models'] if a['semantic_id'] == asset_id), None)
    if asset is None:
        raise ProjectError('Choose a model from the active imported scene')
    with _disc_context(project.disc_path):
        data = project._model_source(asset_id, project.active_scene)
        source_hash = sha256(data).hexdigest()
        if layer == 'authored':
            binding = project.model_overrides.get(asset_id)
            if binding is None:
                raise ProjectError('No authored shape exists for this model')
            data = project.read_model_replacement(asset_id, binding)
        preview = decode_tmd(data)
    if key != source_key(project):
        raise ProjectError('Model source changed while reading; refresh again')
    result = dict(semantic_id=asset_id, scene_id=project.active_scene, source_key=key,
                source_sha256=source_hash, effective_sha256=sha256(data).hexdigest(), representation=layer, byte_length=len(data),
                filename='original-model.tmd', tmd_base64=base64.b64encode(data).decode('ascii'),
                object_count=len(preview['objects']), coordinate_system=preview['coordinate_system'],
                limitations=['Model files preserve the qualified Current packet layout and object/vector capacities. Existing face-removal bindings retain their exact removed Retail identities; other count-changing file imports remain unsupported. Reserved fields and opaque bytes remain source-owned.'])
    if format == 'json':
        import json
        from importer.model_json import export_shape_json
        document = json.loads(export_shape_json(data))
        document['source_sha256'] = source_hash
        content = (json.dumps(document, sort_keys=True, indent=2) + '\n').encode('utf-8')
        result.pop('tmd_base64')
        result.update(json_base64=base64.b64encode(content).decode('ascii'), filename='original-model.json', byte_length=len(content))
        result['limitations'].append('Complete ordered source vertex and normal arrays; signed16 values without unit conversion.')
    if format == 'obj':
        from importer.model_obj import export_shape_obj
        obj = export_shape_obj(data)
        result.pop('tmd_base64')
        result.update(obj_base64=base64.b64encode(obj).decode('ascii'), filename='original-model.obj', byte_length=len(obj))
        result['limitations'].append('OBJ preserves vertex/face order and integer Y-down coordinates; TMD normals remain unchanged.')
    result['filename'] = ('authored' if layer == 'authored' else 'original') + '-model.' + format
    return result


def refresh_resource_catalog(project) -> dict:
    from importer.texture_catalog import load_texture_asset_catalog
    from importer.animation_catalog import load_animation_asset_catalog, load_global_animation_asset_catalog
    from importer.script_catalog import load_script_asset_catalog
    from importer.field_map import load_field_map_catalog
    from importer.worldmap_menu import load_worldmap_asset_catalog
    from importer.audio_catalog import load_audio_asset_catalog
    document, key = _scene(project)
    # Remove stale metadata before attempting a new source read. A failed refresh
    # must never leave a prior catalog presented as the current verified result.
    project.assets.resource_catalogs.pop(project.active_scene, None)
    flag_key = scene_flag_state_key(project)
    transition_key = scene_transition_state_key(project)
    region_key = scene_region_state_key(project)
    trigger_key = scene_trigger_state_key(project)
    records, limitations = [], []
    with _disc_context(project.disc_path):
        _verify(project, document)
        for kind, loader in (("Textures", load_texture_asset_catalog), ("Animations", load_animation_asset_catalog),
                             ("Shared field animations", load_global_animation_asset_catalog),
                             ("Source audio", load_audio_asset_catalog),
                             ("World-map landmarks", load_worldmap_asset_catalog),
                             ("Scripts and dialogue", load_script_asset_catalog),
                             ("Field collision and triggers", load_field_map_catalog)):
            try:
                catalog = loader(project.disc_path, document["scene"]["name"])
                records.extend(catalog["assets"])
                limitations.extend(catalog.get("limitations", []))
                if kind == 'Scripts and dialogue':
                    from .flag_assets import build_flag_assets
                    records.extend(build_flag_assets(catalog, _flag_edits(project, project.active_scene)))
                    from .transition_assets import build_transition_assets
                    records.extend(build_transition_assets(catalog, project.imports, _transition_edits(project, project.active_scene)))
            except RetailImportError as exc:
                limitations.append(f"{kind} unavailable: {exc}")
    from .texture_slots import current_items,metadata
    records.extend(metadata(*row) for row in current_items(project))
    from .retained_animation_assets import records as retained_records
    records.extend(retained_records(project))
    if (key != source_key(project) or flag_key != scene_flag_state_key(project) or
            transition_key != scene_transition_state_key(project) or region_key != scene_region_state_key(project) or
            trigger_key != scene_trigger_state_key(project)):
        raise ProjectError("Resource source changed during discovery; refresh again")
    if len(records) > 4096:
        raise ProjectError("Resource catalog exceeds the bounded record budget")
    return project.assets.register_resources(project.active_scene, key, records, limitations, flag_state_key=flag_key, transition_state_key=transition_key, region_state_key=region_key, trigger_state_key=trigger_key)


def scene_trigger_state_key(project) -> str:
    """Invalidate source trigger layers without reloading model geometry."""
    from .project import digest
    scene = project.active_scene
    return digest(dict(scene_id=scene, trigger_cells=deepcopy(project.overrides.get(scene, {}).get('TriggerCells')), trigger_scripts=deepcopy(project.overrides.get(scene, {}).get('TriggerScripts'))))


def scene_region_state_key(project) -> str:
    """Invalidate region annotations while preserving the geometry source key."""
    from .project import digest
    scene = project.active_scene
    return digest(dict(scene_id=scene, region_bounds=deepcopy(project.overrides.get(scene, {}).get('RegionBounds'))))


def scene_transition_state_key(project) -> str:
    """Transition annotation changes must invalidate resources without geometry edits."""
    from .project import digest
    scene = project.active_scene
    return digest(dict(scene_id=scene, transitions={owner: deepcopy(parts['Transitions'])
                  for owner, parts in project.overrides.items()
                  if scene and owner.startswith(scene + '/') and 'Transitions' in parts}))


def _transition_edits(project, scene_id):
    """Reverify authored transition spans before exposing effective entry metadata."""
    requested, owners = {}, {}
    for owner, components in deepcopy(getattr(project, 'overrides', {})).items():
        if not owner.startswith(scene_id + '/') or 'Transitions' not in components:
            continue
        value = components['Transitions']
        project._validate_transitions(owner, value)
        owners[owner] = {'Transitions': value}
        for key, values in value['entries'].items():
            if key in requested:
                raise ProjectError('Transition entry has multiple authored owners')
            requested[key] = values
    if requested:
        from importer.transition_authoring import load_transition_authoring_context
        try:
            context = load_transition_authoring_context(project.disc_path, project.imports[scene_id]['scene']['name'])
            context.patch(requested)
        except RetailImportError as exc:
            raise ProjectError('Authored transition entries failed source verification: ' + str(exc)) from exc
    return owners


def scene_flag_state_key(project) -> str:
    """Operand annotations have their own freshness key, separate from geometry."""
    from .project import digest
    scene = project.active_scene
    return digest(dict(scene_id=scene, flags={owner: deepcopy(parts['ScriptFlags'])
                  for owner, parts in project.overrides.items()
                  if scene and owner.startswith(scene + '/') and 'ScriptFlags' in parts}))


def project_flag_state_key(project) -> str:
    """Project reference annotations include source and authored operand identity."""
    from .project import digest
    return digest(dict(project_path=str(project.root), disc_path=project.disc_path,
                       imports=project.imports,
                       flags={owner: deepcopy(parts['ScriptFlags'])
                              for owner, parts in getattr(project, 'overrides', {}).items()
                              if 'ScriptFlags' in parts}))


def _flag_edits(project, scene_id):
    """Validate authored references against the source serializer before annotation."""
    requested = {}
    for owner, components in deepcopy(getattr(project, 'overrides', {})).items():
        if not owner.startswith(scene_id + '/') or 'ScriptFlags' not in components:
            continue
        project._validate_flags(owner, components['ScriptFlags'])
        for key, values in components['ScriptFlags']['entries'].items():
            if key in requested:
                raise ProjectError('Flag operand has multiple authored owners')
            requested[key] = values
    if requested:
        from importer.flag_authoring import load_flag_authoring_context
        try:
            context = load_flag_authoring_context(project.disc_path, project.imports[scene_id]['scene']['name'])
            context.patch(requested)
        except RetailImportError as exc:
            raise ProjectError("Authored flag operands failed source verification: " + str(exc)) from exc
    return requested


def scene_text_state_key(project) -> str:
    from .project import digest
    return digest({owner: deepcopy(parts['Dialogue']) for owner, parts in project.overrides.items()
                   if owner.startswith((project.active_scene or '') + '/') and 'Dialogue' in parts})


def scene_text_index(project) -> dict:
    """Private, bounded supported text discovery; never scan unknown bytes."""
    from importer.script_catalog import load_script_asset_catalog
    from importer.dialogue_authoring import load_dialogue_authoring_context
    document, key = _scene(project)
    text_key = scene_text_state_key(project)
    owners, rows, unavailable = [], [], []
    total_bytes = 0
    with _disc_context(project.disc_path):
        _verify(project, document)
        catalog = load_script_asset_catalog(project.disc_path, document['scene']['name'])
        context = load_dialogue_authoring_context(project.disc_path, document['scene']['name'])
        scripts = [item for item in catalog['assets'] if item['asset_kind'] == 'script']
        if len(scripts) > 1024:
            raise ProjectError('Text discovery exceeds the script budget')
        for script in scripts:
            owner = script.get('owner_semantic_id') or script['actor_semantic_id']
            if owner in owners:
                raise ProjectError('Text discovery has duplicate script owners')
            owners.append(owner)
            try:
                options = project._dialogue_options(context, owner)
            except RetailImportError as exc:
                unavailable.append(dict(owner_id=owner, reason=str(exc)))
                continue
            if not options['supported'] or options.get('reason') or options['unresolved_overrides']:
                unavailable.append(dict(owner_id=owner, reason=options.get('reason') or 'No supported plain-glyph runs',
                                        unresolved_overrides=options['unresolved_overrides']))
            for run in options['runs']:
                total_bytes += run['max_length']
                if len(rows) >= 8192 or total_bytes > 1024 * 1024:
                    raise ProjectError('Text discovery exceeds the run/text budget')
                rows.append(dict(id=run['semantic_id'], owner_id=owner,
                                 script_name=script['name'], partition=script['source_record']['partition'],
                                 script_status=script['status'], pc=run['pc'],
                                 kind=run.get('kind', 'dialogue'), capacity=run['max_length'],
                                 retail_text=run['text'], authored_text=run['authored_text'],
                                 effective_text=run['effective_text'], validation_error=run.get('validation_error'),
                                 menu_pc=run.get('menu_pc'), option_index=run.get('option_index')))
    if key != source_key(project) or text_key != scene_text_state_key(project):
        raise ProjectError('Scene source changed during text discovery; refresh again')
    return dict(schema='legaia.scene-text.v1', read_only=True, scene_id=project.active_scene,
                source_key=key, text_state_key=text_key, runs=rows, coverage=dict(script_count=len(owners),
                partial_script_count=catalog['partial_script_count'], unavailable_script_count=catalog['unavailable_script_count']),
                restrictions=unavailable, limitations=[
                    'Only source-qualified editable plain-glyph runs are searched; unknown/unvisited bytes and unsupported dialogue are excluded.',
                    'Partial scripts may offer decoded menu labels while ordinary dialogue remains unavailable.',
                    'Runs are separate source spans, not complete sentences or dialogue boxes; runtime reachability and story state are not evaluated.',
                    'This private response contains retail text; no source payload is added to the metadata-only Asset Database.'])


def project_text_state_key(project) -> str:
    from .project import digest
    return digest(dict(imports=project.imports, source_key=source_key(project),
                       dialogue={owner: deepcopy(parts['Dialogue']) for owner, parts in project.overrides.items()
                                 if 'Dialogue' in parts}))


def project_text_index(project) -> dict:
    """Search imported scenes using detached views, without switching the project."""
    from copy import copy
    if not project.disc_path or not 1 <= len(project.imports) <= 64:
        raise ProjectError('Project text discovery requires a disc and 1-64 imported scenes')
    key = project_text_state_key(project)
    view = copy(project)
    view.imports = deepcopy(project.imports)
    view.overrides = deepcopy(project.overrides)
    rows, scenes, restrictions = [], [], []
    total_bytes = 0
    coverage = dict(script_count=0, partial_script_count=0, unavailable_script_count=0)
    with _disc_context(project.disc_path):
        for scene_id, document in sorted(view.imports.items()):
            view.active_scene = scene_id
            try:
                result = scene_text_index(view)
            except RetailImportError as exc:
                scenes.append(dict(scene_id=scene_id, scene_name=document['scene']['name'],
                                   status='unavailable', reason=str(exc)))
                continue
            for row in result['runs']:
                total_bytes += row['capacity']
                if len(rows) >= 32768 or total_bytes > 4 * 1024 * 1024:
                    raise ProjectError('Project text exceeds the run/text budget')
                rows.append({**row, 'scene_id':scene_id, 'scene_name':document['scene']['name']})
            restrictions.extend({**item, 'scene_id':scene_id} for item in result['restrictions'])
            for field in coverage:
                coverage[field] += result['coverage'][field]
            scenes.append(dict(scene_id=scene_id, scene_name=document['scene']['name'], status='verified',
                               run_count=len(result['runs']), coverage=result['coverage']))
    if key != project_text_state_key(project):
        raise ProjectError('Project source or text changed during discovery; refresh again')
    return dict(schema='legaia.project-text.v1', read_only=True, project_path=str(project.root),
                project_text_state_key=key, runs=rows, coverage=coverage, scenes=scenes,
                restrictions=restrictions, limitations=[
                    'Only imported scenes and source-qualified editable plain-glyph runs are included.',
                    'Unknown/unvisited bytes, unsupported ordinary dialogue and controller records are excluded.',
                    'Partial scripts may offer menu labels; complete sentences, boxes and story reachability are not reconstructed.',
                    'This private text response does not add retail payload to the metadata-only Asset Database.'])


def scene_flag_index(project) -> dict:
    from importer.script_catalog import load_script_asset_catalog
    from .flags import build_flag_index
    document, key = _scene(project)
    flag_key = scene_flag_state_key(project)
    with _disc_context(project.disc_path):
        _verify(project, document)
        catalog = load_script_asset_catalog(project.disc_path, document["scene"]["name"])
        index = build_flag_index(catalog, _flag_edits(project, project.active_scene))
    if key != source_key(project) or flag_key != scene_flag_state_key(project):
        raise ProjectError("Scene source changed during flag discovery; refresh again")
    return {**index, "source_key": key, "flag_state_key": flag_key}


def project_flag_index(project) -> dict:
    """Inspect imported scenes without changing selection or inventing shared banks."""
    from importer.script_catalog import load_script_asset_catalog
    from .flags import build_flag_index
    if not project.disc_path or not project.imports or len(project.imports) > 64:
        raise ProjectError('Project flag discovery requires a disc and 1–64 imported scenes')
    key = project_flag_state_key(project)
    authored_snapshot = deepcopy(getattr(project, "overrides", {}))
    groups, scenes = [], []
    authored_count = 0
    coverage = dict(script_count=0,partial_script_count=0,unavailable_script_count=0)
    with _disc_context(project.disc_path):
        for scene_id, document in sorted(project.imports.items()):
            _verify(project,document)
            name = document['scene']['name']
            try:
                index = build_flag_index(load_script_asset_catalog(project.disc_path,name), _flag_edits(project,scene_id))
            except RetailImportError as exc:
                scenes.append(dict(scene_id=scene_id,scene_name=name,status='unavailable',reason=str(exc)))
                continue
            if index['scene_id'] != scene_id:
                raise ProjectError('Flag catalog identity differs from the imported scene')
            authored_count += index['authored_reference_count']
            for group in index['groups']:
                groups.append({**group,'scene_id':scene_id,'scene_name':name})
            if len(groups) > 32768 or sum(len(g['references']) for g in groups) > 262144:
                raise ProjectError('Project flag references exceed the bounded discovery budget')
            for field in coverage:
                coverage[field] += index['coverage'][field]
            scenes.append(dict(scene_id=scene_id,scene_name=name,status='verified',
                               reference_count=index['reference_count'],coverage=index['coverage']))
    if key != project_flag_state_key(project):
        raise ProjectError('Project sources or flag operands changed during flag discovery')
    if authored_snapshot != getattr(project, 'overrides', {}):
        raise ProjectError('Authored project state changed during flag discovery')
    return dict(schema_version='legaia.project-flag-references.v1',read_only=True,
                project_path=str(project.root),source_key=key,scene_ids=sorted(project.imports),
                groups=groups,scenes=scenes,coverage=coverage,authored_reference_count=authored_count,grouping_layer='retail',
                reference_count=sum(len(g['references']) for g in groups),
                limitations=['Encoded operands retain separate scene/script identities; matching bank/index does not prove one runtime variable.',
                             'Only imported scenes and decoded instructions are covered; unavailable and partial scripts retain their coverage limits.',
                             'Retail grouping with separately validated authored/effective operands; no current flag values, story names, runtime writes or path execution are inferred.'])


def scene_transition_graph(project) -> dict:
    from importer.script_catalog import load_script_asset_catalog
    from .transitions import build_transition_graph
    document, key = _scene(project)
    transition_key = scene_transition_state_key(project)
    with _disc_context(project.disc_path):
        _verify(project, document)
        catalog = load_script_asset_catalog(project.disc_path, document["scene"]["name"])
        authored = _transition_edits(project, project.active_scene)
    if key != source_key(project) or transition_key != scene_transition_state_key(project):
        raise ProjectError("Scene source changed during transition discovery; refresh again")
    return {**build_transition_graph(catalog, project.imports, authored), "source_key": key,
            "transition_state_key": transition_key}


def trigger_script_preview(project, asset_id: str) -> dict:
    from importer.trigger_scripts import inspect_trigger_script
    document, key = _scene(project)
    with _disc_context(project.disc_path):
        _verify(project, document)
        report = inspect_trigger_script(project.disc_path, document["scene"]["name"], asset_id)
    if key != source_key(project):
        raise ProjectError("Trigger script source changed during inspection; refresh again")
    return {**report, "scene_id": project.active_scene, "source_key": key}


def partition_two_script_preview(project, identifier: str) -> dict:
    from importer.dialogue_authoring import validate_run_id
    from importer.trigger_scripts import inspect_partition_two_script
    document, key = _scene(project)
    validate_run_id(identifier, "script://" + identifier.removeprefix("scene://") + "/dialogue/0000/run/0000")
    prefix = project.active_scene + "/scripts/man-p2/"
    if not identifier.startswith(prefix):
        raise ProjectError("Partition-two script must belong to the active imported scene")
    with _disc_context(project.disc_path):
        _verify(project, document)
        report = inspect_partition_two_script(project.disc_path, document["scene"]["name"], int(identifier[len(prefix):]))
    if key != source_key(project):
        raise ProjectError("Script source changed during inspection; refresh again")
    return {**report, "scene_id": project.active_scene, "source_key": key}


def field_map_preview(project, asset_id: str, layer: str = "imported") -> dict:
    from importer.field_map import preview_field_map
    if layer not in ("imported", "effective"):
        raise ProjectError("Choose imported or effective collision preview")
    document, key = _scene(project)
    region_key = scene_region_state_key(project)
    trigger_key = scene_trigger_state_key(project)
    with _disc_context(project.disc_path):
        _verify(project, document)
        preview = preview_field_map(project.disc_path, document["scene"]["name"], asset_id)
        from .field_spatial import build_field_spatial
        preview["spatial"] = build_field_spatial(preview)
        from .region_bounds import effective_annotations
        preview["region_bounds"] = effective_annotations(project, project.active_scene)
        from .trigger_cells import effective_annotations as trigger_annotations
        preview["trigger_cells"] = trigger_annotations(project, project.active_scene)
        preview["representation"] = layer
        if layer == "effective":
            from importer.collision_authoring import patch_collision_walls
            from importer.field_map import _rectangles
            binding = project.overrides.get(project.active_scene, {}).get("Collision")
            preview["authored"] = deepcopy(binding)
            if binding is not None:
                project._validate_collision(project.active_scene, binding)
                changed, audit = patch_collision_walls(project._environment_source(project.active_scene), binding["source_sha256"], binding["edits"])
                preview["rectangles"] = _rectangles(changed[0x4000:0x8000])
                preview["rectangle_count"] = len(preview["rectangles"])
                preview["authored_changes"] = audit
            preview["limitations"] = [*preview["limitations"], "Effective source wall edits only; runtime script paints and actor blockers remain unobserved."]
    if (key != source_key(project) or region_key != scene_region_state_key(project) or
            trigger_key != scene_trigger_state_key(project)):
        raise ProjectError("Field map source changed during preview; refresh again")
    return {**preview, "semantic_id": preview["asset"]["semantic_id"], "asset_kind": "collision",
            "scene_id": project.active_scene, "source_key": key, "region_state_key": region_key, "trigger_state_key": trigger_key}


def texture_preview(project, asset_id: str, palette_index: int, layer: str = "effective") -> dict:
    from importer.texture_catalog import preview_texture_asset
    from importer.textures import decode_tim
    if layer not in ("imported", "effective"):
        raise ProjectError("Choose imported or effective texture preview")
    document, key = _scene(project)
    if asset_id in project.texture_additions:
        if layer!='effective':raise ProjectError('New texture slots have no Imported Retail counterpart')
        if type(palette_index) is not int:raise ProjectError('Texture palette must be an existing integer index')
        from .texture_slots import current_items,metadata
        selected=next((row for row in current_items(project) if row[0]==asset_id),None)
        if selected is None:raise ProjectError('New texture is outside the active scene')
        identifier,binding,content=selected
        decoded=decode_tim(content,palette_index)
        if key!=source_key(project):raise ProjectError('New texture source changed during preview')
        return dict(metadata(identifier,binding,content),source_key=key,scene_id=project.active_scene,layer=layer,
            authored=deepcopy(binding),palette_index=palette_index,
            rgba_base64=base64.b64encode(decoded['rgba']).decode('ascii'),
            stp_base64=base64.b64encode(decoded['stp']).decode('ascii'))
    with _disc_context(project.disc_path):
        _verify(project, document)
        preview = preview_texture_asset(project.disc_path, document["scene"]["name"], asset_id, palette_index)
        authored = project.texture_overrides.get(asset_id)
        if authored is not None and layer == "effective":
            content = project.read_texture_replacement(authored)
            project.validate_effective_texture(asset_id,content)
            preview.update(decode_tim(content, palette_index))
    if key != source_key(project):
        raise ProjectError("Texture source changed during preview; refresh again")
    asset = preview["asset"]
    return {**asset, "source_key": key, "scene_id": project.active_scene, "layer": layer,
            "authored": authored,
            "width": preview["width"], "height": preview["height"], "palette_index": palette_index,
            "rgba_base64": base64.b64encode(preview["rgba"]).decode("ascii"),
            "stp_base64": base64.b64encode(preview["stp"]).decode("ascii"),
            "limitations": preview.get("limitations", asset.get("limitations", []))}


def texture_source(project, asset_id: str) -> dict:
    context = project._texture_context(asset_id)
    content = context.original_tim(asset_id)
    return {"tim_base64": base64.b64encode(content).decode("ascii"),
            "filename": "retail-" + asset_id.removeprefix("texture://").replace("/", "-") + ".tim"}


def apply_texture_overrides(project, catalog):
    """Return an effective private catalog; imported texture facts stay intact."""
    from copy import deepcopy
    from importer.texture_authoring import load_texture_authoring_context
    from importer.textures import parse_tim
    bindings = {identifier: binding for identifier, binding in project.texture_overrides.items()
                if binding["source_scene_id"] == "scene://" + catalog.scene}
    from .texture_slots import current_items,metadata
    added=current_items(project,'scene://'+catalog.scene)
    if not bindings and not added:
        return catalog
    context = load_texture_authoring_context(project.disc_path, catalog.scene)
    replacements = {}
    for identifier, binding in bindings.items():
        content = project.read_texture_replacement(binding)
        project.validate_effective_texture(identifier,content,context=context)
        replacements[identifier] = parse_tim(content)
    result = deepcopy(catalog)
    result.textures = [(replacements.get(source["semantic_id"], tim), source)
                       for tim, source in result.textures]
    for identifier,binding,content in added:
        result.textures.append((parse_tim(content),metadata(identifier,binding,content)['source_record']))
    result.diagnostics.append(f'Current preview includes {len(added)} authored TIM uploads; overlapping addresses retain static ambiguity.')
    result.diagnostics.append(f"Effective preview applies {len(replacements)} project-authored TIM replacements; source locators remain retail provenance.")
    return result


def project_transition_state_key(project):
    from .project import digest
    return digest({'root':str(project.root),'disc':project.disc_path,
                   'imports':project.imports,'overrides':project.overrides})


def project_transition_graph(project):
    """Source-qualified decoded references across imported scenes; no route inference."""
    from importer.script_catalog import load_script_asset_catalog
    from .transitions import build_transition_graph
    if not project.disc_path or not 1<=len(project.imports)<=64:
        raise ProjectError('Project transition discovery requires a disc and1–64 imported scenes')
    key=project_transition_state_key(project)
    documents=deepcopy(project.imports)
    nodes={};edges=[];scenes=[]
    coverage=dict(script_count=0,partial_script_count=0,unavailable_script_count=0)
    with _disc_context(project.disc_path):
        for scene_id,document in sorted(documents.items()):
            _verify(project,document)
            name=document['scene']['name']
            nodes.setdefault(scene_id,dict(id=scene_id,name=name,imported=True,roles=[],in_scene_index=True))
            try:
                catalog=load_script_asset_catalog(project.disc_path,name)
                graph=build_transition_graph(catalog,documents,_transition_edits(project,scene_id))
            except RetailImportError as exc:
                scenes.append(dict(scene_id=scene_id,scene_name=name,status='unavailable',reason=str(exc)))
                continue
            if graph['scene_id']!=scene_id:raise ProjectError('Transition catalog differs from imported scene identity')
            for node in graph['nodes']:
                merged=nodes.setdefault(node['id'],deepcopy(node))
                for role in node['roles']:
                    if role not in merged['roles']:merged['roles'].append(role)
            edges.extend(graph['edges'])
            if len(edges)>16384 or len(nodes)>16448:
                raise ProjectError('Project transition graph exceeds discovery bounds')
            for field in coverage:coverage[field]+=graph['coverage'][field]
            scenes.append(dict(scene_id=scene_id,scene_name=name,status='verified',reference_count=len(graph['edges']),coverage=graph['coverage']))
    if key!=project_transition_state_key(project):
        raise ProjectError('Project sources or authored state changed during transition discovery')
    if len({edge['id'] for edge in edges})!=len(edges):raise ProjectError('Transition source identities are ambiguous')
    return dict(schema_version='legaia.project-transitions.v1',read_only=True,
                project_path=str(project.root),source_key=key,scene_ids=sorted(documents),
                nodes=[nodes[id] for id in sorted(nodes)],edges=edges,scenes=scenes,coverage=coverage,
                limitations=['Edges are decoded source instructions, not verified routes or runtime scene connections.',
                             'Only imported scenes and supported script paths are covered; partial and unavailable sources remain explicit.',
                             'Imported, authored and effective entry operands remain separate; no story-state evaluation or path finding.'])


def audio_sequence_preview(project, asset_id, expected_source_key, expected_entry_sha256):
    from importer.audio_catalog import read_audio_sequence
    from importer.audio_sequence import inspect_sequence
    document,key=_scene(project)
    if expected_source_key!=key:raise ProjectError('Audio inspection source changed; refresh resources')
    with _disc_context(project.disc_path):
        _verify(project,document)
        sequence,source=read_audio_sequence(project.disc_path,asset_id,expected_entry_sha256)
        report=inspect_sequence(sequence)
    if key!=source_key(project):raise ProjectError('Audio source changed during inspection')
    return dict(schema_version='legaia.audio-sequence-inspection.v1',asset_id=asset_id,
                scene_id=project.active_scene,source_key=key,source_record=source,
                read_only=True,project_changed=False,runtime_state='not_observed',**report)


def audio_bank_preview(project, asset_id, expected_source_key, expected_entry_sha256):
    from importer.audio_bank import read_audio_bank
    document,key=_scene(project)
    if expected_source_key!=key:raise ProjectError('Audio bank source changed; refresh resources')
    with _disc_context(project.disc_path):
        _verify(project,document)
        report=read_audio_bank(project.disc_path,asset_id,expected_entry_sha256)
    if key!=source_key(project):raise ProjectError('Audio bank source changed during inspection')
    return dict(schema_version='legaia.audio-bank-inspection.v1',asset_id=asset_id,scene_id=project.active_scene,
                source_key=key,read_only=True,project_changed=False,runtime_state='not_observed',**report)
