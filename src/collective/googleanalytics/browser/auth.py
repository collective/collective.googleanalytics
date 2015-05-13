from zope.publisher.browser import BrowserPage
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics import GoogleAnalyticsMessageFactory as _
from collective.googleanalytics.browser.controlpanel import get_flow


class AnalyticsAuth(BrowserPage):
    """
    Browser view to receive the Google AuthSub token.
    """

    def __call__(self):
        """
        [TODO] Tests here. Not sure for these clients.data and clients.accounts
        For OAuth2:
            gets the code from URL
            gets the credentials based on flow and code
            gets token from credentials
            takes the appropriate action
        """
        code = self.context.REQUEST.form.get('code', None)

        analytics_tool = getToolByName(self.context, 'portal_analytics')
        plone_utils = getToolByName(self.context, 'plone_utils')
        clients = analytics_tool.getClients()

        # Check if we are revoking the token.
        if self.request.get('revoke_token', 0):
            analytics_tool.auth_token = None

            clients.data = ''

            message = _(u'Authorization revoked. You may now reauthorize with \
                a different Google account.')
            plone_utils.addPortalMessage(message)

        # Otherwise, we are setting the token.
        elif code is not None:
            flow = get_flow()
            credentials = flow.step2_exchange(code)
            token_response = credentials.token_response
            access_token = token_response.get('access_token')

            analytics_tool.auth_token = access_token
            clients.data = access_token
            clients.accounts = access_token

            message = _(u'Authorization succeeded. You may now configure \
            Google Analytics for Plone.')
            plone_utils.addPortalMessage(message)

        # Redirect back to the control panel.
        portal_url = getToolByName(self.context, 'portal_url')
        next_url = '%s/portal_analytics/@@analytics-controlpanel' % \
            portal_url()
        self.request.response.redirect(next_url)
