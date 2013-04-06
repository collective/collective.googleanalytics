# -*- coding: utf-8 -*-

from collective.googleanalytics.testing import INTEGRATION_TESTING
from collective.googleanalytics.interfaces.browserlayer import IAnalyticsLayer
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getMultiAdapter
from zope.interface import directlyProvides

import unittest2 as unittest


class ControlPanelTestCase(unittest.TestCase):

    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        # XXX: the control panel view is registered only for the package's
        #      browser layer
        self.request = self.layer['request']
        directlyProvides(self.request, IAnalyticsLayer)

        self.controlpanel = self.portal['portal_controlpanel']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    @unittest.skip("FIXME: ComponentLookupError")
    def test_controlpanel_has_view(self):
        view = getMultiAdapter((self.portal, self.request),
                               name='analytics-controlpanel')
        view = view.__of__(self.portal)
        self.assertTrue(view())

    def test_controlpanel_view_is_protected(self):
        from AccessControl import Unauthorized
        logout()
        # XXX: shouldn't control panel view live only in Plone's root?
        #      get rid of 'portal_analytics'
        self.assertRaises(Unauthorized,
                          self.portal.restrictedTraverse,
                          'portal_analytics/@@analytics-controlpanel')

    def test_controlpanel_installed(self):
        actions = [a.getAction(self)['id']
                   for a in self.controlpanel.listActions()]
        self.assertTrue('Analytics' in actions,
                        'control panel was not installed')

    # FIXME: control panel configlet is not being removed on unistall
    @unittest.expectedFailure
    def test_controlpanel_removed_on_uninstall(self):
        qi = self.portal['portal_quickinstaller']
        qi.uninstallProducts(products=['collective.googleanalytics'])
        actions = [a.getAction(self)['id']
                   for a in self.controlpanel.listActions()]
        self.assertTrue('Analytics' not in actions,
                        'control panel was not removed')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ControlPanelTestCase))
    return suite
