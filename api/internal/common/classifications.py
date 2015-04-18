'''
Created on 30/08/2014

@author: Ismail Faizi
'''
from protorpc import messages, remote, message_types
from api.common import aWareInternalAPI
import endpoints
from models import ProductCategory

'''
### MESSAGES ###
'''
class CategoryMessage(messages.Message):
    key = messages.StringField(1)
    name = messages.StringField(2)

class CategoriesCollection(messages.Message):
    items = messages.MessageField(CategoryMessage, 1, repeated=True)
'''
### END of MESSAGES ###

'''


@aWareInternalAPI.api_class(resource_name='common.classifications',
                            path='common/classifications')
class Classifications(remote.Service):
    '''
    Classification API for the different classifications supported by aWare
    '''

    @endpoints.method(message_types.VoidMessage,
                      CategoriesCollection,
                      name='list',
                      path='list',
                      http_method='GET')
    def get_list(self, request):
        '''
        Returns a list of all the product categories supported by aWare
        '''
        categories = ProductCategory.query().fetch()

        collection = []
        for category in categories:
            msg = CategoryMessage()
            msg.key = category.key.urlsafe()
            msg.name = category.name
            collection.append(msg)

        return CategoriesCollection(items=collection)
