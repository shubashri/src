'''
Created on 22/07/2014

@author: Ismail Faizi
'''
from protorpc import messages, remote, message_types
from api.common import aWareInternalAPI
import endpoints
from models.guides import AppGuide

'''
### MESSAGES ###
'''

class AppGuideItemRequest(messages.Message):
    guideItemKey = messages.StringField(1, required=True)
    
class AppGuideItemResponse(messages.Message):
    guideItemKey = messages.StringField(1, required=True)
    image = messages.StringField(2)
    text = messages.StringField(3)

class AppGuideItemCollection(messages.Message):
    items = messages.MessageField(AppGuideItemResponse, 1, repeated=True)

'''
### END of MESSAGES ###
'''
    
@aWareInternalAPI.api_class(resource_name='guide', 
                            path='app/guide')
class AppGuideAPI(remote.Service):
    '''
    The API for App guide
    '''
    
    @endpoints.method(AppGuideItemRequest,
                      AppGuideItemResponse,
                      http_method='GET',
                      path='item',
                      name='item')
    def get_guide_item(self, request):
        '''
        Returns an App guide item based on the given datastore key
        '''
        item = AppGuide.get_by_urlsafe_key(request.guideItemKey)
        
        if not item:
            message = 'No guide item with the key "%s" exists.' % request.guideItemKey
            raise endpoints.NotFoundException(message)
        
        return AppGuideHelper.create_item(item)
    
    @endpoints.method(message_types.VoidMessage,
                     AppGuideItemCollection,
                     http_method='GET',
                     path='items',
                     name='items')
    def get_guide_items(self, request):
        '''
        Returns all available guide items in the datastore
        '''
        items = AppGuide.get_all()
        
        return AppGuideHelper.create_collection(items)
    
class AppGuideHelper():
    
    @classmethod
    def create_item(cls, entity):
        item = AppGuideItemResponse()
        item.guideItemKey = entity.key.urlsafe()
        item.image = entity.get_serving_url_for_image()
        item.text = entity.text
        
        return item
    
    @classmethod
    def create_collection(cls, entity_list):
        collection = AppGuideItemCollection()
        for entity in entity_list:
            collection.items.append(cls.create_item(entity))
        return collection