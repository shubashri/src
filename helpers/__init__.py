'''
Created on 06/10/2013

@author: Ismail Faizi
'''

from lib.bitap import bitapSearch
import math

class HazardProfile:
    
    def __init__(self):
        self.hazards = []
    
    def add_hazard(self, hazard):
        self.hazards.append(hazard)
        
    def get_hazards(self):
        return self.hazards
    
    # @deprecated: we use GCE instead
    def toJSON(self):
        l = []
        for hazard in self.hazards:
            l.append(hazard.toJSON())
        return l
    
class Hazard:
        
    def __init__(self, pictogram):
        self.pictogram = pictogram
        self.count = 1
        self.ingredients = []
        
    def increment_count(self):
        self.count = self.count + 1
        
    def decrement_count(self):
        if self.count > 0:
            self.count = self.count - 1    
        
    def get_pictogram(self):
        return self.pictogram
        
    def get_count(self):
        return self.count
    
    def add_ingredient(self, ingredient):
        self.ingredients.append(ingredient)
        
    def get_ingredients(self):
        return self.ingredients
        
    #@deprecated: it will be removed, using GCE instead    
    def toJSON(self):
        ingredients = []
        for ingredient in self.ingredients:
            obj = {'ingredient': ingredient.get_name(),
                   'statements': []}
            statements = ingredient.getHStatements()
            for statement in statements:
                stmt = statement.hstatement.get().statement
                if stmt and len(stmt) > 0:
                    obj['statements'].append(stmt)
            ingredients.append(obj)
                
        pictogram = "/pictogram?ID="+ self.pictogram.key.urlsafe()
        return {'pictogram': pictogram, 
                'count': self.count,
                'hazard': {'title': self.pictogram.title,
                           'description': self.pictogram.description
                           },
                'ingredients': ingredients
                }
    
class IngredientsFinder:
    THREASHOLD = 0.30
    
    def __init__(self, ingredients):
        if ingredients:
            self.ingredients = ingredients;
        else:
            self.ingredients = ""

    def contains(self, ingredient):
        if not ingredient or len(ingredient) == 0:
            return False
        
        haystack = self.ingredients.lower()
        needle = ingredient.lower()
        maxErrors = int(math.ceil(len(needle)*self.THREASHOLD))
        (match, result) = bitapSearch(haystack, needle, maxErrors)  # @UnusedVariable
        if result >= 0:
            return True

        return False