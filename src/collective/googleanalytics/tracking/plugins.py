
try:
    import simplejson as json
except ImportError:
    import json
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics.config import FILE_EXTENSION_CHOICES
from collective.googleanalytics.interfaces.tracking import IAnalyticsTrackingPlugin
from collective.googleanalytics.interfaces.browserlayer import IAnalyticsLayer
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


def is_response_ext_a_download(request):
    context = getSite()
    tool = getToolByName(context, "mimetypes_registry", None)
    entry = tool.lookup(request.response.headers['content-type'])
    mimetypes = [item for item in entry for ext in item.extensions if ext in FILE_EXTENSION_CHOICES]
    if not mimetypes:
        return False
    # images that don't have content-disposition we won't include
    if not set([mt for mt in mimetypes if mt.major() != 'image']):
        return False
    return True


# for general purpose content (instead of images) its
#    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
# for images is something like
#    Accept: image/webp,image/apng,image/*,*/*;q=0.8
# more complete - https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation/List_of_default_Accept_values
GENERAL_MOST_BROWSERS = set(['text/html', 'application/xhtml+xml', '*/*'])
GENERAL_IE8 = set(['application/xaml+xml', 'application/msword', '*/*'])


def is_accept_for_generic_content(request):

    if not request.HTTP_ACCEPT:
        # maybe some weird crawler?
        return True
    elif all([mime in request.HTTP_ACCEPT for mime in GENERAL_MOST_BROWSERS]):
        return True
    elif all([mime in request.HTTP_ACCEPT for mime in GENERAL_IE8]):
        return True
    else:
        # it could be video or audio or image or js or css?
        return False


# Special hooks for registeringa virtual page view for downloads
#
# on_start - so we can record the time for the page view
# on_download - for normal 200 requests that are downloads set webproperty so we can record the page view later
# on_abort - this is called instead of on_download in the case of 304 not modifed caching
# on_after_download - does the actual virtual page view (in a seperate thread)


def on_start(event):
    annotations = IAnnotations(event.request)
    annotations['ga_start_load'] = datetime.datetime.now()


def on_download(event):
    if event.request is None or event.request.response is None:
        return
    if not IAnalyticsLayer.providedBy(event.request):
        return
    elif event.request.response.getStatus() != 200:
        # we don't want 206 range responses or errors to be reported
        return
    elif not is_accept_for_generic_content(event.request):
        # TODO: just when we have content-disposition or should video streams or other downloads be counted?
        # in plone the site-logo uses @@download which sets a content-disposition. We shouldn't count this
        # since its being used inside a img tag.
        return
    elif 'content-disposition' in event.request.response.headers:
        annotate_web_property(event.request)
        return
    elif is_response_ext_a_download(event.request):
        # it could be using @@display-file for pdf which doesn't set content-disposition
        annotate_web_property(event.request)

    # TODO: test support xsendfile


def on_abort(event):
    # Special case where plone.caching.hooks.Intercepted aborts in order to return 304 not modified
    if not IAnalyticsLayer.providedBy(event.request):
        return
    elif event.request.response.getStatus() != 304:
        return
    elif not is_accept_for_generic_content(event.request):
        return
    elif not event.request.response.headers.get('x-cache-rule', None) == 'plone.content.file':
        # HACK: distiquish between file downloads and html content
        return
    else:
        annotate_web_property(event.request)


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
    # Since we have no filename for 304 responses we should not set one so hits look the same
    # filename = get_filename(event.request)
    # if filename:
    #    page.title = u"Attachment: %s" % filename

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


def annotate_web_property(request):
    context = getSite()
    analytics_tool = getToolByName(context, "portal_analytics", None)
    if analytics_tool is None:
        return
    analytics_settings = analytics_tool.get_settings()
    if 'File downloads (Server-side)' not in analytics_settings.tracking_plugin_names:
        return

    membership_tool = getToolByName(context, "portal_membership")
    member = membership_tool.getAuthenticatedMember()
    for role in analytics_settings.tracking_excluded_roles:
        if member.has_role(role):
            return

    web_property = analytics_settings.tracking_web_property
    annotations = IAnnotations(request)
    annotations['web_property'] = web_property


def get_filename(request):
    value, params = cgi.parse_header(request.response.headers.get('content-disposition', ''))
    if value != "attachment":
        return None
    filename = None
    for key, v in params.items():
        if key == 'filename*':
            encoding, filename = v.split("''")
            filename = filename.decode(encoding)
        elif key == 'filename':
            filename = v
    if filename:
        filename = unquote(filename)
    return filename
