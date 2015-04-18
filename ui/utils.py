'''
Created on 01/10/2013

@author: Ismail Faizi
'''

from common import AuthorizedPage
from google.appengine.ext import blobstore
from zipfile import ZipFile
from helpers.importers import HazardsImporter
from helpers.importers import IngredientsImporter
from google.appengine.ext.webapp import blobstore_handlers
from helpers.uploadhandler import UploadHandler
from models import User, UserRole
from models import Product
from models import Image
from models import ImageType
from models import Ingredient
from models import ProductIngredient
from google.appengine.api import users
from models.uac import Role

class UtilsPage(AuthorizedPage):
    ACTION_HAZARD = 'hazards'
    ACTION_INGREDIENT = 'ingredients'
    ACTION_PRODUCT = 'products'
    ACTION_ADMIN = 'admin'

    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'utils.html', request, response)

    def handleGetRequest(self):
        self.addCommon()
        self.setActivePage('Utilities')

    def handlePostRequest(self):
        action = self.request.get('action', None)
        data = None
        try:
            if action != self.ACTION_ADMIN:
                data = self.request.POST['data']
        except KeyError:
            self.addMessage('You must upload a file.')
        else:
            if action == self.ACTION_HAZARD:
                key = blobstore.parse_blob_info(data)
                zfile = ZipFile(blobstore.BlobReader(key), 'r')
                reader = HazardsImporter(zfile)
                if reader.read():
                    self.addMessage('The operation was successful.', self.MSG_TYPE_SUCCESS)
                else:
                    self.addMessage('<strong>Error</strong>: %s' % reader.error)
                key.delete()

            if action == self.ACTION_INGREDIENT:
                key = blobstore.parse_blob_info(data)
                user = User.load(users.get_current_user())
                if not user:
                    user = User.system_user()

                reader = IngredientsImporter(blobstore.BlobReader(key), user)
                if reader.read():
                    self.addMessage('The operation was successful.', self.MSG_TYPE_SUCCESS)
                else:
                    self.addMessage('<strong>Error</strong>: %s' % reader.error)
                key.delete()

            if action == self.ACTION_ADMIN:
                email = self.request.get('email')
                user = User.find_by_email(email)
                if not user:
                    user = User.create_by_email(email)

                admin_role = Role.get_admin_role()

                UserRole.create(user, admin_role)

                self.addMessage('The admin "%s" was successfully added.' % email,
                                self.MSG_TYPE_SUCCESS)

        self.addCommon()
        self.setActivePage('Utilities')

    def addCommon(self):
        self.addTemplateValue('hazards_form', blobstore.create_upload_url('/utils'))
        self.addTemplateValue('ingredients_form', blobstore.create_upload_url('/utils'))
        self.addTemplateValue('products_form', blobstore.create_upload_url(success_path='/utils/product',
                                                                           gs_bucket_name=UploadHandler.get_gs_bucket_for_images()))

class TestProductCreationHandler(blobstore_handlers.BlobstoreUploadHandler):

    PRODUCT_BARCODE = '000000000000'
    PRODUCT_NAME = 'Test Product'

    def post(self):
        # get the info about the uploaded images
        upload_files_front = self.get_file_infos('front_image')
        upload_files_ing = self.get_file_infos('ingredients_image')
        if not len(upload_files_front) or not len(upload_files_ing):
            self.response.out.write('Images not uploaded')
            return

        front_image = upload_files_front[0]
        ingredients_image = upload_files_ing[0]

        # check whether the image has been uploaded
        if not front_image.gs_object_name or not ingredients_image.gs_object_name:
            self.response.out.write('Image info not found. Seems to be upload error!')
            return

        ingredients = self.request.get('ingredients')
        if not ingredients:
            self.response.out.write('You must provide a list of ingredients for the product to be created.')
            return

        user = User.load(users.get_current_user())

        product = Product.create_by_barcode(self.PRODUCT_BARCODE, user)
        product.name = self.PRODUCT_NAME
        product.put()

        Image.create(creator=user,
                     product=product,
                     blob=blobstore.create_gs_key(front_image.gs_object_name),
                     image_type=ImageType.Front,
                     ocr_result='',
                     featured=True)

        Image.create(creator=user,
                     product=product,
                     blob=blobstore.create_gs_key(ingredients_image.gs_object_name),
                     image_type=ImageType.Ingredient,
                     ocr_result=ingredients,
                     featured=False)

        for ingredient_name in ingredients.splitlines():
            ingredient = Ingredient.find_by_name(ingredient_name)
            if ingredient:
                ProductIngredient.add_entry(product, ingredient, user)

        self.redirect('/utils')
