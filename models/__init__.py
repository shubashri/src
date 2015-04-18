'''
Created on 20/04/2014

@author: Ismail Faizi
'''
from google.appengine.ext import ndb
from helpers import IngredientsFinder
from helpers import HazardProfile, Hazard
from google.appengine.api import images
import datetime
from models.history import ProductHistory, ProductAction
from models.i18n import Unit, CurrencyUnit, Language
from models.uac import Role, Permission
import os

APPLICATION_ID = os.environ['APPLICATION_ID']

CLASS_CATEGORY_KEY = ndb.Key("ClassCategory", 'root', app=APPLICATION_ID)
CLASSIFICATION_KEY = ndb.Key("Classification", 'root', app=APPLICATION_ID)
CLASS_KEY = ndb.Key("Class", 'root', app=APPLICATION_ID)
HELP_TOPIC_KEY = ndb.Key("HelpTopic", 'root', app=APPLICATION_ID)
HREFERENCE_KEY = ndb.Key("HReference", 'root', app=APPLICATION_ID)
HSTATEMENT_KEY = ndb.Key("HStatement", 'root', app=APPLICATION_ID)
IMAGE_KEY = ndb.Key("Image", 'root', app=APPLICATION_ID)
INGREDIENT_KEY = ndb.Key("Ingredient", 'root', app=APPLICATION_ID)
INGREDIENT_HSTATEMENT_KEY = ndb.Key("IngredientHStatement", 'root', app=APPLICATION_ID)
MANUFACTURER_KEY = ndb.Key("Manufacturer", 'root', app=APPLICATION_ID)
NOTIFICATION_KEY = ndb.Key("Notification", 'root', app=APPLICATION_ID)
PICTOGRAM_KEY = ndb.Key("Pictogram", 'root', app=APPLICATION_ID)
PRICE_KEY = ndb.Key("Price", 'root', app=APPLICATION_ID)
PRODUCT_KEY = ndb.Key("Product", 'root', app=APPLICATION_ID)
PRODUCT_CATEGORY_KEY = ndb.Key("ProductCategory", 'root', app=APPLICATION_ID)
SCANNING_KEY = ndb.Key("Scanning", 'root', app=APPLICATION_ID)
SPECIFICATION_VALUE_KEY = ndb.Key("SpecificationValue", 'root', app=APPLICATION_ID)
USER_KEY = ndb.Key("User", 'root', app=APPLICATION_ID)
INGREDIENT_WIKI_LINK_KEY = ndb.Key("IngredientWikiLink", 'root', app=APPLICATION_ID)


class AbstractModel(ndb.Model):

    @classmethod
    def get_by_urlsafe_key(cls, urlsafe_key):
        try:
            key = ndb.Key(urlsafe=urlsafe_key)
            return key.get()
        except:
            pass  # Just ignore it
        return None

class Lockable(ndb.Model):
    lock_owner = ndb.KeyProperty(kind='User')
    locked = ndb.BooleanProperty(default=False)
    locked_at = ndb.DateTimeProperty()

    def lock(self, user):
        if self.locked and self.owner != user.key:
            return False

        self.lock_owner = user.key
        self.locked = True
        self.locked_at = datetime.datetime.now()
        self.put()

        return True

    def unlock(self):
        self.lock_owner = None
        self.locked = False
        self.put()

        return True

class ClassCategory(ndb.Model):
    title = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)

    def getClassifications(self):
        q = Classification.gql("WHERE category = :1", self.key)
        return q.fetch()

    @classmethod
    def load(cls, catTitle):
        q = cls.gql("WHERE title = :1", catTitle)
        c = q.get()
        if c is None:
            c = ClassCategory(parent=CLASS_CATEGORY_KEY, title=catTitle)
            c.put()
        return c

class Classification(ndb.Model):
    clazz = ndb.KeyProperty(kind='Class')
    category = ndb.KeyProperty(kind='ClassCategory')
    hstatement = ndb.KeyProperty(kind='HStatement')
    created = ndb.DateTimeProperty(auto_now_add=True)

class Class(ndb.Model):
    name = ndb.StringProperty()
    pictogram = ndb.KeyProperty(kind='Pictogram')
    created = ndb.DateTimeProperty(auto_now_add=True)

    def getClassifications(self):
        q = Classification.gql("WHERE clazz = :1", self.key)
        return q.fetch()

    @classmethod
    def laod(cls, className):
        q = cls.gql("WHERE name = :1", className)
        c = q.get()
        if c is None:
            c = Class(parent=CLASS_KEY, name=className)
            c.put()
        return c

class HelpTopic(ndb.Model):
    title = ndb.StringProperty()
    description = ndb.TextProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty()

    def toJSON(self):
        return {'title': self.title, 'description': self.description}

    @classmethod
    def toJSONTitles(cls):
        q = cls.query(ancestor=HELP_TOPIC_KEY)
        titles = []
        for topic in q.fetch():
            titles.append({'key': topic.key.urlsafe(), 'title': topic.title})
        return titles


    @classmethod
    def get_all(cls):
        topics = cls.query(ancestor=HELP_TOPIC_KEY).order(-cls.created)
        return topics.fetch()

class HReference(ndb.Model):
    ID = ndb.StringProperty()
    name = ndb.StringProperty()
    source = ndb.StringProperty()

    @classmethod
    def get(cls, ID):
        return cls.gql('WHERE ID = :1', ID).get()

    @classmethod
    def exists(cls, ID):
        q = cls.gql('WHERE ID = :1', ID)
        ref = q.get()
        if ref is None:
            return False
        return True

class SignalWord():
    Danger = 1
    Warning = 2

    @classmethod
    def list_of_numbers(cls):
        return [1, 2]

    @classmethod
    def default(cls):
        return cls.Warning

class HStatement(ndb.Model):
    code = ndb.StringProperty()
    statement = ndb.StringProperty()
    signalWord = ndb.IntegerProperty(choices=SignalWord.list_of_numbers())
    created = ndb.DateTimeProperty(auto_now_add=True)
    # Deprecated
    SW_DANGER = 1
    SW_WARNING = 2
    SW_WORDS = ['danger', 'warning']

    def getSignalWord(self):
        return self.SW_WORDS[self.signalWord - 1].capitalize()

    def set_signal_word(self, word):
        if self.is_signal_word(word):
            self.signalWord = self.SW_WORDS.index(word.lower()) + 1
            return True
        else:
            return False

    def getClassifications(self):
        return Classification.gql("WHERE hstatement = :1", self.key).fetch()

    @classmethod
    def load(cls, code):
        q = cls.gql('WHERE code = :1', code)
        statement = q.get()
        if statement is None:
            statement = HStatement(parent=HSTATEMENT_KEY,
                                   code=code,
                                   signalWord=cls.SW_WARNING)
            statement.put()
        return statement

    @classmethod
    def is_signal_word(cls, word=''):
        return word.lower() in cls.SW_WORDS

class ImageType():
    Unknown = 0
    Ingredient = 1
    Front = 2

    @classmethod
    def list_of_numbers(cls):
        return [0, 1, 2]

    @classmethod
    def default(cls):
        return cls.Unknown

    @classmethod
    def get_from_string(cls, type_name):
        if type_name.lower() == 'ingredients' or type_name.lower() == 'ingredient':
            return cls.Ingredient
        if type_name.lower == 'front':
            return cls.Front
        return cls.Unknown

class Image(AbstractModel):
    created = ndb.DateTimeProperty(auto_now_add=True)
    creator = ndb.KeyProperty(kind='User')
    product = ndb.KeyProperty(kind='Product')
    blob = ndb.StringProperty()
    ocr_result = ndb.TextProperty()
    type = ndb.IntegerProperty(choices=ImageType.list_of_numbers(), default=ImageType.default())
    featured = ndb.BooleanProperty(default=False)

    def read(self):
        if len(self.ocr_result) and type == ImageType.Ingredient:
            ocrReadings = self.ocr_result.lower()
            reader = IngredientsFinder(ocrReadings)
            ingredients = Ingredient.query(ancestor=INGREDIENT_KEY).fetch()
            for ingredient in ingredients:
                for name in ingredient.inci_names:
                    if reader.contains(name.lower()):
                        if not ProductIngredient.exists(self.product, ingredient.key):
                            pi = ProductIngredient(product=self.product,
                                                   ingredient=ingredient.key,
                                                   state=ProductIngredient.STATE_OK)
                            pi.put()

    def get_serving_url(self, size=0):
        return images.get_serving_url(self.blob, size)

    def is_front_image(self):
        return self.type == ImageType.Front

    @classmethod
    def create(cls, creator, product, blob, image_type, ocr_result='', featured=False):
        img = Image(parent=IMAGE_KEY)
        img.creator = creator.key
        img.product = product.key
        img.blob = blob

        # determine the type of the image
        if isinstance(image_type, basestring):
            img.type = ImageType.get_from_string(image_type)
        else:
            img.type = image_type

        img.ocr_result = ocr_result
        img.featured = featured
        img.put()
        return img

class Ingredient(AbstractModel):
    ID = ndb.IntegerProperty()
    cas_numbers = ndb.StringProperty(repeated=True)
    has_cas_number = ndb.BooleanProperty(default=True)
    ec_numbers = ndb.StringProperty(repeated=True)
    has_ec_number = ndb.BooleanProperty(default=True)
    inci_names = ndb.StringProperty(repeated=True)
    has_inci_name = ndb.BooleanProperty(default=True)
    iupac_names = ndb.StringProperty(repeated=True)
    has_iupac_name = ndb.BooleanProperty(default=True)
    e_numbers = ndb.StringProperty(repeated=True)
    has_e_number = ndb.BooleanProperty(default=True)
    aliases = ndb.StringProperty(repeated=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    wiki_links = ndb.IntegerProperty(default=0)
    creator = ndb.KeyProperty(kind='User')

    def get_name(self):
        for name in self.inci_names:
            if name and len(name) > 0:
                return name
        for name in self.iupac_names:
            if name and len(name) > 0:
                return name
        for name in self.aliases:
            if name and len(name):
                return name

    def getHStatements(self):
        return IngredientHStatement.gql('WHERE ingredient = :1', self.key)

    def hasClass(self):
        return len(self.getClasses().fetch()) > 0

    def classList(self):
        l = []
        for cls in self.getClasses().fetch():
            l.append(cls.classification.get().name)
        return ', '.join(l)

    def increment_wiki_links(self):
        self.wiki_links += 1
        self.put()

    def get_profile(self):
        profile = HazardProfile()
        pictograms = {}
        statements = self.getHStatements().fetch()
        for statement in statements:
            classifications = statement.hstatement.get().getClassifications()
            for classification in classifications:
                clazz = classification.clazz.get()
                pictogram = clazz.pictogram.get()
                if not pictograms.has_key(pictogram.name):
                    pictograms[pictogram.name] = Hazard(pictogram)
                else:
                    pictograms[pictogram.name].increment_count()
        for hazard in pictograms.itervalues():
            profile.add_hazard(hazard)
        return profile

    def get_label_name(self):
        mappings = IngredientLabelName.gql("WHERE ingredient = :1", self.key).fetch()
        if not len(mappings):
            return None

        language = Language.get_by_code('en')
        for mapping in mappings:
            label_name = mapping.label_name.get()
            if language.key == label_name.language:
                return label_name

        return mappings[0].label_name.get()

    @classmethod
    def load(cls, ID):
        i = cls.gql("WHERE ID = :1", ID).get()
        if i is None:
            i = Ingredient(parent=INGREDIENT_KEY)
            i.ID = ID
            i.cas_numbers = []
            i.ec_numbers = []
            i.inci_names = []
            i.iupac_names = []
            i.aliases = []
            i.e_numbers = []

            i.put()

        return i

    @classmethod
    def find_by_name(cls, name):
        name = name.lower()
        q = cls.query(ndb.OR(cls.inci_names == name,
                             ndb.OR(cls.iupac_names == name, cls.aliases == name)))
        return q.get()

	def find_by_e_number(cls,name):
		e_number = cls.query(ndb.OR(cls.e_numbers))
		return e_number.get()
	
    @classmethod
    def create(cls, user, inci_name=None):
        i = Ingredient(parent=INGREDIENT_KEY)
        i.cas_numbers = []
        i.ec_numbers = []
        i.inci_names = []
        i.iupac_names = []
        i.aliases = []
        i.e_numbers = []
        i.creator = user.key

        if inci_name:
            i.inci_names.append(inci_name)

        i.put()

        return i


class IngredientHStatement(ndb.Model):
    ingredient = ndb.KeyProperty(kind=Ingredient)
    hstatement = ndb.KeyProperty(kind=HStatement)
    hreference = ndb.KeyProperty(kind=HReference)

    @classmethod
    def exists(cls, i_key, s_key, r_key):
        q = cls.gql('WHERE ingredient = :1 AND hstatement = :2 AND hreference = :3',
                    i_key, s_key, r_key)
        ih = q.get()
        if ih is None:
            return False
        return True


class IngredientWikiLink(ndb.Model):
    ingredient = ndb.KeyProperty(kind='Ingredient')
    link = ndb.StringProperty()
    language = ndb.KeyProperty(kind=Language)
    creator = ndb.KeyProperty(kind="User")
    is_valid = ndb.BooleanProperty(default=False)

    @classmethod
    def create(cls, ingredient, link, language, creator, is_valid=False):
        entity = IngredientWikiLink()

        entity.ingredient = ingredient.key
        entity.link = link
        entity.language = language.key
        entity.creator = creator.key
        entity.is_valid = is_valid

        entity.put()

        ingredient.increment_wiki_links()

        return entity

    @classmethod
    def exists(cls, ingredient, language):
        return None != cls.gql("WHERE ingredient = :1 AND language = :2", ingredient.key, language.key).get()

    @classmethod
    def find_by_ingredient_and_language(cls, ingredient, language):
        return cls.gql("WHERE ingredient = :1 AND language = :2", ingredient.key, language.key).get()

class LabelName(ndb.Model):
    name = ndb.StringProperty()
    language = ndb.KeyProperty(kind='Language')
    creator = ndb.KeyProperty(kind='User')
    created = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def create(cls, name, language, user):
        if not name or not language or not user:
            raise ValueError('Please provide both ingredient, language, user and the label name.')

        ln = LabelName()
        ln.name = name
        ln.language = language.key
        ln.creator = user.key

        ln.put()
        return ln

    @classmethod
    def exists(cls, name):
        return None != cls.gql("WHERE name = :1", name).get()

    @classmethod
    def find_by_name(cls, name):
        return cls.gql("WHERE name = :1", name).get()


class IngredientLabelName(ndb.Model):
    ingredient = ndb.KeyProperty(kind='Ingredient')
    label_name = ndb.KeyProperty(kind='LabelName')
    creator = ndb.KeyProperty(kind='User')
    created = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def find_by_label_name(cls, label_name):
        return cls.gql("WHERE label_name = :1", label_name.key).get()
    @classmethod
    def create(cls, ingredient, label_name, user):
        if not ingredient or not label_name or not user:
            raise ValueError('You must provide both ingredient, label name and the creator.')

        entity = IngredientLabelName()
        entity.ingredient = ingredient.key
        entity.label_name = label_name.key
        entity.creator = user.key

        entity.put()
        return entity


class Manufacturer(ndb.Model):
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)
    approved = ndb.BooleanProperty(default=False)
    creator = ndb.KeyProperty(kind='User')

    @classmethod
    def load(cls, name, user):
        m = cls.gql("WHERE name = :1 ORDER BY created DESC", name).fetch()
        if len(m):
            return m[0]

        m = Manufacturer(parent=MANUFACTURER_KEY)
        m.name = name
        m.creator = user.key
        m.put()

        return m

class Notification(ndb.Model):
    user = ndb.KeyProperty(kind='User')
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)

class ProductUpdateNotification(Notification):

    class NotificationType():
        App = 1
        Email = 2

        @classmethod
        def list_of_numbers(cls):
            return [1, 2]

        @classmethod
        def default(cls):
            return cls.App

        @classmethod
        def is_literal(cls, literal):
            return literal in cls.list_of_numbers() or literal in ['APP', 'EMAIL']

        @classmethod
        def convert_to_number(cls, literal):
            if literal == 'APP':
                return cls.App
            if literal == 'EMAIL':
                return cls.Email

            raise ValueError('The "%s" is not a literal.' % literal)

    product = ndb.KeyProperty(kind='Product')
    type = ndb.IntegerProperty(choices=NotificationType.list_of_numbers(),
                               default=NotificationType.default())

    def update_type(self, notification_type):
        if not self.NotificationType.is_literal(notification_type):
            msg = 'Notification type must be either APP (1) or EMAIL (2), "%s" was given.' % notification_type
            raise ValueError(msg)

        self.type = self.NotificationType.convert_to_number(notification_type)
        self.put()

    @classmethod
    def load(cls, user, product):
        n = cls.gql("WHERE user = :1 AND product = :2", user.key, product.key).get()
        if n:
            return n

        n = ProductUpdateNotification(parent=NOTIFICATION_KEY)
        n.user = user.key
        n.product = product.key
        n.put()
        return n

class Pictogram(AbstractModel):
    title = ndb.StringProperty()
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    image = ndb.BlobProperty()
    order = ndb.IntegerProperty(default=0)

    @classmethod
    def load(cls, name, image):
        q = cls.gql("WHERE name = :1", name)
        pic = q.get()
        if pic is None:
            pic = Pictogram(parent=PICTOGRAM_KEY,
                            name=name,
                            image=image)
            pic.put()
        return pic

    @classmethod
    def get_all(cls):
        return cls.query(ancestor=PICTOGRAM_KEY).order(cls.order).fetch()

    @classmethod
    def get_by_name(cls, name):
        return cls.gql("WHERE name = :1", name).get()

class ProductCategory(AbstractModel):
    name = ndb.StringProperty()
    creator = ndb.KeyProperty(kind='User')
    created = ndb.DateTimeProperty(auto_now_add=True)

    def get_ancestors(self):
        result = []
        p = self.parent

        while p:
            cat = p.get()
            result.append(cat)
            p = cat.parent

        return result

    def get_boxes(self):
        result = []
        mappings = BoxCategory.gql("WHERE category = :1", self.key).fetch()
        for mapping in mappings:
            try:
                result.append(mapping.box.get())
            except:
                pass  # ignore the exception for now
        return result

    @classmethod
    def get_unknown(cls):
        name = 'Other'
        cat = cls.gql("WHERE name = :1", name).get()
        if cat:
            return cat

        # we create and return one
        cat = ProductCategory(parent=PRODUCT_CATEGORY_KEY)
        cat.name = name
        cat.creator = User.system_user().key

        cat.put()
        return cat

    @classmethod
    def create(cls, name, user, parent=None):
        cat = cls.gql("WHERE name = :1", name).get()
        if cat:
            raise ValueError('A category with name "%s" already exists.' % name)

        if not parent:
            parent = PRODUCT_CATEGORY_KEY

        cat = ProductCategory(parent=parent)
        cat.name = name
        cat.creator = user.key

        cat.put()
        return cat


class ProductCategoryMapping(ndb.Model):
    product = ndb.KeyProperty(kind='Product')
    category = ndb.KeyProperty(kind='ProductCategory')
    creator = ndb.KeyProperty(kind='User')

    @classmethod
    def load(cls, product, category, user=None):
        pcm = cls.gql("WHERE product = :1 AND category = :2",
                      product.key, category.key).get()
        if pcm:
            return pcm

        pcm = ProductCategoryMapping()
        pcm.product = product.key
        pcm.category = category.key

        if user:
            pcm.creator = user.key

        pcm.put()

        return pcm

class ProductState():
    OcrProcessing = 0
    UserCreated = 1
    Accepted = 2
    HazardOK = 3
    IngredientsCompleted = 4
    Complete = 5

    @classmethod
    def list_of_numbers(cls):
        return [0, 1, 2, 3, 4, 5]

    @classmethod
    def default(cls):
        return cls.UserCreated

class Price(ndb.Model):
    value = ndb.FloatProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)
    creator = ndb.KeyProperty(kind='User')
    currency = ndb.KeyProperty(kind='CurrencyUnit', required=True)
    validFrom = ndb.DateTimeProperty()
    validUntil = ndb.DateTimeProperty()
    location = ndb.KeyProperty()

    def to_dollars(self):
        currency = self.currency.get()
        if currency.code == '$':
            return self.value
        else:
            # TODO use a service to convert from currency to USD
            pass
        return self.value


    @classmethod
    def create(cls, user, value, currency, location, validFrom=None, validUntil=None):
        if not user:
            raise ValueError("The creator of the price must be specified.")

        if not value:
            raise ValueError("Price value must be specified!")

        if not currency:
            raise ValueError("The currency of the price must be specified!")

        if not isinstance(currency, CurrencyUnit):
            raise ValueError("The currency of the price must be specified as a CurrencyUnit object.")

        if location and not isinstance(location, Location):
            raise ValueError("The location of the price must be specified as a Location object.")

        if not validFrom:
            validFrom = datetime.datetime.now()

        if not validUntil:
            delta = datetime.timedelta(days=6 * 31)  # 6 months duration
            validUntil = validFrom + delta

        if not isinstance(validFrom, datetime.datetime):
            raise ValueError("The validFrom property must be a datetime object.")

        if not isinstance(validUntil, datetime.datetime):
            raise ValueError("The validUntil property must be a datetime object.")

        price = Price(parent=PRICE_KEY)
        price.value = float(value)
        price.currency = currency.key
        price.location = location.key if location else None
        price.validFrom = validFrom if validFrom else None
        price.validUntil = validUntil if validUntil else None
        price.creator = user.key
        price.put()

        return price

class ProductApproval(ndb.Model):
    product = ndb.KeyProperty(kind='Product')
    name = ndb.BooleanProperty()
    category = ndb.BooleanProperty()
    manufacturer = ndb.BooleanProperty()

    @classmethod
    def load(cls, product):
        pa = cls.gql("WHERE product = :1", product.key).get()
        if pa:
            return pa

        pa = ProductApproval()
        pa.product = product.key
        pa.put()

        return pa


class Product(AbstractModel, Lockable):
    barcode = ndb.StringProperty(required=True)
    name = ndb.StringProperty()
    manufacturer = ndb.KeyProperty(kind='Manufacturer')
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)
    creator = ndb.KeyProperty(kind='User', required=True)
    state = ndb.IntegerProperty(choices=ProductState.list_of_numbers(),
                                default=ProductState.default())
    published = ndb.BooleanProperty(default=True)
    scans = ndb.IntegerProperty()
    inappropriate = ndb.BooleanProperty(default=False)
    inappropriate_reports = ndb.IntegerProperty(default=0)
    wrong_product_reports = ndb.IntegerProperty(default=0)
    creation_location = ndb.KeyProperty(kind='PhysicalLocation')

    def mark_inapproriate(self, user):
        report = InappropriateProductReport()
        report.product = self.key
        report.reporter = user.key
        report.put_aysnc()

        self.inappropriate = True
        self.inappropriate_reports += 1
        self.put()

    def mark_wrong(self, user, correct_product):
        report = WrongProductReport()
        report.correct_product = correct_product.key
        report.wrong_product = self.key
        report.reporter = user.key
        report.put()

        self.wrong_product_reports += 1
        self.put()

    def get_names(self):
        names = ProductName.gql("WHERE product = :1", self.key).fetch()

        if len(names) == 0:
            name = ProductName.create(self, self.creator.get(), self.name)
            names.append(name)

        return names

    def has_name(self, name):
        for n in self.get_names():
            if n.key == name.key:
                return True

        return False

    def avg_price(self):
        total = 0
        now = datetime.datetime.now()
        productPriceMappings = ProductPrice.gql("WHERE product = :1", self.key).fetch()
        for mapping in productPriceMappings:
            price = mapping.price.get()
            if price.validFrom >= now and price.validUntil <= now:
                total = total + price.to_dollars()
        if len(productPriceMappings):
            return round(total / len(productPriceMappings), 2)
        return 0.00

    def get_images(self):
        return Image.gql('WHERE product = :1', self.key).fetch()

    def has_image(self, image):
        images = self.get_images()

        for img in images:
            if image.key == img.key:
                return True

        return False

    def get_default_image(self):
        return Image.gql('WHERE product = :1 AND featured = :2', self.key, True).get()

    def set_default_image(self, image):
        current_default = self.get_default_image()
        if current_default:
            current_default.featured = False
            current_default.put()

        image.featured = True
        image.put()

    def get_added_ingredients(self, since):
        ingredients = []
        histories = ProductHistory.gql("WHERE product = :1 AND action = :2 AND created >= :3",
                                       self.key, ProductAction.AddIngredient, since).fetch()
        for history in histories:
            for ingredient in history.ingredients:
                ingredients.append(ingredient.get())

        return ingredients

    def get_deleted_ingredients(self, since):
        ingredients = []
        histories = ProductHistory.gql("WHERE product = :1 AND action = :2 AND created >= :3",
                                       self.key, ProductAction.DeleteIngredient, since).fetch()
        for history in histories:
            for ingredient in history.ingredients:
                ingredients.append(ingredient.get())

        return ingredients

    def get_specifications(self):
        specifications = []
        productSpecMappings = ProductSpec.gql("WHERE product = :1", self.key)
        for mapping in productSpecMappings.fetch():
            specifications.append(mapping.specification.get())
        return specifications

    def get_ingredients(self):
        pro_ings = ProductIngredient.gql('WHERE  = :1', self.key).fetch()

        ingredients = []
        for pi in pro_ings:
            ingredients.append(pi.ingredient.get())

        return ingredients

    def has_ingredients(self):
        return len(self.getIngredients()) > 0

    def get_category(self):
        mappings = ProductCategoryMapping.gql("WHERE product = :1", self.key).fetch()
        if len(mappings):
            return mappings[0].category.get()
        return ProductCategory.get_unknown()

    def get_categories(self):
        mappings = ProductCategoryMapping.gql("WHERE product = :1", self.key).fetch()
        if len(mappings):
            cats = []
            for mapping in mappings:
                cats.append(mapping.category.get())
            return cats
        return []

    def get_category_heirarchy(self):
        cats = []
        leafs = self.get_categories()
        for leaf in leafs:
            cats.append(leaf)
            path = leaf.get_ancestors()
            for cat in path:
                if cat not in cats:
                    cats.append(cat)
        return cats

    def get_boxes(self):
        categories = self.get_category_heirarchy()
        boxes = []
        for category in categories:
            boxes.extend(category.get_boxes())
        return boxes

    def get_spec_value(self, specification):
        ps = ProductSpec.load(self, specification)
        return SpecificationValue.get_by_product_specification(ps)

    def update(self, user, name, category, manufacturer, price, specs):
        if not isinstance(user, User):
            raise ValueError("The user argument must be of type User")

        # if not isinstance(category, ProductCategory):
        #    raise ValueError("The category argument must be of type ProductCategory")

        # if not isinstance(manufacturer, Manufacturer):
        #    raise ValueError("The manufacturer argument must be of type Manufacturer")

        # if not isinstance(specs, list):
        #    raise ValueError("The specs argument must be specified as a list.")

        updated = False
        approved = ProductApproval.load(self)

        # update product specifications
        specifications = self.get_specifications()
        for spec in specs:
            specification = spec[0]
            value = spec[1]
            unit = spec[2]

            if specification not in specifications:
                raise ValueError("One of the provided specification is not among product specifications.")

            old_value = self.get_spec_value(specification)
            if not old_value:
                ps = ProductSpec.load(self, specification)
                SpecificationValue.create(user=user,
                                          value=value,
                                          productSpec=ps,
                                          unit=unit)
                updated = True
            else:
                if old_value.approved:
                    # customize the unit
                    ProductSpecUnit.load(user=user,
                                         spec=old_value,
                                         product=self,
                                         value=unit)
                else:
                    # update the value and unit
                    if old_value.value != value or old_value.unit != unit.key:
                        old_value.value = value
                        old_value.unit = unit.key
                        old_value.put()
                        updated = True

        # update product name
        old_name = ProductName.get_by_owner(self, user)
        if old_name:
            if name != old_name.value:
                ProductName.update(self, user, name)
                updated = True
        else:
            ProductName.update(self, user, name)
            updated = True

        if (not self.name or self.name == '') and not approved.name:
            self.name = name
            updated = True

        # update product category
        if category and not approved.category:
            old_cat = ProductCategoryMapping.load(self, category, user)
            if category != old_cat.category:
                updated = True

        # update product manufacturer
        if manufacturer and not approved.manufacturer:
            if self.manufacturer != manufacturer.key:
                self.manufacturer = manufacturer.key
                updated = True

        # update product price
        if price:
            ProductPrice.load(self, price)
            updated = True

        if updated:
            ProductEditor.add_or_update(self, user)
            self.put()

        return self

    def get_profile(self):
        profile = HazardProfile()

        # Build the mapping of pictogram-name => Hazard object
        pictograms = {}
        for pic in Pictogram.get_all():
            h = Hazard(pic)
            h.decrement_count()
            pictograms[pic.name] = h

        # Aggregate all the hazard profiles of this product's
        # ingredients
        ingredients = self.get_ingredients()
        for ingredient in ingredients:
            if ingredient:
                ingHazards = ingredient.get_profile().get_hazards()
                for hazard in ingHazards:
                    pictograms[hazard.get_pictogram().name].increment_count()
                    pictograms[hazard.get_pictogram().name].add_ingredient(ingredient);

        # Build the hazard profile now
        for hazard in pictograms.itervalues():
            profile.add_hazard(hazard)
        return profile

    def increment_scans(self):
        if not self.scans:
            self.scans = 1
        else:
            self.scans += 1

        self.put()

    def publish(self):
        self.published = True
        self.put()

    def unpublish(self):
        self.published = False
        self.put()

    def change_state(self, new_state):
        if not new_state in ProductState.list_of_numbers():
            raise ValueError('The product state must be one of %s, instead %s was given.' % (ProductState.list_of_numbers(), new_state))

        if self.state == new_state:
            return

        self.state = new_state
        self.put()

    @classmethod
    def lookup_barcode(cls, barcode):
        return cls.gql('WHERE barcode = :1 AND published = :2', barcode, True).fetch()

    @classmethod
    def create_by_barcode(cls, barcode, user, location=None):
        if not user:
            msg = 'User must be provided in order to create the product.'
            raise ndb.InvalidPropertyError(msg)

        p = Product(parent=PRODUCT_KEY)
        p.barcode = barcode
        p.creator = user.key

        if location:
            p.creation_location = location.key

        p.put()

        return p

class ProductEditor(ndb.Model):
    product = ndb.KeyProperty(kind='Product')
    editor = ndb.KeyProperty(kind='User')
    count = ndb.IntegerProperty(default=1)
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def add_or_update(cls, product, user):
        pe = cls.gql("WHERE product = :1 AND editor = :2", product.key, user.key).get()

        if pe:
            pe.count = pe.count + 1
        else:
            pe = ProductEditor()
            pe.product = product.key
            pe.user = user.key

        pe.put()

class ProductIngredientState():
    OK = 1
    Flaged = 2

    @classmethod
    def list_of_numbers(cls):
        return [1, 2]

    @classmethod
    def default(cls):
        return cls.OK

class ProductIngredient(ndb.Model):
    product = ndb.KeyProperty(kind='Product')
    ingredient = ndb.KeyProperty(kind='Ingredient')
    state = ndb.IntegerProperty(choices=ProductIngredientState.list_of_numbers(),
                                default=ProductIngredientState.default())
    creator = ndb.KeyProperty(kind='User')

    @classmethod
    def exists(cls, p_key, i_key):
        q = cls.gql('WHERE product = :1 AND ingredient = :2', p_key, i_key)
        pi = q.get()
        if pi is None:
            return False

        return True

    @classmethod
    def add_entry(cls, product, ingredient, user):
        if not cls.exists(product.key, ingredient.key):
            pi = ProductIngredient()
            pi.product = product.key
            pi.ingredient = ingredient.key
            pi.creator = user.key
            pi.put()

            return pi
        else:
            return cls.gql('WHERE product = :1 AND ingredient = :2', product.key, ingredient.key).get()

class ProductPrice(ndb.Model):
    product = ndb.KeyProperty(kind='Product')
    price = ndb.KeyProperty(kind='Price')

    @classmethod
    def load(cls, product, price):
        pp = cls.gql("WHERE product = :1 AND price = :2", product.key, price.key).get()
        if pp:
            return pp

        pp = ProductPrice()
        pp.product = product.key
        pp.price = price.key
        pp.put()

        return pp


class InappropriateProductReport(ndb.Model):
    product = ndb.KeyProperty(kind='Product')
    reporter = ndb.KeyProperty(kind='User')
    created = ndb.DateTimeProperty(auto_now_add=True)


class WrongProductReport(ndb.Model):
    reporter = ndb.KeyProperty(kind='User', required=True)
    correct_product = ndb.KeyProperty(kind='Product')
    wrong_product = ndb.KeyProperty(kind='Product')
    created = ndb.DateTimeProperty(auto_now_add=True)



class Scanning(ndb.Model):
    user = ndb.KeyProperty(kind='User')
    barcode = ndb.StringProperty()
    result = ndb.KeyProperty(kind='Product', repeated=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    deleted = ndb.BooleanProperty(default=False)

    def do_delete(self):
        self.deleted = True
        self.put()

    @classmethod
    def create(cls, barcode, products, user):
        scanning = Scanning(parent=SCANNING_KEY)
        scanning.barcode = barcode
        scanning.user = user.key
        scanning.deleted = False

        result = []
        for product in products:
            result.append(product.key)
            product.increment_scans()

        scanning.result = result
        scanning.put()

        return scanning

    @classmethod
    def find(cls, user, barcode):
        return cls.gql("WHERE user = :1 AND barcode = :2", user.key, barcode).fetch()

class UserSettingKey(ndb.Model):
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    values = ndb.StringProperty(repeated=True)

    @classmethod
    def get_send_email(cls):
        name = 'SEND_EMAIL'
        setting = cls.gql("WHERE name = :1", name).get()
        if not setting:
            setting = UserSettingKey()
            setting.name = name
            setting.description = 'I agree to receive email and newsletters from aWare.'
            setting.values = ['0', '1']
            setting.put()

        return setting


class UserSetting(ndb.Model):
    setting_key = ndb.KeyProperty(kind='UserSettingKey')
    value = ndb.StringProperty()
    user = ndb.KeyProperty(kind='User')


    @classmethod
    def create_or_update(cls, user, setting, value):
        if not value in setting.values:
            raise ValueError('The given value "%s" is not a valid value among these values: %s' % (value, setting.values))

        user_setting = cls.gql("WHERE setting_key = :1 AND user = :2", setting.key, user.key).get()
        if not user_setting:
            user_setting = UserSetting()
            user_setting.setting_key = setting.key
            user_setting.user = user.key

        user_setting.value = value
        user_setting.put()

        return user_setting


class Specification(AbstractModel):
    name = ndb.StringProperty()
    units = ndb.KeyProperty(repeated=True)
    description = ndb.StringProperty()
    productCategories = ndb.KeyProperty(kind='ProductCategory', repeated=True)

    def get_value(self, product):
        mapping = ProductSpec.gql("WHERE product = :1 AND specification = :2",
                                  product.key, self.key).fetch()
        if mapping:
            # return the approved value of the specification
            value = SpecificationValue.gql("WHERE productSpec = :1 AND approved = :2",
                                           mapping.key, True).get
            if value:
                return value

            # return the newest added value of the specification
            value = SpecificationValue.gql("WHERE productSpec = :1 ORDER BY created DESC").get()
            if value:
                return value

        return None

class ProductSpec(ndb.Model):
    product = ndb.KeyProperty(kind='Product')
    specification = ndb.KeyProperty(kind='Specification')

    @classmethod
    def load(cls, product, specification):
        if not product or not isinstance(product, Product):
            raise ValueError("Product must be specified and must be an object of type Product.")

        if not specification or not isinstance(specification, Specification):
            raise ValueError("Specification must be specified and must be an object of type Specification")

        ps = cls.gql("WHERE product = :1 AND specification = :2",
                     product.key, specification.key).fetch()
        if len(ps):
            return ps[0]

        ps = ProductSpec()
        ps.product = product.key
        ps.specification = specification.key
        ps.put()

        return ps

class SpecificationValue(ndb.Model):
    value = ndb.StringProperty()
    approved = ndb.BooleanProperty(default=False)
    created = ndb.DateTimeProperty(auto_now_add=True)
    productSpec = ndb.KeyProperty(kind='ProductSpec')
    creator = ndb.KeyProperty(kind='User')
    unit = ndb.KeyProperty()

    @classmethod
    def create(cls, user, value, productSpec, unit):
        if not user or not isinstance(user, User):
            raise ValueError("User must be specified and must be an object of type User")

        if not productSpec or not isinstance(productSpec, ProductSpec):
            raise ValueError("ProductSpec must be specified and must be an object of type ProductSpec")

        if not unit or not isinstance(unit, Unit):
            raise ValueError("Unit must be specified and must be an object of type Unit")

        spec = productSpec.specification.get()
        if unit.key not in spec.units:
            raise ValueError("The specified unit must be among the units of the specification.")

        spec_val = SpecificationValue(parent=SPECIFICATION_VALUE_KEY)
        spec_val.value = value
        spec_val.creator = user.key
        spec_val.productSpec = productSpec.key
        spec_val.unit = unit.key
        spec_val.put()

        return spec_val

    @classmethod
    def get_by_product_specification(cls, ps):
        return cls.gql("WHERE productSpec = :1", ps.key).get()

class UserState():
    Default = 0
    Blocked = 1
    Activated = 2
    Quarantined = 3

    @classmethod
    def list_of_numbers(cls):
        return [0, 1, 2, 3]

    @classmethod
    def default(cls):
        return cls.Default

class User(AbstractModel):
    name = ndb.StringProperty()
    clientID = ndb.StringProperty()
    photo = ndb.BlobKeyProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    last_visit = ndb.DateTimeProperty()
    current_visit = ndb.DateTimeProperty()
    modified = ndb.DateTimeProperty(auto_now=True)
    state = ndb.IntegerProperty(choices=UserState.list_of_numbers(),
                                default=UserState.default())

    def get_settings(self):
        return UserSetting.gql("WHERE user = :1", self.key).fetch()

    def update_setting(self, setting, value):
        return UserSetting.create_or_update(self, setting, value)

    def get_scanned_products(self):
        return Scanning.gql("WHERE user = :1", self.key).fetch()

    def get_scanned_products_count(self):
        return Scanning.gql("WHERE user= :1",self.key).count()
    
    def get_added_products_count(self):
        return Product.gql("WHERE creator= :1",self.key).count()

    def get_count_for_wrong_products_added_by_user(self):
        return WrongProductReport.query().filter(WrongProductReport.wrong_product.creator == self.key).count()

    def get_count_for_wrong_products_added_by_others(self):
        return WrongProductReport.query().filter(WrongProductReport.wrong_product.creator != self.key).count()

    def get_count_for_inappropriate_content_added_by_user(self):
        return InappropriateProductReport.query().filter(InappropriateProductReport.reporter == self.key).count()

    def get_count_for_inappropriate_content_added_by_others(self):
        return InappropriateProductReport.query().filter(InappropriateProductReport.reporter != self.key).count()
    
    def update_visit_time(self):
        self.last_visit = self.current_visit
        self.current_visit = datetime.datetime.now()
        self.put()

    def upate(self, email=None, name=None):
        update = False

        if name and name != self.name:
            self.name = name
            update = True

        UserEmail.create_or_update(self, email)

        if update:
            self.put()

    def is_admin(self):
        user_role = UserRole.gql('WHERE user = :1', self.key).get()
        if user_role:
            role = user_role.role.get()

            return role.is_admin()

        return False

    def has_email(self):
        return None != UserEmail.gql("WHERE user = :1", self.key).get()

    def get_default_email(self):
        ue = UserEmail.gql("WHERE user = :1 AND is_default = :2", self.key, True).get()
        if ue:
            return ue.email

        return None

    @classmethod
    def load(cls, user):
        u = UserEmail.find_user(user.email())
        if not u:
            u = User(parent=USER_KEY)
            u.name = user.nickname()
            u.put()

            UserEmail.create_or_update(u, user.email(), True)

        return u

    @classmethod
    def client(cls, ID):
        user = cls.gql("WHERE clientID = :1", ID).get()
        if not user:
            user = User(parent=USER_KEY)
            user.clientID = ID
            user.put()

        return user

    @classmethod
    def system_user(cls):
        ID = 'ABS0000000000'
        user = cls.gql("WHERE clientID = :1", ID).get()

        if user is None:
            user = User(parent=USER_KEY)
            user.name = "aWare Backend System"
            user.clientID = ID
            user.put()

            UserEmail.create_or_update(user, 'backend.system@aWareApS.com', True, True)

        return user

    @classmethod
    def find_by_email(cls, email):
        return UserEmail.find_user(email)

    @classmethod
    def create_by_email(cls, email):
        user = User(parent=USER_KEY)
        user.put()

        UserEmail.create_or_update(user, email, True)

        return user


class UserEmail(ndb.Model):
    user = ndb.KeyProperty(kind='User')
    email = ndb.StringProperty()
    is_activated = ndb.BooleanProperty()
    is_default = ndb.BooleanProperty()
    activation_key = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def find_user(cls, email):
        ue = cls.gql("WHERE email = :1", email).get()
        if ue:
            return ue.user.get()

        return None

    @classmethod
    def create_or_update(cls, user, email, default=False, activated=False):
        ue = cls.gql("WHERE user = :1 AND email = :2", user.key, email).get()
        if not ue:
            ue = UserEmail()
            ue.user = user.key
            ue.email = email
        ue.is_activated = activated
        ue.is_default = default
        ue.put()

        if default == True:
            cls.make_default(user, email)

        return ue

    @classmethod
    def make_default(cls, user, email):
        user_emails = cls.gql("WHERE user = :1", user.key).fetch()
        for user_email in user_emails:
            if email == user_email.email:
                user_email.is_default = True
            else:
                user_email.is_default = False
            user_email.put()


class UserIP(ndb.Model):

    class IPVersion():
        IPv4 = 1
        IPv6 = 2

        @classmethod
        def list_of_numbers(cls):
            return [1, 2]

    version = ndb.IntegerProperty(choices=IPVersion.list_of_numbers())
    address = ndb.StringProperty()
    user = ndb.KeyProperty(kind=User)

class UserRole(ndb.Model):
    user = ndb.KeyProperty(kind='User')
    role = ndb.KeyProperty(kind='Role')

    @classmethod
    def exists(cls, user, role):
        return None != cls.gql("WHERE user = :1 AND role = :2", user.key, role.key).get()

    @classmethod
    def create(cls, user, role):
        if cls.exists(user, role):
            return cls.gql("WHERE user = :1 AND role = :2", user.key, role.key).get()

        ur = UserRole()
        ur.user = user.key
        ur.role = role.key
        ur.put()

        return ur

class Entitlement(ndb.Model):
    user = ndb.KeyProperty(kind=User)
    permission = ndb.IntegerProperty(choices=Permission.listOfNumbers())
    item = ndb.StringProperty()

class WStatement(ndb.Model):
    code = ndb.StringProperty()
    statement = ndb.StringProperty()
    signalWord = ndb.IntegerProperty(choices=SignalWord.list_of_numbers())

'''
### aWare Box concept
'''
class Box(AbstractModel):
    label = ndb.StringProperty()
    icon = ndb.BlobProperty()
    description = ndb.StringProperty()

class BoxCategory(ndb.Model):
    category = ndb.KeyProperty(kind='ProductCategory')
    box = ndb.KeyProperty(kind='Box')

'''
### Location
'''
class Location(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)

class PhysicalLocation(Location):
    location = ndb.GeoPtProperty()

    @classmethod
    def load(cls, lat, lon):
        obj = ndb.GeoPt(lat, lon)
        loc = cls.gql("WHERE location = :1", obj).fetch()
        if len(loc):
            return loc[0]

        loc = PhysicalLocation(location=obj)
        loc.put()
        return loc

class VirtualLocation(Location):
    address = ndb.StringProperty()

'''
### Customization
'''
class Customization(AbstractModel):
    owner = ndb.KeyProperty(kind=User)
    created = ndb.DateTimeProperty(auto_now_add=True)

class ProductCustomization(Customization):
    product = ndb.KeyProperty(kind=Product)

class ProductName(ProductCustomization):
    value = ndb.StringProperty()

    @classmethod
    def get_by_owner(cls, product, user):
        return cls.gql("WHERE product = :1 AND owner = :2",
                       product.key,
                       user.key).get()

    @classmethod
    def update(cls, product, user, name):
        old_name = cls.get_by_owner(product, user)
        if not old_name:
            old_name = ProductName()
            old_name.product = product.key
            old_name.owner = user.key

        old_name.value = name
        old_name.put()

        return old_name

    @classmethod
    def create(cls, product, user, value):
        name = ProductName()
        name.product = product.key
        name.owner = user.key
        name.value = value
        name.put()

        return name

class ProductSpecUnit(ProductCustomization):
    value = ndb.KeyProperty()
    spec = ndb.KeyProperty(kind=SpecificationValue)

    @classmethod
    def load(cls, user, spec, product, value):
        psu = cls.gql("WHERE value = :1 AND spec = :2 AND product = :3 AND owner = :4",
                      value.key, spec.key, product.key, user.key).get()
        if psu:
            return psu

        psu = ProductSpecUnit()
        psu.owner = user.key
        psu.product = product.key
        psu.spec = spec.key
        psu.value = value.key
        psu.put()

        return psu


    @classmethod
    def get(cls, product, user, spec):
        return cls.gql("WHERE owner = :1 AND product = :2 AND spec = :3",
                       user.key, product.key, spec.key).get()
