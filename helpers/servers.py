'''
Created on 16/05/2014

@author: Ismail Faizi
'''

import webapp2
from models import Pictogram, Box

class ImageServer(webapp2.RequestHandler):
    
    def get(self):
        kind = self.request.get('kind')
        
        if kind == 'pictogram':
            self.serve_pictogram()
        if kind == 'boxIcon':
            self.server_box_icon()
  
    def serve_pictogram(self):
        ID = self.request.get('ID')
        
        if ID:
            pictogram = Pictogram.get_by_urlsafe_key(ID)
            if pictogram:
                self.response.headers['Content-Type'] = 'image/png'
                self.response.out.write(pictogram.image)
                return
        
        self.error(404)
        
    def server_box_icon(self):
        ID = self.request.get('ID')
        
        if ID:
            box = Box.get_by_urlsafe_key(ID)
            if box:
                self.response.headers['Content-Type'] = 'image/png'
                self.response.out.write(box.icon)
                return
        
        self.error(404)
