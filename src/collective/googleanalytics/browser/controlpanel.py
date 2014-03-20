
from zope.annotation import IAnnotations

from zope.interface import Interface
from zope.interface import implements

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.controlpanel.form import ControlPanelForm
from plone.app.controlpanel.widgets import MultiCheckBoxVocabularyWidget
from plone.fieldsets.fieldsets import FormFieldsets

from gdata.client import RequestError
import gdata.auth
import gdata.gauth
from collective.googleanalytics import error
from collective.googleanalytics.interfaces.utility import \
    IAnalyticsReportsAssignment, IAnalyticsTracking, IAnalyticsSettings

from collective.googleanalytics import GoogleAnalyticsMessageFactory as _

import logging
logger = logging.getLogger('collective.googleanalytics')


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
    analytics_assignment.description = _(
        u'analytics_assignment_description',
        default=u'Configure the reports that are displayed in the Google Analytics control panel.')
    analytics_assignment['reports'].custom_widget = MultiCheckBoxVocabularyWidget

    analytics_tracking = FormFieldsets(IAnalyticsTracking)
    analytics_tracking.id = 'analytics_tracking'
    analytics_tracking.label = _(u'analytics_tracking', default=u'Tracking')
    analytics_tracking.description = _(
        u'analytics_tracking_description',
        default=u'Configure the way Google Analytics tracks statistics about this site.')
    analytics_tracking['tracking_plugin_names'].custom_widget = MultiCheckBoxVocabularyWidget
    analytics_tracking['tracking_excluded_roles'].custom_widget = MultiCheckBoxVocabularyWidget

    analytics_settings = FormFieldsets(IAnalyticsSettings)
    analytics_settings.id = 'analytics_settings'
    analytics_settings.label = _(u'analytics_settings', default=u'Settings')
    analytics_settings.description = _(
        u'analytics_settings_description',
        default=u'Configure the settings of the Google Analytics product.')

    form_fields = FormFieldsets(analytics_tracking, analytics_assignment, analytics_settings)

    label = _(u"Google Analytics")
    form_name = _("Google Analytics Settings")

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

            next = '%s/analytics-auth' % self.context.portal_url()

            oauth2_token = gdata.gauth.OAuth2Token(
                client_id=key,
                client_secret=secret,
                scope="https://www.googleapis.com/auth/analytics",
                user_agent='collective-googleanalytics',
            )
            logger.debug(u"Created new OAuth2 token with id: '%s' and secret:"
                         u" '%s'" % (key, secret))

            oauth2_token.redirect_uri = next
            ann = IAnnotations(analytics_tool)
            ann['auth_token'] = oauth2_token

            auth_url = oauth2_token.generate_authorize_url(
                redirect_uri=next,
                approval_prompt='force'
            )

            logger.debug(u"Auth URL: %s" % auth_url)

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

    def _on_save(self, data={}):
        """
        Checks to make sure that tracking code is not duplicated in the site
        configlet.
        """

        tracking_web_property = data.get('tracking_web_property', None)
        properties_tool = getToolByName(self.context, "portal_properties")
        snippet = properties_tool.site_properties.webstats_js
        snippet_analytics = '_gat' in snippet or '_gaq' in snippet
        if tracking_web_property and snippet_analytics:
            plone_utils = getToolByName(self.context, 'plone_utils')
            plone_utils.addPortalMessage(
                _(u"You have enabled the tracking feature of this product, "
                  u"but it looks like you still have tracking code in the "
                  u"Site control panel. Please remove any Google Analytics "
                  u"tracking code from the Site control panel to avoid "
                  u"conflicts.'"), 'warning')
