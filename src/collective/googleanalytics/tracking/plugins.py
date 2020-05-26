
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
import logging
from urllib2 import URLError
import threading
import datetime
import cgi
try:
    from urllib.parse import unquote
except ImportError:
    from urllib2 import unquote

logger = logging.getLogger('collective.googleanalytics')


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


def on_start(event):
    annotations = IAnnotations(event.request)
    annotations['ga_start_load'] = datetime.datetime.now()


# Special hooks for registeringa virtual page view for downloads
def on_download(event):
    if event.request is None or event.request.response is None:
        return
    # TODO: just when we have content-disposition or should video streams or other downloads be counted?
    if 'content-disposition' not in event.request.response.headers:
        return
    if event.request.response.getStatus() != 200:
        # we don't want 206 range responses or errors to be reported
        return

    context = getSite()
    analytics_tool = getToolByName(context, "portal_analytics")
    analytics_settings = analytics_tool.get_settings()
    if 'File downloads (Server-side)' not in analytics_settings.tracking_plugin_names:
        return

    membership_tool = getToolByName(context, "portal_membership")
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

    tracker = Tracker(web_property, event.request.HTTP_HOST)
    visitor = Visitor()
    visitor.extract_from_server_meta(event.request)
    utma = event.request.cookies.get('__utma', None)
    if utma is not None:
        visitor.extract_from_utma(utma)

    session = Session()
    utmb = event.request.cookies.get('__utmb', None)
    if utmb is not None:
        session.extract_from_utmb(utmb)

    page = Page(event.request.PATH_INFO)
    page.referrer = event.request.HTTP_REFERER
    if 'ga_start_load' in annotations:
        page.load_time = int((datetime.datetime.now() - annotations.get('ga_start_load')).total_seconds() * 1000)
    filename = get_filename(event.request)
    if filename:
        page.title = u"Attachment: %s" % filename

    # TODO: should update utma and utmb with changed data via setcookie?
    visitor.add_session(session)  # Not sure if we are supposed to do this or after pageview or at all?

    def virtual_pageview(page, session, visitor):
        logger.debug("Trying Virtual Page View to %s (sesion %s)" % (event.request.PATH_INFO, session.session_id))
        try:
            tracker.track_pageview(page, session, visitor)
        except URLError, e:
            logger.warning("Virtual Page View Failed: %s" % e.reason)
        else:
            logger.debug("Virtual Success")
    # Do in seperate thread just in case its slow. Doesn't touch zodb so its fine
    thread = threading.Thread(target=virtual_pageview, args=(page, session, visitor))
    thread.start()


def get_filename(request):
    value, params = cgi.parse_header(request.response.headers['content-disposition'])
    filename = None
    if value == "attachment":
        for key, v in params.items():
            if key == 'filename*':
                encoding, filename = v.split("''")
                filename = filename.decode(encoding)
            elif key == 'filename':
                filename = v
    if filename:
        filename = unquote(filename)
    return filename
