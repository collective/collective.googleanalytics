from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo

from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty

from OFS.ObjectManager import IFAwareObjectManager
from OFS.OrderedFolder import OrderedFolder

from Products.CMFPlone.PloneBaseTool import PloneBaseTool

from collective.googleanalytics.interfaces.utility import IAnalytics
from collective.googleanalytics.interfaces.report import IAnalyticsReport
from collective.googleanalytics import error

import gdata.analytics.service
from gdata.service import BadAuthentication, CaptchaRequired

class Analytics(PloneBaseTool, IFAwareObjectManager, OrderedFolder):
    """
    Analytics utility
    """
    
    implements(IAnalytics)
    
    security = ClassSecurityInfo()
    
    id = 'portal_analytics'
    meta_type = 'Google Analytics Tool'
    
    _product_interfaces = (IAnalyticsReport,)
    
    security.declarePrivate('email')
    email = FieldProperty(IAnalytics['email'])
    
    security.declarePrivate('password')
    password = FieldProperty(IAnalytics['password'])
    
    security.declarePrivate('profile')
    profile = FieldProperty(IAnalytics['profile'])
    
    security.declarePrivate('reports')
    reports = FieldProperty(IAnalytics['reports'])
    
    security.declarePrivate('cache_interval')
    cache_interval = FieldProperty(IAnalytics['cache_interval'])
    
    security.declarePrivate('tracking_excluded_roles')
    tracking_excluded_roles = FieldProperty(IAnalytics['tracking_excluded_roles'])
    
    security.declarePrivate('data_client')
    data_client = gdata.analytics.service.AnalyticsDataService()
    
    security.declarePrivate('accounts_client')
    accounts_client = gdata.analytics.service.AccountsService()
    
    security.declarePrivate('getAuthenticatedClient')
    def getAuthenticatedClient(self, service='data'):
        """
        Get the client object and authenticate using our stored credentials.
        """
        
        if self.email == None or self.password == None:
            raise error.MissingCredentialsError, 'Enter e-mail and password in the control panel'
        
        # Get the appropriate client class.
        if service == 'accounts':
            client = self.accounts_client
        else:
            client = self.data_client
        
        # If we're already authenticated, return the client.
        if client.email and client.password:
            return client
        
        # Otherwise try to do the authentication, and raise an error if it doesn't work.
        try:
            client.ClientLogin(self.email, self.password, account_type='GOOGLE')
        except (BadAuthentication, CaptchaRequired):
            # Don't store credentials that didn't authenticate correctly.
            client.email = None
            client.password = None
            raise error.BadAuthenticationError, 'Incorrect e-mail or password'
        return client
    
    security.declarePrivate('getReports')
    def getReports(self):
        """
        List the available Analytics reports.
        """
                
        for obj in self.objectValues():
            if IAnalyticsReport.providedBy(obj):
                yield obj

InitializeClass(Analytics)