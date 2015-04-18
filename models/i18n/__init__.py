'''
Created on 24/04/2014

@author: Ismail Faizi
'''
from google.appengine.ext import ndb

class Language(ndb.Model):
    code = ndb.StringProperty()
    name = ndb.StringProperty()
    native = ndb.StringProperty()

    LANG_NC_NAME = 'Default (INCI)'
    LANG_NC_CODE = 'nc'

    def is_default(self):
        return self.code == self.LANG_NC_CODE and self.name == self.LANG_NC_NAME

    @classmethod
    def create(cls, code, name):
        lang = Language(code=code,
                        name=name)
        lang.put()
        return lang

    @classmethod
    def find_by_code(cls, code):
        return cls.gql("WHERE code = :1", code).get()

    @classmethod
    def get_by_code(cls, code):
        lang = cls.gql("WHERE code = :1", code).fetch()
        if len(lang):
            return lang[0]

        # return the default language (English)
        return cls.get_by_name('English')

    @classmethod
    def get_by_name(cls, name):
        lang = cls.gql("WHERE name = :1", name).fetch()
        if len(lang):
            return lang[0]

        # return the default language (English)
        lang = cls.gql("WHERE name = 'English'").fetch()
        if len(lang):
            return lang[0]

        # create and return the default language (English)
        return cls.create("en", "English")

    @classmethod
    def get_unknown(cls):
        name = 'Other'
        code = 'or'
        lang = cls.gql("WHERE name = :1 AND code = :2", name, code).get()
        if not lang:
            lang = Language()
            lang.name = name
            lang.code = code
            lang.put()

        return lang

    @classmethod
    def get_nc_lang(cls):
        lang = cls.gql("WHERE name = :1 AND code = :2", 
                       cls.LANG_NC_NAME, 
                       cls.LANG_NC_CODE).get()
        if not lang:
            lang = Language()
            lang.name = cls.LANG_NC_NAME
            lang.code = cls.LANG_NC_CODE
            lang.put()

        return lang


class Locale(ndb.Model):
    name = ndb.StringProperty()
    language = ndb.KeyProperty(kind=Language)

class TranslationKey(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)

class UITranslationKey(TranslationKey):
    value = ndb.StringProperty()

    @classmethod
    def load(cls, key):
        tk = cls.gql("WHERE value = :1", key).fetch()
        if len(tk):
            return tk[0]

        # create and return the key
        tk = UITranslationKey(value=key)
        tk.put()
        return tk

class DataTranslationKey(TranslationKey):
    value = ndb.StringProperty()

    @classmethod
    def load(cls, key):
        tKey = cls.gql("WHERE value = :1", key).fetch()
        if len(tKey):
            return tKey[0]

        # create and return the key
        tKey = DataTranslationKey()
        tKey.value = key
        tKey.put()
        return tKey

class Translation(ndb.Model):
    value = ndb.StringProperty()
    tKey = ndb.KeyProperty()
    language = ndb.KeyProperty(kind=Language)

    @classmethod
    def load(cls, languageKey, translationKey):
        trans = cls.gql("WHERE language = :1 AND tKey = :2",
                        languageKey, translationKey).fetch()
        if len(trans):
            return trans[0]

        trans = Translation()
        trans.value = ''
        trans.tKey = translationKey
        trans.language = languageKey
        trans.put()
        return trans

class SystemOfMeasurement():
    SI = 1
    Other = 2

    @classmethod
    def list_of_numbers(cls):
        return [1, 2]

    @classmethod
    def default(cls):
        return cls.SI

class Unit(ndb.Model):
    title = ndb.StringProperty()
    system = ndb.IntegerProperty(choices=SystemOfMeasurement.list_of_numbers(),
                                 default=SystemOfMeasurement.default())
    locale = ndb.KeyProperty(kind=Locale)

    def to_string(self):
        return self.title

    @classmethod
    def get_by_urlsafe_key(cls, urlsafe_key):
        key = ndb.Key(urlsafe=urlsafe_key)
        try:
            return key.get()
        except:
            pass  # Just ignore it
        return None

    # abstract method
    def has_same_dimension(self, u):
        return

class CurrencyUnit(Unit):
    code = ndb.StringProperty()

    def to_string(self):
        return self.code + "(" + self.title + ")"

    def has_same_dimension(self, u):
        return isinstance(u, CurrencyUnit)

class MassUnit(Unit):
    denotation = ndb.StringProperty()

    def to_string(self):
        return self.denotation + "(" + self.title + ")"

    def has_same_dimension(self, u):
        return isinstance(u, MassUnit)

class VolumeUnit(Unit):
    denotation = ndb.StringProperty()

    def to_string(self):
        return self.denotation + "(" + self.title + ")"

    def has_same_dimension(self, u):
        return isinstance(u, VolumeUnit)

class LengthUnit(Unit):
    denotation = ndb.StringProperty()

    def to_string(self):
        return self.denotation + "(" + self.title + ")"

    def has_same_dimension(self, u):
        return isinstance(u, LengthUnit)

class UnitConversionFactor(ndb.Model):
    aUnit = ndb.KeyProperty()
    aUnitQuantity = ndb.FloatProperty()
    bUnit = ndb.KeyProperty()
    bUnitQuantity = ndb.FloatProperty()

    @classmethod
    def get_ratio(cls, aUnit, bUnit):
        if not isinstance(aUnit, Unit) or not isinstance(bUnit, Unit):
            raise ValueError("The arguments must be of type Unit.")

        ucf = cls.gql("WHERE aUnit = :1 AND bUnit = :2", aUnit.key, bUnit.key).get()
        if ucf:
            return ucf.aUnitQuantity / ucf.bUnitQuantity
        else:
            ucf = cls.gql("WHERE aUnit = :1 AND bUnit = :2", bUnit.key, aUnit.key).get()
            if ucf:
                return ucf.bUnitQuantity / ucf.aUnitQuantity

        return None

