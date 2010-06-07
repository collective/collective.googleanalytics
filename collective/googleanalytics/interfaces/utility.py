from zope.interface import Interface
from zope import schema
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('collective.googleanalytics')

class IAnalyticsCredentials(Interface):
    """
    This interface defines the configlet.
    """

    auth_token = schema.TextLine(required=False)

class IAnalyticsTracking(Interface):
    """
    Tracking settings for Google Analytics.
    """

    tracking_web_property = schema.Choice(title=_(u"Tracking Profile"),
        vocabulary='collective.googleanalytics.WebProperties',
        description=_(u"Choose the Web property profile from Google Analytics."),
        required=False)

    tracking_plugin_names = schema.List(title=_(u"Plugins"),
        value_type=schema.Choice(vocabulary='collective.googleanalytics.TrackingPluginNames'),
        default=[],
        description=_(u"Choose which tracking plugins to use."),
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
    
    reports_profile = schema.Choice(title=_(u"Reports Profile"),
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
        description=_(u"Enter the number of minutes for which account \
            information and report results should be cached."),
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
        
