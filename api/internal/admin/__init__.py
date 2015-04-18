'''
Created on 05/08/2014

@author: Ismail Faizi
'''
from protorpc import messages
import endpoints
from models.i18n import Language

class OAuthInfo():
    CLIENT_IDS  = [
                      '1019526038686.apps.googleusercontent.com',
                      '1019526038686-5jg4a5s4rrqfadms9cmmko6lnrqb80v6.apps.googleusercontent.com',
                      endpoints.API_EXPLORER_CLIENT_ID
                  ]
    SCOPES      = [
                      'https://www.googleapis.com/auth/userinfo.email'
                  ]
    AUDIENCES   = CLIENT_IDS

class AdminUtils():

    @classmethod
    def calc_ingredient_name(cls, ingredient):
        label_name = ingredient.get_label_name()
        inci_name = None
        if len(ingredient.inci_names):
            inci_name = ingredient.inci_names[0]

        # build the name as "(INCI name|Label name) E-number"
        if len(ingredient.e_numbers) and not label_name and not inci_name:
            return [Language.get_by_code('en'),
                    ingredient.e_numbers[0]]
        if len(ingredient.e_numbers) and inci_name:
            return [Language.get_nc_lang(),
                    '(%s) %s' % (inci_name, ingredient.e_numbers[0])]
        if len(ingredient.e_numbers) and label_name:
            return [label_name.language.get(),
                    '(%s) %s' % (label_name.name, ingredient.e_numbers[0])]

        # build the name as "INCI name"
        if inci_name:
            return [Language.get_nc_lang(),
                    inci_name]

        # build the name as "Label name"
        if label_name:
            return [label_name.language.get(), 
                    label_name.name]

        return [Language.get_unknown(),
                'UNKNOWN']

### Cross-API Messages
class UserResponse(messages.Message):
    user_key = messages.StringField(1, required=True)

class LanguageResponse(messages.Message):
    language_key = messages.StringField(1, required=True)
    name = messages.StringField(2)
    code = messages.StringField(3)

