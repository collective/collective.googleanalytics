from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from collective.googleanalytics.interfaces.loader import IAnalyticsAsyncLoader


class Reports(BrowserView):
    """
    A view that displays the reports available for the context.
    """
    
    def __init__(self, context, request):
        """
        """
        self.context = context
        self.request = request
        self.analytics_tool = getToolByName(self.context,'portal_analytics', None)
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
        profile = getattr(self.analytics_tool, 'reports_profile', None)
        reports = ['page-top-users-table',]
        date_range = self.request.get('date_range', 'year')
        return self.async_loader.getJavascript(reports, profile, date_range)
