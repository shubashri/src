'''
Created on 04/11/2014

@author: Ismail Faizi
'''
import unittest
from google.appengine.ext import testbed
from models import Product, Ingredient, IngredientLabelName, LabelName, \
    IngredientWikiLink, User, ProductIngredient
from models.i18n import Language
from api.internal.admin.ingredients import IngredientHelper

class Test(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.users = []
        self.users.append(User())
        self.users[0].name = 'Foo Bar'
        self.users[0].put()

        self.langs = []
        self.langs.append(Language())
        self.langs[0].name = 'English'
        self.langs[0].code = 'en'
        self.langs[0].put()
        self.langs.append(Language())
        self.langs[1].name = 'Danish'
        self.langs[1].code = 'da'
        self.langs[1].put()
        self.langs.append(Language())
        self.langs[2].name = 'Default (INCI)'
        self.langs[2].code = 'nc'
        self.langs[2].put()

        self.label_names = []
        self.label_names.append(LabelName())
        self.label_names[0].name = 'Vand'
        self.label_names[0].language = self.langs[1].key
        self.label_names[0].put()
        self.label_names.append(LabelName())
        self.label_names[1].name = 'Water'
        self.label_names[1].language = self.langs[0].key
        self.label_names[1].put()
        self.label_names.append(LabelName())
        self.label_names[2].name = 'Aqua'
        self.label_names[2].language = self.langs[2].key
        self.label_names[2].put()

        self.wiki_links = []
        self.wiki_links.append(IngredientWikiLink())
        self.wiki_links[0].ingredient = None
        self.wiki_links[0].link = 'http://en.wikipedia.org/wiki/water'
        self.wiki_links[0].is_valid = True
        self.wiki_links[0].creator = None
        self.wiki_links[0].language = None
        self.wiki_links[0].put()
        self.wiki_links.append(IngredientWikiLink())
        self.wiki_links[1].ingredient = None
        self.wiki_links[1].link = 'http://da.wikipedia.org/wiki/vand'
        self.wiki_links[1].is_valid = True
        self.wiki_links[1].creator = None
        self.wiki_links[1].language = None
        self.wiki_links[1].put()

        self.ingredients = []
        self.ingredients.append(Ingredient())
        self.ingredients[0].put()

    def tearDown(self):
        self.testbed.deactivate()

    def testGetIngredientsWhenIngredientHasNoNamesAndWikiLinks(self):
        ings = IngredientHelper.get_ingredients(self.products[0])
        self.assertEqual(1, len(ings))

        msg = ings[0]
        self.assertEqual('UNKNOWN', msg.name)
        self.assertEqual('or', msg.language.code)
        self.assertEqual(None, msg.wiki_link.key)

    def testGetIngredientsWhenIngredientHasINCINameAndNoWikiLinks(self):
        self.ingredients[0].inci_names = ['BUTAN']
        self.ingredients[0].put()

        ings = ProductHelper.get_ingredients(self.products[0])
        self.assertEqual(1, len(ings))

        msg = ings[0]
        self.assertEqual('BUTAN', msg.name)
        self.assertEqual('nc', msg.language.code)
        self.assertEqual(None, msg.wiki_link.key)

    def testGetIngredientsWhenIngredientHasENumberWithINCINameAndNoWikiLinks(self):
        self.ingredients[0].e_numbers = ['E042']
        self.ingredients[0].inci_names = ['Foo']
        self.ingredients[0].put()

        ings = ProductHelper.get_ingredients(self.products[0])
        self.assertEqual(1, len(ings))

        msg = ings[0]
        self.assertEqual('(Foo) E042', msg.name)
        self.assertEqual('nc', msg.language.code)
        self.assertEqual(None, msg.wiki_link.key)

    def testGetIngredientsWhenIngredientHasENumberWithLabelNameAndNoWikiLinks(self):
        self.ingredients[0].e_numbers = ['E042']
        self.ingredients[0].put()

        self.ing_ln.append(IngredientLabelName())
        self.ing_ln[0].ingredient = self.ingredients[0].key
        self.ing_ln[0].label_name = self.label_names[0].key
        self.ing_ln[0].put()

        ings = ProductHelper.get_ingredients(self.products[0])
        self.assertEqual(1, len(ings))

        msg = ings[0]
        self.assertEqual('(Vand) E042', msg.name)
        self.assertEqual('da', msg.language.code)
        self.assertEqual(None, msg.wiki_link.key)

    def testGetIngredientsWhenIngredientHasENumberWithoutAnyNameAndWikiLink(self):
        self.ingredients[0].e_numbers = ['E042']
        self.ingredients[0].put()

        ings = ProductHelper.get_ingredients(self.products[0])
        self.assertEqual(1, len(ings))

        msg = ings[0]
        self.assertEqual('E042', msg.name)
        self.assertEqual('en', msg.language.code)
        self.assertEqual(None, msg.wiki_link.key)

    def testGetIngredientsWhenIngredientHasOneLabelNameAndNoWikiLinks(self):
        self.ing_ln.append(IngredientLabelName())
        self.ing_ln[0].ingredient = self.ingredients[0].key
        self.ing_ln[0].label_name = self.label_names[0].key
        self.ing_ln[0].put()

        ings = ProductHelper.get_ingredients(self.products[0])
        self.assertEqual(1, len(ings))

        msg = ings[0]
        self.assertEqual('Vand', msg.name)
        self.assertEqual('da', msg.language.code)
        self.assertEqual(None, msg.wiki_link.key)

    def testGetIngredientsWhenIngredientHasOneLabelNameAndCorrespondingWikiLink(self):
        self.ing_ln.append(IngredientLabelName())
        self.ing_ln[0].ingredient = self.ingredients[0].key
        self.ing_ln[0].label_name = self.label_names[0].key
        self.ing_ln[0].put()

        self.wiki_links[1].ingredient = self.ingredients[0].key
        self.wiki_links[1].language = self.langs[1].key
        self.wiki_links[1].put()

        ings = ProductHelper.get_ingredients(self.products[0])
        self.assertEqual(1, len(ings))

        msg = ings[0]
        self.assertEqual('Vand', msg.name)
        self.assertEqual('da', msg.language.code)
        self.assertTrue(msg.wiki_link.is_valid)
        self.assertEqual(self.wiki_links[1].link, msg.wiki_link.url)

    def testGetIngredientsWhenIngredientHasOneLabelNameAndOneWikiLink(self):
        self.ing_ln.append(IngredientLabelName())
        self.ing_ln[0].ingredient = self.ingredients[0].key
        self.ing_ln[0].label_name = self.label_names[0].key
        self.ing_ln[0].put()

        self.wiki_links[0].ingredient = self.ingredients[0].key
        self.wiki_links[0].language = self.langs[0].key
        self.wiki_links[0].put()

        ings = ProductHelper.get_ingredients(self.products[0])
        self.assertEqual(1, len(ings))

        msg = ings[0]
        self.assertEqual('Vand', msg.name)
        self.assertEqual('da', msg.language.code)
        self.assertEqual(None, msg.wiki_link.is_valid)
        self.assertEqual(None, msg.wiki_link.url)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
