'''
Created on 16/05/2014

@author: Ismail Faizi
'''
from protorpc import messages, remote
from api.common import aWareInternalAPI
import endpoints
from models import Product, User, Box

'''
### MESSAGES ###
'''
class BoxRequest(messages.Message):
    boxKey = messages.StringField(1, required=True)

class ProductBoxes(messages.Message):
    productKey = messages.StringField(1, required=True)
    userKey = messages.StringField(2, required=True)

class BoxResponse(messages.Message):
    key = messages.StringField(1)
    label = messages.StringField(2)
    icon = messages.StringField(3)
    description = messages.StringField(4)
    
class BoxCollection(messages.Message):
    items = messages.MessageField(BoxResponse, 1, repeated=True)
'''
### END of MESSAGES ###
'''
@aWareInternalAPI.api_class(resource_name='boxes', 
                            path='boxes')
class Boxes(remote.Service):
    '''
    The API for the aWare Box concept
    '''

    @endpoints.method(BoxRequest,
                      BoxResponse,
                      http_method='GET',
                      path='box',
                      name='box')
    def get_box(self, request):
        '''
        Retrieve a single box for a specific product and user
        '''
        # fetch the product and user based on the request
        box = Box.get_by_urlsafe_key(request.boxKey)

        if not box:
            message = 'No box with the key "%s" exists.' % request.boxKey
            raise endpoints.NotFoundException(message)

        return BoxHelper.create_box(box)
        
    @endpoints.method(ProductBoxes, 
                      BoxCollection,
                      http_method='GET',
                      path='boxes',
                      name='boxes')
    def get_boxes(self, request):
        '''
        Retrieve a list of boxes for a specific product and user
        '''
        # fetch the product and user based on the request
        product = Product.get_by_urlsafe_key(request.productKey)
        user = User.get_by_urlsafe_key(request.userKey)
        
        if not product:
            message = 'No product with the key "%s" exists.' % request.productKey
            raise endpoints.NotFoundException(message)
        
        if not user:
            message = 'No user with the key "%s" exists.' % request.userKey
            raise endpoints.NotFoundException(message)
        
        boxes = product.get_boxes()
        return BoxHelper.create_collection(boxes)
        
class BoxHelper():
    
    @classmethod
    def create_box(cls, model):
        box = BoxResponse()
        box.key = model.key.urlsafe()
        box.label = model.label
        box.icon = '/images?kind=boxIcon&ID='+ model.key.urlsafe()
        box.description = model.description
        return box
        
    @classmethod
    def create_collection(cls, boxList):
        collection = BoxCollection()
        for box in boxList:
            res = cls.create_box(box)
            collection.items.append(res)
        return collection
        
        
        