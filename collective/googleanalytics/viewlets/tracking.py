from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode

from plone.app.layout.analytics.view import AnalyticsViewlet

class AnalyticsTrackingViewlet(AnalyticsViewlet):
    """
    A viewlet that inserts the Google Analytics tracking code 
    at the end of the page. We override the default Plone viewlet
    so that we can exclude the code for certain roles.
    """

    def __init__(self, context, request, view, manager):
        super(AnalyticsViewlet, self).__init__(context, request)
        self.analytics_tool = getToolByName(context, "portal_analytics")
        self.properties_tool = getToolByName(context, "portal_properties")
        self.membership_tool = getToolByName(context, "portal_membership")

    def render(self):
        """
        Render the web stats code if the user does not have one
        of the excluded roles.
        """
        
        member = self.membership_tool.getAuthenticatedMember()
        
        for role in self.analytics_tool.tracking_excluded_roles:
            if member.has_role(role):
                return ''
        
        snippet = safe_unicode(self.properties_tool.site_properties.webstats_js)
        return snippet

