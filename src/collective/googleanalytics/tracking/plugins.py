
try:
    import simplejson as json
except ImportError:
    import json
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics.config import FILE_EXTENSION_CHOICES
from collective.googleanalytics.interfaces.tracking import IAnalyticsTrackingPlugin
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.interface import implementer
from pyga.requests import Tracker, Page, Session, Visitor
from zope.site.hooks import getSite
from zope.annotation.interfaces import IAnnotations


@implementer(IAnalyticsTrackingPlugin)
class AnalyticsBaseTrackingPlugin(object):
    """
    Base plugin for tracking information in Google Analytics.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def relative_url(self):
        """
        Returns the relative URL of the request.
        """

        relative_url = self.request.ACTUAL_URL.replace(self.request.SERVER_URL, '').strip()
        if relative_url.endswith('/') and len(relative_url) > 1:
            return relative_url[:-1]
        return relative_url


class AnalyticsExternalLinkPlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track external links.
    """

    __call__ = ViewPageTemplateFile('external.pt')


class AnalyticsEmailLinkPlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track e-mail links.
    """

    __call__ = ViewPageTemplateFile('email.pt')


class AnalyticsDownloadPlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track file downloads.
    """

    __call__ = ViewPageTemplateFile('download.pt')

    file_extensions = json.dumps(FILE_EXTENSION_CHOICES)


class AnalyticsDownloadServerSidePlugin(AnalyticsBaseTrackingPlugin):
    """
    Performs virtual page views on the serverside to track actual downloads instead of clicks on downloads
    esp on deep linked files
    WARNING: Caching may prevent tracking.
    """
    def __call__(self):
        # It's serverside so no JS to load
        return ""


class AnalyticsCommentPlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track posting of comments.
    """

    __call__ = ViewPageTemplateFile('comment.pt')


class AnalyticsUserTypePlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track user type as a custom variable.
    """

    __call__ = ViewPageTemplateFile('usertype.pt')

    def user_type(self):
        """
        Returns Member if the user is logged or Visitor otherwise.
        """

        membership = getToolByName(self.context, 'portal_membership')
        if membership.isAnonymousUser():
            return 'Visitor'
        return 'Member'


class AnalyticsPageLoadTimePlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track page load time.
    """

    __call__ = ViewPageTemplateFile('pageloadtime.pt')


# Special hooks for registeringa virtual page view for downloads
def on_download(event):
    if event.request is None or event.request.response is None or 'content-disposition' not in event.request.response.headers:
        return

    # TODO: do we need to look at content-type header also?
    if event.request.response.getStatus() == 200:
        # we don't want 206 range responses or errors to be reported
        return

    context = getSite()
    analytics_tool = getToolByName(context, "portal_analytics")
    membership_tool = getToolByName(context, "portal_membership")
    analytics_settings = analytics_tool.get_settings()
    if 'File downloads (Server-side)' not in analytics_settings.tracking_plugin_names:
        return

    member = membership_tool.getAuthenticatedMember()
    for role in analytics_settings.tracking_excluded_roles:
        if member.has_role(role):
            return

    web_property = analytics_settings.tracking_web_property
    annotations = IAnnotations(event.request)
    annotations['web_property'] = web_property


def on_after_download(event):
    annotations = IAnnotations(event.request)
    web_property = annotations.get('web_property', None)
    if web_property is None:
        return

    # TODO: Ideally should be done in a seperate thread so doesn't slow accepting the next request

    tracker = Tracker(web_property, event.request.HTTP_HOST)
    visitor = Visitor()
    visitor.ip_address = get_ip(event.request)
    session = Session()
    utmb = event.request.cookies.get('__utmb', None)
    if utmb:
        session.extract_from_utmb(utmb)
    page = Page(event.request.PATH_INFO)
    # TODO: set title from content-disposition
    tracker.track_pageview(page, session, visitor)


def get_ip(request):
    """ Extract the client IP address from the HTTP request in a proxy-compatible way.

    @return: IP address as a string or None if not available
    """
    if "HTTP_X_FORWARDED_FOR" in request.environ:
        # Virtual host
        ip = request.environ["HTTP_X_FORWARDED_FOR"]
    elif "HTTP_HOST" in request.environ:
        # Non-virtualhost
        ip = request.environ["REMOTE_ADDR"]
    else:
        # Unit test code?
        ip = None
    return ip
