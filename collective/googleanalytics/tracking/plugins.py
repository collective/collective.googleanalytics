from zope.interface import implements
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from collective.googleanalytics.interfaces.tracking import IAnalyticsTrackingPlugin
from collective.googleanalytics.config import FILE_EXTENSION_CHOICES
from collective.googleanalytics.utils import json_serialize

class AnalyticsBaseTrackingPlugin(object):
    """
    Base plugin for tracking information in Google Analytics.
    """
    
    implements(IAnalyticsTrackingPlugin)
    
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
    
    file_extensions = json_serialize(FILE_EXTENSION_CHOICES)
    
class AnalyticsCommentPlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track posting of comments.
    """

    __call__ = ViewPageTemplateFile('comment.pt')