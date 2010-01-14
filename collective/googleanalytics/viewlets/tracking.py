from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.layout.analytics.view import AnalyticsViewlet

class AnalyticsTrackingViewlet(AnalyticsViewlet):
    """
    A viewlet that inserts the Google Analytics tracking code 
    at the end of the page. We override the default Plone viewlet
    so that we can exclude the code for certain roles.
    """

    render = ViewPageTemplateFile('tracking.pt')

    def __init__(self, context, request, view, manager):
        super(AnalyticsViewlet, self).__init__(context, request)
        self.analytics_tool = getToolByName(context, "portal_analytics")
        self.properties_tool = getToolByName(context, "portal_properties")
        self.membership_tool = getToolByName(context, "portal_membership")

    def available(self):
        """
        Checks to see whether the viewlet should be rendered based on the role
        of the user and the selections for excluded roles in the configlet.
        """
                
        member = self.membership_tool.getAuthenticatedMember()
        
        for role in self.analytics_tool.tracking_excluded_roles:
            if member.has_role(role):
                return False
        return True
        
    def getTrackingWebProperty(self):
        """
        Returns the Google web property ID for the selected tracking profile,
        or an empty string if no tracking profile is selected.
        """
        
        return self.analytics_tool.tracking_web_property or None
        
    def getExternalTrackingPrefix(self):
        """
        Returns the prefix to use for tracking external links or False if external
        link tracking is disabled.
        """
        
        if self.analytics_tool.tracking_external_prefix:
            return self.analytics_tool.tracking_external_prefix
        return False
        
    def getMailtoTrackingPrefix(self):
        """
        Returns the prefix to use for tracking e-mail addresses or False if
        e-mail address tracking is disabled.
        """

        if self.analytics_tool.tracking_mailto_prefix:
            return self.analytics_tool.tracking_mailto_prefix
        return False
        
    def getFileTrackingPrefix(self):
        """
        Returns the prefix to use for tracking file downloads or False if
        e-mail address tracking is disabled.
        """

        if self.analytics_tool.tracking_file_prefix:
            return self.analytics_tool.tracking_file_prefix
        return False
        
    def getFileExtensions(self):
        """
        Returns a list of the selected file extensions for tracking.
        """

        if self.analytics_tool.tracking_file_extensions:
            return self.analytics_tool.tracking_file_extensions
        return []
    
    def getExtraTrackingJS(self):
        """
        Gets the extra tracking javascript (i.e. the content of the web stats
        javascript field in the site configlet).
        """
        
        snippet = safe_unicode(self.properties_tool.site_properties.webstats_js)
        return snippet

