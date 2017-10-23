# -*- coding: utf-8 -*-
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.ObjectManager import IFAwareObjectManager
from OFS.OrderedFolder import OrderedFolder
from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from collective.googleanalytics.config import SCOPES
from collective.googleanalytics.interfaces.report import IAnalyticsReport
from collective.googleanalytics.interfaces.utility import IAnalytics
from collective.googleanalytics.interfaces.utility import IAnalyticsSchema
from plone.memoize.volatile import cache
from plone.registry.interfaces import IRegistry
from time import time
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.component import getUtility
from zope.interface import implementer
from zope.schema.fieldproperty import FieldProperty
from httplib import ResponseNotReady
from httplib2 import ServerNotFoundError
from googleapiclient.http import HttpError
from googleapiclient.discovery import build
from googleapiclient.discovery_cache import DISCOVERY_DOC_MAX_AGE
from google.oauth2.service_account import Credentials

import json
import logging


logger = logging.getLogger('collective.googleanalytics')


def account_feed_cachekey(func, instance, feed_path):
    """
    Cache key for the account feed. We only refresh it every ten minutes.
    """

    cache_interval = instance.cache_interval
    cache_interval = (cache_interval > 0 and cache_interval * 60) or 1
    return hash((time() // cache_interval, feed_path))


@implementer(IAnalytics, IAttributeAnnotatable)
class Analytics(PloneBaseTool, IFAwareObjectManager, OrderedFolder):
    """
    Analytics utility
    """

    security = ClassSecurityInfo()

    id = 'portal_analytics'
    meta_type = 'Google Analytics Tool'

    _product_interfaces = (IAnalyticsReport, )

    security.declarePrivate('tracking_web_property')
    tracking_web_property = FieldProperty(IAnalytics['tracking_web_property'])

    security.declarePrivate('tracking_plugin_names')
    tracking_plugin_names = FieldProperty(IAnalytics['tracking_plugin_names'])

    security.declarePrivate('tracking_excluded_roles')
    tracking_excluded_roles = FieldProperty(IAnalytics['tracking_excluded_roles'])

    security.declarePrivate('reports_profile')
    reports_profile = FieldProperty(IAnalytics['reports_profile'])

    security.declarePrivate('reports')
    reports = FieldProperty(IAnalytics['reports'])

    security.declarePrivate('cache_interval')
    cache_interval = FieldProperty(IAnalytics['cache_interval'])

    security.declarePrivate('report_categories')
    report_categories = FieldProperty(IAnalytics['report_categories'])

    security.declarePrivate('_v_temp_clients')
    _v_temp_clients = None

    security.declarePrivate('_getAuthenticatedClient')
    security.declarePrivate('is_auth')
    security.declarePrivate('makeClientRequest')
    security.declarePrivate('getReports')
    security.declarePrivate('getCategoriesChoices')
    security.declarePrivate('getAccountsFeed')

    def is_auth(self):
        return self.ga_service() is not None

    @cache(lambda x, y: time() // DISCOVERY_DOC_MAX_AGE)
    def ga_service(self):
        settings = self.get_settings()
        try:
            client_credentials = json.loads(settings.service_account)
        except TypeError:
            logger.warn('Could not extract credentials from {0}'.format(
                settings.service_account))
            return None

        credentials = Credentials.from_service_account_info(
            client_credentials, scopes=SCOPES)
        try:
            # Don't use caching of API, we have our own
            service = build(
                'analytics', 'v3', credentials=credentials,
                cache_discovery=False)
        except ResponseNotReady:
            logger.warn('Could not connect. Not connected to the')
            return None
        return service

    def ga_request(self, meth, slice='data', **kwargs):
        service = self.ga_service()
        if service is not None:

            try:
                if slice == 'data':
                    return getattr(service.data(), meth)().list(**kwargs).execute()
                elif slice == 'management':
                    return getattr(service.management(), meth)().list(**kwargs).execute()
                else:
                    logger.error('Unknown slice "{0}". Allowed values are "data" and "mangement"'.format(slice))
            except HttpError:
                logger.warn('Could not authenticate!')
            except ServerNotFoundError:
                logger.warn('Server not found!')
        else:
            logger.error('Service not found')
        return {}

    def get_accounts(self):
        return self.ga_request('accounts', slice='management')

    def getReports(self, category=None):
        """
        List the available Analytics reports. If a category is specified, only
        reports of that category are returned. Otherwise, all reports are
        returned.
        """
        for obj in self.values():
            if IAnalyticsReport.providedBy(obj):
                if (category and category in obj.categories) or not category:
                    yield obj

    def getCategoriesChoices(self):
        """
        Return a list of possible report categories.
        """
        return self.report_categories

    def get_settings(self):
        registry = getUtility(IRegistry)
        return registry.forInterface(IAnalyticsSchema)


InitializeClass(Analytics)
