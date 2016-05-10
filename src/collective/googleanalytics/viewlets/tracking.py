import sys
from urllib import urlencode
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
        super(AnalyticsTrackingViewlet, self).__init__(context, request, view, manager)
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

        return self.analytics_tool.__dict__.get('tracking_web_property', None)

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

    def getsearchcat(self):
        return self.view.__name__

    def renderPageview(self):
        push_params = ["'_trackPageview'"]
        exc_info = sys.exc_info()[0]
        if self.view.__name__.startswith("search"):
            query = {'q': self.request.get('SearchableText', ''),
                     'searchcat': self.getsearchcat()}
            push_params.append("'/searchresult?%s'" % urlencode(query))
        elif exc_info is not None:
            if exc_info == NotFound:
                errorcode = 404
            else:
                errorcode = 500
            push_params.append(
            ("'/error/%s?page=' + document.location.pathname + "
             "document.location.search + '&from=' + document.referrer")
            % errorcode)
        return "_gaq.push([%s]);" % ', '.join(push_params)
