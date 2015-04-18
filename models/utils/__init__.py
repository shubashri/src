'''
Created on 29/05/2014

@author: Ismail Faizi
'''
from google.appengine.ext import ndb
from models import User, APPLICATION_ID

CONTACT_REQUEST_KEY  = ndb.Key("ContactRequest", 'root', app = APPLICATION_ID)
AWARE_PARAMETERS_KEY = ndb.Key("aWareParameters", 'root', app = APPLICATION_ID)

class ContactRequest(ndb.Model):
    email = ndb.StringProperty()
    subject = ndb.StringProperty()
    message = ndb.TextProperty()
    owner = ndb.KeyProperty(kind=User)
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)
    
    @classmethod
    def create(cls, email, subject, message, owner):
        if not email or email == '':
            raise ValueError("Email must be specified!")
        
        if not message or message == '':
            raise ValueError("Message must be specified!")
        
        cr = ContactRequest(parent=CONTACT_REQUEST_KEY)
        cr.email = email
        cr.subject = subject
        cr.message = message
        cr.owner = owner.key
        cr.put()
        
        return cr
    
class AwareParameters(ndb.Model):
    '''
    A singleton class that contains the parameters of aWare
    
    Always get the instance through the get_instance() method
    '''
    tou_updated = ndb.DateTimeProperty()
    
    def update_tou(self, date_time):
        self.tou_updated = date_time
        self.put()
        
    def is_tou_updated_since(self, date_time):
        if not date_time or not self.tou_updated:
            return False
        
        return self.tou_updated >= date_time
    
    @classmethod
    def get_instance(cls):
        item = cls.query(ancestor=AWARE_PARAMETERS_KEY).get()
        
        if not item:
            item = AwareParameters(parent=AWARE_PARAMETERS_KEY)
            item.put()
        
        return item