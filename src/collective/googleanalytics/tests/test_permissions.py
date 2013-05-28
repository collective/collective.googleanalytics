import unittest
from Acquisition import aq_inner
from zope.component import getUtility, getMultiAdapter

from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletRenderer

from collective.googleanalytics.tests.base import FunctionalTestCase
from collective.googleanalytics.portlets import analyticsportlet

class TestPortlet(FunctionalTestCase):

    def test_portlet_available_to_correct_roles(self):
        """
        Test that the Analytics portlet is only available to users with
        the ViewAnalyticsResults permission (Managers by default).
        """

        self.setRoles(['Manager'])
        
        context = self.folder
        request = self.folder.REQUEST
        # Simulate being on the default view.
        request.set('ACTUAL_URL', aq_inner(context).absolute_url() + '/view')
        view = self.folder.restrictedTraverse('@@plone')
        manager = getUtility(IPortletManager, name='plone.leftcolumn', context=self.portal)
        assignment = analyticsportlet.Assignment()
        renderer = getMultiAdapter((context, request, view, manager, assignment), IPortletRenderer)
        
        self.assertEquals(renderer.available, True)
        

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPortlet))
    return suite