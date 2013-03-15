import csv
from StringIO import StringIO
from zope.interface import Interface
from zope.interface import implements
from z3c.form import form, field, button
from plone.z3cform.layout import wrap_form
from zope.component import getMultiAdapter

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.controlpanel.form import ControlPanelForm
from plone.app.controlpanel.widgets import MultiCheckBoxVocabularyWidget
from plone.fieldsets.fieldsets import FormFieldsets

import gdata.auth
from collective.googleanalytics import error
from collective.googleanalytics.interfaces.utility import \
    IAnalyticsReportsAssignment, IAnalyticsTracking, IAnalyticsSettings, IDateRangeDownload
from collective.googleanalytics.interfaces.report import IAnalyticsReportRenderer

from collective.googleanalytics import GoogleAnalyticsMessageFactory as _

class IAnalyticsControlPanelForm(Interface):
	"""
	Google Analytics Control Panel Form
	"""

class AnalyticsControlPanelForm(ControlPanelForm):
    """
    Google Analytics Control Panel Form
    """
    
    implements(IAnalyticsControlPanelForm)
    template = ViewPageTemplateFile('controlpanel.pt')
    
    analytics_assignment = FormFieldsets(IAnalyticsReportsAssignment)
    analytics_assignment.id = 'analytics_assignment'
    analytics_assignment.label = _(u'analytics_assignment', default=u'Reports')
    analytics_assignment.description = _(u'analytics_assignment_description', 
        default=u'Configure the reports that are displayed in the Google Analytics control panel.')
    analytics_assignment['reports'].custom_widget = MultiCheckBoxVocabularyWidget
    
    analytics_tracking = FormFieldsets(IAnalyticsTracking)
    analytics_tracking.id = 'analytics_tracking'
    analytics_tracking.label = _(u'analytics_tracking', default=u'Tracking')
    analytics_tracking.description = _(u'analytics_tracking_description', 
        default=u'Configure the way Google Analytics tracks statistics about this site.')
    analytics_tracking['tracking_plugin_names'].custom_widget = MultiCheckBoxVocabularyWidget
    analytics_tracking['tracking_excluded_roles'].custom_widget = MultiCheckBoxVocabularyWidget
    
    analytics_settings = FormFieldsets(IAnalyticsSettings)
    analytics_settings.id = 'analytics_settings'
    analytics_settings.label = _(u'analytics_settings', default=u'Settings')
    analytics_settings.description = _(u'analytics_settings_description', 
        default=u'Configure the settings of the Google Analytics product.')
    
    form_fields = FormFieldsets(analytics_tracking, analytics_assignment, analytics_settings)
    
    label = _(u"Google Analytics")
    form_name = _("Google Analytics Settings")
    
    def authorized(self):
        """
        Returns True if we have an auth token, or false otherwise.
        """
        
        if self.context.auth_token:
            return True
        return False
    
    def auth_url(self):
        """
        Returns the URL used to retrieve a Google AuthSub token.
        """
    
        next = '%s/analytics-auth' % self.context.portal_url()
        scope = 'https://www.google.com/analytics/feeds/'
        return gdata.auth.GenerateAuthSubUrl(next, scope, secure=False, session=True)
        
    def account_name(self):
        """
        Returns the account name for the currently authorized account.
        """
        
        analytics_tool = getToolByName(self.context, 'portal_analytics')
        
        try:
            res = analytics_tool.getAccountsFeed('accounts')
        except error.BadAuthenticationError:
            return None
        except error.RequestTimedOutError:
            return None
        return res.title.text.split(' ')[-1]
    
    def _on_save(self, data={}):
        """
        Checks to make sure that tracking code is not duplicated in the site
        configlet.
        """
        
        tracking_web_property = data.get('tracking_web_property', None)
        properties_tool = getToolByName(self.context, "portal_properties")
        snippet = properties_tool.site_properties.webstats_js
        snippet_analytics =  '_gat' in snippet or '_gaq' in snippet
        if tracking_web_property and snippet_analytics:
            plone_utils = getToolByName(self.context, 'plone_utils')
            plone_utils.addPortalMessage(_(u'You have enabled the tracking \
            feature of this product, but it looks like you still have tracking \
            code in the Site control panel. Please remove any Google Analytics \
            tracking code from the Site control panel to avoid conflicts.'),
            'warning')


class DateRangeDownloadForm(form.Form):
    fields = field.Fields(IDateRangeDownload)
    ignoreContext = True # don't use context to get widget data
    label = "CSV Download"
    output = None

    def render(self):
        if self.output:
            return self.output
        return super(DateRangeDownloadForm, self).render() 

    @button.buttonAndHandler(u'Download')
    def handleDownload(self, action):
        data, errors = self.extractData()
        if errors:
            return
        analytics_tool = getToolByName(self.context, 'portal_analytics')        
        profile = getattr(analytics_tool, 'reports_profile', None)
        self.request['profile_ids'] = profile
        report = analytics_tool['top-users-table']
        renderer = getMultiAdapter(
            (self.context, self.request, report),
            interface=IAnalyticsReportRenderer
        )
        data = renderer.data()
        if data:
            csvdata = StringIO()
            csvwriter = csv.DictWriter(csvdata, data[0].keys())
            csvwriter.writeheader()
            csvwriter.writerows(data)
            self.request.response.setHeader('Content-Type', 'text/csv') 
            self.request.response.addHeader("Content-Disposition",
                                            "attachment;filename=top-users.csv")
            self.output = csvdata.getvalue()

DateRangeDownloadView = wrap_form(DateRangeDownloadForm)
