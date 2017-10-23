# -*- coding: utf-8 -*-
from collective.googleanalytics.interfaces.tracking import IAnalyticsTrackingPlugin
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone import api
from plone.app.layout.analytics.view import AnalyticsViewlet
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
        analytics_tool = api.portal.get_tool(name="portal_analytics")
        self.analytics_settings = analytics_tool.get_settings()

    def available(self):
        """
        Checks to see whether the viewlet should be rendered based on the role
        of the user and the selections for excluded roles in the configlet.
        """
        member = api.user.get_current()
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

    def ga_events(self):
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
                plugin.set_view(self.view)
                results.append(plugin())
        status = self.request.response.getStatus()
        if status >= 400:
            results.append('')  # XXX
            #    ("'/error/%s?page=' + document.location.pathname + "
            #     "document.location.search + '&from=' + document.referrer")
            #    % status)
        elif self.view.__name__.startswith("search"):
            results.append('')   # XXX
            # query = {'q': self.request.get('SearchableText', ''),
            #         'searchcat': self.getsearchcat()}
            # results.append("'/searchresult?%s'" % urlencode(query))
        return '\n'.join(results)

    def getsearchcat(self):
        return self.view.__name__
