'''
Created on 06/05/2014

@author: Ismail Faizi
'''
from models.i18n import CurrencyUnit, VolumeUnit, MassUnit, LengthUnit

class UnitHelper():

    @classmethod
    def to_string(cls, unit):
        if unit is CurrencyUnit:
            return ""+ unit.code +" ("+ unit.title +")"
        if (unit is VolumeUnit) or (unit is MassUnit) or (unit is LengthUnit):
            return ""+ unit.denotation +" ("+ unit.title +")"
        return ""+ unit.title
