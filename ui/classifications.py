'''
Created on 01/10/2013

@author: Ismail Faizi
'''

from common import AuthorizedPage
from models import Classification, CLASSIFICATION_KEY

class ClassificationsPage(AuthorizedPage):
    
    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'classifications.html', request, response)
    
    def handleGetRequest(self):
        # get the recent 10 classifications added to datastore
        q = Classification.query(ancestor=CLASSIFICATION_KEY)
        classifications = q.order(-Classification.created).fetch(20)
        
        self.addTemplateValue('classifications', classifications)
        
        self.setActivePage('Classifications')    
            
        
    