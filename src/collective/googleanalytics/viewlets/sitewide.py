
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.googleanalytics.interfaces.loader import IAnalyticsAsyncLoader
from plone.app.layout.viewlets import ViewletBase


class SiteWideAnalyticsViewlet(ViewletBase):
    """
    A viewlet that displays the results of the reports selected in the Analytics
    control panel.
    """

    render = ViewPageTemplateFile('sitewide.pt')

    def update(self):
        """
        Initialize the viewlet.
        """
        super(SiteWideAnalyticsViewlet, self).update()
        analytics_tool = getToolByName(self.context, 'portal_analytics', None)
        self.async_loader = IAnalyticsAsyncLoader(self.context)
        self.analytics_settings = analytics_tool.get_settings()

    def available(self):
        """
        Returns True if there are site-wide reports selected.
        """

        profile = getattr(self.analytics_settings, 'reports_profile', None)
        reports = getattr(self.analytics_settings, 'reports', None)
        if reports and profile:
            return True
        return False

    def getContainerId(self):
        """
        Returns the element ID for the results container.
        """

        return self.async_loader.getContainerId()

    def getJavascript(self):
        """
        Returns a list of AnalyticsReportResults objects for the selected reports.
        """

        profile = getattr(self.analytics_settings, 'reports_profile', None)
        reports = getattr(self.analytics_settings, 'reports', None)
        return self.async_loader.getJavascript(reports, profile)
