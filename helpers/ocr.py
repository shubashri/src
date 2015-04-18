'''
Created on 31/05/2014

@author: Ismail Faizi
'''
from google.appengine.api import urlfetch, images
import json

class OCRServiceInterface():
    OCR_API_URL = 'https://worker-aws-us-east-1.iron.io/2/projects/5393d2795c23f9000900000a/tasks/webhook?code_name=ocr-worker&oauth=zB4UP7MAC85DPWDbfXR3_O5_49o'
    
    @classmethod
    def ocr_analyze(cls, image):
        request = {}
        request["imageId"] = image.key.urlsafe()
        request["imageUrl"] = images.get_serving_url(image.blob)
        request["resultPutUrl"] = "http://aware-backend.appspot.com/ocr/results"
        
        payload = json.dumps(request)
        
        result = urlfetch.fetch(url=cls.OCR_API_URL, 
                                payload=payload, 
                                method=urlfetch.POST, 
                                follow_redirects=True, 
                                headers={'Content-Type': 'application/json'})
        
        return result
