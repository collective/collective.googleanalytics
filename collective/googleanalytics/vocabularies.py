from zope.app.component.hooks import getSite
from zope.schema.vocabulary import SimpleVocabulary
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics import error
from collective.googleanalytics.config import FILE_EXTENSION_CHOICES

def getProfiles(context):
    """
    Return list of Google Analytics profiles and corresponding account IDs (e.g. ga:30481).
    """
    analytics_tool = getToolByName(getSite(), 'portal_analytics')
    
    try:
        client = analytics_tool.getAuthenticatedClient(service='accounts')
    except error.MissingCredentialsError:
        choices = [('Set Google Analytics e-mail and password in the control panel', None)]
        return SimpleVocabulary.fromItems(choices)
    except error.BadAuthenticationError:
        choices = [('Incorrect Google Analytics e-mail or password', None)]
        return SimpleVocabulary.fromItems(choices)
    accounts = client.GetAccountList()
    if accounts:
        unique_choices = {}
        for entry in accounts.entry:
            unique_choices.update({entry.title.text : entry.tableId[0].text})
        choices = unique_choices.items()
    else:
        choices = [('No profiles available', None)]
    return SimpleVocabulary.fromItems(choices)

def getWebProperties(context):
    """
    Return list of Google Analytics profiles and web property IDs (e.g. UA-30481-22).
    """
    analytics_tool = getToolByName(getSite(), 'portal_analytics')

    try:
        client = analytics_tool.getAuthenticatedClient(service='accounts')
    except error.MissingCredentialsError:
        choices = [('Set Google Analytics e-mail and password in the control panel', None)]
        return SimpleVocabulary.fromItems(choices)
    except error.BadAuthenticationError:
        choices = [('Incorrect Google Analytics e-mail or password', None)]
        return SimpleVocabulary.fromItems(choices)
    accounts = client.GetAccountList()
    if accounts:
        unique_choices = {}
        # In vocabularies, both the terms and the values must be unique. Since
        # there can be more than one profile for a given web property, we create a list
        # of all the profiles for each property. (Ideally we would use the URL for the
        # web property, but Google doesn't expose it through the Analytics API.)
        for entry in accounts.entry:
            if not entry.webPropertyId.value in unique_choices.keys():
                unique_choices.update({entry.webPropertyId.value : entry.title.text})
            else:
                unique_choices[entry.webPropertyId.value] += ', ' + entry.title.text
        # After we reverse the terms so that the profile name(s) is now the key, we need
        # to ensure that these keys are unique. So, we pass the resulting list through
        # dict() and then output a list of items.
        choices = dict([(title, property_id) for (property_id, title) in unique_choices.items()]).items()
    else:
        choices = [('No profiles available', None)]
    return SimpleVocabulary.fromItems(choices)

def getReports(context):
    """
    Return list of Google Analytics reports.
    """

    analytics_tool = getToolByName(getSite(), 'portal_analytics')
    reports = analytics_tool.getReports()
    choices = []
    if reports:
        choices = [(report.title, report.id,) for report in reports]
    return SimpleVocabulary.fromItems(choices)
    
def getRoles(context):
    """
    Return a list of user roles.
    """
    
    pmemb = getToolByName(getSite(), 'portal_membership')
    roles = [role for role in pmemb.getPortalRoles() if role != 'Owner']
    return SimpleVocabulary.fromValues(roles)
    
def getFileExtensions(context):
    """
    Return a list of file extensions that we can track.
    """

    return SimpleVocabulary.fromValues(FILE_EXTENSION_CHOICES)