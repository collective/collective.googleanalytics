from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from plone.app.layout.viewlets import ViewletBase

from collective.googleanalytics import error

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
        
    def getDateRangeLabel(self):
        """
        Returns a string the describes the date range that corresponds to
        the resutls.
        """

        return 'Last 30 Days'
        
    def getResults(self):
        """
        Returns a list of AnalyticsReportResults objects for the selected reports.
        """
        profile = getattr(self.analytics_tool, 'profile', None)
        reports = getattr(self.analytics_tool, 'reports', None)
        if not profile or not reports:
            return []
        
        results = []
        for report_id in reports:
            try:
                report = self.analytics_tool[report_id]
            except KeyError:
                continue

            try:
                results.append(report.getResults(self.context, profile, date_range='month'))
            except error.BadAuthenticationError:
                return 'BadAuthenticationError'
            except error.MissingCredentialsError:
                return 'MissingCredentialsError'

        return results
