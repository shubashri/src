'''
Created on 01/10/2013

@author: Ismail Faizi
'''

from common import AuthorizedPage
from helpers import IngredientsFinder
import time
from models import Ingredient, INGREDIENT_KEY
from helpers.uploadhandler import UploadHandler

class DebugPage(AuthorizedPage):
    
    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'debug.html', request, response)
    
    def handleGetRequest(self):
        self.addCommon()
        
    def handlePostRequest(self):
        action = self.request.get('action')
        
        if action == 'sim-ocr-reading':
            ingredients = self.request.get('ocr_result')
            datastore = self.request.get('datastore')
            ingList = self.request.get('ingredients')
            if ingredients:
                reader = IngredientsFinder(ingredients)
                result = {}
                if datastore == "1":
                    # use the ingredients from datastore
                    ingList = Ingredient.query(ancestor=INGREDIENT_KEY).fetch()
                    startTime = time.clock()
                    for g in ingList:
                        for n in g.inci_names:
                            if reader.contains(n.lower()):
                                result[n] = 'YES'
                            else:
                                result[n] = 'NO'
                    elapsedTime = (time.clock() - startTime)
                    self.addTemplateValue('ocrReadingResults', result.items())
                    self.addTemplateValue('elapsedTime', elapsedTime)
                else:
                    if ingList:
                        ings = ingList.splitlines()
                        startTime = time.clock()
                        for g in ings:
                            if reader.contains(g):
                                result[g] = 'YES'
                            else:
                                result[g] = 'NO'
                        elapsedTime = (time.clock() - startTime)
                        self.addTemplateValue('ocrReadingResults', result.items())
                        self.addTemplateValue('elapsedTime', elapsedTime)
                    else:
                        self.addTemplateValue('ocrReadingError', "You must either select the datastore as the provider of ingredients list or provide a list of ingredients (separated by new line)")
            else:
                self.addTemplateValue('ocrReadingError', "You must provide a valid OCR Result.")
                        
        self.addCommon()
            
    def addCommon(self):
        self.addTemplateValue('upload_url', UploadHandler.create_upload_urls())
        
        