'''
Created on 20/03/2014

@author: Ismail Faizi
'''

import endpoints  # @UnresolvedImport
from internal.products import Products
from api.internal.registration import Registration
from api.internal.documents import Documents
from api.internal.boxes import Boxes
from api.internal.translations import Translations
from api.internal.help import HelpAPI
from api.internal.utils import Utilities
from api.internal.notifications import Notifications
from api.internal.users import Users
from api.internal.appguide import AppGuideAPI
from api.internal.admin.products import AdminProducts
from api.internal.admin.users import AdminUsers
from api.internal.admin.ingredients import AdminIngredients
from api.internal.admin.authentication import AdminAuthentication
from api.internal.common.languages import Languages
from api.internal.common.classifications import Classifications

application = endpoints.api_server([Languages,
                                    Classifications,
                                    Products,
                                    Users,
                                    Registration,
                                    Documents,
                                    Boxes,
                                    Translations,
                                    HelpAPI,
                                    Utilities,
                                    Notifications,
                                    AppGuideAPI,
                                    AdminAuthentication,
                                    AdminUsers,
                                    AdminIngredients,
                                    AdminProducts])
