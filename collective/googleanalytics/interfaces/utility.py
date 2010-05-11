from zope.interface import Interface
from zope import schema
from zope.i18nmessageid import MessageFactory

from collective.googleanalytics.config import FILE_EXTENSION_CHOICES

_ = MessageFactory('analytics')

class IAnalyticsCredentials(Interface):
    """
    This interface defines the configlet.
    """

    email = schema.TextLine(title=_(u"E-mail address"),
        description=_(u"Enter the e-mail address used to log in to Google Analytics."),
        required=True)
                                 
    password = schema.Password(title=_(u"Password"),
        description=_(u"Enter the Google Analytics password for the e-mail address above."),
        required=True)

class IAnalyticsTracking(Interface):
    """
    Tracking settings for Google Analytics.
    """

    tracking_web_property = schema.Choice(title=_(u"Profile"),
        vocabulary='collective.googleanalytics.WebProperties',
        description=_(u"Choose the Web property profile from Google Analytics."),
        required=False)

    tracking_external_prefix = schema.TextLine(title=_(u"External Link Prefix"),
        description=_(u'Enter the prefix to add to external links for tracking \
            in Google Analytics. Do not include leading or trailing slashes. Leave \
            blank to turn off external link tracking.'),
        default=u'external',
        required=False)

    tracking_mailto_prefix = schema.TextLine(title=_(u"E-mail Address Prefix"),
        description=_(u'Enter the prefix to add to e-mail addresses for tracking \
            in Google Analytics. Do not include leading or trailing slashes. Leave blank \
            to turn off e-mail address tracking.'),
        default=u'mailto',
        required=False)

    tracking_file_prefix = schema.TextLine(title=_(u"Download File Prefix"),
        description=_(u'Enter the prefix to add to file downloads for tracking \
            in Google Analytics. Do not include leading or trailing slashes. Leave blank \
            to turn off download file tracking.'),
        default=u'download',
        required=False)

    tracking_file_extensions = schema.List(title=_(u"Download File Types"),
        value_type=schema.Choice(vocabulary='collective.googleanalytics.FileExtensions'),
        default=list(FILE_EXTENSION_CHOICES),
        description=_(u"Choose which file types to track to track in Google Analytics."),
        required=False)

    tracking_excluded_roles = schema.List(title=_(u"Excluded Roles"),
        value_type=schema.Choice(vocabulary='collective.googleanalytics.Roles'),
        default=[],
        description=_(u"Choose the roles that should be excluded from tracking."),
        required=False)

class IAnalyticsReportsAssignment(Interface):
    """
    An assignment that specifies a profile and one or more reports.
    """
    
    reports_profile = schema.Choice(title=_(u"Profile"),
        vocabulary='collective.googleanalytics.Profiles',
        description=_(u"Choose the Web property profile from Google Analytics."),
        required=False)
        
    reports = schema.List(title=_(u"Reports"),
        value_type=schema.Choice(vocabulary='collective.googleanalytics.SiteWideReports'),
        default=[],
        description=_(u"Choose the reports to display."),
        required=False)

class IAnalyticsSettings(Interface):
    """
    Settings for the Analytics configlet.
    """
    
    cache_interval = schema.Int(title=_(u"Cache interval"),
        description=_(u"Enter the number of minutes for which report results should be cached."),
        default=60,
        required=True)

class IAnalytics(
        IAnalyticsCredentials, 
        IAnalyticsReportsAssignment, 
        IAnalyticsTracking, 
        IAnalyticsSettings):
    """
    Analytics utility
    """
    
    report_categories = schema.List(title=_(u"Report Categories"),
        default=['Site Wide', 'Portlet'],
        required=False)
        
