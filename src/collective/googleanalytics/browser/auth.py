
from zope.annotation import IAnnotations

from zope.publisher.browser import BrowserPage
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics import error
from collective.googleanalytics import GoogleAnalyticsMessageFactory as _
from gdata.gauth import OAuth2RevokeError
from gdata.gauth import OAuth2AccessTokenError

import socket

import logging
logger = logging.getLogger('collective.googleanalytics')


class AnalyticsAuth(BrowserPage):
    """
    Browser view to receive the Google AuthSub token.
    """

    def __call__(self):
        """
        Gets the token from the URL and takes the appropriate action.
        """

        analytics_tool = getToolByName(self.context, 'portal_analytics')
        plone_utils = getToolByName(self.context, 'plone_utils')

        # Check if we are revoking the token.
        if self.request.get('revoke_token', 0):
            logger.debug("Trying to revoke token")
            ann = IAnnotations(analytics_tool)
            try:
                oauth2_token = ann.get('auth_token', None)
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

            ann['auth_token'] = None
            ann['valid_token'] = False

            message = _(u'Authorization revoked. You may now reauthorize with \
                a different Google account.')
            plone_utils.addPortalMessage(message)

        # Otherwise, we are setting the token.
        elif self.request.QUERY_STRING and 'code' in self.request:
            code = self.request.get('code')
            logger.debug(
                "Received callback from Google with code '%s' " % code
            )
            ann = IAnnotations(analytics_tool)
            oauth2_token = ann.get('auth_token', None)
            try:
                oauth2_token.get_access_token(code)
                logger.debug(
                    "Code was valid, got '%s' as access_token and '%s' as "
                    "refresh_token. Token will expire on '%s'" %
                    (oauth2_token.access_token,
                     oauth2_token.refresh_token,
                     oauth2_token.token_expiry))
                message = _(u'Authorization succeeded. You may now configure \
                Google Analytics for Plone.')
                ann['valid_token'] = True

            except OAuth2AccessTokenError:
                logger.debug("Code was invalid, could not get tokens")
                ann['auth_token'] = None
                ann['valid_token'] = False
                message = _(u'Authorization failed. Google Analytics for \
                    Plone received an invalid token.')

            plone_utils.addPortalMessage(message)

        # Redirect back to the control panel.
        portal_url = getToolByName(self.context, 'portal_url')
        next_url = '%s/portal_analytics/@@analytics-controlpanel' % portal_url()
        self.request.response.redirect(next_url)
