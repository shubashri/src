'''
Created on 1/06/2013

@author: Ismail Faizi
'''

from common import AuthorizedPage
from google.appengine.ext import ndb
from helpers.ocr import OCRServiceInterface

class OCRPage(AuthorizedPage):
    
    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'ocr.html', request, response)
        self.ocr_result = ''
    
    def handleGetRequest(self):
        self.addCommon()
        self.setActivePage('OCR')
    
    def handlePostRequest(self):
        image = self.request.get('image', None)
        
        img_key = None
        try:
            img_key = ndb.Key(urlsafe=image)
        except:
            self.ocr_result = 'Invalid image key.'
        
        if img_key:
            blob = img_key.get()
            OCRServiceInterface.ocr_analyze(blob)
            self.ocr_result = 'OCR Service has been called in order to analyze the image.'
        
        self.addCommon()
        self.setActivePage('OCR')
        
    def addCommon(self):
        self.addTemplateValue('ocr_result', self.ocr_result)
        