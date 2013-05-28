import unittest
import datetime
import os
import re
from string import Template
from zope.component import getMultiAdapter
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics.tests.base import FunctionalTestCase
from collective.googleanalytics.interfaces.report import IAnalyticsReportRenderer
from collective.googleanalytics.utils import evaluateTALES, getDate, getTimeDelta, unique_list
from gdata.analytics import AnalyticsDataFeedFromString

class TestReports(FunctionalTestCase):

    def test_default_expression_context(self):
        """
        Test that the default expression context used to render TAL and TALES in the
        Analytics report is populated with the correct objects.
        """
        
        analytics_tool = getToolByName(self.portal, 'portal_analytics', None)
        report = analytics_tool['site-visits-line']

        context = self.portal
        request = self.portal.REQUEST
        
        renderer = getMultiAdapter(
            (context, request, report),
            interface=IAnalyticsReportRenderer
        )
                
        expression = 'python:[context, request, today, date, timedelta, unique_list]'
        
        result = [
            self.portal,
            self.portal.REQUEST,
            datetime.date.today(),
            getDate,
            getTimeDelta,
            unique_list,
        ]
        
        exp_context = renderer._getExpressionContext()
        evaluated_exp = evaluateTALES(expression, exp_context)
        self.assertEqual(evaluated_exp, result)
        
    def test_report_returns_correct_results(self):
        """
        Test that the report's getResults method produces an AnalyticsReportResults object
        with the correct values.
        """
        
        analytics_tool = getToolByName(self.portal, 'portal_analytics', None)
        report = analytics_tool['site-visits-line']
        
        context = self.portal
        request = self.portal.REQUEST
        
        # Set the start and end date in the request.
        request.set('start_date', '20100401')
        request.set('end_date', '20100430')
        
        # Load the example feed data from a file.
        feed_xml_file = os.path.join(os.path.dirname(__file__), 'data_feed.xml')
        feed_xml = open(feed_xml_file).read()
        feed = AnalyticsDataFeedFromString(feed_xml)
            
        renderer = getMultiAdapter(
            (context, request, report),
            interface=IAnalyticsReportRenderer
        )
        
        # Set the test data feed.
        renderer._data_feed = feed
        
        # Render the results.
        results = renderer()
        
        # Load the expected results.
        results_js_file = os.path.join(os.path.dirname(__file__), 'report_results.tpl')
        template = Template(open(results_js_file).read())
        template_vars = {
            'id': renderer._getVisualization().id(),
        }
        results_js = template.substitute(template_vars)
        
        # We normalize all whitespace to spaces to avoid getting false
        # negatives.
        whitespace = re.compile(r'\s+')
        
        # Test that the results match what we expect.
        self.assertEqual(
            re.sub(whitespace, ' ', results).strip(),
            re.sub(whitespace, ' ', results_js).strip()
        )

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestReports))
    return suite