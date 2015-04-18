'''
Created on 31/05/2014

@author: Ismail Faizi
'''
import unittest
from models.i18n import LengthUnit, UnitConversionFactor, MassUnit
from helpers.engines import UnitConversionEngine
from google.appengine.ext import testbed


class Test(unittest.TestCase):


    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        # create the meter unit
        self.a_unit = LengthUnit()
        self.a_unit.title = 'meter'
        self.a_unit.denotation = 'm'
        self.a_unit.put()
        
        # create the centimeter unit
        self.b_unit = LengthUnit()
        self.b_unit.title = 'centimeter'
        self.b_unit.denotation = 'cm'
        self.b_unit.put()
        
        # create the gram unit
        self.c_unit = MassUnit()
        self.c_unit.title = 'gram'
        self.c_unit.denotation = 'g'
        self.c_unit.put()

        # add entry for the conversion factor between m and cm, i.e 1 m = 100 cm
        self.cf_a_b = UnitConversionFactor()
        self.cf_a_b.aUnit = self.a_unit.key
        self.cf_a_b.aUnitQuantity = 1.0
        self.cf_a_b.bUnit = self.b_unit.key
        self.cf_a_b.bUnitQuantity = 100.0
        self.cf_a_b.put()
        
    def tearDown(self):
        self.testbed.deactivate()

    def testConvert(self):
        # convert 10 meters to centimeters = 1000.0 cm
        result = UnitConversionEngine.convert(self.a_unit, self.b_unit, 10.0)
        self.assertEqual(result, 1000.0)
        
        # convert 10 centimeters to meters = 0.1 m
        result = UnitConversionEngine.convert(self.b_unit, self.a_unit, 10.0)
        self.assertEqual(result, 0.1)
        
        # raise ValueError on incompatible dimensions
        self.assertRaises(ValueError, UnitConversionEngine.convert, self.a_unit, self.c_unit, 10.0)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testConvert']
    unittest.main()