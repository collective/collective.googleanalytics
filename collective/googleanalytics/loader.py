from zope.interface import implements
from zope.component import getMultiAdapter
from zope.publisher.browser import BrowserPage
from bbb import ViewPageTemplateFile
from plone.memoize.instance import memoize
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics.interfaces.loader import IAnalyticsAsyncLoader
from collective.googleanalytics.interfaces.report import IAnalyticsReportRenderer
from collective.googleanalytics import error
from string import Template
import time
import os
from collective.googleanalytics import GoogleAnalyticsMessageFactory as _

class DefaultAnalyticsAsyncLoader(object):
    
    implements(IAnalyticsAsyncLoader)
    
    def __init__(self, context):
        self.context = context
    
    @memoize
    def getContainerId(self):

        return 'analytics-%s' % str(hash(time.time()))
    
    def getJavascript(self, report_ids, profile_id, date_range='month', container_id=None):
        if not report_ids or not profile_id:
            return ''
            
        if not container_id:
            container_id = self.getContainerId()
            
        analytics_tool = getToolByName(self.context, 'portal_analytics')
        reports = []
        packages = []
        for report_id in report_ids:
            try:
                report = analytics_tool[report_id]
                reports.append(report_id)
                package = report.viz_type.lower()
                if not package in packages and not package == 'none':
                    packages.append(package)
            except KeyError:
                continue
                
        url_tool = getToolByName(self.context, 'portal_url')
        portal_url = url_tool.getPortalObject().absolute_url()
        
        template_file = os.path.join(os.path.dirname(__file__), 'loader.tpl')
        template = Template(open(template_file).read())
        
        template_vars = {
            'visualization_packages': '[%s]' % ', '.join(["'%s'" % p for p in packages]), 
            'container_id': container_id, 
            'report_ids': ','.join(reports), 
            'profile_ids': profile_id,
            'portal_url': portal_url,
            'context_url': self.context.absolute_url(),
            'request_url': self.context.REQUEST.ACTUAL_URL, 
            'date_range': date_range,
        }
            
        return template.substitute(template_vars)

class AsyncAnalyticsResults(BrowserPage):
    """
    Returns a HTML snippet for report results to be inserted dynamically
    in the page.
    """
    
    bad_auth = ViewPageTemplateFile('loader_templates/badauth.pt')
    timed_out = ViewPageTemplateFile('loader_templates/timedout.pt')
    
    def __call__(self):
        """
        Returns a list of AnalyticsReportResults objects for the selected reports.
        """
                
        report_ids = self.request.get('report_ids', '').split(',')
        
        if not report_ids:
            return []
            
        analytics_tool = getToolByName(self.context, 'portal_analytics')
        
        results = []
        for report_id in report_ids:
            try:
                report = analytics_tool[report_id]
            except KeyError:
                continue
                
            try:
                renderer = getMultiAdapter(
                    (self.context, self.request, report),
                    interface=IAnalyticsReportRenderer
                )
                results.append(renderer())
            except error.BadAuthenticationError:
                return self.bad_auth()
            except error.RequestTimedOutError:
                return self.timed_out()
                
        # Once we expose the date range optoin in the UI, we'll need to find a
        # way to generate this label dynamically, probably by using the variable
        # date range plugin from one of the report renderers.
        date_range_msg = _('Last 30 Days')
        return '<h2>%s</h2>'%(self.context.translate(date_range_msg)) + '\n'.join(results)
