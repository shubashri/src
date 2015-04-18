'''
Created on 31/05/2014

@author: Ismail Faizi
'''
from models.i18n import UnitConversionFactor, Unit

class UnitConversionEngine():
    
    @classmethod
    def get_conversion_factor(cls, fromUnit, toUnit):
        if not isinstance(fromUnit, Unit) or not isinstance(toUnit, Unit):
            raise ValueError("The arguments fromUnit and toUnit must be of type Unit")
        
        return UnitConversionFactor.get_ratio(toUnit, fromUnit)
    
    @classmethod
    def convert(cls, fromUnit, toUnit, quantity):
        if not isinstance(fromUnit, Unit) or not isinstance(toUnit, Unit):
            raise ValueError("The arguments fromUnit and toUnit must be of type Unit")
        
        if not fromUnit.has_same_dimension(toUnit):
            raise ValueError("The arguments must be of same dimension.")
        
        cf = cls.get_conversion_factor(fromUnit, toUnit)
        if cf:
            return quantity * cf
        
        raise Exception("No conversion factor exist for the given units.")
    
