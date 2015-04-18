'''
Created on 01/10/2013

@author: Ismail Faizi
'''
from google.appengine.api import images

import webapp2
from ui.common import AuthorizedPage
from ui.ingredients import IngredientsPage
from ui.classifications import ClassificationsPage
from ui.hstatements import HStatementsPage
from ui.classes import ClassesPage
from ui.utils import UtilsPage, TestProductCreationHandler
from ui.hreferences import HReferencesPage
from ui.helps import HelpsPage
from ui.debug import DebugPage
from google.appengine.ext import ndb
from models import Product, PRODUCT_KEY
from helpers.servers import ImageServer
from helpers.uploadhandler import UploadHandler
from ui.ocr import OCRPage
from ui.appguide import AppGuidePage, AppGuideCreationHandler
from ui.parameters import ParametersPage
from ui.pictograms import PictogramsPage
from ui.updates import SchemaUpdateHandler
from ocr import OCRResults

class MainPage(AuthorizedPage):

    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'products.html', request, response)

    def addCommon(self):
        # get the recent 10 products added to datastore
        q = Product.query(ancestor=PRODUCT_KEY)
        products = q.order(-Product.created).fetch(20)

        count = 0
        if products:
            count = len(products)

        self.addTemplateValue('products', products)
        self.addTemplateValue('count', count)
        self.addTemplateValue('images', images)

        self.setActivePage('Products')

    def handleGetRequest(self):
        self.addCommon()

    def handlePostRequest(self):
        action = self.request.get('action', None)
        if action == 'delete':
            p_key = ndb.Key(urlsafe=self.request.get('key'))
            if p_key:
                p_key.delete()

        self.addCommon()

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/ingredients', IngredientsPage),
    ('/classifications', ClassificationsPage),
    ('/hstatements', HStatementsPage),
    ('/hreferences', HReferencesPage),
    ('/classes', ClassesPage),
    ('/pictograms', PictogramsPage),
    ('/utils', UtilsPage),
    ('/utils/product', TestProductCreationHandler),
    ('/images', ImageServer),
    ('/helps', HelpsPage),
    ('/guide', AppGuidePage),
    ('/guide/create', AppGuideCreationHandler),
    ('/upload', UploadHandler),
    ('/debug', DebugPage),
    ('/ocr', OCRPage),
    ('/ocr/results', OCRResults),
    ('/parameters', ParametersPage),
    ('/updates/schema/update', SchemaUpdateHandler)
], debug=True)
