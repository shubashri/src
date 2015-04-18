'''
Created on 21/05/2014

@author: Ismail Faizi
'''
from protorpc import remote, messages
from api.common import aWareInternalAPI
import endpoints
from models.i18n import Language, UITranslationKey, Translation,\
    DataTranslationKey

'''
### MESSAGES ###
'''
class TranslationRequest(messages.Message):
    lang = messages.StringField(2, required=True)
    translationKey = messages.StringField(1)
    
class TranslationResponse(messages.Message):
    translation = messages.StringField(1)
        
'''
### END of MESSAGES ###
'''

@aWareInternalAPI.api_class(resource_name='translations', 
                            path='translations')
class Translations(remote.Service):
    '''
    The API for retrieving translations for both UI text and various data items
    '''
    
    @endpoints.method(TranslationRequest,
                      TranslationResponse,
                      http_method='GET',
                      path='ui',
                      name='ui')
    def get_ui(self, request):
        '''
        Retrieve translation for UI text
        '''
        language = Language.get_by_code(request.lang)
        translationKey = UITranslationKey.load(request.translationKey)
        translation = Translation.load(language.key, translationKey.key)
        return TranslationResponse(translation=translation.value)
    
    @endpoints.method(TranslationRequest,
                      TranslationResponse,
                      http_method='GET',
                      path='data',
                      name='data')
    def get_data(self, request):
        '''
        Retrieve translation for data items
        '''
        language = Language.get_by_code(request.lang)
        translationKey = DataTranslationKey.load(request.translationKey)
        translation = Translation.load(language.key, translationKey.key)        
        return TranslationResponse(translation=translation.value)
    