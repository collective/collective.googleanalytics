import unittest
import datetime
import os
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics.tests.base import FunctionalTestCase
from collective.googleanalytics.report import AnalyticsReport
from gdata.analytics import AnalyticsDataFeedFromString

class TestReports(FunctionalTestCase):

    def test_default_expression_context(self):
        """
        Test that the default expression context used to render TAL and TALES in the
        Analytics report is populated with the correct objects.
        """
        
        report = AnalyticsReport('foo')
        exp_context = report._getExpressionContext(self.portal)
        
        expression = 'python:[context, request, today, date, timedelta, page_url]'
        
        RESULT = [
            self.portal,
            self.portal.REQUEST,
            datetime.date.today(),
            report._getDate,
            report._getTimeDelta,
            self.portal.REQUEST.ACTUAL_URL.replace(self.portal.REQUEST.SERVER_URL, '')
        ]
        
        evaluated_exp = report._evaluateExpression(expression, exp_context)
        
        self.assertEqual(evaluated_exp, RESULT)
        
    def test_report_returns_correct_results(self):
        """
        Test that the report's getResults method produces an AnalyticsReportResults object
        with the correct values.
        """
        
        analytics_tool = getToolByName(self.portal, 'portal_analytics', None)
        
        # Load the example feed data from a file.
        feed_xml_file = os.path.join(os.path.dirname(__file__), 'data_feed.xml')
        feed_xml = open(feed_xml_file).read()
        feed = AnalyticsDataFeedFromString(feed_xml)
        
        # Create a report.
        report = AnalyticsReport(id='results-test',
            title='Site Visits This Month: Line Chart',
            description='Displays the number of site visits for the last 30 days as a line graph.',
            i18n_domain='analytics',
            is_page_specific=False,
            metrics=['ga:visits'],
            dimensions=['ga:day', 'ga:month'],
            filters=[],
            sort=['ga:month'],
            start_date='python:today - timedelta(days=30)',
            end_date='today',
            max_results=1000,
            column_labels=['string:Day', 'string:Visits'],
            column_exps=['python:str(ga_day)', 'python:int(ga_visits)'],
            introduction='',
            conclusion='''<p><strong tal:content="python:sum(data_columns[1])">1000</strong> visits this month</p>
                <p><strong tal:content="python:int(sum(data_columns[1])/len(data_columns[1]))">1000</strong> 
                average visits per day</p>''',
            viz_type='LineChart',
            viz_options=[
            'title string:Site Visits this Month',
            'height python:250',
            'legend string:none',
            'titleX string:Day',
            'titleY string:Visits',
            'axisFontSize python:10',
            ]
        )
                
        # Set the aquisition parent for the report.
        report.aq_parent = analytics_tool
        
        # Get the results object.
        results = report.getResults(self.portal, profile=12345, data_feed=feed)
        
        # Load the expected results.
        results_js_file = os.path.join(os.path.dirname(__file__), 'report_results.js')
        results_js = open(results_js_file).read()
        
        # Test that the results match what we expect.
        self.assertEqual(results.getVizJS(), results_js)
        

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestReports))
    return suite