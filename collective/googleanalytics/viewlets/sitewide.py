from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from plone.app.layout.viewlets import ViewletBase
from collective.googleanalytics.interfaces.loader import IAnalyticsAsyncLoader


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
        self.analytics_tool = getToolByName(self.context, 'portal_analytics', None)
        self.async_loader = IAnalyticsAsyncLoader(self.context)
        
    def getContainerId(self):
        """
        Returns the element ID for the results container.
        """
        
        return self.async_loader.getContainerId()

    def getJavascript(self):
        """
        Returns a list of AnalyticsReportResults objects for the selected reports.
        """
        
        profile = getattr(self.analytics_tool, 'profile', None)
        reports = getattr(self.analytics_tool, 'reports', None)
        return self.async_loader.getJavascript(reports, profile)
