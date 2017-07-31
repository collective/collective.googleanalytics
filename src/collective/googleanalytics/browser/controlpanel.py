
import logging
from Products.CMFCore.utils import getToolByName
try:
    from Products.CMFPlone.interfaces import ISiteSchema
    HAS_PLONE5 = True
except ImportError:
    HAS_PLONE5 = False
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.googleanalytics import GoogleAnalyticsMessageFactory as _
from collective.googleanalytics import error
from collective.googleanalytics.interfaces.utility import \
    IAnalyticsReportsAssignment
from collective.googleanalytics.interfaces.utility import IAnalyticsSchema
from collective.googleanalytics.interfaces.utility import IAnalyticsSettings
from collective.googleanalytics.interfaces.utility import IAnalyticsTracking
from gdata.client import RequestError
from plone.app.registry.browser import controlpanel
from plone import api
from plone.registry.interfaces import IRegistry
from z3c.form import field
from z3c.form import group
from zope.component import getUtility
from zope.interface import Interface
from zope.interface import implementer

logger = logging.getLogger('collective.googleanalytics')


class IAnalyticsControlPanelForm(Interface):
    """
    Google Analytics Control Panel Form
    """


class AnalyticsReportsAssignmentForm(group.GroupForm):
    label = _(u'analytics_assignment', default=u'Reports')
    description = _(
        u'analytics_assignment_description',
        default=(u'Configure the reports that are displayed in the Google '
                 u'Analytics control panel.'))
    fields = field.Fields(IAnalyticsReportsAssignment)


class AnalyticsTrackingForm(group.GroupForm):
    fields = field.Fields(IAnalyticsTracking)
    label = _(u'analytics_tracking', default=u'Tracking')
    description = _(
        u'analytics_tracking_description',
        default=(u'Configure the way Google Analytics tracks statistics '
                 u'about this site.'))


class AnalyticsSettingsForm(group.GroupForm):
    fields = field.Fields(IAnalyticsSettings)
    label = _(u'analytics_settings', default=u'Settings')
    description = _(
        u'analytics_settings_description',
        default=u'Configure the settings of the Google Analytics product.')


@implementer(IAnalyticsControlPanelForm)
class AnalyticsControlPanelForm(controlpanel.RegistryEditForm):
    """
    Google Analytics Control Panel Form
    """

    schema = IAnalyticsSchema

    groups = (AnalyticsTrackingForm, AnalyticsReportsAssignmentForm,
              AnalyticsSettingsForm)

    label = _(u"Google Analytics")

    def extractData(self, setErrors=True):
        """
        Checks to make sure that tracking code is not duplicated in the site
        configlet.
        """
        data, errors = super(AnalyticsControlPanelForm, self).extractData(
            setErrors=setErrors
        )
        tracking_web_property = data.get('tracking_web_property', None)
        if HAS_PLONE5:
            registry = getUtility(IRegistry)
            site_records = registry.forInterface(ISiteSchema, prefix='plone')
            snippet = site_records.webstats_js
        else:   # Plone 4 stores the analytics script in the properties
            properties_tool = api.portal.get_tool(name="portal_properties")
            snippet = properties_tool.site_properties.webstats_js
        snippet = snippet or ''
        snippet_analytics = '_gat' in snippet or '_gaq' in snippet
        if tracking_web_property and snippet_analytics:
            api.portal.show_message(
                _(u"You have enabled the tracking feature of this product, "
                  u"but it looks like you still have tracking code in the "
                  u"Site control panel. Please remove any Google Analytics "
                  u"tracking code from the Site control panel to avoid "
                  u"conflicts.'"), self.request, type='warning')
        return data, errors


class AnalyticsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = AnalyticsControlPanelForm
    index = ViewPageTemplateFile('controlpanel_layout.pt')

    def authorized(self):
        """
        Returns True if we have a valid token, or false otherwise.
        """
        analytics_tool = getToolByName(self.context, 'portal_analytics')
        return analytics_tool.is_auth()

    def auth_url(self):
        """
        Returns the URL used to retrieve a Google OAuth2 token.
        """
        key = self.request.get('consumer_key', '')
        secret = self.request.get('consumer_secret', '')
        auth_url = None
        if key and secret:

            analytics_tool = getToolByName(self.context, 'portal_analytics')
            auth_url = analytics_tool.auth_url(key, secret)

        return auth_url

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
        except RequestError:
            return None
        return res.title.text.split(' ')[-1]
