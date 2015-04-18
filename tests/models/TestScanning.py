'''
Created on 02/10/2014

@author: Ismail Faizi
'''
import unittest
from google.appengine.ext import testbed
from models import User, Scanning


class Test(unittest.TestCase):


    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.user_a = User()
        self.user_a.put()

        self.user_b = User()
        self.user_b.put()

        self.scan_a = Scanning()
        self.scan_a.barcode = '12345'
        self.scan_a.user = self.user_a.key
        self.scan_a.put()

        self.scan_b = Scanning()
        self.scan_b.barcode = '12345'
        self.scan_b.user = self.user_a.key
        self.scan_b.put()

        self.scan_c = Scanning()
        self.scan_c.barcode = '67890'
        self.scan_c.user = self.user_a.key
        self.scan_c.put()

    def tearDown(self):
        self.testbed.deactivate()

    def testDoDelete(self):
        self.assertFalse(self.scan_a.deleted)

        self.scan_a.do_delete()
        self.assertTrue(self.scan_a.deleted)

    def testFind(self):
        result = Scanning.find(self.user_a, '12345')

        self.assertEqual(2, len(result))

        for scanning in result:
            self.assertEqual(scanning.barcode, '12345')

        result = Scanning.find(self.user_b, '67890')

        self.assertEqual(0, len(result))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
