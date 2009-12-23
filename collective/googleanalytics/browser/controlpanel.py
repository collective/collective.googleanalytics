from zope.interface import Interface
from zope.interface import implements
from zope.i18nmessageid import MessageFactory
from zope.app.form.browser import MultiCheckBoxWidget as _MultiCheckBoxWidget

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.controlpanel.form import ControlPanelForm
from plone.fieldsets.fieldsets import FormFieldsets

from collective.googleanalytics.interfaces.utility import IAnalyticsCredentials, IAnalyticsReportsAssignment, IAnalyticsTracking, IAnalyticsSettings

_ = MessageFactory('analytics')

class IAnalyticsControlPanelForm(Interface):
	"""
	Google Analytics Control Panel Form
	"""

def MultiCheckBoxWidget(field, request):
    vocabulary = field.value_type.vocabulary
    return _MultiCheckBoxWidget(field, vocabulary, request)

class AnalyticsControlPanelForm(ControlPanelForm):
    """
    Google Analytics Control Panel Form
    """
    
    implements(IAnalyticsControlPanelForm)
    template = ViewPageTemplateFile('controlpanel.pt')
    
    analytics_credentials = FormFieldsets(IAnalyticsCredentials)
    analytics_credentials.id = 'analytics_credentials'
    analytics_credentials.label = _(u'analytics_credentials', default=u'Credentials')
    analytics_credentials.description = _(u'analytics_credentials_description', 
        default=u'Enter the login information that Plone will use to access Google Analytics.')
    
    analytics_assignment = FormFieldsets(IAnalyticsReportsAssignment)
    analytics_assignment.id = 'analytics_assignment'
    analytics_assignment.label = _(u'analytics_assignment', default=u'Reports')
    analytics_assignment.description = _(u'analytics_assignment_description', 
        default=u'Configure the reports that are displayed in the Google Analytics control panel.')
    analytics_assignment['reports'].custom_widget = MultiCheckBoxWidget
    
    analytics_tracking = FormFieldsets(IAnalyticsTracking)
    analytics_tracking.id = 'analytics_tracking'
    analytics_tracking.label = _(u'analytics_tracking', default=u'Tracking')
    analytics_tracking.description = _(u'analytics_tracking_description', 
        default=u'Configure the way Google Analytics tracks statistics about this site.')
    analytics_tracking['tracking_excluded_roles'].custom_widget = MultiCheckBoxWidget
    
    analytics_settings = FormFieldsets(IAnalyticsSettings)
    analytics_settings.id = 'analytics_settings'
    analytics_settings.label = _(u'analytics_settings', default=u'Settings')
    analytics_settings.description = _(u'analytics_settings_description', 
        default=u'Configure the settings of the Google Analytics product.')
    
    form_fields = FormFieldsets(analytics_credentials, analytics_assignment, analytics_tracking, analytics_settings)
    
    label = _(u"Google Analytics")
    description = _(u"Settings for Google Analytics.")
    form_name = _("Google Analytics Settings")