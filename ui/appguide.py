'''
Created on 22/07/2014

@author: Ismail Faizi
'''

from common import AuthorizedPage
from models.guides import AppGuide
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import blobstore, users
from models import User
from helpers.uploadhandler import UploadHandler

class AppGuidePage(AuthorizedPage):
    
    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'appguide.html', request, response)
    
    def handleGetRequest(self):
        self.addCommon()
        self.setActivePage('Guide')
    
    def addCommon(self):
        # get all the guide items from datastore
        self.addTemplateValue('items', AppGuide.get_all())
        self.addTemplateValue('form_action', blobstore.create_upload_url(success_path='/guide/create',
                                                                         gs_bucket_name=self.get_gs_bucket()))
    def get_gs_bucket(self):
        return UploadHandler.GS_BUCKET_NAME +'/guides/'
    
class AppGuideCreationHandler(blobstore_handlers.BlobstoreUploadHandler):
    
    def post(self):
        # or we updating or creating a new one
        item_key = self.request.get('item', None)
        is_new = (item_key is None)
        
        # get the info about the uploaded image
        upload_files = self.get_file_infos('image')
        if is_new and not len(upload_files):
            self.response.out.write('<p>Image not uploaded, please try again!</p>')
            self.response.out.write('<p><a href="/guide">Return</a></p>')
            return
        
        # check whether the image has been uploaded
        if is_new and not upload_files[0].gs_object_name:
            self.response.out.write('<p>Image info not found. Seems to be upload error! Please report this to an administrator.</p>')
            self.response.out.write('<p><a href="/guide">Return</a></p>')
            return
        
        text = self.request.get('text')
        if not text:
            self.response.out.write('You must provide the text for the guide. Please try again.')
            self.response.out.write('<p><a href="/guide">Return</a></p>')
            return
        
        user = User.load(users.get_current_user())
        
        if is_new:
            # create the guide item
            AppGuide.create(user=user, 
                            image=blobstore.create_gs_key(upload_files[0].gs_object_name), 
                            text=text)
        else:
            image = None
            if upload_files and upload_files[0].gs_object_name:
                image = blobstore.create_gs_key(upload_files[0].gs_object_name)
            
            item = AppGuide.get_by_urlsafe_key(item_key)
            if item:
                item.update(editor=user,
                            text=text,
                            image=image)
        
        self.redirect('/guide')
