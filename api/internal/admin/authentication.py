'''
Created on 27/08/2014

@author: Ismail Faizi
'''
from protorpc import remote, messages
from api.common import aWareInternalAPI
import endpoints
from models import User
from api.internal.admin import OAuthInfo
from endpoints.api_config import AUTH_LEVEL

'''
### MESSAGES ###
'''
class AuthenticationRequest(messages.Message):
    email = messages.StringField(1)

class AuthenticationResponse(messages.Message):
    key = messages.StringField(1)

'''
### END of MESSAGES ###

'''

@aWareInternalAPI.api_class(resource_name='admin.authentication',
                            path='admin/authentication',
                            allowed_client_ids=OAuthInfo.CLIENT_IDS,
                            scopes=OAuthInfo.SCOPES,
                            audiences=OAuthInfo.AUDIENCES)
class AdminAuthentication(remote.Service):
    '''
    Performs authentication of administrators in aWare
    '''

    @endpoints.method(AuthenticationRequest,
                      AuthenticationResponse,
                      http_method='GET',
                      path='authenticate',
                      name='authenticate')
    def authenticate(self, request):
        '''
        Authenticates an administrator by E-mail
        '''
        # retrieve the user
        user = User.find_by_email(request.email)
        if not user:
            message = 'No user with the E-mail address "%s" exists.' % request.email
            raise endpoints.NotFoundException(message)

        if not user.is_admin():
            message = 'The user has no administrator privileges.'
            raise endpoints.BadRequestException(message)

        return AuthenticationResponse(key=user.key.urlsafe())
