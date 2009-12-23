from zope.app.component.hooks import getSite
from zope.schema.vocabulary import SimpleVocabulary
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics import error

def getProfiles(context):
    """
    Return list of Google Analytics profiles and corresponding IDs.
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