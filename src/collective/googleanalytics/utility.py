
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
# from collective.googleanalytics.config import GOOGLE_REQUEST_TIMEOUT
from collective.googleanalytics.interfaces.report import IAnalyticsReport
from collective.googleanalytics.interfaces.utility import IAnalytics
from collective.googleanalytics.interfaces.utility import IAnalyticsSchema
# from datetime import datetime
# from gdata.client import Unauthorized
from gdata.gauth import OAuth2AccessTokenError
from gdata.gauth import OAuth2RevokeError
# from gdata.service import RequestError
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
from apiclient.discovery import build
from google.oauth2.credentials import Credentials
from httplib import ResponseNotReady
# from urllib.request import Unauthorized, RequestError
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
import requests

logger = logging.getLogger('collective.googleanalytics')

DEFAULT_TIMEOUT = socket.getdefaulttimeout()

SCOPES = ["https://www.googleapis.com/auth/analytics"]

_ = MessageFactory('collective.googleanalytics')


def account_feed_cachekey(func, instance):
    """
    Cache key for the account feed. We only refresh it every ten minutes.
    """

    cache_interval = instance.cache_interval
    cache_interval = (cache_interval > 0 and cache_interval * 60) or 1
    return hash((time() // cache_interval))


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
    security.declarePrivate('_creds')
    _creds = None

    security.declarePrivate('_getAuthenticatedClient')

    # def _getAuthenticatedClient(self):
    #     """
    #     Get the client object and authenticate using our stored credentials.
    #     """
    #     client = None
    #     if self.is_auth():
    #         client = gdata.analytics.client.AnalyticsClient()
    #         self._auth_token.authorize(client)
    #     else:
    #         raise error.BadAuthenticationError, 'You need to authorize with Google'

    #     return client

    security.declarePrivate('is_auth')

    def is_auth(self):
        valid_token = self._valid_token
        if valid_token:
            return True
        return False

    def _getService(self):

        if not self.is_auth():
            raise error.BadAuthenticationError, 'You need to authorize with Google'

        if getattr(self, '_creds', None):
            creds = self._creds
        else:
            # upgrade from gdata auth token structure
            creds = Credentials(
                token=self._auth_token.access_token,
                refresh_token=self._auth_token.refresh_token,
                token_uri=self._auth_token.token_uri,
                client_id=self._auth_token.client_id,
                client_secret=self._auth_token.client_secret,
            )
            self._creds = creds
        if creds and creds.expired and creds.refresh_token:
            logger.debug("This access token expired, will try to "
                         "refresh it.")
            creds.refresh(Request())
            logger.debug("Token was refreshed successfuly. New expire "
                         "date: %s" % self._auth_token.token_expiry)

        service = build('analytics', 'v3', credentials=creds)
        return service

    security.declarePrivate('makeClientRequest')

    def makeClientRequest(self, api_request):
        """
        Get the authenticated client object and make the specified request.
        We need this wrapper method so that we can intelligently handle errors.
        """

        safeWrite(self)

        # Workaround for the lack of timeout handling in gdata. This approach comes
        # from collective.twitterportlet. See:
        # https://svn.plone.org/svn/collective/collective.twitterportlet/
        # timeout = socket.getdefaulttimeout()

        # If the current timeout is set to GOOGLE_REQUEST_TIMEOUT, then another
        # thread has called this method before we had a chance to reset the
        # default timeout. In that case, we fall back to the system default
        # timeout value.
        # if timeout == GOOGLE_REQUEST_TIMEOUT:
        #     timeout = DEFAULT_TIMEOUT
        #     logger.warning('Conflict while setting socket timeout.')

        try:
            # socket.setdefaulttimeout(GOOGLE_REQUEST_TIMEOUT)
            try:

                # Token gets refreshed when a new request is made to Google,
                # so check before
                service = self._getService()
                if api_request == 'webproperties':
                    account = self.getAccountId()
                    return service.management().webproperties().list(accountId=account).execute()
                elif api_request == 'accounts':
                    return service.management().accounts().list().execute()
            except RefreshError, e:
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
            except (socket.gaierror, ResponseNotReady):
                raise error.RequestTimedOutError, 'You may not have internet access. Please try again later.'
        finally:
            # socket.setdefaulttimeout(timeout)
            pass

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

    security.declarePrivate('getAccounts')

    @ram.cache(account_feed_cachekey)
    def getAccounts(self):
        """
        Returns the list of accounts.
        """
        accounts = self.makeClientRequest('accounts')
        return accounts.get('items', [])

    security.declarePrivate('getAccountId')

    @ram.cache(account_feed_cachekey)
    def getAccountId(self):
        """
        Returns the list of accounts.
        """
        accounts = self.getAccounts()
        return accounts[0].get('id') if accounts else None

    security.declarePrivate('getWebProperties')

    @ram.cache(account_feed_cachekey)
    def getWebProperties(self):
        account = self.getAccountId()
        if account is None:
            return []
        properties = self.makeClientRequest('webproperties').get('items', [])
        return properties

    def revoke_token(self):
        logger.debug("Trying to revoke token")

        if getattr(self, '_creds'):
            requests.post('https://oauth2.googleapis.com/revoke',
                          params={'token': self._creds.token},
                          headers={'content-type': 'application/x-www-form-urlencoded'})
            self._creds = None

            return
        else:
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
                scope=SCOPES,
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

    # def auth_url(self, key, secret):
    #     flow = google_auth_oauthlib.flow.Flow.from_client_secrets_config(
    #         dict(web=dict(client_id=key, client_secret=secret)), scopes=SCOPES)

    #     # The URI created here must exactly match one of the authorized redirect URIs
    #     # for the OAuth 2.0 client, which you configured in the API Console. If this
    #     # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    #     # error.
    #     flow.redirect_uri = '%s/analytics-auth' % api.portal.get().absolute_url()

    #     authorization_url, state = flow.authorization_url(
    #         # Enable offline access so that you can refresh an access token without
    #         # re-prompting the user for permission. Recommended for web server apps.
    #         access_type='offline',
    #         # Enable incremental authorization. Recommended as a best practice.
    #         include_granted_scopes='true')

    #     # Store the state so the callback can verify the auth server response.
    #     self.state = state

    #     return authorization_url

    def get_settings(self):
        registry = getUtility(IRegistry)
        records = registry.forInterface(IAnalyticsSchema)
        return records


InitializeClass(Analytics)
