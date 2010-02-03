from zope.interface import implements
from zope import schema
from zope.formlib import form

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base
from plone.app.controlpanel.widgets import MultiCheckBoxVocabularyWidget

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from zope.i18nmessageid import MessageFactory
_ = MessageFactory('analytics')

from collective.googleanalytics import error

class IAnalyticsPortlet(IPortletDataProvider):
    """A portlet

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """
    
    portlet_title = schema.TextLine(title=_(u'Title'),
        description=_(u'Enter the title of the portlet.'),
        required=True,
        default=u'Google Analytics'
        )
        
    profile = schema.Choice(title=_(u"Profile"),
        vocabulary='collective.googleanalytics.Profiles',
        description=_(u"Choose the Web property profile from Google Analytics."),
        required=True)

    reports = schema.List(title=_(u"Reports"),
        value_type=schema.Choice(vocabulary='collective.googleanalytics.PortletReports'),
        min_length=1,
        description=_(u"Choose the reports to display."),
        required=True)
        
class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(IAnalyticsPortlet)

    def __init__(self, portlet_title=u'Google Analytics', profile=u"", reports=u""):
        self.portlet_title = portlet_title
        self.profile = profile
        self.reports = reports

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen.
        """
        return self.portlet_title or "Google Analytics"

class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """
    
    @property
    def available(self):
        """
        Determines whether the user has permission to see the portlet.
        """
        
        mtool = getToolByName(self.context, 'portal_membership')
        return mtool.checkPermission('collective.googleanalytics.ViewAnalyticsResults', self.context)
    
    def getTitle(self):
        """
        Return the title of the portlet.
        """
        return self.data.portlet_title
        
    def getDateRangeLabel(self):
        """
        Returns a string the describes the date range that corresponds to
        the resutls.
        """
        
        return 'Last 30 Days'
            
    def getResults(self):
        """
        Returns a list of AnalyticsReportResults objects for the selected reports.
        """
        analytics_tool = getToolByName(self.context, 'portal_analytics')
        
        results = []
        for report_id in self.data.reports:
            try:
                report = analytics_tool[report_id]
            except KeyError:
                continue
                
            try:
                results.append(report.getResults(self.context, self.data.profile, date_range='month'))
            except error.BadAuthenticationError:
                return 'BadAuthenticationError'
            except error.MissingCredentialsError:
                return 'MissingCredentialsError'
                
        return results
    
    render = ViewPageTemplateFile('analyticsportlet.pt')
            
class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(IAnalyticsPortlet)
    form_fields['reports'].custom_widget = MultiCheckBoxVocabularyWidget

    def create(self, data):
        return Assignment(**data)

class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(IAnalyticsPortlet)
    form_fields['reports'].custom_widget = MultiCheckBoxVocabularyWidget
