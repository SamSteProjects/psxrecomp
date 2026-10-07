import unittest
from sdk.placement_angle import rotate_position,Q,sine
from sdk.project import ProjectError
class PlacementAngle(unittest.TestCase):
 def test_cardinal_diagonal_grid_and_sign(self):
  pivot={'x':512,'z':512};point={'x':640,'z':512}
  self.assertEqual(rotate_position(point,pivot,1,45),{'x':603,'z':603})
  self.assertEqual(rotate_position(point,pivot,64,45),{'x':576,'z':576})
  self.assertEqual(rotate_position(point,pivot,1,-45),{'x':603,'z':421})
  self.assertEqual(rotate_position(point,pivot,1,90),{'x':512,'z':640})
  self.assertEqual(rotate_position(point,pivot,64,0),point)
  self.assertEqual(rotate_position({'x':-32,'z':32},{'x':0,'z':0},64,0),{'x':-64,'z':64})
  for degree in range(-359,360):
   self.assertEqual(sine(degree),-sine(-degree));self.assertEqual(sine(degree),sine(degree+360));self.assertLessEqual(abs(sine(degree)),Q)
   self.assertEqual(rotate_position(pivot,pivot,1,degree),pivot)
 def test_invalid_input_is_atomic(self):
  point={'x':128,'z':256};pivot={'x':64,'z':64}
  for degree in [True,1.5,'45',-360,360,None]:
   with self.assertRaises(ProjectError):rotate_position(point,pivot,1,degree)
  for step in [True,0,32]:
   with self.assertRaises(ProjectError):rotate_position(point,pivot,step,45)
  with self.assertRaises(ProjectError):rotate_position({'x':1048577,'z':0},pivot,1,45)
  self.assertEqual(point,{'x':128,'z':256})
