'''
Created on 07/05/2014

@author: Ismail Faizi
'''
import endpoints
from protorpc import messages, remote, message_types
from api.common import aWareInternalAPI
from models import User, Scanning, Product, UserSettingKey
from google.appengine.datastore.datastore_query import Cursor

'''
### MESSAGES ###
'''
class SettingResponse(messages.Message):
    key = messages.StringField(1)
    settingKey = messages.StringField(2)
    settingValue = messages.StringField(3)

class SettingCollection(messages.Message):
    items = messages.MessageField(SettingResponse, 1, repeated=True)

class UserUpdateRequest(messages.Message):
    userKey = messages.StringField(1, required=True)
    email = messages.StringField(2)
    name = messages.StringField(3)
    send_email = messages.StringField(4, default='1')

class ScannedProductsRequest(messages.Message):
    user_key = messages.StringField(1, required=True)
    size = messages.IntegerField(2, default=10)
    cursor = messages.StringField(3)

class ScannedProductResponse(messages.Message):
    product_key = messages.StringField(1, required=True)
    name = messages.StringField(2, default='')
    thumbnail = messages.StringField(3)
    updated = messages.BooleanField(4, default=False)

class ScannedProductsCollection(messages.Message):
    products = messages.MessageField(ScannedProductResponse, 1, repeated=True)
    cursor = messages.StringField(2)
    more = messages.BooleanField(3)

class DeleteScannedProductRequest(messages.Message):
    user_key = messages.StringField(1, required=True)
    barcodes = messages.StringField(2, repeated=True)

'''
### END of MESSAGES ###
'''

@aWareInternalAPI.api_class(resource_name='users',
                            path='users')
class Users(remote.Service):
    '''
    API for aWare users
    '''

    @endpoints.method(UserUpdateRequest,
                      message_types.VoidMessage,
                      name='update',
                      path='update',
                      http_method='POST')
    def update_user(self, request):
        '''
        Updates a user
        '''
        user = User.get_by_urlsafe_key(request.userKey)
        if not user:
            message = 'No user with the key "%s" exists.' % request.userKey
            raise endpoints.NotFoundException(message)

        user.upate(email=request.email, name=request.name)

        user.update_setting(UserSettingKey.get_send_email(), request.send_email)

        return message_types.VoidMessage()

    @endpoints.method(ScannedProductsRequest,
                      ScannedProductsCollection,
                      name='products.scanned',
                      path='products/scanned',
                      http_method='GET')
    def get_scanned_products(self, request):
        '''
        Retrieve user's scanned products
        '''
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        products, next_cursor, more = UsersHelper.fetch_scanned_products(user,
                                                                         request.cursor,
                                                                         request.size)

        cursor = ''
        if next_cursor:
            cursor = next_cursor.urlsafe()

        return UsersHelper.create_scanned_products_collection(user,
                                                              products,
                                                              cursor,
                                                              more);

    @endpoints.method(DeleteScannedProductRequest,
                      message_types.VoidMessage,
                      http_method='POST',
                      path='products/scanned/delete',
                      name='products.scanned.delete')
    def delete_scanned_products(self, request):
        '''
        Delete user's scanned product based on a barcode
        '''
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        scannings = []
        for barcode in request.barcodes:
            results = Scanning.find(user, barcode)
            if len(results):
                scannings.extend(results)

        for scanning in scannings:
            scanning.do_delete()

        return message_types.VoidMessage()

class UsersHelper(object):

    @classmethod
    def fetch_scanned_products(cls, user, cursor=None, size=10):
        if cursor and isinstance(cursor, basestring):
            cursor = Cursor(urlsafe=cursor)

        # build the query
        query = Scanning.query()
        query = query.filter(Scanning.user == user.key)
        query = query.filter(Scanning.deleted == False)
        query = query.order(Scanning.created)

        scannings, next_cursor, more = query.fetch_page(size, start_cursor=cursor)

        barcode_product_map = {}

        for scanning in scannings:
            if scanning.barcode not in barcode_product_map:
                products = Product.lookup_barcode(scanning.barcode)
                barcode_product_map[scanning.barcode] = products

        if not more:
            return cls.create_result_set(barcode_product_map), next_cursor, False

        fetched = len(barcode_product_map)
        if fetched < size:
            products, next_cursor, more = cls.fetch_scanned_products(user, next_cursor, size - fetched)
            result = cls.create_result_set(barcode_product_map)
            for product in products:
                result.append(product)

            return result, next_cursor, more

        return cls.create_result_set(barcode_product_map), next_cursor, more

    @classmethod
    def create_result_set(cls, barcode_product_map):
        result = []
        for products in barcode_product_map.itervalues():
            for product in products:
                result.append(product)
        return result

    @classmethod
    def create_scanned_product(cls, entity, user):
        msg = ScannedProductResponse()
        msg.product_key = entity.key.urlsafe()
        msg.name = entity.name

        img = entity.get_default_image()
        if img:
            msg.thumbnail = img.get_serving_url(50)

        if user.last_visit and entity.modified and user.last_visit < entity.modified:
            msg.updated = True
        else:
            msg.updated = False

        return msg

    @classmethod
    def create_scanned_products_collection(cls, user, entities, cursor='', more=False):
        collection = ScannedProductsCollection()
        collection.cursor = cursor
        collection.more = more
        collection.products = []

        if not entities:
            return collection

        for entity in entities:
            collection.products.append(cls.create_scanned_product(entity, user))

        return collection
