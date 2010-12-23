from zope.app.component.hooks import getSite
from zope.component import getGlobalSiteManager
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics.interfaces.tracking import IAnalyticsTrackingPlugin
from collective.googleanalytics import error

def getProfiles(context):
    """
    Return list of Google Analytics profiles and corresponding
    account IDs (e.g. ga:30481).
    """
    
    analytics_tool = getToolByName(getSite(), 'portal_analytics')
    
    try:
        accounts = analytics_tool.getAccountsFeed()
    except error.BadAuthenticationError:
        choices = [('Please authorize with Google in the Google Analytics \
            control panel.', None)]
        return SimpleVocabulary.fromItems(choices)
    except error.RequestTimedOutError:
        choices = [('The request to Google Analytics timed out. Please try \
            again later.', None)]
        return SimpleVocabulary.fromItems(choices)
    if accounts:
        unique_choices = {}
        for entry in accounts.entry:
            title = unicode(entry.title.text, 'utf-8')
            unique_choices.update({title: entry.tableId[0].text})
        choices = unique_choices.items()
    else:
        choices = [('No profiles available', None)]
    return SimpleVocabulary([SimpleTerm(c[1], c[1], c[0]) for c in choices])

def getWebProperties(context):
    """
    Return list of Google Analytics profiles and web property
    IDs (e.g. UA-30481-22).
    """
    
    analytics_tool = getToolByName(getSite(), 'portal_analytics')

    try:
        accounts = analytics_tool.getAccountsFeed()
    except error.BadAuthenticationError:
        choices = [('Please authorize with Google in the Google Analytics \
            control panel.', None)]
        return SimpleVocabulary.fromItems(choices)
    except error.RequestTimedOutError:
        choices = [('The request to Google Analytics timed out. Please try \
            again later.', None)]
        return SimpleVocabulary.fromItems(choices)
    if accounts:
        unique_choices = {}
        # In vocabularies, both the terms and the values must be unique. Since
        # there can be more than one profile for a given web property, we create a list
        # of all the profiles for each property. (Ideally we would use the URL for the
        # web property, but Google doesn't expose it through the Analytics API.)
        for entry in accounts.entry:
            title = unicode(entry.title.text, 'utf-8')
            if not entry.webPropertyId.value in unique_choices.keys():
                unique_choices.update({entry.webPropertyId.value : title})
            else:
                unique_choices[entry.webPropertyId.value] += ', ' + title
        # After we reverse the terms so that the profile name(s) is now the key, we need
        # to ensure that these keys are unique. So, we pass the resulting list through
        # dict() and then output a list of items.
        choices = dict([(title, property_id) for (property_id, title) in unique_choices.items()]).items()
    else:
        choices = [('No profiles available', None)]
    return SimpleVocabulary([SimpleTerm(c[1], c[1], c[0]) for c in choices])

def getReports(context, category=None):
    """
    Return list of Google Analytics reports.
    """

    analytics_tool = getToolByName(getSite(), 'portal_analytics')
    reports = analytics_tool.getReports(category=category)
    choices = []
    if reports:
        choices = [(report.title, report.id,) for report in reports]
    return SimpleVocabulary.fromItems(choices)
    
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
    
    pmemb = getToolByName(getSite(), 'portal_membership')
    roles = [role for role in pmemb.getPortalRoles() if role != 'Owner']
    return SimpleVocabulary.fromValues(roles)
    
def getTrackingPluginNames(context):
    """
    Return a list of the names of the available tracking plugins.
    """

    gsm = getGlobalSiteManager()
    global_plugins = set([p.name for p in gsm.registeredAdapters() \
        if p.provided == IAnalyticsTrackingPlugin])
    
    lsm = getSite().getSiteManager()
    local_plugins = set([p.name for p in lsm.registeredAdapters() \
        if p.provided == IAnalyticsTrackingPlugin])
    
    values = sorted(list(global_plugins | local_plugins))
    return SimpleVocabulary.fromValues(values)