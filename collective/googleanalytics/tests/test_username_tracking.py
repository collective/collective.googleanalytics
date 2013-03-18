# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from zope.component import getMultiAdapter, queryMultiAdapter, getUtility
from zope.interface import alsoProvides

from collective.googleanalytics.tests.base import FunctionalTestCase
from collective.googleanalytics.interfaces.browserlayer import IAnalyticsLayer
from collective.googleanalytics.interfaces.tracking import IAnalyticsTrackingPlugin


class TestPageAnalytics(FunctionalTestCase):

    def test_get_images(self):
        self.setRoles(['Manager'])
        context = self.folder
        request = self.folder.REQUEST
        alsoProvides(request, IAnalyticsLayer)
        
        plugin = getMultiAdapter((context, request),
                                 IAnalyticsTrackingPlugin,
                                 u'User name')
        self.assertEqual(plugin(),
                         u'<script type="text/javascript">\n    /*<![CDATA[*/\n    _gaq.push([\'_setCustomVar\', 2, \'User name\', \'test_user_1_\', 2]);\n    /*]]>*/\n</script>\n')
