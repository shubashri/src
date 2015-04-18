'''
Created on 01/10/2013

@author: Ismail Faizi
'''
import jinja2
import os
import webapp2
from google.appengine.api import users
from models import User

ADMINS = ['kanafghan@gmail.com',
          'jopsen@gmail.com',
          'anders.kousgaard@gmail.com',
          'ismail@awareaps.com',
          'jonas@awareaps.com',
          'anders@awareaps.com']

JINJA_ENVIRONMENT = jinja2.Environment(
                                       loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                                       extensions=['jinja2.ext.autoescape'])

NAVIGATION = [
        {'caption': 'Products', 'url': '/', 'isActive': False},
        {'caption': 'Ingredients', 'url': '/ingredients', 'isActive': False},
        {'caption': 'Classifications', 'url': '/classifications', 'isActive': False},
        {'caption': 'HStatements', 'url': '/hstatements', 'isActive': False},
        {'caption': 'HReferences', 'url': '/hreferences', 'isActive': False},
        {'caption': 'Classes', 'url': '/classes', 'isActive': False},
        {'caption': 'Pictograms', 'url': '/pictograms', 'isActive': False},
        {'caption': 'Utilities', 'url': '/utils', 'isActive': False},
        {'caption': 'Helps', 'url': '/helps', 'isActive': False},
        {'caption': 'Guide', 'url': '/guide', 'isActive': False},
        {'caption': 'OCR', 'url': '/ocr', 'isActive': False},
        {'caption': 'Parameters', 'url': '/parameters', 'isActive': False}]

class AuthorizedPage(webapp2.RequestHandler):
    MSG_TYPE_ERROR = 'error'
    MSG_TYPE_SUCCESS = 'success'
    MSG_TYPE_INFO = 'info'
    
    def __init__(self, template, request, response):
        webapp2.RequestHandler.__init__(self, request, response)
        self.template = template
        self.templateValues = {}
        self.messages = []
    
    def get(self):
        if users.get_current_user():
            self.addUserValues(True)
            self.handleGetRequest()
        else:
            self.addUserValues()
        
        self.initTemplate()
    
    def initTemplate(self):
        self.addTemplateValue('pages', NAVIGATION)
        tmpl = JINJA_ENVIRONMENT.get_template('pages/%s' %self.template)
        self.response.write(tmpl.render(self.templateValues))
    
    def addUserValues(self, loggedIn=False):
        if loggedIn:
            self.addTemplateValue('url', users.create_logout_url(self.request.uri))
            self.addTemplateValue('url_linktext', 'Logout')
            self.addTemplateValue('loggedIn', True)
            self.addTemplateValue('authorized', (users.get_current_user().email().lower() in ADMINS))
            self.addTemplateValue('user', User.load(users.get_current_user()).key.urlsafe())
        else:
            self.addTemplateValue('url', users.create_login_url(self.request.uri))
            self.addTemplateValue('url_linktext', 'Login')
        self.addTemplateValue('messages', self.messages)
    
    def post(self):
        if users.get_current_user():
            self.addUserValues(True)
            self.handlePostRequest()
        else:
            self.addUserValues()
        
        self.initTemplate()
        
    def addTemplateValue(self, name, value):
        self.templateValues[name] = value
            
    def setActivePage(self, page):
        for n in NAVIGATION:
            n['isActive'] = False
            if n['caption'].lower() == page.lower():
                n['isActive'] = True
    
    def addMessage(self, message, msgType=MSG_TYPE_ERROR):
        self.messages.append({'msg': message, 'type': msgType})
        
    def clearMessages(self):
        self.messages = []
        
    def handleGetRequest(self):
        # This must be implemented by subclasses
        pass
    
    def handlePostRequest(self):
        # This must be implemented by subclasses
        pass