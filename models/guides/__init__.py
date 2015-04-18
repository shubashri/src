'''
Created on 22/07/2014

@author: Ismail Faizi
'''
from google.appengine.ext import ndb
from models import AbstractModel, APPLICATION_ID
from google.appengine.api import images, blobstore

APP_GUIDE_KEY = ndb.Key('AppGuide', 'root', app = APPLICATION_ID)

class AppGuide(AbstractModel):
    image = ndb.StringProperty()
    text = ndb.StringProperty()
    creator = ndb.KeyProperty(kind='User')
    editor = ndb.KeyProperty(kind='User')
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)
    
    def get_serving_url_for_image(self):
        return images.get_serving_url(self.image)
        
    def update(self, editor, text, image=None):
        if not editor or not editor.key:
            raise ValueError('No valid user as editor is provided.')
        
        self.editor = editor.key
        self.text = text
        if image:
            self.delete_image()
            self.image = image
        self.put()
        
        return self
    
    def delete_image(self):
        blobstore.delete(self.image)
    
    @classmethod
    def create(cls, user, image, text):
        if not user or not user.key:
            raise ValueError('No valid user is provided.')
        
        if not image or len(image) == 0:
            raise ValueError('No image is provided.')
        
        if not text or len(text) == 0:
            raise ValueError('No text is provided.')
        
        app_guide = AppGuide(parent=APP_GUIDE_KEY)
        app_guide.image = image
        app_guide.text = text
        app_guide.creator = user.key
        app_guide.editor = user.key
        app_guide.put()
        
        return app_guide
    
    @classmethod
    def is_updated_since(cls, date_time):
        if not date_time:
            return False
        
        item = cls.query(ancestor=APP_GUIDE_KEY).order(-cls.modified).get()
        if item and item.modified and item.modified >= date_time:
            return True
        return False
    
    @classmethod
    def get_all(cls):
        q = cls.query(ancestor=APP_GUIDE_KEY)
        return q.order(-cls.created).fetch()

