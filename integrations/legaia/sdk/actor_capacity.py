"""Shared retail actor-pool assessment for normal and growth candidates."""
from importer.actor_runtime_capacity import qualify_actor_pool, assess_initial_placement_capacity
from importer.man_layout import read_man_layout


def actor_pool_assessment(archive, candidate):
    executable = archive.image.read_file(archive.image.find('SCUS_942.54'))
    return assess_initial_placement_capacity(qualify_actor_pool(executable),
                                             read_man_layout(candidate)['partition_counts'])
