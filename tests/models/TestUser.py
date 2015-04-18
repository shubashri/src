'''
Created on 12/10/2014

@author: Ismail Faizi
'''
import unittest
from models import User, UserSettingKey, UserSetting, UserEmail
from google.appengine.ext import testbed


class Test(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.user_a = User()
        self.user_a.put()

        self.user_b = User()
        self.user_b.name = 'Foo Bar'
        self.user_b.clientID = 'C123'
        self.user_b.put()

        self.setting = UserSettingKey()
        self.setting.name = 'SEND_EMAIL'
        self.setting.description = 'Acceptance to receiv E-mail'
        self.setting.values = ['0', '1']
        self.setting.put()

        self.user_setting = UserSetting()
        self.user_setting.setting_key = self.setting.key
        self.user_setting.user = self.user_b.key
        self.user_setting.value = '0'
        self.user_setting.put()

        self.email_a = UserEmail()
        self.email_a.email = 'foo@bar.com'
        self.email_a.is_activated = False
        self.email_a.is_default = False
        self.email_a.user = self.user_b.key
        self.email_a.put()

        self.email_b = UserEmail()
        self.email_b.email = 'foobar@gmail.com'
        self.email_b.is_activated = True
        self.email_b.is_default = True
        self.email_b.user = self.user_b.key
        self.email_b.put()


    def tearDown(self):
        self.testbed.deactivate()

    def testGetSettings(self):
        self.assertEqual(0, len(self.user_a.get_settings()))

        settings = self.user_b.get_settings()
        self.assertEqual(1, len(settings))

        self.assertEqual('SEND_EMAIL', settings[0].setting_key.get().name)

    def testUpdateSettings(self):
        self.user_a.update_setting(self.setting, '1')
        self.assertEqual('0', self.user_setting.value)

        self.user_b.update_setting(self.setting, '1')
        self.assertEqual('1', self.user_setting.value)

    def testUpdate(self):
        self.user_a.upate('bar@gmail.com', 'Bar Foy')
        self.assertEqual('Bar Foy', self.user_a.name)
        self.assertTrue(self.user_a.has_email())
        self.assertEqual(self.user_a, UserEmail.find_user('bar@gmail.com'))

        self.user_b.upate('foo@awareaps.com', 'Foo Bar')
        self.assertEqual('Foo Bar', self.user_b.name)
        self.assertEqual('foobar@gmail.com', self.user_b.get_default_email())
        self.assertEqual(self.user_b, UserEmail.find_user('foo@awareaps.com'))

    def testHasEmail(self):
        self.assertFalse(self.user_a.has_email())
        self.assertTrue(self.user_b.has_email())

    def testDefaultEmailConsistancy(self):
        self.assertEqual(None, self.user_a.get_default_email())
        self.assertEqual('foobar@gmail.com', self.user_b.get_default_email())

        UserEmail.create_or_update(self.user_a, 'bar@gmail.com', True)
        UserEmail.create_or_update(self.user_b, 'foo@awareaps.com', True)

        user_a_emails = UserEmail.gql("WHERE user = :1", self.user_a.key).fetch()
        user_b_emails = UserEmail.gql("WHERE user = :1", self.user_b.key).fetch()

        self.assertEqual(1, len(user_a_emails))
        self.assertTrue(user_a_emails[0].is_default)

        self.assertEqual(3, len(user_b_emails))
        for email in user_b_emails:
            if 'foo@awareaps.com' == email.email:
                self.assertTrue(email.is_default)
            else:
                self.assertFalse(email.is_default)

    def testFindByEmail(self):
        user = User.find_by_email('foobar@gmail.com')
        self.assertEqual(self.user_b, user)

        user = User.find_by_email('foo@bar.com')
        self.assertEqual(self.user_b, user)

        user = User.find_by_email('none@unknown.com')
        self.assertEqual(None, user)

    def testClinet(self):
        self.assertEqual(self.user_b, User.client('C123'))

        user = User.client('C001')
        self.assertNotEqual(None, user)
        self.assertEqual('C001', user.clientID)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
