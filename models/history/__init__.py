'''
Created on 02/05/2014

@author: Ismail Faizi
'''

from google.appengine.ext import ndb

class ProductAction():
    AddIngredient = 1
    DeleteIngredient = 2
    
    @classmethod
    def listOfNumbers(cls):
        return [1,2]
    
class ProductHistory(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    user = ndb.KeyProperty(kind='User')
    product = ndb.KeyProperty(kind='Product')
    ingredients = ndb.KeyProperty(kind='Ingredient', repeated=True)
    action = ndb.IntegerProperty(choices=ProductAction.listOfNumbers())
    