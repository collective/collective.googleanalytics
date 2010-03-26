import unittest
import datetime
import os
import re
from string import Template
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
            title='Site Visits: Line Chart',
            description='Displays the number of site visits as a line graph.',
            i18n_domain='analytics',
            is_page_specific=False,
            categories=['Site Wide',],
            metrics=['ga:visits'],
            dimensions=['date_range_dimension', 'date_range_sort_dimension'],
            filters=[],
            sort=['date_range_sort_dimension', 'date_range_dimension'],
            max_results=1000,
            column_labels=['python:date_range_unit', 'string:Visits'],
            column_exps=['python:str(date_range_dimension)', 'python:int(ga_visits)'],
            introduction='',
            conclusion='''<p tal:condition="data_length"><strong tal:content="python:sum(data_columns[1])">1000</strong> visits in the last <span tal:replace="string:${data_length} ${date_range_unit_plural/lower}"></span></p>
            <p tal:condition="data_length"><strong tal:content="python:int(sum(data_columns[1])/len(data_columns[1]))">1000</strong> 
            average visits per <span tal:replace="string:${date_range_unit/lower}"></span></p>''',
            viz_type='LineChart',
            viz_options=[
            'title string:Site Visits',
            'height python:250',
            'legend string:none',
            'titleX python:date_range_unit',
            'titleY string:Visits',
            'axisFontSize python:10',
            ]
        )
                
        # Set the aquisition parent for the report.
        report.aq_parent = analytics_tool
        
        # Get the results object.
        results = report.getResults(self.portal, profile=12345, data_feed=feed)
        
        # Load the expected results.
        results_js_file = os.path.join(os.path.dirname(__file__), 'report_results.js.tpl')
        template = Template(open(results_js_file).read())
        template_vars = {
            'id': results.getVizID(),
        }
        results_js = template.substitute(template_vars)
        
        # We normalize all whitespace to spaces to avoid getting false
        # negatives.
        whitespace = re.compile(r'\s+')
        
        # Test that the results match what we expect.
        self.assertEqual(
            re.sub(whitespace, ' ', results.getVizJS()).strip(),
            re.sub(whitespace, ' ', results_js).strip()
        )

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestReports))
    return suite