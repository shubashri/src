'''
Created on 19/07/2014

@author: Ismail Faizi
'''
import re
from models import User, INGREDIENT_HSTATEMENT_KEY, CLASSIFICATION_KEY
from models import Product
from models import Image
from models import ImageType
from models import Ingredient
from models import HStatement
from models import HReference
from models import IngredientHStatement
from models import Pictogram
from models import Class
from models import Classification
from models import ClassCategory
from google.appengine.api import users, blobstore, urlfetch
from helpers.uploadhandler import UploadHandler
import time
import urllib
import os
import tempfile

class IngredientsImporter():
    ING_IN_COL_DELIMITER = '#'
    ING_COL_DELIMITER = ';'
    ING_COL_COUNT = 7
    ING_COL_ID = 0
    ING_COL_INCI = 1
    ING_COL_CAS = 2
    ING_COL_EC = 3
    ING_COL_IUPAC = 4
    ING_COL_ALIAS = 5
    ING_COL_E = 6

    h_references = []
    total_cols = 0
    csv_file = None
    error = ''

    def __init__(self, csv_file, user):
        self.csv_file = csv_file
        self.user = user

    def read(self):
        if self.csv_file is None:
            raise AttributeError('No file has been provided!')

        success = True
        i = 0
        for line in self.csv_file:
            i = i + 1
            if line.strip():
                if not self.parse_line(line):
                    self.error = self.error + ': on line %d' % i
                    success = False
                    break

        return success

    def parse_line(self, line):
        columns = line.split(self.ING_COL_DELIMITER)

        # Check to see whether we have anything to work with
        if columns[self.ING_COL_ID] == '':
            return True  # Skip empty lines

        # Set total columns number if not set
        # and get the H-Reference IDs
        if self.total_cols == 0:
            self.total_cols = len(columns)
            h_cols_count = self.total_cols - self.ING_COL_COUNT
            if h_cols_count <= 0:
                self.error = 'Number of columns are fewer then expected, must at least be %d' % (self.ING_COL_COUNT + 1)
                return False
            else:
                for col_number in range(self.ING_COL_COUNT, (self.ING_COL_COUNT + h_cols_count)):
                    hreference_id = columns[col_number].strip()
                    if hreference_id != '':
                        self.h_references.append(hreference_id)

                # First line is not further read
                return True

        # Check columns count
        if len(columns) != self.total_cols:
            self.error = 'Number of columns are not consistent, expected %d columns but got %d' % (self.total_cols, len(columns))
            return False

        # Retrieve/Create the ingredient
        ID = int(columns[self.ING_COL_ID].strip())
        if ID > 0:
            ing = Ingredient.load(ID)
        else:
            self.error = 'The ID must be a positive integer instead got %d' % ID
            return False

        # INCI Names
        if columns[self.ING_COL_INCI].strip() != '':
            inci_names = columns[self.ING_COL_INCI].strip().split(self.ING_IN_COL_DELIMITER)
            for name in inci_names:
                name = name.strip().lower()
                if name != '' and name not in ing.inci_names:
                    ing.inci_names.append(name)

        # CAS Numbers
        if columns[self.ING_COL_CAS].strip() != '':
            cas_numbers = columns[self.ING_COL_CAS].strip().split(self.ING_IN_COL_DELIMITER)
            for number in cas_numbers:
                number = number.strip()
                if number != '' and number not in ing.cas_numbers:
                    ing.cas_numbers.append(number)

        # EC Numbers
        if columns[self.ING_COL_EC].strip() != '':
            ec_numbers = columns[self.ING_COL_EC].strip().split(self.ING_IN_COL_DELIMITER)
            for number in ec_numbers:
                number = number.strip()
                if number != '' and number not in ing.ec_numbers:
                    ing.ec_numbers.append(number)

        # IUPAC Names
        if columns[self.ING_COL_IUPAC].strip() != '':
            iupac_names = columns[self.ING_COL_IUPAC].strip().split(self.ING_IN_COL_DELIMITER)
            for name in iupac_names:
                name = name.strip().lower()
                if name != '' and name not in ing.iupac_names:
                    ing.iupac_names.append(name)

        # Aliases
        if columns[self.ING_COL_ALIAS].strip() != '':
            aliases = columns[self.ING_COL_ALIAS].strip().split(self.ING_IN_COL_DELIMITER)
            for alias in aliases:
                alias = alias.strip().lower()
                if alias != '' and alias not in ing.aliases:
                    ing.aliases.append(alias)

        # E Numbers
        if columns[self.ING_COL_E].strip() != '':
            e_numbers = columns[self.ING_COL_E].strip().split(self.ING_IN_COL_DELIMITER)
            for e_no in e_numbers:
                e_no = e_no.strip()
                if e_no != '' and e_no not in ing.e_numbers:
                    ing.e_numbers.append(e_no)

        h_cols_count = self.total_cols - self.ING_COL_COUNT
        ref_idx = 0
        for col_number in range(self.ING_COL_COUNT, (self.ING_COL_COUNT + h_cols_count)):
            if ref_idx >= len(self.h_references):
                continue

            if not self.parse_hstatements(columns[col_number].strip(), ing, self.h_references[ref_idx]):
                return False
            ref_idx = ref_idx + 1

        ing.creator = self.user.key
        ing.put()

        return True

    def parse_hstatements(self, column, ingredient, reference):
        hcodes = column.split(self.ING_IN_COL_DELIMITER)
        for hcode in hcodes:
            hstatement = HStatement.load(hcode.strip())
            hreference = HReference.get(reference)
            if not hreference:
                self.error = "HReference with ID '%s' does not exists" % reference
                return False
            if not IngredientHStatement.exists(ingredient.key, hstatement.key, hreference.key):
                ih = IngredientHStatement(parent=INGREDIENT_HSTATEMENT_KEY,
                                          ingredient=ingredient.key,
                                          hstatement=hstatement.key,
                                          hreference=hreference.key)
                ih.put()

        return True


class HazardsImporter():
    HAZARDS_FILE_NAME = 'hazards.txt'
    HAZARDS_PICTOGRAM_TYPE = '.png'
    HAZARDS_DELIMITER = '#'
    HAZARDS_CAT_PREFIX = ['category', 'additional category']
    HAZARDS_COL_COUNT = 6
    HAZARDS_COL_CODE = 0
    HAZARDS_COL_HSTATEMENT = 1
    HAZARDS_COL_CLASS = 2
    HAZARDS_COL_CATEGORY = 3
    HAZARDS_COL_SIGNALWORD = 4
    HAZARDS_COL_PICTOGRAM = 5

    def __init__(self, zip_file):
        self.zip_file = zip_file
        self.error = ''

    def read(self):
        if self.zip_file is None:
            raise AttributeError('No zip-file has been provided!')

        hazards = None
        try:
            hazards = self.zip_file.read(self.HAZARDS_FILE_NAME)
        except KeyError:
            self.error = 'Did not find <b>%s</b> in zip-file.' % self.HAZARDS_FILE_NAME
            return False
        else:
            success = True
            i = 0
            lines = hazards.split('\n')
            for line in lines:
                i = i + 1
                if line.strip():
                    if not self.parse_line(line):
                        self.error = self.error + ': on line %d' % i
                        success = False
                        break

            return success

    def parse_line(self, line):
        columns = line.split(self.HAZARDS_DELIMITER)

        # Check columns count
        if len(columns) != self.HAZARDS_COL_COUNT:
            self.error = 'Number of columns must be %d' % self.HAZARDS_COL_COUNT
            return False

        # Clean columns
        temp = []
        for col in columns:
            temp.append(col.strip())
        columns = temp

        # Check signal word
        if not HStatement.is_signal_word(columns[self.HAZARDS_COL_SIGNALWORD]):
            self.error = "'%s' is not a signal word!" % columns[self.HAZARDS_COL_SIGNALWORD]
            return False

        pictogram_names = columns[self.HAZARDS_COL_PICTOGRAM].strip()
        for pic_name in pictogram_names.split(','):
            pic_name = pic_name.strip()
            image_name = pic_name + self.HAZARDS_PICTOGRAM_TYPE
            image = None
            try:
                image = self.zip_file.read(image_name)
            except KeyError:
                self.error = 'Did not find <b>%s</b> in zip-file.' % image_name
                return False
            else:
                # Parse Pictogram
                pic = Pictogram.load(pic_name, image)

                # Parse H-Statement
                hstatement = HStatement.load(columns[self.HAZARDS_COL_CODE])
                hstatement.statement = columns[self.HAZARDS_COL_HSTATEMENT]
                hstatement.set_signal_word(columns[self.HAZARDS_COL_SIGNALWORD])

                # Parse Class
                cls = Class.laod(columns[self.HAZARDS_COL_CLASS])
                cls.pictogram = pic.key

                # Parse Category (can be a list)
                cats = self.parse_category(columns[self.HAZARDS_COL_CATEGORY])
                if cats:
                    for cat in cats:
                        c = Classification(parent=CLASSIFICATION_KEY,
                                           clazz=cls.key,
                                           category=cat.key,
                                           hstatement=hstatement.key)
                        c.put()
                        cat.put()
                else:
                    self.error = "Category '%s' could not be understood." % columns[self.HAZARDS_COL_CATEGORY]
                    return False

                # Store all the entities now where everything is fine
                pic.put()
                hstatement.put()
                cls.put()

        return True

    def parse_category(self, column):
        if not column:
            raise AttributeError('No category to parse: %s' % column)

        cats = []
        cat_names = column.strip().split(',')

        if len(cat_names) > 1:
            prefix = ''
            for pfx in self.HAZARDS_CAT_PREFIX:
                idx = column.lower().find(pfx)
                if idx != -1:
                    prefix = pfx.capitalize()
                    break
            first = True
            for cat_name in cat_names:
                if first:
                    cats.append(ClassCategory.load(cat_name.strip()))
                    first = False
                else:
                    cats.append(ClassCategory.load(prefix + cat_name))
        else:
            cats.append(ClassCategory.load(column.strip()))

        return cats
