
import datetime
import os
import re
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics.interfaces.report import IAnalyticsReportRenderer
from collective.googleanalytics.tests.base import FunctionalTestCase
from collective.googleanalytics.utils import evaluateTALES
from collective.googleanalytics.utils import getDate
from collective.googleanalytics.utils import getTimeDelta
from collective.googleanalytics.utils import unique_list
from string import Template
from zope.component import getMultiAdapter


TEST_FEED = {'rows': [['01', '20100401', '458'], ['02', '20100402', '274'], ['03', '20100403', '150'], ['04', '20100404', '160'], ['05', '20100405', '376'], ['06', '20100406', '453'], ['07', '20100407', '579'], ['08', '20100408', '520'], ['09', '20100409', '369'], ['10', '20100410', '161'], ['11', '20100411', '205'], ['12', '20100412', '482'], ['13', '20100413', '539'], ['14', '20100414', '473'], ['15', '20100415', '485'], ['16', '20100416', '317'], ['17', '20100417', '157'], ['18', '20100418', '206'], ['19', '20100419', '446'], ['20', '20100420', '517'], ['21', '20100421', '439'], ['22', '20100422', '436'], ['23', '20100423', '365'], ['24', '20100424', '153'], ['25', '20100425', '183'], ['26', '20100426', '441'], ['27', '20100427', '668'], ['28', '20100428', '493'], ['29', '20100429', '455'], ['30', '20100430', '192']], 'columnHeaders': [{'dataType': None, 'columnType': 'Dimension', 'name': 'ga:day'}, {'dataType': None, 'columnType': 'Dimension', 'name': 'ga:date'}, {'dataType': 'integer', 'columnType': 'Metric', 'name': 'ga:visits'}]}

# def xml_to_v3(xml):
#     from gdata.analytics import AnalyticsDataFeedFromString
#     feed = AnalyticsDataFeedFromString(feed_xml)
#     feed_json = dict(rows=[[v.value for v in r.dimension + r.metric] for r in feed.entry])
#     feed_json["columnHeaders"] = [dict(name=h.name, columnType=h.__class__.__name__, dataType=h.type) for h in feed.entry[0].dimension + feed.entry[0].metric]
#     return feed_json


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
        # feed_xml_file = os.path.join(os.path.dirname(__file__), 'data_feed.xml')
        # feed_xml = open(feed_xml_file).read()
        renderer = getMultiAdapter(
            (context, request, report),
            interface=IAnalyticsReportRenderer
        )

        # Set the test data feed.
        renderer._data_feed = TEST_FEED

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
