'''
Created on 12/05/2014

@author: Ismail Faizi
'''
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import blobstore
import json
from models import Image, Product, User, ProductState
from helpers.ocr import OCRServiceInterface

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):

    GS_BUCKET_NAME = 'aware-backend.appspot.com'
    GS_BUCKET_FOLDER = 'images'

    def options(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Headers'] = 'X-Request, X-Requested-With'
        self.response.headers['Allow'] = 'POST, OPTIONS'

    def post(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Content-Type'] = 'json/application'

        # get and check the request data
        product = None  # @UnusedVariable
        user = None  # @UnusedVariable
        img_type = self.request.get('type')
        featured = False

        # get and check the provided product
        product = Product.get_by_urlsafe_key(self.request.get('productKey'))
        if not product:
            data = {'error': 'Invalid product!'}
            self.response.out.write(json.dumps(data))
            return

        # get and check the provided user
        user = User.get_by_urlsafe_key(self.request.get('userKey'))
        if not user:
            data = {'error': 'Invalid user!'}
            self.response.out.write(json.dumps(data))
            return

        # cast the type of featured to Boolean
        if self.request.get('featured') == 'true':
            featured = True

        # get the info about the uploaded image
        upload_files = self.get_file_infos('image')  # self.get_uploads('image')
        if not len(upload_files):
            data = {'error': 'Image not uploaded!'}
            self.response.out.write(json.dumps(data))
            return
        file_info = upload_files[0]

        # check whether the image has been uploaded
        if not file_info.gs_object_name:
            data = {'error': 'Image info not found. Seems to be upload error!'}
            self.response.out.write(json.dumps(data))
            return

        # create the blob_key to be stored in the datastore
        blob_key = blobstore.create_gs_key(file_info.gs_object_name)

        # create the image
        image = Image.create(
                    creator=user,
                    product=product,
                    blob=blob_key,
                    image_type=img_type,
                    featured=featured)

        # Get the text from the image if it is an ingredient image
        if img_type == 'ingredient':
            OCRServiceInterface.ocr_analyze(image)
            product.change_state(ProductState.OcrProcessing)

        # respond
        data = {'key': image.key.urlsafe(),
                'url': image.get_serving_url()}
        self.response.out.write(json.dumps(data))

    @classmethod
    def get_gs_bucket_for_images(cls):
        return cls.GS_BUCKET_NAME + '/' + cls.GS_BUCKET_FOLDER + '/'

    @classmethod
    def create_upload_urls(cls, amount=1):
        if amount == 1:
            return blobstore.create_upload_url(success_path='/upload',
                                               gs_bucket_name=cls.get_gs_bucket_for_images())

        urls = []
        for i in range(amount):  # @UnusedVariable
            urls.append(blobstore.create_upload_url(success_path='/upload',
                                                    gs_bucket_name=cls.get_gs_bucket_for_images()))
        return urls
