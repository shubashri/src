'''
Created on 28/04/2014

@author: Ismail Faizi
'''
from google.appengine.ext import ndb

class Permission():
    View = 1
    Add = 2
    Edit = 3
    Delete = 4

    @classmethod
    def listOfNumbers(cls):
        return [1, 2, 3, 4]

class Role(ndb.Model):
    name = ndb.StringProperty()
    permissions = ndb.IntegerProperty(choices=Permission.listOfNumbers(),
                                      repeated=True)

    def is_super_user(self):
        return self.name == Role.get_super_user_role().name

    def is_admin(self):
        return self.name == Role.get_admin_role().name

    @classmethod
    def get_super_user_role(cls):
        su = 'super'
        r = cls.gql("WHERE name = :!", su).get()

        if not r:
            r = Role()
            r.name = su
            r.permissions = Permission.listOfNumbers()
            r.put()

        return r

    @classmethod
    def get_admin_role(cls):
        admin = 'admin'
        r = cls.gql("WHERE name = :1", admin).get()

        if not r:
            r = Role()
            r.name = admin
            r.permissions = [Permission.Add, Permission.View, Permission.Edit]
            r.put()

        return r
