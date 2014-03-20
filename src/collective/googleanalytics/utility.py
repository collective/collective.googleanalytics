try:
    from App.class_init import InitializeClass
except ImportError:
    from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from zope.annotation import IAnnotations
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty

from OFS.ObjectManager import IFAwareObjectManager
from OFS.OrderedFolder import OrderedFolder

from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from plone.memoize import ram
from datetime import datetime
from time import time
import socket

from collective.googleanalytics.interfaces.utility import IAnalytics
from collective.googleanalytics.interfaces.report import IAnalyticsReport
from collective.googleanalytics import error
from collective.googleanalytics.config import GOOGLE_REQUEST_TIMEOUT

import gdata.gauth
import gdata.analytics.client
import gdata.analytics.service
from gdata.service import RequestError
from gdata.client import Unauthorized

import logging
logger = logging.getLogger('collective.googleanalytics')

DEFAULT_TIMEOUT = socket.getdefaulttimeout()


def account_feed_cachekey(func, instance, feed_path):
    """
    Cache key for the account feed. We only refresh it every ten minutes.
    """

    cache_interval = instance.cache_interval
    cache_interval = (cache_interval > 0 and cache_interval * 60) or 1
    return hash((time() // cache_interval, feed_path))


class Analytics(PloneBaseTool, IFAwareObjectManager, OrderedFolder):
    """
    Analytics utility
    """

    implements(IAnalytics, IAttributeAnnotatable)

    security = ClassSecurityInfo()

    id = 'portal_analytics'
    meta_type = 'Google Analytics Tool'

    _product_interfaces = (IAnalyticsReport,)

    security.declarePrivate('email')
    security.declarePrivate('password')

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
    security.declarePrivate('is_auth')
    security.declarePrivate('makeClientRequest')
    security.declarePrivate('getReports')
    security.declarePrivate('getCategoriesChoices')
    security.declarePrivate('getAccountsFeed')

    def _getAuthenticatedClient(self):
        """
        Get the client object and authenticate using our stored credentials.
        """
        client = None
        if self.is_auth():
            ann = IAnnotations(self)
            client = gdata.analytics.client.AnalyticsClient()
            ann['auth_token'].authorize(client)
        else:
            raise error.BadAuthenticationError, 'You need to authorize with Google'

        return client

    def is_auth(self):
        ann = IAnnotations(self)
        valid_token = ann.get('valid_token', None)
        if valid_token:
            return True
        return False

    def makeClientRequest(self, feed, *args, **kwargs):
        """
        Get the authenticated client object and make the specified request.
        We need this wrapper method so that we can intelligently handle errors.
        """

        # XXX: Have to use v2.4. gdata 2.0.18 doesn't yet support v3 for
        #      analytics
        feed_url = 'https://www.googleapis.com/analytics/v2.4/' + feed
        client = self._getAuthenticatedClient()

        if feed.startswith('management'):
            query_method = client.get_management_feed
        if feed.startswith('data'):
            query_method = client.get_data_feed

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
                ann = IAnnotations(self)
                expired = False
                # Token gets refreshed when a new request is made to Google,
                # so check before
                if ann['auth_token'].token_expiry < datetime.now():
                    logger.debug("This access token expired, will try to "
                                 "refresh it.")
                    expired = True
                result = query_method(feed_url, *args, **kwargs)
                if expired:
                    logger.debug("Token was refreshed successfuly. New expire "
                                 "date: %s" % ann['auth_token'].token_expiry)
                    IAnnotations(self)['auth_token'] = ann['auth_token']
                return result
            except (Unauthorized, RequestError), e:
                if hasattr(e, 'reason'):
                    reason = e.reason
                else:
                    reason = e[0]['reason']
                if 'Token invalid' in reason or reason in ('Forbidden', 'Unauthorized'):
                    # Reset the stored auth token.
                    self.auth_token = None
                    self.__dict__['reports_profile'] = None
                    raise error.BadAuthenticationError, 'You need to authorize with Google'
                else:
                    raise
            except (socket.sslerror, socket.timeout):
                raise error.RequestTimedOutError, 'The request to Google timed out'
            except socket.gaierror:
                raise error.RequestTimedOutError, 'You may not have internet access. Please try again later.'
        finally:
            socket.setdefaulttimeout(timeout)

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

    def getCategoriesChoices(self):
        """
        Return a list of possible report categories.
        """

        return self.report_categories

    @ram.cache(account_feed_cachekey)
    def getAccountsFeed(self, feed_path):
        """
        Returns the list of accounts.
        """
        feed = 'management/' + feed_path
        res = self.makeClientRequest(feed)
        return res

InitializeClass(Analytics)
