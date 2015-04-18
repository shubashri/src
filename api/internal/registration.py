'''
Created on 06/05/2014

@author: Ismail Faizi
'''
import endpoints  # @UnresolvedImport @UnusedImport
from protorpc import messages
from protorpc import remote
from api.common import aWareInternalAPI
from api.internal.users import SettingResponse, SettingCollection
from models import User
from models.guides import AppGuide
from models.utils import AwareParameters

'''
### MESSAGES ###
'''
class RegistrationRequest(messages.Message):
    clientID = messages.StringField(1)


class UpdateMessage(messages.Message):
    guide = messages.BooleanField(1)
    tou = messages.BooleanField(2)

class RegistrationResponse(messages.Message):
    userKey = messages.StringField(1)
    name = messages.StringField(2)
    email = messages.StringField(3)
    photo = messages.StringField(4)
    clientID = messages.StringField(5)
    settings = messages.MessageField(SettingCollection, 6)
    updates = messages.MessageField(UpdateMessage, 8)

'''
### END of MESSAGES ###
'''

@aWareInternalAPI.api_class(resource_name='registration',
                            path='registration')

class Registration(remote.Service):
    '''
    The API for registering a smartphone client
    '''

    @endpoints.method(RegistrationRequest,
                  RegistrationResponse,
                  http_method='GET',
                  path='register',
                  name='register')
    def register(self, request):
        '''
        Register a smartphone client based on the Unique Device ID (UUID)
        '''
        user = User.client(request.clientID)

        # update visit time
        user.update_visit_time()

        response = RegistrationResponse(userKey=user.key.urlsafe(),
                                        clientID=request.clientID)
        # set user's name
        if user.name:
            response.name = user.name
        else:
            response.name = ''
        # set user's default e-mail
        if user.has_email():
            response.email = user.get_default_email()
        else:
            response.email = ''
        # set user's settings
        response.settings = SettingCollection(items=[])
        settings = user.get_settings()
        if len(settings):
            for setting in settings:
                setting_response = SettingResponse()
                setting_response.key = setting.key.urlsafe()
                setting_response.settingKey = setting.setting_key.urlsafe()
                setting_response.settingValue = setting.value

                response.settings.items.append(setting_response)

        # set what has been updated since user's last visit
        update_msg = UpdateMessage()
        update_msg.guide = AppGuide.is_updated_since(user.last_visit)
        update_msg.tou = AwareParameters.get_instance().is_tou_updated_since(user.last_visit)
        response.updates = update_msg

        return response
