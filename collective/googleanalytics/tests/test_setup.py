import unittest
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics.tests.base import FunctionalTestCase
from collective.googleanalytics.report import AnalyticsReport

class TestInstall(FunctionalTestCase):

    def test_installation_creates_tool(self):
        """
        Test that the portal_analytics tool is created.
        """
        analytics_tool = getToolByName(self.portal, 'portal_analytics', None)
        self.assertNotEqual(analytics_tool, None)
        
    def test_installation_creates_reports(self):
        """
        Test that the Analytics reports defined in analytics.xml are
        imported correctly.
        """
        analytics_tool = getToolByName(self.portal, 'portal_analytics', None)
        
        # Test the 'Site Visits: Line Chart' report.
        report = analytics_tool.get('site-visits-line', None)
        self.assertNotEqual(report, None)
        self.assertEqual(report.title, 'Site Visits: Line Chart')
        self.assertTrue('ga:visits' in report.metrics)
        
        # Test the 'Top 5 Page Views: Table' report.
        report = analytics_tool.get('top-5-pageviews-table', None)
        self.assertNotEqual(report, None)
        self.assertEqual(report.column_labels, ('string:URL', 'string:Views'))
        self.assertEqual(report.column_exps, ('ga_pagePath', 'ga_pageviews'))
        
        # Test the 'Top 5 Sources: Table' report.
        report = analytics_tool.get('top-5-sources-table', None)
        self.assertNotEqual(report, None)
        self.assertEqual(report.viz_type, 'Table')
        self.assertNotEqual(report.introduction, '')
        self.assertEqual(report.conclusion, '')

class TestReinstall(FunctionalTestCase):

    def test_reinstallation_preserves_settings(self):
        """
        Test that reinstalling the product does not wipe out the settings
        stored on the portal_analytics tool.
        """
        # Set some properties on the portal_analytics tool.
        analytics_tool = getToolByName(self.portal, 'portal_analytics')
        analytics_tool.email = u'john@doe.com'
        analytics_tool.password = u'J0hnD03'
        analytics_tool.cache_interval = 100

        # Reinstall the product.
        self.setRoles(['Manager'])
        quick_installer = getToolByName(self.portal, "portal_quickinstaller")
        quick_installer.reinstallProducts(products=['collective.googleanalytics',])

        # Make sure the properties are still set.
        analytics_tool = getToolByName(self.portal, 'portal_analytics')
        self.assertEqual(analytics_tool.email, u'john@doe.com')
        self.assertEqual(analytics_tool.password, u'J0hnD03')
        self.assertEqual(analytics_tool.cache_interval, 100)
        
    def test_reinstallation_preserves_reports(self):
        """
        Test that reinstalling the product does not wipe out custom reports.
        """        
        # Make some reports.
        analytics_tool = getToolByName(self.portal, 'portal_analytics')
        analytics_tool['foo'] = AnalyticsReport('foo')
        analytics_tool['bar'] = AnalyticsReport('bar')

        # Reinstall the product.
        self.setRoles(['Manager'])
        quick_installer = getToolByName(self.portal, "portal_quickinstaller")
        quick_installer.reinstallProducts(products=['collective.googleanalytics',])

        # Make sure the reports are still there.
        analytics_tool = getToolByName(self.portal, 'portal_analytics')
        report = analytics_tool.get('foo', None)
        self.assertNotEqual(report, None)
        
        report = analytics_tool.get('bar', None)
        self.assertNotEqual(report, None)
        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestInstall))
    suite.addTest(unittest.makeSuite(TestReinstall))
    return suite