'''
Created on 30/08/2014

@author: Ismail Faizi
'''
from protorpc import messages, remote, message_types
from api.common import aWareInternalAPI
import endpoints
from models.i18n import Language

'''
### MESSAGES ###
'''
class LanguageMessage(messages.Message):
    code = messages.StringField(1)
    name = messages.StringField(2)

class LanguageCollection(messages.Message):
    items = messages.MessageField(LanguageMessage, 1, repeated=True)
'''
### END of MESSAGES ###

'''


@aWareInternalAPI.api_class(resource_name='common.languages',
                            path='common/languages')
class Languages(remote.Service):
    '''
    Languages API for languages supported by aWare
    '''

    @endpoints.method(message_types.VoidMessage,
                      LanguageCollection,
                      name='list',
                      path='list',
                      http_method='GET')
    def get_list(self, request):
        '''
        Returns a list of all the languages supported by aWare
        '''
        languages = Language.query().fetch()

        collection = []
        for language in languages:
            msg = LanguageMessage()
            msg.code = language.code
            msg.name = language.name
            collection.append(msg)

        return LanguageCollection(items=collection)
