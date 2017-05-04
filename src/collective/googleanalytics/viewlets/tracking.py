
import sys
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.googleanalytics.interfaces.tracking import IAnalyticsTrackingPlugin
from plone.app.layout.analytics.view import AnalyticsViewlet
from urllib import urlencode
from zExceptions import NotFound
from zope.component import queryMultiAdapter


class AnalyticsTrackingViewlet(AnalyticsViewlet):
    """
    A viewlet that inserts the Google Analytics tracking code
    at the end of the page. We override the default Plone viewlet
    so that we can exclude the code for certain roles.
    """

    render = ViewPageTemplateFile('tracking.pt')

    def __init__(self, context, request, view, manager):
        super(AnalyticsTrackingViewlet, self).__init__(context, request, view, manager)
        analytics_tool = getToolByName(context, "portal_analytics")
        self.membership_tool = getToolByName(context, "portal_membership")
        self.analytics_settings = analytics_tool.get_settings()

    def available(self):
        """
        Checks to see whether the viewlet should be rendered based on the role
        of the user and the selections for excluded roles in the configlet.
        """

        member = self.membership_tool.getAuthenticatedMember()

        for role in self.analytics_settings.tracking_excluded_roles:
            if member.has_role(role):
                return False
        return True

    def getTrackingWebProperty(self):
        """
        Returns the Google web property ID for the selected tracking profile,
        or an empty string if no tracking profile is selected.
        """

        return self.analytics_settings.tracking_web_property

    def renderPlugins(self):
        """
        Render each of the selected tracking plugins for the current context
        and request.
        """

        results = []
        for plugin_name in self.analytics_settings.tracking_plugin_names:
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
        status = self.request.response.getStatus()
        if status >= 400:
            push_params.append(
                ("'/error/%s?page=' + document.location.pathname + "
                 "document.location.search + '&from=' + document.referrer")
                % status)
        elif self.view.__name__.startswith("search"):
            query = {'q': self.request.get('SearchableText', ''),
                     'searchcat': self.getsearchcat()}
            push_params.append("'/searchresult?%s'" % urlencode(query))
        return "_gaq.push([%s]);" % ', '.join(push_params)
