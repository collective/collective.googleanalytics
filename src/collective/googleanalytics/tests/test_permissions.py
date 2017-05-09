
import unittest
from Acquisition import aq_inner
from collective.googleanalytics.portlets import analyticsportlet
from collective.googleanalytics.tests.base import FunctionalTestCase
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletRenderer
from zope.component import getMultiAdapter
from zope.component import getUtility


class TestPortlet(FunctionalTestCase):

    def test_portlet_available_to_correct_roles(self):
        """
        Test that the Analytics portlet is only available to users with
        the ViewAnalyticsResults permission (Managers by default).
        """
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        context = self.portal
        request = self.layer['request']
        # Simulate being on the default view.
        request.set('ACTUAL_URL', aq_inner(context).absolute_url() + '/view')
        view = self.portal.restrictedTraverse('@@plone')
        manager = getUtility(IPortletManager, name='plone.leftcolumn', context=self.portal)
        assignment = analyticsportlet.Assignment()
        renderer = getMultiAdapter((context, request, view, manager, assignment), IPortletRenderer)

        self.assertEquals(renderer.available, True)
