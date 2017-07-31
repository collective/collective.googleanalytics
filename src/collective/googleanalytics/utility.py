
import gdata.analytics.client
import gdata.analytics.service
import gdata.gauth
import logging
import socket
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.ObjectManager import IFAwareObjectManager
from OFS.OrderedFolder import OrderedFolder
from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from collective.googleanalytics import error
from collective.googleanalytics.config import GOOGLE_REQUEST_TIMEOUT
from collective.googleanalytics.interfaces.report import IAnalyticsReport
from collective.googleanalytics.interfaces.utility import IAnalytics
from collective.googleanalytics.interfaces.utility import IAnalyticsSchema
from datetime import datetime
from gdata.client import Unauthorized
from gdata.gauth import OAuth2AccessTokenError
from gdata.gauth import OAuth2RevokeError
from gdata.service import RequestError
from plone import api
from plone.memoize import ram
try:
    from plone.protect.auto import safeWrite
except ImportError:
    # older Plone versions (< 5.0) don't support this, so we provide a stub
    def safeWrite(obj):
        pass
from plone.registry.interfaces import IRegistry
from time import time
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.component import getUtility
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from zope.schema.fieldproperty import FieldProperty

logger = logging.getLogger('collective.googleanalytics')

DEFAULT_TIMEOUT = socket.getdefaulttimeout()

_ = MessageFactory('collective.googleanalytics')


def account_feed_cachekey(func, instance, feed_path):
    """
    Cache key for the account feed. We only refresh it every ten minutes.
    """

    cache_interval = instance.cache_interval
    cache_interval = (cache_interval > 0 and cache_interval * 60) or 1
    return hash((time() // cache_interval, feed_path))


@implementer(IAnalytics, IAttributeAnnotatable)
class Analytics(PloneBaseTool, IFAwareObjectManager, OrderedFolder):
    """
    Analytics utility
    """

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

    security.declarePrivate('_auth_token')
    _auth_token = None
    security.declarePrivate('_valid_token')
    _valid_token = None

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
            client = gdata.analytics.client.AnalyticsClient()
            self._auth_token.authorize(client)
        else:
            raise error.BadAuthenticationError, 'You need to authorize with Google'

        return client

    def is_auth(self):
        valid_token = self._valid_token
        if valid_token:
            return True
        return False

    def makeClientRequest(self, feed, *args, **kwargs):
        """
        Get the authenticated client object and make the specified request.
        We need this wrapper method so that we can intelligently handle errors.
        """

        safeWrite(self)
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
                expired = False
                # Token gets refreshed when a new request is made to Google,
                # so check before
                if self._auth_token.token_expiry < datetime.now():
                    logger.debug("This access token expired, will try to "
                                 "refresh it.")
                    expired = True
                result = query_method(feed_url, *args, **kwargs)
                if expired:
                    logger.debug("Token was refreshed successfuly. New expire "
                                 "date: %s" % self._auth_token.token_expiry)
                return result
            except (Unauthorized, RequestError), e:
                if hasattr(e, 'reason'):
                    reason = e.reason
                else:
                    reason = e[0]['reason']
                if 'Token invalid' in reason or reason in ('Forbidden', 'Unauthorized'):
                    # Reset the stored auth token.
                    self._auth_token = None
                    settings = self.get_settings()
                    settings.reports_profile = None
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

    def revoke_token(self):
        logger.debug("Trying to revoke token")
        try:
            oauth2_token = self._auth_token
            if oauth2_token:
                oauth2_token.revoke()
                logger.debug("Token revoked successfuly")
        except OAuth2RevokeError:
            # Authorization already revoked
            logger.debug("Token was already revoked")
            pass
        except socket.gaierror:
            logger.debug("There was a connection issue, could not revoke "
                         "token.")
            raise error.RequestTimedOutError, (
                'You may not have internet access. Please try again '
                'later.'
            )

        self._auth_token = None
        self._valid_token = False

    def set_token(self, code):
        logger.debug(
            "Received callback from Google with code '%s' " % code
        )
        oauth2_token = self._auth_token
        try:
            oauth2_token.get_access_token(code)
            logger.debug(
                "Code was valid, got '%s' as access_token and '%s' as "
                "refresh_token. Token will expire on '%s'" %
                (oauth2_token.access_token,
                 oauth2_token.refresh_token,
                 oauth2_token.token_expiry))
            message = _(u'Authorization succeeded. You may now configure '
                        u'Google Analytics for Plone.')
            self._valid_token = True

        except OAuth2AccessTokenError:
            logger.debug("Code was invalid, could not get tokens")
            self._auth_token = None
            self._valid_token = False
            message = _(u'Authorization failed. Google Analytics for '
                        u'Plone received an invalid token.')
        return message

    def auth_url(self, key, secret):
        """
        Returns the URL used to retrieve a Google OAuth2 token.
        """
        safeWrite(self)
        auth_url = None
        if key and secret:
            next = '%s/analytics-auth' % api.portal.get().absolute_url()

            oauth2_token = gdata.gauth.OAuth2Token(
                client_id=key,
                client_secret=secret,
                scope="https://www.googleapis.com/auth/analytics",
                user_agent='collective-googleanalytics',
            )
            logger.debug(u"Created new OAuth2 token with id: '%s' and secret:"
                         u" '%s'" % (key, secret))

            oauth2_token.redirect_uri = next
            self._auth_token = oauth2_token

            auth_url = oauth2_token.generate_authorize_url(
                redirect_uri=next,
                approval_prompt='force'
            )

            logger.debug(u"Auth URL: %s" % auth_url)

        return auth_url

    def get_settings(self):
        registry = getUtility(IRegistry)
        records = registry.forInterface(IAnalyticsSchema)
        return records

InitializeClass(Analytics)
