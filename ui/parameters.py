'''
Created on 30/07/2014

@author: Ismail Faizi
'''

from common import AuthorizedPage
from models.utils import AwareParameters
import datetime

class ParametersPage(AuthorizedPage):
    
    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'parameters.html', request, response)
    
    def handleGetRequest(self):
        self.addCommon()
        self.setActivePage('Parameters')
        
    def handlePostRequest(self):
        tou = self.request.get('tou', None)
        
        if tou:
            # Save terms update
            date_time = None
            try:
                date_time = datetime.datetime.strptime(tou, '%d/%m/%Y')
            except ValueError:
                self.addMessage('The specified date is not valid.', self.MSG_TYPE_ERROR)
            
            if date_time:
                params = AwareParameters.get_instance()
                params.update_tou(date_time)
                
                self.addMessage('The update date of Terms of Use was updated successfully.', self.MSG_TYPE_SUCCESS)
        
        self.addCommon()
        self.setActivePage('parameters')
            
    def addCommon(self):
        # get the parameters
        params = AwareParameters.get_instance()
        
        self.addTemplateValue('parameters', params)
        