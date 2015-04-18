'''
Created on 01/10/2013

@author: Ismail Faizi
'''

from common import AuthorizedPage
from google.appengine.ext import ndb
from models import HelpTopic, HELP_TOPIC_KEY

class HelpsPage(AuthorizedPage):
    
    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'helps.html', request, response)
    
    def handleGetRequest(self):
        self.addCommon()
        self.setActivePage('Helps')
        
    def handlePostRequest(self):    
        key = self.request.get('key', None)
        title = self.request.get('title', None)
        description = self.request.get('description', None)
        
        if key:
            # Save an existing topic
            topic_key = ndb.Key(urlsafe=key)
            topic = topic_key.get()
            topic.name = title
            topic.description = description
            topic.put()
            self.addMessage('The topic was successfully saved.', self.MSG_TYPE_SUCCESS)
        else:
            # Add new one
            if not title or not description:
                self.addMessage('You must specify both title and description of topic.', self.MSG_TYPE_ERROR)
            else:
                topic = HelpTopic(parent=HELP_TOPIC_KEY,
                               title=title,
                               description=description)
                topic.put()
                self.addMessage('The topic was created successfully.', self.MSG_TYPE_SUCCESS)
        
        self.addCommon()
        self.setActivePage('Helps')
            
    def addCommon(self):
        # get all the Help Topics added to datastore
        q = HelpTopic.query(ancestor=HELP_TOPIC_KEY)
        helps = q.order(-HelpTopic.created).fetch()
        
        self.addTemplateValue('helps', helps)
        