'''
Created on 13/05/2014

@author: Ismail Faizi
'''
import endpoints  # @UnusedImport
from protorpc import messages, remote
from api.common import aWareInternalAPI
from models.legal import LegalDocument

'''
### MESSAGES ###
'''
class TOURequest(messages.Message):
    lang = messages.StringField(1)    

class TOUResponse(messages.Message):
    result = messages.StringField(1)
    
'''
### END of MESSAGES ###
'''

@aWareInternalAPI.api_class(resource_name='documents', 
                            path='documents')
class Documents(remote.Service):
    '''
    The API for retrieving aWare app documents, e.g. Term of Use, Privacy Policy etc. 
    '''
    @endpoints.method(TOURequest, 
                  TOUResponse,
                  http_method='GET',
                  path='tou',
                  name='tou')
    def tou(self, request):
        '''
        Provides the Term of Use (TOU) document of aWare app
        '''
        # request.lang contains the language code
        # in the moment we only use English
        return TOUResponse(result=LegalDocument.get_tou())