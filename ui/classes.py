'''
Created on 01/10/2013

@author: Ismail Faizi
'''

from common import AuthorizedPage
from models import Class, CLASS_KEY, CLASS_CATEGORY_KEY
from models import ClassCategory

class ClassesPage(AuthorizedPage):
    
    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'classes.html', request, response)
    
    def handleGetRequest(self):
        # get the recent 10 classes added to datastore
        q = Class.query(ancestor=CLASS_KEY)
        classes = q.order(-Class.created).fetch(20)
        
        # get the recent 10 class-categories added to datastore
        q = ClassCategory.query(ancestor=CLASS_CATEGORY_KEY)
        categories = q.order(-ClassCategory.created).fetch(20)
        
        self.addTemplateValue('classes', classes)
        self.addTemplateValue('categories', categories)
        
        self.setActivePage('Classes')
            
        
    