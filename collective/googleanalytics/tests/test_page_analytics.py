# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from zope.component import getMultiAdapter, queryMultiAdapter, getUtility
from zope.interface import alsoProvides

from collective.googleanalytics.tests.base import FunctionalTestCase
from collective.googleanalytics.interfaces.browserlayer import IAnalyticsLayer


class TestPageAnalytics(FunctionalTestCase):

    def test_get_images(self):
        self.setRoles(['Manager'])
        context = self.folder
        request = self.folder.REQUEST
        alsoProvides(request, IAnalyticsLayer)
        
        view = getMultiAdapter((context, request), name='page-analytics-reports')
        self.assertTrue('analytics-async-container' in view())
