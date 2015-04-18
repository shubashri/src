'''
Created on 01/10/2013

@author: Ismail Faizi
'''

from common import AuthorizedPage
from models import Ingredient, INGREDIENT_KEY

class IngredientsPage(AuthorizedPage):
    
    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'ingredients.html', request, response)
    
    def handleGetRequest(self):
        # get the recent 10 ingredients added to datastore
        q = Ingredient.query(ancestor=INGREDIENT_KEY)
        ingredients = q.order(-Ingredient.created).fetch(10)
        
        self.addTemplateValue('ingredients', ingredients)
        
        self.setActivePage('Ingredients')    
            
        
    