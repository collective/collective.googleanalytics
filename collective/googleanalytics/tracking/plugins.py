from zope.interface import implements
from string import Template
import os
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
        
        return self.request.ACTUAL_URL.replace(self.request.SERVER_URL, '').strip()
        
    def render_file(self, file_path, template_vars={}):
        """
        Renders a Python string template.
        """
        
        if not template_vars:
            return open(file_path).read()
        
        template = Template(open(file_path).read())
        return template.substitute(template_vars)

class AnalyticsExternalLinkPlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track external links.
    """
    
    def __call__(self):
        """
        Renders the tracking plugin.
        """
        
        template_file = os.path.join(os.path.dirname(__file__), 'external.tpl')
        return self.render_file(template_file)
    
class AnalyticsEmailLinkPlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track e-mail links.
    """

    def __call__(self):
        """
        Renders the tracking plugin.
        """
        
        template_file = os.path.join(os.path.dirname(__file__), 'email.tpl')
        return self.render_file(template_file)
    
class AnalyticsDownloadPlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track file downloads.
    """

    def __call__(self):
        """
        Renders the tracking plugin.
        """
        
        template_file = os.path.join(os.path.dirname(__file__), 'download.tpl')
        return self.render_file(template_file, {
            'file_extensions': json_serialize(FILE_EXTENSION_CHOICES),
        })