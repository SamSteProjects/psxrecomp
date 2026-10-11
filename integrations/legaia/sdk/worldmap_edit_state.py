"""Project-authored World bindings for independent editor scene admission."""
from copy import deepcopy

SCENES = ('map01', 'map02', 'map03')
SCENE_COMPONENTS = ('Environment', 'Collision', 'FloorTiers', 'FloorHeights',
                    'RegionBounds', 'TriggerCells', 'TriggerScripts')
WORLD_OWNERS = ('placements', 'placement-allocations', 'scripted-placement-allocations',
                'script-operands', 'script-branches', 'animation-channels')


def snapshot(project):
    """Copy known World scopes, retaining complete dedicated-owner components.

    Unknown dedicated components must reach the qualifiers so they can refuse;
    unrelated scene components and other project owners are not exposed here.
    This is metadata only and does not read or qualify native source bytes.
    """
    result = {}
    for scene in SCENES:
        scene_owner = 'scene://' + scene
        components = project.overrides.get(scene_owner, {})
        selected = {name: deepcopy(value) for name, value in components.items()
                    if name in SCENE_COMPONENTS}
        if selected:
            result[scene_owner] = selected
        for suffix in WORLD_OWNERS:
            owner = f'worldmap://{scene}/{suffix}'
            if owner in project.overrides:
                result[owner] = deepcopy(project.overrides[owner])
    return result
