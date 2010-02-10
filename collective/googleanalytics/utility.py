try:
    from App.class_init import InitializeClass
except ImportError:
    from Globals import InitializeClass
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
from gdata.service import BadAuthentication, CaptchaRequired, RequestError

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
    
    security.declarePrivate('report_categories')
    report_categories = FieldProperty(IAnalytics['report_categories'])
    
    security.declarePrivate('data_client')
    data_client = gdata.analytics.service.AnalyticsDataService()
    
    security.declarePrivate('accounts_client')
    accounts_client = gdata.analytics.service.AccountsService()
    
    security.declarePrivate('_getAuthenticatedClient')
    def _getAuthenticatedClient(self, service='data', reauthenticate=False):
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
        if client.email == self.email and client.password == self.password \
            and not reauthenticate:
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
        
    security.declarePrivate('makeClientRequest')
    def makeClientRequest(self, service, method, *args, **kwargs):
        """
        Get the authenticated client object and make the specified request.
        We need this wrapper method so that we can intelligently handle errors.
        """
        
        client = self._getAuthenticatedClient(service)
        query_method = getattr(client, method, None)
        if not query_method:
            raise error.InvalidRequestMethodError, \
                '%s does not have a method %s' % (client.__class__.__name__, method)
        try:
            return query_method(*args, **kwargs)
        except RequestError, e:
            if e.reason == 'Token invalid':
                # The auth token has expired, so the client needs to be reauthenticated.
                client = getAuthenticatedClient(service, reauthenticate=True)
                return query_method(*args, **kwargs)
            else:
                raise
    
    security.declarePrivate('getReports')
    def getReports(self, category=None):
        """
        List the available Analytics reports. If a category is specified, only
        reports of that category are returned. Otherwise, all reports are
        returned.
        """
                
        for obj in self.objectValues():
            if IAnalyticsReport.providedBy(obj):
                if (category and category in obj.categories) or not category:
                    yield obj

    security.declarePrivate('getCategoriesChoices')
    def getCategoriesChoices(self):
        """
        Return a list of possible report categories.
        """
        
        return self.report_categories
        
InitializeClass(Analytics)