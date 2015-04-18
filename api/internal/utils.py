'''
Created on 29/05/2014

@author: Ismail Faizi
'''
from protorpc import messages, remote, message_types
from api.common import aWareInternalAPI
import endpoints
from models import User
from models.utils import ContactRequest

'''
### MESSAGES ###
'''

class ContactRequestMessage(messages.Message):
    userKey = messages.StringField(1, required=True)
    email = messages.StringField(2, required=True)
    subject = messages.StringField(3)
    message = messages.StringField(4, required=True)
    
'''
### END of MESSAGES ###
'''
@aWareInternalAPI.api_class(resource_name='utils', 
                            path='utils')
class Utilities(remote.Service):
    '''
    The API for achieving utility tasks such as contact request
    '''
    
    @endpoints.method(ContactRequestMessage, 
                      message_types.VoidMessage, 
                      name='contact', 
                      path='contact', 
                      http_method='GET')
                      
    def contact(self, request):
        '''
        Add a contact request
        '''
        user = User.get_by_urlsafe_key(request.userKey)
        if not user:
            message = 'No user with the key "%s" exists.' % request.userKey
            raise endpoints.NotFoundException(message) 
                
        ContactRequest.create(email=request.email, 
                              subject=request.subject, 
                              message=request.message, 
                              owner=user)
        
        return message_types.VoidMessage()
    
