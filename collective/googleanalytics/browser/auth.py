from zope.publisher.browser import BrowserPage
from Products.CMFCore.utils import getToolByName
from zope.i18nmessageid import MessageFactory
from gdata.service import NonAuthSubToken, TokenUpgradeFailed
import gdata.analytics.service
import gdata.auth
_ = MessageFactory('collective.googleanalytics')

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
        clients = analytics_tool.getClients()
        
        # Check if we are revoking the token.
        if self.request.get('revoke_token', 0):
            analytics_tool.auth_token = None
            try:
                clients.data.RevokeAuthSubToken()
            except NonAuthSubToken:
                # Authorization already revoked
                pass
                
            message = _(u'Authorization revoked. You may now reauthorize with \
                a different Google account.')
            plone_utils.addPortalMessage(message)
            
        # Otherwise, we are setting the token.
        elif self.request.QUERY_STRING and 'token' in self.request:
            current_url = '%s?%s' % (self.request.ACTUAL_URL, self.request.QUERY_STRING)
            single_token = gdata.auth.extract_auth_sub_token_from_url(current_url)
            
            try:
                session_token = clients.data.upgrade_to_session_token(single_token)

                # Save a string representation of the token.
                analytics_tool.auth_token = unicode(session_token.get_token_string())

                # Set the token on the two servcies using SetAuthSubToken.
                clients.data.SetAuthSubToken(session_token)
                clients.accounts.SetAuthSubToken(session_token)
            
                message = _(u'Authorization succeeded. You may now configure \
                Google Analytics for Plone.')
                
            except TokenUpgradeFailed:
                message = _(u'Authorization failed. Google Analytics for \
                    Plone received an invalid token.')
                
            plone_utils.addPortalMessage(message)
            
        # Redirect back to the control panel.
        portal_url = getToolByName(self.context, 'portal_url')
        next_url = '%s/portal_analytics/@@analytics-controlpanel' % portal_url()
        self.request.response.redirect(next_url)
        