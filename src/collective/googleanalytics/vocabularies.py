# -*- coding: utf-8 -*-
from collective.googleanalytics.interfaces.tracking import IAnalyticsTrackingPlugin
from plone import api
from zope.component.hooks import getSite
from zope.component import getGlobalSiteManager
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

import logging


logger = logging.getLogger('collective.googleanalytics')


def crop(text, length):
    if len(text) > 40:
        text = text[:40]
        l = text.rfind(' ')
        if l > 20:  # 40 / 2
            text = text[:l + 1]
        text += '...'
    return text


def getProfiles(context):
    """
    Return list of Google Analytics profiles and corresponding
    account IDs (e.g. ga:30481).
    """

    analytics_tool = api.portal.get_tool(name='portal_analytics')
    # short circuit if user hasn't authorized yet
    if not analytics_tool.is_auth():
        return SimpleVocabulary([])

    accounts = analytics_tool.get_accounts()
    if not accounts:
        return SimpleVocabulary([])

    choices = []
    if accounts.get('items'):
        firstAccountId = accounts.get('items')[0].get('id')
        webproperties = analytics_tool.ga_request('webproperties', slice='management', accountId=firstAccountId)

        if webproperties.get('items'):
            firstWebpropertyId = webproperties.get('items')[0].get('id')
            profiles = analytics_tool.ga_request(
                'profiles', slice='management', accountId=firstAccountId,
                webPropertyId=firstWebpropertyId)
            if profiles.get('items'):
                choices = profiles.get('items')

    return SimpleVocabulary([
        SimpleTerm(c['webPropertyId'], c['webPropertyId'], c['name'])
        for c in choices])


def getWebProperties(context):
    """
    Return list of Google Analytics profiles and web property
    IDs (e.g. UA-30481-22).
    """

    analytics_tool = api.portal.get_tool(name='portal_analytics')
    # short circuit if user hasn't authorized yet
    if not analytics_tool.is_auth():
        return SimpleVocabulary([])

    accounts = analytics_tool.get_accounts()
    if not accounts:
        return SimpleVocabulary([])

    account_items = accounts.get('items')
    unique_choices = {}
    if account_items:
        service = analytics_tool.ga_service()
        for account in account_items:
            webprops = service.management().webproperties().list(
                accountId=account['id']).execute()
            for webprop in webprops['items']:
                if webprop['id'] not in unique_choices:
                    unique_choices[webprop['id']] = webprop['name']

        choices = {crop(_title, 40): property_id
                   for property_id, _title in unique_choices.items()}.items()
    else:
        choices = [('No profiles available', None)]
    return SimpleVocabulary([SimpleTerm(c[1], c[1], c[0]) for c in choices])


def getReports(context, category=None):
    """
    Return list of Google Analytics reports.
    """

    analytics_tool = api.portal.get_tool(name='portal_analytics')
    reports = analytics_tool.getReports(category=category)
    choices = []
    if reports:
        choices = [SimpleTerm(value=report.id, token=report.id, title=report.title) for report in reports]
    return SimpleVocabulary(choices)


def getSiteWideReports(context):
    """
    Return list of site wide Google Analytics reports.
    """

    return getReports(context, category="Site Wide")


def getPortletReports(context):
    """
    Return list of portlet Google Analytics reports.
    """

    return getReports(context, category="Portlet")


def getRoles(context):
    """
    Return a list of user roles.
    """
    pmemb = api.portal.get_tool(name='portal_membership')
    roles = [role for role in pmemb.getPortalRoles() if role != 'Owner']
    return SimpleVocabulary.fromValues(roles)


def getTrackingPluginNames(context):
    """
    Return a list of the names of the available tracking plugins.
    """

    gsm = getGlobalSiteManager()
    global_plugins = set([p.name for p in gsm.registeredAdapters()
                          if p.provided == IAnalyticsTrackingPlugin])

    lsm = getSite().getSiteManager()
    local_plugins = set([p.name for p in lsm.registeredAdapters()
                         if p.provided == IAnalyticsTrackingPlugin])

    values = sorted(list(global_plugins | local_plugins))
    return SimpleVocabulary.fromValues(values)
