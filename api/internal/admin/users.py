'''
Created on 14/11/2014

@author: Adhavan
'''

import endpoints  # @UnresolvedImport @UnusedImport
from protorpc import messages, message_types
from protorpc import remote
from api.common import aWareInternalAPI
from models import User,UserState
from google.appengine.datastore.datastore_query import Cursor
from api.internal.admin import OAuthInfo, LanguageResponse,AdminUtils
from models.i18n import Language

'''
### MESSAGES ###
'''


class UserListRequest(messages.Message):
    cursor = messages.StringField(1)
    size = messages.IntegerField(2, default=10)


'''class InappropriateReportsMessage(messages.Message):
    own = messages.IntegerField(1)
    others = messages.IntegerField(2)

'''
class WrongProductsMessage(messages.Message):
    own = messages.IntegerField(1)
    others = messages.IntegerField(2)

class UserResponse(messages.Message):
    
    class State(messages.Enum):
        Default = 0
        Blocked = 1
        Activated = 2
        Quarantined = 3
        
    user_key = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)
    email = messages.StringField(3)
    scans = messages.IntegerField(4)
    products_added = messages.IntegerField(5)
    wrong_products=messages.MessageField(WrongProductsMessage, 6)
    #inappropriate_reports=messages.MessageField(InappropriateReportsMessage, 7)
    state = messages.EnumField(State, 7, default='Default')
    device_id = messages.StringField(8)
    last_visit = messages.StringField(9)

    
class UserCollection(messages.Message):
    users = messages.MessageField(UserResponse, 1, repeated=True)
    cursor = messages.StringField(2)
    more = messages.BooleanField(3)
'''
### END of MESSAGES ###
'''


@aWareInternalAPI.api_class(resource_name='admin.users',
                            path='admin/users',
                            allowed_client_ids=OAuthInfo.CLIENT_IDS,
                            scopes=OAuthInfo.SCOPES,
                            audiences=OAuthInfo.AUDIENCES)

class AdminUsers(remote.Service):
    '''
    The aWare users API for aWare administrator interface
    '''
    @endpoints.method(UserListRequest,
                      UserCollection,
                      http_method='GET',
                      path='list',
                      name='list')
    
    def get_user_list(self, request):
        '''
        Retrieve a list of Users 
        '''
        # get size of the list to return
        size = request.size

        cursor = None
        if request.cursor:
            cursor = Cursor(urlsafe=request.cursor)
            
        # build the query
        query = User.query()

        users = None
        next_cursor = None
        more = False
        if cursor:
            users, next_cursor, more = query.fetch_page(size, start_cursor=cursor)
        else:
            users, next_cursor, more = query.fetch_page(size, start_cursor=cursor)

        if next_cursor:
            return UserHelper.create_collection(users, next_cursor.urlsafe(), more)

        return UserHelper.create_collection(users)

class UserHelper():
    
    @classmethod
    def get_email(cls, entity):
        return User.get_default_email(entity)

    @classmethod
    def get_wrong_products_info(cls, entity):
        msg = WrongProductsMessage()
        msg.own = entity.get_count_for_wrong_products_added_by_user()
        msg.others = entity.get_count_for_wrong_products_added_by_others()
        return msg
    
    @classmethod
    def get_inappropriate_reports(cls, entity):
        msg = InappropriateReportsMessage()
        msg.own = entity.get_count_for_inappropriate_content_added_by_user()
        msg.others = entity.get_count_for_inappropriate_content_added_by_others()
        return msg
    
    @classmethod
    def get_status(cls, entity):
        if entity.state == UserState.Default:
            return UserResponse.State.Default
        if entity.state == UserState.Blocked:
            return UserResponse.State.Blocked
        if entity.state == UserState.Activated:
            return UserResponse.State.Activated
        if entity.state == UserState.Quarantined:
            return UserResponse.State.Quarantined
        return None
    
    @classmethod
    def create_user(cls, entity):
        user = UserResponse()
        user.user_key = entity.key.urlsafe()
        user.name = entity.name
        user.email = cls.get_email(entity)
        user.state = cls.get_status(entity)
        user.scans = User.get_scanned_products_count(entity)
        user.products_added = User.get_added_products_count(entity)
        user.wrong_products = cls.get_wrong_products_info(entity)
        #user.inappropriate_reports = cls.get_inappropriate_reports(entity)
        user.device_id = entity.clientID
        user.last_visit = entity.last_visit
        return user 

    @classmethod
    def create_collection(cls, users, cursor='', more=False):
        collection = UserCollection()
        collection.cursor = cursor
        collection.more = more
        for u in users:
            collection.users.append(cls.create_user(u))
        return collection
