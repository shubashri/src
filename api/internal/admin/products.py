'''
Created on 20/03/2014

@author: Ismail Faizi
'''
import endpoints  # @UnresolvedImport @UnusedImport
from protorpc import messages, message_types
from protorpc import remote
from api.common import aWareInternalAPI
from models import Product, ProductState, ImageType, User, Image, \
    ProductEditor, ProductName, ProductCategoryMapping, ProductCategory, \
    Ingredient, LabelName, IngredientLabelName, IngredientWikiLink, \
    ProductIngredient, PRODUCT_KEY
from google.appengine.api import images  # @UnusedImport
from google.appengine.datastore.datastore_query import Cursor
from api.internal.admin import UserResponse, OAuthInfo, LanguageResponse,\
    AdminUtils
from models.i18n import Language

'''
### MESSAGES ###
'''
class ProductSorting(messages.Message):

    class SortEnum(messages.Enum):
        CREATED = 1
        SCANS = 2
        NAME = 3

    sort_by = messages.EnumField(SortEnum, 1, default='NAME')
    desc = messages.IntegerField(2, default=0)

class ProductFilter(messages.Message):

    class FilterEnum(messages.Enum):
        INAPPROPRIATE_CONTENT = 1
        STATE = 2
        PUBLISHED = 3

    filter_by = messages.EnumField(FilterEnum, 1)
    value = messages.IntegerField(2)

class ProductListRequest(messages.Message):
    cursor = messages.StringField(1)
    size = messages.IntegerField(2, default=10)
    orders = messages.MessageField(ProductSorting, 3, repeated=True)
    filters = messages.MessageField(ProductFilter, 4, repeated=True)
    user_key = messages.StringField(5, required=True)

class ProductImage(messages.Message):

    class ImageType(messages.Enum):
        INGREDIENTS = 1
        FRONT = 2

    image_key = messages.StringField(1)
    url = messages.StringField(2)
    type = messages.EnumField(ImageType, 3, default='INGREDIENTS')
    featured = messages.BooleanField(4)
    creator = messages.MessageField(UserResponse, 5)
    ocr_result = messages.StringField(6)


class IngredientWikiLinkMessage(messages.Message):
    key = messages.StringField(1)
    is_valid = messages.BooleanField(2)
    url = messages.StringField(3)


class ProductIngredientMessage(messages.Message):
    ingredient_key = messages.StringField(1, required=True)
    name = messages.StringField(2)
    wiki_link = messages.MessageField(IngredientWikiLinkMessage, 3)
    language = messages.MessageField(LanguageResponse, 4)


class ProductNameMessage(messages.Message):
    name_key = messages.StringField(1)
    value = messages.StringField(2)
    creator = messages.MessageField(UserResponse, 3)
    is_default = messages.BooleanField(4, default=False)


class ProductCategoryMessage(messages.Message):
    category_key = messages.StringField(1)
    name = messages.StringField(2)
    creator = messages.MessageField(UserResponse, 3)


class ProductResponse(messages.Message):

    class State(messages.Enum):
        OCR_PROCESSING = 0
        USER_CREATED = 1
        ACCEPTED = 2
        HAZARD_OK = 3
        INGREDIENTS_COMPLETED = 4
        COMPLETE = 5

    key = messages.StringField(1, required=True)
    barcode = messages.StringField(2, required=True)
    names = messages.MessageField(ProductNameMessage, 3, repeated=True)
    created = messages.StringField(4)
    category = messages.MessageField(ProductCategoryMessage, 5)
    state = messages.EnumField(State, 6, default='USER_CREATED')
    images = messages.MessageField(ProductImage, 7, repeated=True)
    scans = messages.IntegerField(8)
    creator = messages.MessageField(UserResponse, 9)
    published = messages.BooleanField(10)
    ingredients = messages.MessageField(ProductIngredientMessage, 11, repeated=True)
    inappropriate = messages.BooleanField(12)
    wrong_product_reports = messages.IntegerField(13)
    content_reports = messages.IntegerField(14)


class ProductCollection(messages.Message):
    products = messages.MessageField(ProductResponse, 1, repeated=True)
    cursor = messages.StringField(2)
    more = messages.BooleanField(3)


class DefaultImageRequest(messages.Message):
    product_key = messages.StringField(1)
    user_key = messages.StringField(2)
    image_key = messages.StringField(3)


class DefaultNameRequest(messages.Message):
    product_key = messages.StringField(1)
    user_key = messages.StringField(2)
    name_key = messages.StringField(3)


class ChangeCategoryRequest(messages.Message):
    product_key = messages.StringField(1)
    user_key = messages.StringField(2)
    category_key = messages.StringField(3)


class PublishingRequest(messages.Message):
    products = messages.StringField(1, repeated=True)
    user_key = messages.StringField(2)


class NewWikiLinkMessage(messages.Message):
    link = messages.StringField(1, required=True)
    is_valid = messages.BooleanField(2, default=False)


class NewIngredientMessage(messages.Message):
    label_name = messages.StringField(1, required=True)
    language = messages.StringField(2, required=True)


class MapIngredientRequest(messages.Message):
    user_key = messages.StringField(1, required=True)
    product_key = messages.StringField(2, required=True)
    ingredient_key = messages.StringField(3, required=True)


class AddIngredientRequest(messages.Message):
    user_key = messages.StringField(1, required=True)
    product_key = messages.StringField(2, required=True)
    ingredient = messages.MessageField(NewIngredientMessage, 3, required=True)


class DatastoreKeyResponse(messages.Message):
    key = messages.StringField(1)


class AddWikiLinkRequest(messages.Message):
    user_key = messages.StringField(1, required=True)
    ingredient_key = messages.StringField(2, required=True)
    language = messages.StringField(3, required=True)
    wiki_link = messages.MessageField(NewWikiLinkMessage, 4, required=True)


class LockProductRequest(messages.Message):
    user_key = messages.StringField(1, required=True)
    product_key = messages.StringField(2, required=True)


class LockProductResponse(messages.Message):
    locked = messages.BooleanField(1, required=True)


class UnlockProductRequest(messages.Message):
    product_key = messages.StringField(1, required=True)
'''
### END of MESSAGES ###

'''


@aWareInternalAPI.api_class(resource_name='admin.products',
                            path='admin/products',
                            allowed_client_ids=OAuthInfo.CLIENT_IDS,
                            scopes=OAuthInfo.SCOPES,
                            audiences=OAuthInfo.AUDIENCES)
class AdminProducts(remote.Service):
    '''
    The aWare products API for aWare administrator interface
    '''

    @endpoints.method(ProductListRequest,
                      ProductCollection,
                      http_method='GET',
                      path='list',
                      name='list')
    def get_product_list(self, request):
        '''
        Retrieve a list of products based on the request
        '''
        # retrieve the user
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        # get size of the list to return
        size = request.size

        # get the cursor for paging if given
        cursor = None
        if request.cursor:
            cursor = Cursor(urlsafe=request.cursor)

        # build the query
        query = Product.query(ancestor=PRODUCT_KEY)

        # filter the result
        if request.filters:
            for _filter in request.filters:
                # filter the product list by products marked as having inappropriate content
                if _filter.filter_by == ProductFilter.FilterEnum.INAPPROPRIATE_CONTENT:
                    val = False
                    if _filter.value == 1:
                        val = True
                    query = query.filter(Product.inappropriate == val)
                # filter the product list by product status
                if _filter.filter_by == ProductFilter.FilterEnum.STATE:
                    val = _filter.value
                    if not val in ProductState.list_of_numbers():
                        message = 'Unknown product state "%d".' % val
                        raise endpoints.NotFoundException(message)
                    query = query.filter(Product.state == val)
                # filter the product list by whether product is published or not
                if _filter.filter_by == ProductFilter.FilterEnum.PUBLISHED:
                    val = True
                    if val == 0:
                        val = False
                    query = query.filter(Product.published == val)

        # order the result
        is_ordered_by_name = False
        if request.orders:
            for ordering in request.orders:
                # order by the creation date
                if ordering.sort_by == ProductSorting.SortEnum.CREATED:
                    if ordering.desc:
                        query = query.order(-Product.created)
                    else:
                        query = query.order(Product.created)
                # order by the number of scans
                if ordering.sort_by == ProductSorting.SortEnum.SCANS:
                    if ordering.desc:
                        query = query.order(-Product.scans)
                    else:
                        query = query.order(Product.scans)
                # order by the default name of the product
                if ordering.sort_by == ProductSorting.SortEnum.NAME:
                    if ordering.desc:
                        query = query.order(-Product.name)
                    else:
                        query = query.order(Product.name)
                    is_ordered_by_name = True

        # as the default ordering, always order by product default name
        if not is_ordered_by_name:
            query = query.order(Product.name)

        # fetch the products
        products = None
        next_cursor = None
        more = False
        if cursor:
            products, next_cursor, more = query.fetch_page(size, start_cursor=cursor)
        else:
            products, next_cursor, more = query.fetch_page(size, start_cursor=cursor)

        if next_cursor:
            return ProductHelper.create_collection(products, next_cursor.urlsafe(), more)

        return ProductHelper.create_collection(products)

    @endpoints.method(DefaultImageRequest,
                      message_types.VoidMessage,
                      http_method='POST',
                      path='images/default',
                      name='images.default')
    def set_default_image(self, request):
        '''
        Set a front image of a product as its default image
        '''
        # retrieve the requested product
        product = Product.get_by_urlsafe_key(request.product_key)
        if not product:
            message = 'No product with the key "%s" exists.' % request.product_key
            raise endpoints.NotFoundException(message)

        # retrieve the user
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        # retrieve the image
        image = Image.get_by_urlsafe_key(request.image_key)
        if not image:
            message = 'No image with the key "%s" exists.' % request.image_key
            raise endpoints.NotFoundException(message)

        # the image must belong to the product and it must be a front image
        if not image.is_front_image() or not product.has_image(image):
            message = 'The given image either not a front image or it does not belong to the given product.'
            raise endpoints.BadRequestException(message)

        # set the image as default (featured) image
        product.set_default_image(image)

        # register the user as editor of the product
        ProductEditor.add_or_update(product, user)

        return message_types.VoidMessage()

    @endpoints.method(DefaultNameRequest,
                      message_types.VoidMessage,
                      http_method='POST',
                      path='names/default',
                      name='names.default')
    def set_default_name(self, request):
        '''
        Set one of the names of a product as its default name
        '''
        # retrieve the requested product
        product = Product.get_by_urlsafe_key(request.product_key)
        if not product:
            message = 'No product with the key "%s" exists.' % request.product_key
            raise endpoints.NotFoundException(message)

        # retrieve the user
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        # retrieve the name
        name = ProductName.get_by_urlsafe_key(request.name_key)
        if not name:
            message = 'No product name with the key "%s" exists.' % request.name_key
            raise endpoints.NotFoundException(message)

        # the name must belong to the given product
        if not product.has_name(name):
            message = 'The given name does not belong to the given product.'
            raise endpoints.BadRequestException(message)

        # set the name as the default name
        product.name = name.value
        product.put()

        # register the user as editor of the product
        ProductEditor.add_or_update(product, user)

        return message_types.VoidMessage()

    @endpoints.method(ChangeCategoryRequest,
                      message_types.VoidMessage,
                      http_method='POST',
                      path='category/change',
                      name='category.change')
    def change_category(self, request):
        '''
        Change the category of a product
        '''
        # retrieve the requested product
        product = Product.get_by_urlsafe_key(request.product_key)
        if not product:
            message = 'No product with the key "%s" exists.' % request.product_key
            raise endpoints.NotFoundException(message)

        # retrieve the user
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        # retrieve the category
        category = ProductCategory.get_by_urlsafe_key(request.category_key)
        if not category:
            message = 'No category with the key "%s" exists.' % request.category_key
            raise endpoints.NotFoundException(message)

        # remove the product from the old category
        old_category = product.get_category()
        old_mapping = ProductCategoryMapping.load(product, old_category)
        if old_mapping:
            old_mapping.key.delete()

        # set the product under the given category
        ProductCategoryMapping.load(product, category, user)

        # register the user as editor of the product
        ProductEditor.add_or_update(product, user)

        return message_types.VoidMessage()

    @endpoints.method(PublishingRequest,
                      message_types.VoidMessage,
                      http_method='POST',
                      path='unpublish',
                      name='unpublish')
    def unpublish(self, request):
        '''
        Unpublish the given products
        '''
        # retrieve the requested products
        products = []
        for p_key in request.products:
            product = Product.get_by_urlsafe_key(p_key)
            if not product:
                message = 'No product with the key "%s" exists.' % request.p_key
                raise endpoints.NotFoundException(message)
            products.append(product)

        # retrieve the user
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        # unpublish the given products
        for product in products:
            product.unpublish()
            # register the user as editor of the product
            ProductEditor.add_or_update(product, user)

        return message_types.VoidMessage()

    @endpoints.method(PublishingRequest,
                      message_types.VoidMessage,
                      http_method='POST',
                      path='publish',
                      name='publish')
    def publish(self, request):
        '''
        Publish the given products
        '''
        # retrieve the requested products
        products = []
        for p_key in request.products:
            product = Product.get_by_urlsafe_key(p_key)
            if not product:
                message = 'No product with the key "%s" exists.' % request.p_key
                raise endpoints.NotFoundException(message)
            products.append(product)

        # retrieve the user
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        # unpublish the given products
        for product in products:
            product.publish()
            # register the user as editor of the product
            ProductEditor.add_or_update(product, user)

        return message_types.VoidMessage()

    @endpoints.method(MapIngredientRequest,
                      DatastoreKeyResponse,
                      http_method='POST',
                      path='ingredients/map',
                      name='ingredients.map')
    def map_ingredient(self, request):
        '''
        Map an existing ingredient to a product
        '''
        # retrieve the requested product
        product = Product.get_by_urlsafe_key(request.product_key)
        if not product:
            message = 'No product with the key "%s" exists.' % request.product_key
            raise endpoints.NotFoundException(message)

        # retrieve the user
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        # retrieve the ingredient
        ingredient = Ingredient.get_by_urlsafe_key(request.ingredient_key)
        if not ingredient:
            message = 'No ingredient with the key "%s" exists.' % request.ingredient_key
            raise endpoints.NotFoundException(message)

        # create the mapping
        mapping = ProductIngredient.add_entry(product, ingredient, user)

        return DatastoreKeyResponse(key=mapping.key.urlsafe())

    @endpoints.method(AddIngredientRequest,
                      DatastoreKeyResponse,
                      http_method='POST',
                      path='ingredients/add',
                      name='ingredients.add')
    def add_ingredient(self, request):
        '''
        Add a new ingredient to a product
        '''
        # retrieve the requested product
        product = Product.get_by_urlsafe_key(request.product_key)
        if not product:
            message = 'No product with the key "%s" exists.' % request.product_key
            raise endpoints.NotFoundException(message)

        # retrieve the user
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        # retrieve the language
        language = Language.find_by_code(request.ingredient.language)
        if not language:
            language = Language.get_unknown()

        # find or create the label name that is requested
        is_new = True
        name = request.ingredient.label_name
        label_name = None
        if LabelName.exists(name):
            label_name = LabelName.find_by_name(name)
            is_new = False
        else:
            label_name = LabelName.create(name, language, user)

        # find or create the ingredient. If it is a new ingredient, we first
        # create it and then map it to the label name
        ingredient = None
        if is_new:
            if language.is_default():
                ingredient = Ingredient.create(user, name)
            else:
                ingredient = Ingredient.create(user)
            IngredientLabelName.create(ingredient, label_name, user)
        else:
            ingredient = IngredientLabelName.find_by_label_name(label_name).ingredient.get()

        # create a mapping for the ingredient and the product
        mapping = ProductIngredient.add_entry(product, ingredient, user)

        return DatastoreKeyResponse(key=mapping.key.urlsafe())

    @endpoints.method(AddWikiLinkRequest,
                      DatastoreKeyResponse,
                      http_method='POST',
                      path='ingredients/wikilink/add',
                      name='ingredients.wikiLink.add')
    def add_ingredient_wiki_link(self, request):
        '''
        Add a Wikipedia link to an ingredient of a product
        '''
        # retrieve the user
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        # retrieve the ingredient
        ingredient = Ingredient.get_by_urlsafe_key(request.ingredient_key)
        if not ingredient:
            message = 'No ingredient with the key "%s" exists.' % request.ingredient_key
            raise endpoints.NotFoundException(message)

        # retrieve the language
        language = Language.find_by_code(request.language)
        if not language:
            language = Language.get_unknown()

        link = request.wiki_link.link
        is_valid = request.wiki_link.is_valid
        wiki_link = None
        if IngredientWikiLink.exists(ingredient, language):
            wiki_link = IngredientWikiLink.find_by_ingredient_and_language(ingredient, language)
            wiki_link.link = link
            wiki_link.is_valid = is_valid
            wiki_link.put()
        else:
            wiki_link = IngredientWikiLink.create(ingredient, link, language, user, is_valid)

        return DatastoreKeyResponse(key=wiki_link.key.urlsafe())

    @endpoints.method(LockProductRequest,
                      LockProductResponse,
                      http_method='POST',
                      path='lock',
                      name='lock')
    def lock(self, request):
        '''
        Acquire mutual exclusion for a specific user for a given product
        '''
        # retrieve the requested product
        product = Product.get_by_urlsafe_key(request.product_key)
        if not product:
            message = 'No product with the key "%s" exists.' % request.product_key
            raise endpoints.NotFoundException(message)

        # retrieve the user
        user = User.get_by_urlsafe_key(request.user_key)
        if not user:
            message = 'No user with the key "%s" exists.' % request.user_key
            raise endpoints.NotFoundException(message)

        if product.lock(user):
            return LockProductResponse(locked=True)

        return LockProductResponse(locked=False)

    @endpoints.method(UnlockProductRequest,
                      message_types.VoidMessage,
                      http_method='POST',
                      path='unlock',
                      name='unlock')
    def unlock(self, request):
        '''
        Release the mutual exclusion on the given product
        '''
        # retrieve the requested product
        product = Product.get_by_urlsafe_key(request.product_key)
        if not product:
            message = 'No product with the key "%s" exists.' % request.product_key
            raise endpoints.NotFoundException(message)

        product.unlock()

        return message_types.VoidMessage()


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
            user = img.creator.get()

            creator = UserResponse(user_key=user.key.urlsafe())

            images.append(ProductImage(image_key=img.key.urlsafe(),
                                       url=img.get_serving_url(),
                                       type=cls.get_image_type(img),
                                       featured=img.featured,
                                       creator=creator,
                                       ocr_result=img.ocr_result))

        return images

    @classmethod
    def get_ingredients(cls, entity):
        ingredients = []

        for ingredient in entity.get_ingredients():
            lang, name = AdminUtils.calc_ingredient_name(ingredient)

            language = LanguageResponse()
            language.language_key = lang.key.urlsafe()
            language.name = lang.name
            language.code = lang.code

            wiki_link_msg = IngredientWikiLinkMessage()
            wiki_link = IngredientWikiLink.find_by_ingredient_and_language(ingredient, lang)
            if wiki_link:
                wiki_link_msg.key = wiki_link.key.urlsafe()
                wiki_link_msg.is_valid = wiki_link.is_valid
                wiki_link_msg.url = wiki_link.link

            msg = ProductIngredientMessage()
            msg.ingredient_key = ingredient.key.urlsafe()
            msg.name = name
            msg.wiki_link = wiki_link_msg
            msg.language = language
            ingredients.append(msg)

        return ingredients

    @classmethod
    def get_product_category(cls, entity):
        category = entity.get_category()
        mapping = ProductCategoryMapping.load(entity, category, User.system_user())

        msg = ProductCategoryMessage()
        msg.category_key = category.key.urlsafe()
        msg.name = category.name
        msg.creator = UserResponse()
        msg.creator.user_key = mapping.creator.urlsafe()

        return msg

    @classmethod
    def get_product_creator(cls, entity):
        user = entity.creator.get()

        msg = UserResponse()
        msg.user_key = user.key.urlsafe()

        return msg

    @classmethod
    def create_product(cls, entity):
        product = ProductResponse()
        product.key = entity.key.urlsafe()
        product.barcode = entity.barcode
        product.names = cls.get_product_names(entity)
        product.category = cls.get_product_category(entity)
        product.created = entity.created.strftime("%Y-%m-%d %H:%M:%S")
        product.creator = cls.get_product_creator(entity)
        product.state = cls.get_state(entity)
        product.images = cls.get_images(entity)
        product.scans = entity.scans
        product.ingredients = cls.get_ingredients(entity)
        product.published = entity.published
        product.inappropriate = entity.inappropriate
        product.wrong_product_reports = entity.wrong_product_reports
        product.content_reports = entity.inappropriate_reports

        return product

    @classmethod
    def create_collection(cls, products, cursor='', more=False):
        collection = ProductCollection()
        collection.cursor = cursor
        collection.more = more

        for p in products:
            collection.products.append(cls.create_product(p))

        return collection
