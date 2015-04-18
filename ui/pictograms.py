'''
Created on 01/10/2013

@author: Ismail Faizi
'''

from common import AuthorizedPage
from models import Pictogram
import re

class PictogramsPage(AuthorizedPage):
    
    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'pictograms.html', request, response)
    
    def handleGetRequest(self):
        self.add_common()
        
    def handlePostRequest(self):
        data = self.get_request_data(self.request.arguments())
        
        for name, info in data.iteritems():
            pictogram = Pictogram.get_by_name(name)
            
            if not pictogram:
                continue
            
            update = False
            if 'title' in info and '' is not info['title']:
                pictogram.title = info['title']
                update = True
            
            if 'description' in info and '' is not info['description']:
                pictogram.description = info['description']
                update = True
            
            if 'order' in info and '' is not info['order']:
                pictogram.order = int(info['order'])
                update = True
            
            if update:
                pictogram.put()
            
        self.addMessage('You changes were successfully saved.', AuthorizedPage.MSG_TYPE_SUCCESS)
        self.add_common()
    
    def get_request_data(self, arguments):
        data = {}
        
        for argument in arguments:
            item = {}
            
            name = self.extract_name(argument)
            if name and name in data:
                item = data[name]
            else:
                data[name] = item
                
            if self.is_title(argument):
                item['title'] = self.request.get(argument)
            if self.is_description(argument):
                item['description'] = self.request.get(argument)
            if self.is_order(argument):
                item['order'] = self.request.get(argument)
            
        return data
    
    def extract_name(self, named_str):
        re_obj = re.compile("(title|description|order)\[(.*)\]")
        match = re_obj.search(named_str)
        
        if match:
            return match.group(2)
        
        return None
    
    def is_title(self, request):
        return re.compile("title\[(.*)\]").search(request) is not None
    
    def is_description(self, request):
        return re.compile("description\[(.*)\]").search(request) is not None
    
    def is_order(self, request):
        return re.compile("order\[(.*)\]").search(request) is not None
    
    def add_common(self):
        # get all the pictograms
        pictograms = Pictogram.get_all()
        self.addTemplateValue('pictograms', pictograms)
        self.setActivePage('Pictograms')