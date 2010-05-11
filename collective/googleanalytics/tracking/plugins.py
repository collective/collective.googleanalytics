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
        
    def render_file(self, file_name, template_vars={}):
        """
        Renders a Python string template.
        """
        
        template_file = os.path.join(os.path.dirname(__file__), file_name)
        if not template_vars:
            return open(template_file).read()
        
        template = Template(open(template_file).read())
        return template.substitute(template_vars)

class AnalyticsExternalLinkPlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track external links.
    """
    
    def __call__(self):
        """
        Renders the tracking plugin.
        """
        
        return self.render_file('external.tpl')
    
class AnalyticsEmailLinkPlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track e-mail links.
    """

    def __call__(self):
        """
        Renders the tracking plugin.
        """
        
        return self.render_file('email.tpl')
    
class AnalyticsDownloadPlugin(AnalyticsBaseTrackingPlugin):
    """
    A tracking plugin to track file downloads.
    """

    def __call__(self):
        """
        Renders the tracking plugin.
        """
        
        return self.render_file('download.tpl', {
            'file_extensions': self.getFileExtensions(),
        })
    
    def getFileExtensions(self):
        """
        Returns a string containing a javascript list of the file extensions
        to be tracked.
        """
        
        return json_serialize(FILE_EXTENSION_CHOICES)