'''
Created on 01/10/2013

@author: Ismail Faizi
'''

from common import AuthorizedPage
from models import HReference, HREFERENCE_KEY

class HReferencesPage(AuthorizedPage):
    ACTION_ADD = 'add'
    
    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'hreferences.html', request, response)
    
    def getReferences(self, count=10):
        # get all the references in the datastore
        q = HReference.query(ancestor=HREFERENCE_KEY)
        return q.order(HReference.ID).fetch(count)
    
    def handleGetRequest(self):
        self.addTemplateValue('reference', None)
        self.addTemplateValue('references', self.getReferences())
        self.setActivePage('HReferences')
        
    def handlePostRequest(self):
        action = self.request.get('action', '')
        
        if action == self.ACTION_ADD:
            reference = {}
            reference['ID'] = self.request.get('id', None)
            reference['name'] = self.request.get('name', '')
            reference['source'] = self.request.get('source', None)
            add = True
            
            if not reference.get('ID'):
                self.addMessage('The required field, <b>ID</b>, is missing value!')
                self.addTemplateValue('reference', reference)
                add = False
            
            if not reference.get('source'):
                self.addMessage('The required field, <b>Source</b>, is missing value!')
                self.addTemplateValue('reference', reference)
                add = False
                
            if HReference.exists(reference.get('ID')):
                self.addMessage('A reference with ID=%s already exists!' %reference.get('ID'), self.MSG_TYPE_ERROR)
                self.addTemplateValue('reference', reference)
                add = False
                
            if add:
                ref = HReference(parent=HREFERENCE_KEY,
                                 ID=reference.get('ID'),
                                 name=reference.get('name'),
                                 source=reference.get('source'))
                ref.put()
                self.addMessage('Reference added successfully.', self.MSG_TYPE_SUCCESS)
        
        self.addTemplateValue('references', self.getReferences())
        self.setActivePage('HReferences')    
        
    