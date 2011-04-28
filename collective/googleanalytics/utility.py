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
from plone.memoize import ram
from time import time
import socket

from collective.googleanalytics.interfaces.utility import IAnalytics
from collective.googleanalytics.interfaces.report import IAnalyticsReport
from collective.googleanalytics import error
from collective.googleanalytics.config import GOOGLE_REQUEST_TIMEOUT

import gdata.analytics.service
from gdata.service import RequestError

import logging
logger = logging.getLogger('collective.googleanalytics')

DEFAULT_TIMEOUT = socket.getdefaulttimeout()

class AnalyticsClients(object):
    """
    An object for storing Google Analytics clients.
    """
    
    def __init__(self):
        self.data = gdata.analytics.service.AnalyticsDataService()
        self.accounts = gdata.analytics.service.AccountsService()

def account_feed_cachekey(func, instance):
    """
    Cache key for the account feed. We only refresh it every ten minutes.
    """
    
    cache_interval = instance.cache_interval
    cache_interval = (cache_interval > 0 and cache_interval * 60) or 1
    return hash((time() // cache_interval, instance.auth_token))

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
    security.declarePrivate('password')
    
    security.declarePrivate('auth_token')
    auth_token = FieldProperty(IAnalytics['auth_token'])
    
    security.declarePrivate('tracking_web_property')
    tracking_web_property = FieldProperty(IAnalytics['tracking_web_property'])
    
    security.declarePrivate('tracking_plugin_names')
    tracking_plugin_names = FieldProperty(IAnalytics['tracking_plugin_names'])
    
    security.declarePrivate('tracking_excluded_roles')
    tracking_excluded_roles = FieldProperty(IAnalytics['tracking_excluded_roles'])
    
    security.declarePrivate('reports_profile')
    reports_profile = FieldProperty(IAnalytics['reports_profile'])
    
    security.declarePrivate('reports')
    reports = FieldProperty(IAnalytics['reports'])
    
    security.declarePrivate('cache_interval')
    cache_interval = FieldProperty(IAnalytics['cache_interval'])
    
    security.declarePrivate('report_categories')
    report_categories = FieldProperty(IAnalytics['report_categories'])
    
    security.declarePrivate('_v_temp_clients')
    _v_temp_clients = None
    
    security.declarePrivate('_getAuthenticatedClient')
    def _getAuthenticatedClient(self, service='data'):
        """
        Get the client object and authenticate using our stored credentials.
        """
        
        if not self.auth_token:
            raise error.BadAuthenticationError, 'You need to authorize with Google'
            
        clients = self.getClients()
        
        # Get the appropriate client class.
        if service == 'accounts':
            client = clients.accounts
        else:
            client = clients.data
            
        if not client.GetAuthSubToken():
            client.SetAuthSubToken(self.auth_token)
        
        return client
        
    security.declarePrivate('getClients')
    def getClients(self):
        """
        Returns an AnalyticsClients object.
        """

        # We store the clients object on the ZODB database connection. This approach
        # comes from alm.solrindex. See the documentation for that product for a
        # full explanation.
        jar = self._p_jar
        oid = self._p_oid

        if jar is None or oid is None:
            # This object is not yet stored in ZODB, so we use a
            # volatile attribute.
            clients = self._v_temp_clients
            if clients is None:
                self._v_temp_clients = clients = AnalyticsClients() 
        else:
            foreign_connections = getattr(jar, 'foreign_connections', None)
            if foreign_connections is None:
                jar.foreign_connections = foreign_connections = {}

            clients = foreign_connections.get(oid)
            if clients is None:
                foreign_connections[oid] = clients = AnalyticsClients()

        return clients
        
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

        # Workaround for the lack of timeout handling in gdata. This approach comes
        # from collective.twitterportlet. See:
        # https://svn.plone.org/svn/collective/collective.twitterportlet/
        timeout = socket.getdefaulttimeout()
        
        # If the current timeout is set to GOOGLE_REQUEST_TIMEOUT, then another
        # thread has called this method before we had a chance to reset the
        # default timeout. In that case, we fall back to the system default
        # timeout value.
        if timeout == GOOGLE_REQUEST_TIMEOUT:
            timeout = DEFAULT_TIMEOUT
            logger.warning('Conflict while setting socket timeout.')

        try:
            socket.setdefaulttimeout(GOOGLE_REQUEST_TIMEOUT)
            try:
                return query_method(*args, **kwargs)
            except RequestError, e:
                reason = e[0]['reason']
                if 'Token invalid' in reason or reason == 'Forbidden':
                    # Reset the stored auth token.
                    self.auth_token = None
                    raise error.BadAuthenticationError, 'You need to authorize with Google'
                else:
                    raise
            except (socket.sslerror, socket.timeout):
                raise error.RequestTimedOutError, 'The request to Google timed out'
        finally:
            socket.setdefaulttimeout(timeout)
    
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
        
    security.declarePrivate('getAccountsFeed')
    @ram.cache(account_feed_cachekey)
    def getAccountsFeed(self):
        """
        Returns the list of accounts.
        """

        return self.makeClientRequest('accounts', 'GetAccountList')
        
InitializeClass(Analytics)
