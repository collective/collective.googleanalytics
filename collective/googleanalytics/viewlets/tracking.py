from zope.component import queryMultiAdapter
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.analytics.view import AnalyticsViewlet
from collective.googleanalytics.interfaces.tracking import IAnalyticsTrackingPlugin

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

        return getattr(self.analytics_tool, 'tracking_web_property', None)
        
    def renderPlugins(self):
        """
        Render each of the selected tracking plugins for the current context
        and request.
        """
        
        results = []
        for plugin_name in self.analytics_tool.tracking_plugin_names:
            plugin = queryMultiAdapter(
                (self.context, self.request),
                interface=IAnalyticsTrackingPlugin,
                name=plugin_name,
                default=None,
            )
            if plugin:
                results.append(plugin())
        return '\n'.join(results)

