'''
Created on 20/08/2014

@author: Ismail Faizi
'''
import webapp2
from google.appengine.ext import deferred
from update import UpdateScanningSchema

class SchemaUpdateHandler(webapp2.RequestHandler):

    def get(self):
        deferred.defer(UpdateScanningSchema)
        self.response.out.write('Schema migration successfully initiated.')

