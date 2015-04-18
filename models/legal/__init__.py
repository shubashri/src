'''
Created on 24/04/2014

@author: Ismail Faizi
'''
from google.appengine.ext import ndb
from models import User, APPLICATION_ID

LEGAL_DOCUMENT_KEY = ndb.Key("LegalDocument", 'root', app = APPLICATION_ID)

class LegalDocument(ndb.Model):
    title = ndb.StringProperty()
    body = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)
    creator = ndb.KeyProperty(kind=User)
    modifiers = ndb.KeyProperty(kind=User, repeated=True)
    
    @classmethod
    def get_tou(cls):
        q = cls.gql("WHERE title = 'Term of Use'")
        doc = q.fetch()
        if len(doc):
            return doc[0].body

        return ''
