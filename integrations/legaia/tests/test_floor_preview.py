import unittest,tempfile
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
from unittest.mock import patch
from sdk.project import ProjectService
from sdk.scene_preview import environment_effective_transforms
from sdk.terrain_preview import terrain_preview
from importer.terrain import decode_terrain
from test_floor_authoring import floor_fixture
class FloorPreview(unittest.TestCase):
 def test_current_ground_and_placement_compose_without_mutating_retail(self):
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.import_metadata(floor_fixture());data=bytearray(0x12000);data[0x8000:0x8002]=(0x1000).to_bytes(2,'little');source=bytes(data);h=sha256(source).hexdigest();lut=[0,64]+[0]*14
   metadata=dict(source_record=dict(map_sha256=h),floor_height_lut=lut,placements=[dict(semantic_id='environment://fixture/field-map/cells/00000',object_record_index=0,tile=dict(x=0,z=0),floor=dict(tier=0,lut_value=0,record_y_offset=4),source_record=dict(grid_byte_offset=0x8000),imported_transform=dict(position=dict(x=64,y=4,z=64),rotation_psx=dict(x=0,y=0,z=0)))])
   ground=decode_terrain(source,lut);ground['source_record']=deepcopy(metadata['source_record']);before=deepcopy(ground)
   p.overrides[p.active_scene]={'FloorTiers':dict(source_sha256=h,edits=[dict(row=0,column=0,tier=1)])}
   with patch.object(ProjectService,'_environment_source',return_value=source),patch('importer.environment.load_environment_placements',return_value=metadata):
    actual=terrain_preview(p,prepared=ground,catalog={});self.assertEqual(actual['vertices'][0],[0,-64,0]);self.assertEqual(actual['vertices'][1:],ground['vertices'][1:]);self.assertEqual(actual['triangles'],ground['triangles']);self.assertEqual(ground,before)
    projected=environment_effective_transforms(p,metadata);self.assertEqual(projected[metadata['placements'][0]['semantic_id']]['position']['y'],-60)
    p.overrides[p.active_scene]['Environment']={'source_sha256':h,'edits':[]}
    change=dict(record_index=0,field='offset.y',before_value=4,after_value=12)
    with patch.object(ProjectService,'_validate_environment'),patch('importer.environment_authoring.patch_environment_overrides',return_value=(source,[change])):
     projected=environment_effective_transforms(p,metadata);self.assertEqual(projected[metadata['placements'][0]['semantic_id']]['position']['y'],-52)
   self.assertEqual(metadata['placements'][0]['imported_transform']['position']['y'],4)
