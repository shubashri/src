'''
Created on 19/11/2014

@author: Adhavan
'''

import endpoints  # @UnresolvedImport @UnusedImport
from protorpc import messages, message_types
from protorpc import remote
from api.common import aWareInternalAPI
from models import Ingredient,IngredientWikiLink
from google.appengine.datastore.datastore_query import Cursor
from api.internal.admin import OAuthInfo, AdminUtils, LanguageResponse
from models.i18n import Language
from api.internal.admin import UserResponse, OAuthInfo, LanguageResponse,\
	AdminUtils

'''
### MESSAGES ###
'''

class IngredientNameRequest(messages.Message):
	cursor = messages.StringField(1)
	size = messages.IntegerField(2, default=10)
	user_key = messages.StringField(5, required=True)

class IngredientWikiLinkMessage(messages.Message):
	is_valid = messages.BooleanField(1, default=False)
	url = messages.StringField(2)
	
class IngredientResponse(messages.Message):
	ingredient_key = messages.StringField(1, required=True)
	name = messages.StringField(2)
	wiki_link = messages.MessageField(IngredientWikiLinkMessage, 3)
	language = messages.MessageField(LanguageResponse, 4)

class IngredientCollection(messages.Message):
	names = messages.MessageField(IngredientResponse, 1, repeated=True)
	cursor = messages.StringField(2)
	more = messages.BooleanField(3)
		
class IngredientCategoryMessage(messages.Message):
	category_key = messages.StringField(1)
	name = messages.StringField(2)
	creator = messages.MessageField(UserResponse, 3)
	
class ChangeCategoryRequest(messages.Message):
	ingredient_key = messages.StringField(1)
	user_key = messages.StringField(2)
	category_key = messages.StringField(3)

class IngredientList(messages.Message):
	ingredient_key = messages.MessageField(IngredientNameRequest,1,required = True)
	e_number = messages.StringField(2,required = False)
	label_name = messages.StringField(3)
	translation = messages.StringField(4)
	wiki_link = messages.MessageField(IngredientWikiLinkMessage,5)
	hazards = messages.StringField(6)
	
'''
### END of MESSAGES ###
'''

@aWareInternalAPI.api_class(resource_name='admin.ingredients',
							path='admin/ingredients',
							allowed_client_ids=OAuthInfo.CLIENT_IDS,
							scopes=OAuthInfo.SCOPES,
							audiences=OAuthInfo.AUDIENCES)

class AdminIngredients(remote.Service):
	'''
	The aWare Ingredients API for aWare administrator interface
	'''
	@endpoints.method(IngredientNameRequest,
					  IngredientCollection,
					  http_method='GET',
					  path='names',
					  name='names')
	
	def get_ingredient_name(self, request):
		'''
		Retrieve a ingredients names
		'''
		# get size of the name to return
		size = request.size

		# cursor state
		cursor = None
		if request.cursor:
			cursor = Cursor(urlsafe=request.cursor)
			
		# build the query
		query = Ingredient.query()
		
		names = None
		next_cursor = None
		more = False
		
		if cursor:
			names, next_cursor, more = query.fetch_page(size, start_cursor=cursor)
		else:
			names, next_cursor, more = query.fetch_page(size, start_cursor=cursor)

		if next_cursor:
			return IngredientHelper.create_collection(names, next_cursor.urlsafe(), more)

		return IngredientHelper.create_collection(names)
		
	@endpoints.method(IngredientList,
						message_types.VoidMessage,
						http_method='POST',
						path='ingredient_list',
						name='ingredient.list')
						
	def ingredient_list(self, request):
		'''
		ingredients List
		'''
		#retrive the requested ingredient
		ingredient = Ingredient.get_by_urlsafe_key(request.ingredient_key)
		if not ingredient:
			message = 'No product with the key "%s" exists.' % request.ingredient_key
			raise endpoints.NotFoundException(message)
		
		# retrieve the user
		user = User.get_by_urlsafe_key(request.user_key)
		if not user:
			message = 'No user with the key "%s" exists.' % request.user_key
			raise endpoints.NotFoundException(message)
		
		#Find lable name for the ingredient
		label_name = request.label_name
		if LabelName.exists(label_name):
			label_name = LabelName.find_by_name(label_name)
		else:
			label_name = None
			
		# retrieve the translation
		tanslation = Language.find_by_code(request.ingredient.language)
		if not language:
			tanslation = Language.get_unknown()
			
		#Find wiki-link for the ingredient
		link = request.wiki_link.link
		is_valid = request.wiki_link.is_valid
		wiki_link = None
		if IngredientWikiLink.exists(ingredient, tanslation):
			wiki_link = IngredientWikiLink.find_by_ingredient_and_language(ingredient, tanslation)
			wiki_link.link = link
			wiki_link.is_valid = is_valid
			wiki_link.put()
		else:
			wiki_link = None
		
		#Find Hazards for the Ingrdient
		hazards = HStatement.getClassifications(hazards)
		if not hazards:
			hazards = None
		
		#Find E_Number for the Ingredient
		e_numbers = request.e_numbers
		if Ingredient.e_numbers.exists(e_number):
			e_number = Ingredient.find_by_e_number(e_number)
			
		
						
	
	@endpoints.method(ChangeCategoryRequest,
					  message_types.VoidMessage,
					  http_method='POST',
					  path='category/change',
					  name='category.change')
		
	def change_category(self, request):
		'''
		Change the category of a Ingredient
		'''
		# retrieve the requested Ingredient
		ingredient = Ingredient.get_by_urlsafe_key(request.ingredient_key)
		if not ingredient:
			message = 'No Ingredient with the key "%s" exists.' % request.ingredient_key
			raise endpoints.NotFoundException(message)

		# retrieve the user
		user = User.get_by_urlsafe_key(request.user_key)
		if not user:
			message = 'No user with the key "%s" exists.' % request.user_key
			raise endpoints.NotFoundException(message)

		# retrieve the category
		category = IngredientCategory.get_by_urlsafe_key(request.category_key)
		if not category:
			message = 'No category with the key "%s" exists.' % request.category_key
			raise endpoints.NotFoundException(message)

		# remove the ingredient from the old category
		old_category = ingredient.get_category()
		old_mapping = IngredientCategoryMapping.load(ingredient, old_category)
		if old_mapping:
			old_mapping.key.delete()

		# set the ingredient under the given category
		IngredientCategoryMessage.load(ingredient, category, user)

		# register the user as editor of the ingredient
		IngredientCategoryMessage.add_or_update(ingredient, user)

		return message_types.VoidMessage()


class IngredientHelper():

	@classmethod
	def get_ingredient_language(cls, entity):
		lang = AdminUtils.calc_ingredient_name(entity)[0]
		msg = LanguageResponse()
		msg.language_key = lang.key.urlsafe()
		msg.name = lang.name
		msg.code = lang.code
		return msg

	@classmethod
	def get_ingredient_wiki_link(cls,entity):
		lang = AdminUtils.calc_ingredient_name(entity)[0]
		wiki_link = IngredientWikiLink.find_by_ingredient_and_language(entity, lang)
		msg = IngredientWikiLinkMessage()
		msg.is_valid = wiki_link.is_valid
		msg.url = wiki_link.link
		return msg
	
	@classmethod
	def create_ingredient(cls, entity):
		ingredient = IngredientResponse()
		ingredient.ingredient_key = entity.key.urlsafe()
		ingredient.name = AdminUtils.calc_ingredient_name(entity)[1]
		ingredient.wiki_link = cls.get_ingredient_wiki_link(entity)
		ingredient.language = cls.get_ingredient_language(entity)
		return ingredient

	@classmethod
	def create_collection(cls, names, cursor='', more=False):
		collection = IngredientCollection()
		collection.cursor = cursor
		collection.more = more
		for n in names:
			collection.names.append(cls.create_ingredient(n))
		return collection
		
	@classmethod
	def get_ingredient_category(cls, entity):
		category = entity.get_category()
		mapping = IngredientCategoryMapping.load(entity, category, User.system_user())
		msg = IngredientCategoryMapping()
		msg.category_key = category.key.urlsafe()
		msg.name = category.name
		msg.creator = UserResponse()
		msg.creator.user_key = mapping.creator.urlsafe()
		return msg

	@classmethod
	def ingredient_list(cls,name_key,e_number,label_name,translation,wikipedia,hazards):
		ingredient_list = IngredientList()
		ingredient_list.ingredient_key = ingredient_key
		ingredient_list.e_number = e_number
		ingredient_list.label_name = label_name
		ingredient_list.translation = translation
		ingredient_list.wiki_link = wiki_link
		ingredient_list.hazards = hazards
		return ingredient_list
