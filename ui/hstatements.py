'''
Created on 01/10/2013

@author: Ismail Faizi
'''

from common import AuthorizedPage
from models import HStatement, HSTATEMENT_KEY

class HStatementsPage(AuthorizedPage):

    def __init__(self, request, response):
        AuthorizedPage.__init__(self, 'hstatements.html', request, response)

    def handleGetRequest(self):
        # get the recent 20 statements added to datastore
        q = HStatement.query(ancestor=HSTATEMENT_KEY)
        statements = q.order(-HStatement.created).fetch(20)

        self.addTemplateValue('statements', statements)

        self.setActivePage('HStatements')


