
import logging
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics import GoogleAnalyticsMessageFactory as _
from zope.publisher.browser import BrowserPage
from plone.protect.interfaces import IDisableCSRFProtection
from zope.interface import alsoProvides

logger = logging.getLogger('collective.googleanalytics')


class AnalyticsAuth(BrowserPage):
    """
    Browser view to receive the Google AuthSub token.
    """

    def __call__(self):
        """
        Gets the token from the URL and takes the appropriate action.
        """
        alsoProvides(self.request, IDisableCSRFProtection)

        analytics_tool = getToolByName(self.context, 'portal_analytics')
        plone_utils = getToolByName(self.context, 'plone_utils')

        # Check if we are revoking the token.
        if self.request.get('revoke_token', 0):
            analytics_tool.revoke_token()
            message = _(u'Authorization revoked. You may now reauthorize with \
                a different Google account.')
            plone_utils.addPortalMessage(message)

        # Otherwise, we are setting the token.
        elif self.request.QUERY_STRING and 'code' in self.request:
            code = self.request.get('code')
            message = analytics_tool.set_token(code)
            plone_utils.addPortalMessage(message)

        # Redirect back to the control panel.
        portal_url = getToolByName(self.context, 'portal_url')
        next_url = '%s/portal_analytics/@@analytics-controlpanel' % portal_url()
        self.request.response.redirect(next_url)
