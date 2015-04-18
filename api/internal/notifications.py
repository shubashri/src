'''
Created on 07/06/2014

@author: Ismail Faizi
'''
import endpoints
from protorpc import messages, remote
from api.common import aWareInternalAPI
from models import User, Product, ProductUpdateNotification

'''
### MESSAGES ###
'''
class ProductUpdateNotificationReq(messages.Message):
    
    class NotificationType(messages.Enum):
        APP = 1
        EMAIL = 2
        
    userKey = messages.StringField(1, required=True)
    productKey = messages.StringField(2, required=True)
    type = messages.EnumField(NotificationType, 3, default='APP')
    
class ProductUpdateNotificationRes(messages.Message):
    key = messages.StringField(1)
    
'''
### END of MESSAGES ###
'''

@aWareInternalAPI.api_class(resource_name='notifications', 
                            path='notifications')    
class Notifications(remote.Service):
    '''
    API for aWare notifications
    '''
    
    @endpoints.method(ProductUpdateNotificationReq, 
                      ProductUpdateNotificationRes, 
                      name='product_update', 
                      path='product_update', 
                      http_method='GET')
    def product_update(self, request):
        '''
        Add a notification for product update
        '''
        user = User.get_by_urlsafe_key(request.userKey)
        if not user:
            message = 'No user with the key "%s" exists.' % request.userKey
            raise endpoints.NotFoundException(message)
        
        product = Product.get_by_urlsafe_key(request.productKey)
        if not product:
            message = 'No product with the key "%s" exists.' % request.productKey
            raise endpoints.NotFoundException(message)
        
        pun = ProductUpdateNotification.load(user, product)
        pun.update_type('%s' % request.type)
        
        return ProductUpdateNotificationRes(key=pun.key.urlsafe())
    