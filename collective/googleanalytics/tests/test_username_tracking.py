# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from zope.component import getMultiAdapter, queryMultiAdapter, getUtility
from zope.interface import alsoProvides

from collective.googleanalytics.tests.base import FunctionalTestCase
from collective.googleanalytics.interfaces.browserlayer import IAnalyticsLayer
from collective.googleanalytics.interfaces.tracking import IAnalyticsTrackingPlugin


class TestPageAnalytics(FunctionalTestCase):

    def test_js(self):
        self.setRoles(['Manager'])
        context = self.folder
        request = self.folder.REQUEST
        portal_state = getMultiAdapter((context, request), name="plone_portal_state")        
        username = portal_state.member().getId()
        alsoProvides(request, IAnalyticsLayer)

        plugin = getMultiAdapter((context, request),
                                 IAnalyticsTrackingPlugin,
                                 u'User name')
        self.assertEqual(plugin(),
                         u'<script type="text/javascript">\n    /*<![CDATA[*/\n    _gaq.push([\'_setCustomVar\', 2, \'User name\', \'%s\', 2]);\n    /*]]>*/\n</script>\n' \
                         % username.encode('rot13'))

    def test_js_unicode(self):
        self.setRoles(['Manager'])
        context = self.folder
        request = self.folder.REQUEST
        username = u'Foo Bar <foo@bar.com>'
        alsoProvides(request, IAnalyticsLayer)

        plugin = getMultiAdapter((context, request),
                                 IAnalyticsTrackingPlugin,
                                 u'User name')
        plugin.username = lambda: username.encode('rot13')
        self.assertEqual(plugin(),
                         u'<script type="text/javascript">\n    /*<![CDATA[*/\n    _gaq.push([\'_setCustomVar\', 2, \'User name\', \'%s\', 2]);\n    /*]]>*/\n</script>\n' \
                         % username.encode('rot13'))
