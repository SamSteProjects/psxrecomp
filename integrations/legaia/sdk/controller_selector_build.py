"""Compose source-qualified controller selector, branch, tile, fade, table-copy, word-triplet and three-word Build receipts."""
from hashlib import sha256
from .controller_system_flags import COMPONENT,validate_components,scene_document
from .system_flags import merge_patch
from importer.controller_system_flags import load_controller_system_flag_context


def collect(project,owner,components):
    value=validate_components(project,owner,components)
    return scene_document(project,owner)['scene']['semantic_id'],value


def compose(project,scene_id,baseline,working,previous=(),*,appended=False):
    from .build import BuildError
    owner=scene_id+'/controllers/man-p1/0000'
    components=validate_components(project,owner,project.overrides[owner])
    value=components.get(COMPONENT,dict(entries={}))
    scene=project.imports[scene_id]['scene']['name']
    context=load_controller_system_flag_context(project.disc_path,scene)
    if context._man!=baseline:raise BuildError('Controller Build MAN differs from verified Retail source')
    source_offset,record,entry=context._source.verified_record(owner)
    if any(sha256(record).hexdigest()!=v['source_record_sha256'] for v in components.values()):raise BuildError('Controller Build record hash changed')
    options={t['semantic_id']:t for t in context.options(owner)['targets']}
    expected={}
    for identity,fields in value['entries'].items():
        if identity not in options:raise BuildError('Controller Build selector is not qualified by its source')
        expected[identity]=dict(options[identity],requested_values=fields)
    if appended:
        from importer.scene_controller import controller_record
        from copy import deepcopy
        offset,current_record,current_entry=controller_record(working,scene)
        from importer.man_layout import read_man_layout
        from importer.script_reindex import reindex_spawn_operands
        old=read_man_layout(baseline)['partition_counts'];new=read_man_layout(working)['partition_counts']
        count=sum(d.get('scene_id')==scene_id for d in project.actor_drafts.values())
        if old[0]!=new[0] or old[2]!=new[2] or new[1]-old[1]!=count:
            raise BuildError('Relocated controller partition growth differs from saved NPC candidates')
        mapping={sum(old[:2])+i:sum(new[:2])+i for i in range(old[2])}
        structural,structural_proof=reindex_spawn_operands(record,sha256(record).hexdigest(),entry,mapping)
        if current_record!=structural or current_entry!=entry:
            raise BuildError('Relocated controller source record changed before selector composition')
        for target in expected.values():target['decoded_byte_offset']+=offset-source_offset
        patched,changes=context.patch_appended(working,value['entries'])
        for receipt in changes:
            original=options.get(receipt.get('system_flag_id'))
            if original is None or receipt.get('source_decoded_man_sha256')!=sha256(baseline).hexdigest() or receipt.get('appended_man_sha256')!=sha256(working).hexdigest() or receipt.get('source_decoded_byte_offset')!=original['decoded_byte_offset']:
                raise BuildError('Relocated controller selector receipt lost its Retail preimage proof')
        validation=deepcopy(changes)
        for receipt in validation:receipt['source_decoded_man_sha256']=sha256(working).hexdigest()
        result=merge_patch(working,working,patched,validation,expected,previous)
        for change in changes:change.update(pre_selector_controller_sha256=sha256(structural).hexdigest(),controller_spawn_reindex=structural_proof['changes'])
    else:
        if working[source_offset:source_offset+len(record)]!=record:raise BuildError('Controller source record changed before Build composition')
        patched,changes=context.patch(value['entries'],original=baseline)
        result=merge_patch(baseline,working,patched,changes,expected,previous)
    for change in changes:
        change.update(semantic_id=owner,record_index=0,owner_kind='scene_controller',scope='script-system-selector-only')
    if 'ControllerBranches' in components:
        from .controller_branch_build import compose_branches
        result,branch_changes=compose_branches(context,owner,components,result,[*previous,*changes],appended=appended)
        changes.extend(branch_changes)
    if 'ControllerTileRects' in components:
        from .controller_tile_build import compose_tiles
        result,tile_changes=compose_tiles(context,owner,components,result,[*previous,*changes],appended=appended)
        changes.extend(tile_changes)
    if 'ControllerFades' in components:
        from .controller_fade_build import compose_fades
        result,fade_changes=compose_fades(context,owner,components,result,[*previous,*changes],appended=appended)
        changes.extend(fade_changes)
    if 'ControllerTableCopies' in components:
        from .controller_table_build import compose_tables
        result,table_changes=compose_tables(context,owner,components,result,[*previous,*changes],appended=appended)
        changes.extend(table_changes)
    if 'ControllerWordTriplets' in components:
        from .controller_word_triplet_build import compose_word_triplets
        result,triplet_changes=compose_word_triplets(context,owner,components,result,[*previous,*changes],appended=appended)
        changes.extend(triplet_changes)
    if 'ControllerThreeWords' in components:
        from .controller_three_word_build import compose_three_words
        result,three_word_changes=compose_three_words(context,owner,components,result,[*previous,*changes],appended=appended)
        changes.extend(three_word_changes)
    if 'ControllerSceneBytes' in components:
        from .controller_scene_byte_build import compose_scene_bytes
        result,scene_byte_changes=compose_scene_bytes(context,owner,components,result,[*previous,*changes],appended=appended)
        changes.extend(scene_byte_changes)
    return result,changes
