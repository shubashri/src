'''
Created on 22/05/2014

@author: Ismail Faizi
'''
from protorpc import remote, messages, message_types
from api.common import aWareInternalAPI
import endpoints
from models import HelpTopic

'''
### MESSAGES ###
'''    
class HTopic(messages.Message):
    title = messages.StringField(1)
    description = messages.StringField(2)
        
class HelpCollection(messages.Message):
    items = messages.MessageField(HTopic, 1, repeated=True)
    
'''
### END of MESSAGES ###
'''

@aWareInternalAPI.api_class(resource_name='help', 
                            path='help')
class HelpAPI(remote.Service):
    '''
    The API for retrieving help topics
    '''
    
    @endpoints.method(message_types.VoidMessage,
                      HelpCollection,
                      http_method='GET',
                      path='topics',
                      name='topics')
    def get_topics(self, request):
        '''
        Retrieve all help topics in the system
        '''
        topics = HelpTopic.get_all()
        return HelpFactory.create_collection(topics)

class HelpFactory():
    
    @classmethod
    def create_collection(cls, topics):
        collection = HelpCollection()
        collection.items = []
        for topic in topics:
            h = HTopic()
            h.title = topic.title
            h.description = topic.description
            collection.items.append(h)
        return collection
            