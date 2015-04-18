'''
Created on 20/03/2014

@author: Ismail Faizi
'''
import endpoints  # @UnresolvedImport @UnusedImport
from protorpc import messages, message_types
from protorpc import remote
from api.common import aWareInternalAPI
from models import Product, ProductState, ImageType, User, ProductCategory, \
    PhysicalLocation, Price, Manufacturer, Specification, ProductSpecUnit, \
    Scanning
from google.appengine.api import images  # @UnusedImport
from models.i18n import CurrencyUnit, Unit
from helpers.engines import UnitConversionEngine
from helpers.uploadhandler import UploadHandler
import datetime

'''
### MESSAGES ###
'''
class ProductInitialData(messages.Message):
    barcode = messages.StringField(1, required=True)
    creator = messages.StringField(2, required=True)
    name = messages.StringField(3)
    category = messages.StringField(4)
    manufacturer = messages.StringField(5)
    wrong_product = messages.StringField(6)

class ProductCreated(messages.Message):
    key = messages.StringField(1, required=True)
    uploadURLs = messages.StringField(2, repeated=True)

class BarcodeRequest(messages.Message):
    barcode = messages.StringField(1, required=True)
    user = messages.StringField(2, required=True)

class ProductImage(messages.Message):

    class ImageType(messages.Enum):
        INGREDIENTS = 1
        FRONT = 2

    url = messages.StringField(1)
    type = messages.EnumField(ImageType, 2, default='INGREDIENTS')
    featured = messages.BooleanField(3)

class HazardStatement(messages.Message):
    key = messages.StringField(1)
    statement = messages.StringField(2)

class HazardousIngredient(messages.Message):
    ingredient = messages.StringField(1)
    statements = messages.MessageField(HazardStatement, 2, repeated=True)

class Hazard(messages.Message):
    name = messages.StringField(1)
    image = messages.StringField(2)
    title = messages.StringField(3)
    description = messages.StringField(4)

class ProductHazardProfile(messages.Message):

    class ProfileUpdate(messages.Enum):
        ADD = 1
        DEL = 2
        BOTH = 3
        NONE = 4

    count = messages.IntegerField(1)
    hazard = messages.MessageField(Hazard, 2)
    ingredients = messages.MessageField(HazardousIngredient, 3, repeated=True)
    updates = messages.EnumField(ProfileUpdate, 4, default='NONE')
    delta = messages.StringField(5, repeated=True)
    order = messages.IntegerField(6)

class UnitMessage(messages.Message):
    key = messages.StringField(1)
    value = messages.StringField(2)

class ProductSpecification(messages.Message):
    key = messages.StringField(1)
    name = messages.StringField(2)
    units = messages.MessageField(UnitMessage, 3, repeated=True)
    value = messages.StringField(4)
    valueUnit = messages.StringField(5)

class ProductRequest(messages.Message):
    product = messages.StringField(1, required=True)
    user = messages.StringField(2, required=True)

class ProductResponse(messages.Message):

    class State(messages.Enum):
        OCR_PROCESSING= 0
        USER_CREATED = 1
        ACCEPTED = 2
        HAZARD_OK = 3
        INGREDIENTS_COMPLETED = 4
        COMPLETE = 5

    key = messages.StringField(1, required=True)
    barcode = messages.StringField(2, required=True)
    name = messages.StringField(3)
    manufacturer = messages.StringField(4)
    category = messages.StringField(5)
    price = messages.FloatField(6)
    state = messages.EnumField(State, 7, default='USER_CREATED')
    images = messages.MessageField(ProductImage, 8, repeated=True)
    hazards = messages.MessageField(ProductHazardProfile, 9, repeated=True)
    specs = messages.MessageField(ProductSpecification, 10, repeated=True)

class ProductCollection(messages.Message):
    items = messages.MessageField(ProductResponse, 1, repeated=True)

class InappropriateRequest(messages.Message):
    productKey = messages.StringField(1, required=True)
    userKey = messages.StringField(2, required=True)

class PysicalLocationRequest(messages.Message):
    lat = messages.StringField(1, required=True)
    lon = messages.StringField(2, required=True)

class ProductPriceUpdate(messages.Message):
    value = messages.StringField(1, required=True)
    currencyKey = messages.StringField(2, required=True)
    location = messages.MessageField(PysicalLocationRequest, 3)

class ProductSpecUpdate(messages.Message):
    key = messages.StringField(1, required=True)
    value = messages.StringField(2, required=True)
    unit = messages.StringField(3)

class ProductUpdateRequest(messages.Message):
    productKey = messages.StringField(1, required=True)
    userKey = messages.StringField(2, required=True)
    name = messages.StringField(3)
    manufacturer = messages.StringField(4)
    category = messages.StringField(5)
    price = messages.MessageField(ProductPriceUpdate, 6)
    specs = messages.MessageField(ProductSpecUpdate, 7, repeated=True)

class ProductUpdatedCollection(messages.Message):
    user_key = messages.StringField(1, required=True)
    last_updated = messages.StringField(2)
    products = messages.StringField(3, repeated=True)
    
class ProductImagesUploadUrlsResponse(messages.Message):
    urls = messages.StringField(1, repeated=True)

'''
### END of MESSAGES ###

'''
@aWareInternalAPI.api_class(resource_name='products',
                            path='products')
class Products(remote.Service):
    '''
    The API for all aWare products
    '''

    @endpoints.method(ProductInitialData,
                      ProductCreated,
                      http_method='GET',
                      path='create',
                      name='create')
    def create_product(self, request):
        '''
        Create a product based on a barcode
        '''
        user = User.get_by_urlsafe_key(request.creator)

        if not user:
            message = 'No user with the key "%s" exists.' % request.creator
            raise endpoints.NotFoundException(message)

        product = Product.create_by_barcode(request.barcode, user)

        # if there is a wrong-product-report, register it
        if request.wrong_product:
            wrong_product = Product.get_by_urlsafe_key(request.wrong_product)

            if not wrong_product:
                message = 'No product with the key "%s" exists.' % request.wrong_product
                raise endpoints.NotFoundException(message)

            wrong_product.mark_wrong(user, product)

        return ProductCreated(key=product.key.urlsafe(),
                              uploadURLs=UploadHandler.create_upload_urls(4))

    @endpoints.method(ProductUpdateRequest,
                      message_types.VoidMessage,
                      name='update',
                      path='update',
                      http_method='POST')
    def update_product(self, request):
        '''
        Update a product
        '''
        product = Product.get_by_urlsafe_key(request.productKey)
        if not product:
            message = 'No product with the key "%s" exists.' % request.productKey
            raise endpoints.NotFoundException(message)

        user = User.get_by_urlsafe_key(request.userKey)
        if not user:
            message = 'No user with the key "%s" exists.' % request.userKey
            raise endpoints.NotFoundException(message)

        category = None
        if request.category:
            category = ProductCategory.get_by_urlsafe_key(request.category)

        price = None
        if request.price:
            price = request.price

            currency = CurrencyUnit.get_by_urlsafe_key(price.currencyKey)

            location = None
            if price.location:
                location = PhysicalLocation.load(lat=price.location.lat,
                                                 lon=price.location.lon)

            price = Price.create(user=user,
                                 value=price.value,
                                 currency=currency,
                                 location=location)

        manufacturer = None
        if request.manufacturer:
            manufacturer = Manufacturer.load(name=request.manufacturer,
                                             user=user)

        specs = []
        if request.specs:
            for spec in request.specs:
                specification = Specification.get_by_urlsafe_key(spec.key)
                unit = Unit.get_by_urlsafe_key(spec.unit)
                specs.append([specification, spec.value, unit])

        product.update(user=user,
                       name=request.name,
                       category=category,
                       manufacturer=manufacturer,
                       price=price,
                       specs=specs
                       )

        return message_types.VoidMessage()

    @endpoints.method(BarcodeRequest,
                      ProductCollection,
                      http_method='GET',
                      path='scan',
                      name='scan')
    def scan_product(self, request):
        '''
        Retrieve a product based on a barcode (scanning the product)
        '''
        # lookup product by barcode
        products = Product.lookup_barcode(request.barcode)

        # retrieve the user
        user = User.get_by_urlsafe_key(request.user)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user
            raise endpoints.NotFoundException(message)

        # register this request as a scanning
        Scanning.create(request.barcode, products, user)

        # build and return the response
        return ProductHelper.create_collection(products, user)

    @endpoints.method(ProductRequest,
                      ProductResponse,
                      http_method='GET',
                      path='product',
                      name='product')
    def get_product(self, request):
        '''
        Retrieve a product based on its datastore key
        '''
        # retrieve the product
        product = Product.get_by_urlsafe_key(request.product)
        if not product:
            message = 'No product with the key "%s" exists.' % request.product

        # retrieve the user
        user = User.get_by_urlsafe_key(request.user)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user
            raise endpoints.NotFoundException(message)

        # build and return the response
        return ProductHelper.create_product(product, user)

    @endpoints.method(InappropriateRequest,
                      message_types.VoidMessage,
                      http_method='GET',
                      path='inappropriate',
                      name='inappropriate')
    def mark_inappropriate(self, request):
        '''
        Mark a product as having inappropriate content
        '''
        # retrieve the requested product
        product = Product.get_by_urlsafe_key(request.productKey)
        if not product:
            message = 'No product with the key "%s" exists.' % request.productKey
            raise endpoints.NotFoundException(message)

        # retrieve the user
        user = User.get_by_urlsafe_key(request.userKey)
        if not user:
            message = 'No user with the key "%s" exists.' % request.userKey
            raise endpoints.NotFoundException(message)

        # mark product as having inappropriate content
        product.mark_inapproriate(user)

        return message_types.VoidMessage()

    @endpoints.method(ProductUpdatedCollection,
                      ProductCollection,
                      http_method='POST',
                      path='updated',
                      name='updated')
    def is_updated(self, request):
        '''
        Find out whether the given list of items are in sync
        '''
        # retrieve the user
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        last_updated = None
        try:
            last_updated = datetime.datetime.strptime(request.last_updated,
                                                      '%Y-%m-%d %H:%M:%S')
        except:
            raise endpoints.BadRequestException('You have probably provided a wrong date time, the format is: yyyy-mm-dd HH:MM:SS, e.g. 2014-09-21 00:03:20')

        products = []
        for item in request.products:
            product = Product.get_by_urlsafe_key(item)

            if product.modified > last_updated:
                products.append(product)

        # build and return the response
        return ProductHelper.create_collection(products, user)
    
    @endpoints.method(message_types.VoidMessage,
                     ProductImagesUploadUrlsResponse,
                     http_method='GET',
                     path='images/urls/upload',
                     name='images.urls.upload')
    def get_images_upload_urls(self, request):
        '''
        Retrieve a list of upload URLs in order to upload product images
        '''
        return ProductImagesUploadUrlsResponse(urls=UploadHandler.create_upload_urls(4))


class ProductHelper():

    @classmethod
    def get_state(cls, entity):
        if entity.state == ProductState.OcrProcessing:
            return ProductResponse.State.OCR_PROCESSING
        if entity.state == ProductState.UserCreated:
            return ProductResponse.State.USER_CREATED
        if entity.state == ProductState.Accepted:
            return ProductResponse.State.ACCEPTED
        if entity.state == ProductState.Complete:
            return ProductResponse.State.COMPLETE
        if entity.state == ProductState.HazardOK:
            return ProductResponse.State.HAZARD_OK
        if entity.state == ProductState.IngredientsCompleted:
            return ProductResponse.State.INGREDIENTS_COMPLETED
        return None

    @classmethod
    def get_image_type(cls, img):
        if img.type == ImageType.Ingredient:
            return ProductImage.ImageType.INGREDIENTS
        if img.type == ImageType.Front:
            return ProductImage.ImageType.FRONT

    @classmethod
    def get_images(cls, entity):
        images = []
        for img in entity.get_images():
            images.append(ProductImage(url=img.get_serving_url(),
                                       type=cls.get_image_type(img),
                                       featured=img.featured))
        return images

    @classmethod
    def get_hazards(cls, entity, user):
        hazards = []
        profile = entity.get_profile()
        for hazard in profile.get_hazards():
            # create the hazard message
            h = Hazard()
            h.name = hazard.get_pictogram().name
            h.image = "/images?kind=pictogram&ID=" + hazard.get_pictogram().key.urlsafe()
            h.title = hazard.get_pictogram().title
            h.description = hazard.get_pictogram().description

            # build the profile
            hazardProfile = ProductHazardProfile()
            hazardProfile.count = hazard.get_count()
            hazardProfile.hazard = h
            hazardProfile.ingredients = []
            hazardProfile.order = hazard.get_pictogram().order

            # create the ingredient message
            for ingredient in hazard.get_ingredients():
                ing = HazardousIngredient()
                ing.ingredient = ingredient.get_name()
                ing.statements = []
                for statement in ingredient.getHStatements():
                    stmt = statement.hstatement.get()
                    hazardStatement = HazardStatement()
                    hazardStatement.key = stmt.key.urlsafe()
                    hazardStatement.statement = stmt.statement
                    ing.statements.append(hazardStatement)
                hazardProfile.ingredients.append(ing)

            # finalize the profile
            hazardProfile.updates = ProductHazardProfile.ProfileUpdate.NONE
            hazardProfile.delta = []

            if user:
                addedIngs = entity.get_added_ingredients(user.last_visit)
                if len(addedIngs):
                    hazardProfile.updates = ProductHazardProfile.ProfileUpdate.ADD
                    hazardProfile.delta.append("+" + len(addedIngs))

                delIngs = entity.get_deleted_ingredients(user.last_visit)
                if len(delIngs):
                    if len(hazardProfile.delta):
                        hazardProfile.updates = ProductHazardProfile.ProfileUpdate.BOTH
                    else:
                        hazardProfile.updates = ProductHazardProfile.ProfileUpdate.DEL
                    hazardProfile.delta.append("-" + len(addedIngs))

            # add the profile to the list
            hazards.append(hazardProfile)
        return hazards

    @classmethod
    def get_specs(cls, entity, user):
        specifications = []

        # get product specs
        specs = entity.get_specifications()
        for spec in specs:
            msg = ProductSpecification()
            # set the datastore key
            msg.key = spec.key.urlsafe()
            # set name of the spec
            msg.name = spec.name
            # set units of the spec
            msg.units = []
            for unit in spec.units:
                unit_msg = UnitMessage()
                unit_msg.key = unit.key.urlsafe()
                unit_msg.value = unit.get().to_string()
                msg.units.append(unit_msg)
            # set value of spec
            spec_value = spec.get_value()
            if spec_value:
                msg.value = spec_value.value
                # load user customization here
                custom_unit = ProductSpecUnit.get(product=entity,
                                                  user=user,
                                                  spec=spec_value)
                if custom_unit:
                    msg.valueUnit = custom_unit.value.get().to_string()
                    # convert the specification value to above unit
                    try:
                        msg.value = UnitConversionEngine.convert(fromUnit=spec_value.unit,
                                                                 toUnit=custom_unit.value,
                                                                 quantity=spec_value.value)
                    except:
                        msg.valueUnit = spec_value.unit.get().to_string()
                else:
                    msg.valueUnit = spec_value.unit.get().to_string()

        return specifications

    @classmethod
    def create_product(cls, entity, user):
        product = ProductResponse()
        product.key = entity.key.urlsafe()
        product.barcode = entity.barcode
        product.name = entity.name
        product.category = entity.get_category().name

        if entity.manufacturer:
            product.manufacturer = entity.manufacturer.get().name
        else:
            product.manufacturer = ''

        product.price = entity.avg_price()
        product.state = cls.get_state(entity)
        product.images = cls.get_images(entity)
        product.hazards = cls.get_hazards(entity, user)
        product.specs = cls.get_specs(entity, user)

        return product

    @classmethod
    def create_collection(cls, pList, user):
        collection = ProductCollection()
        for p in pList:
            collection.items.append(cls.create_product(p, user))
        return collection
