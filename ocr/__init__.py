'''
Created on 08/07/2014

@author: Ismail Faizi
'''

import webapp2
import json
from google.appengine.ext import ndb
from models import Image, ProductState

class OCRResults(webapp2.RequestHandler):

    def put(self):
        if not self.request.body:
            self.response.out.write(json.dumps({'text': 'Invalid request!'}))
            return

        data = json.loads(self.request.body)
        if data is None:
            self.response.out.write(json.dumps({'text': 'No data provided!'}))
            return

        image_key = data.get('imageId')
        ocr_result = data.get('text')

        image = Image.get_by_urlsafe_key(image_key)
        if not image:
            self.response.out.write(json.dumps({'text': 'The image with Id=%s could not be located.' % image_key}))

        image.ocr_result = ocr_result
        image.put()

        image.read()

        product = image.product.get()
        product.change_state(ProductState.UserCreated)

        self.response.out.write(json.dumps({'text': 'Successfully received the OCR result.'}))
