
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
import google_auth_oauthlib
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from httplib import ResponseNotReady
# from urllib.request import Unauthorized, RequestError
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
import requests

logger = logging.getLogger('collective.googleanalytics')

DEFAULT_TIMEOUT = socket.getdefaulttimeout()

# SCOPES = ["https://www.googleapis.com/auth/analytics"]
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
# TODO: do we need readonly instead?

_ = MessageFactory('collective.googleanalytics')


def account_feed_cachekey(func, instance, api_request=None):
    """
    Cache key for the account feed. We only refresh it every ten minutes.
    """

    cache_interval = instance.cache_interval
    cache_interval = (cache_interval > 0 and cache_interval * 60) or 1
    return hash((time() // cache_interval, api_request))


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
    security.declarePrivate('_state')
    _state = {}

    @security.private
    def is_auth(self):
        # valid_token = self._valid_token
        # if valid_token:
        #     return True
        # return False
        creds = self._get_credentials()
        return creds and creds.valid

    @security.private
    def _get_credentials(self):
        if getattr(self, '_auth_token', None):
            # upgrade from gdata auth token structure
            creds = Credentials(
                token=self._auth_token.access_token,
                refresh_token=self._auth_token.refresh_token,
                token_uri=self._auth_token.token_uri,
                client_id=self._auth_token.client_id,
                client_secret=self._auth_token.client_secret,
            )
            self._update_credentials(creds)
            self._auth_token = None
        elif 'token' in self._state:
            CRED_ARGS = ['token', 'refresh_token', 'token_uri', 'client_id', 'client_secret']
            creds = Credentials(**{key: value for key, value in self._state.items() if key in CRED_ARGS})
        else:
            creds = None
        return creds

    @security.private
    def _update_credentials(self, credentials):
        self._state.update(
            {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
        )
        self._state = self._state

    @security.private
    @ram.cache(account_feed_cachekey)
    def _getService(self):
        if not self.is_auth():
            raise error.BadAuthenticationError, 'You need to authorize with Google'
        creds = self._get_credentials()

        if creds and creds.expired and creds.refresh_token:
            logger.debug("This access token expired, will try to "
                         "refresh it.")
            creds.refresh(Request())
            logger.debug("Token was refreshed successfuly. New expire "
                         "date: %s" % self._auth_token.token_expiry)
            self._update_credentials(creds)

        service = build('analytics', 'v3', credentials=creds)
        return creds, service

    @security.private
    @ram.cache(account_feed_cachekey)
    def makeCachedRequest(self, api_request):
        """
        Returns the list of accounts.
        """
        res = self.makeClientRequest(api_request)
        return res.get('items', [])

    @security.private
    def makeClientRequest(self, api_request, **query_args):
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

        creds, service = self._getService()

        try:
            # socket.setdefaulttimeout(GOOGLE_REQUEST_TIMEOUT)
            try:
                result = None
                if api_request == 'webproperties':
                    result = service.management().webproperties().list(accountId='~all').execute()
                elif api_request == 'accounts':
                    result = service.management().accounts().list().execute()
                elif api_request == 'profiles':
                    result = service.management().profiles().list(accountId='~all', webPropertyId='~all').execute()
                elif api_request == 'data':
                    result = service.data().ga().get(**query_args).execute()
                else:
                    raise ValueError("Not supported api")
                self._update_credentials(creds)
                return result
            except RefreshError, e:
                reason = e.message
                if any([r in reason for r in ['Token invalid', 'Forbidden', 'Unauthorized']]):
                    # Reset the stored auth token.
                    self._state['token'] = None
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

    @security.private
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

    @security.private
    def getCategoriesChoices(self):
        """
        Return a list of possible report categories.
        """

        return self.report_categories

    @security.public
    def revoke_token(self):
        logger.debug("Trying to revoke token")

        if getattr(self, '_state'):
            token = self._state.get('token')
        else:
            token = self._auth_token.token

        result = requests.post('https://oauth2.googleapis.com/revoke',
                               params={'token': token}, headers={'content-type': 'application/x-www-form-urlencoded'})
        status_code = getattr(result, 'status_code')
        if status_code == 200:
            logger.debug("Token was already revoked")
            self._auth_token = None
            self._valid_token = False
            self._state['token'] = None
        else:
            logger.warning("Problem revoking token")

            # raise error.RequestTimedOutError, (
            #     'You may not have internet access. Please try again '
            #     'later.'
            # )

    @security.public
    def set_token(self, code, state):
        safeWrite(self)
        logger.debug(
            "Received callback from Google with code '%s' " % code
        )
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            dict(web=self._state), scopes=SCOPES, state=state)
        flow.redirect_uri = '%s/analytics-auth' % api.portal.get().absolute_url()

        try:
            flow.fetch_token(code=code)
        except [InvalidGrantError]:
            logger.debug("Code was invalid, could not get tokens")
            message = _(u'Authorization failed. Google Analytics for '
                        u'Plone received an invalid token.')
        else:
            logger.debug(
                "Code was valid, got '%s' as access_token and '%s' as "
                "refresh_token. Token will expire on '%s'" %
                (flow.credentials.token,
                    flow.credentials.refresh_token,
                    flow.credentials.expiry))
            self._update_credentials(flow.credentials)
            message = _(u'Authorization succeeded. You may now configure '
                        u'Google Analytics for Plone.')

        return message

    @security.public
    def auth_url(self, key=None, secret=None):
        safeWrite(self)

        # Special case to wipe our stored secrets
        if key == '' or secret == '':
            self._state = {}
            return
        elif self._state is None:
            return
        elif key is None or secret is None:
            key = self._state.get('client_id', None)
            secret = self._state.get('client_secret', None)
            if not key or not secret:
                return

        client_config = dict(client_id=key,
                             client_secret=secret,
                             auth_uri="https://accounts.google.com/o/oauth2/auth",
                             token_uri="https://accounts.google.com/o/oauth2/token")

        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            dict(web=client_config), scopes=SCOPES)

        # The URI created here must exactly match one of the authorized redirect URIs
        # for the OAuth 2.0 client, which you configured in the API Console. If this
        # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
        # error.
        flow.redirect_uri = '%s/analytics-auth' % api.portal.get().absolute_url()

        authorization_url, state = flow.authorization_url(
            # Enable offline access so that you can refresh an access token without
            # re-prompting the user for permission. Recommended for web server apps.
            access_type='offline',
            # Enable incremental authorization. Recommended as a best practice.
            include_granted_scopes='true')

        # Store the state so the callback can verify the auth server response.
        self._state = client_config

        return authorization_url

    def get_settings(self):
        registry = getUtility(IRegistry)
        records = registry.forInterface(IAnalyticsSchema)
        return records


InitializeClass(Analytics)
