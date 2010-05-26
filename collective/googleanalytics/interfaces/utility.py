from zope.interface import Interface
from zope import schema
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('analytics')

# Older versions of zope.schema don't allow for an unchanged password.
if not hasattr(schema.Password, 'UNCHANGED_PASSWORD'):
    class Password(schema.TextLine):
        """A text field containing a text used as a password."""

        UNCHANGED_PASSWORD = object()

        def set(self, context, value):
            """Update the password.

            We use a special marker value that a widget can use
            to tell us that the password didn't change. This is
            needed to support edit forms that don't display the
            existing password and want to work together with
            encryption.

            """
            if value is self.UNCHANGED_PASSWORD:
                return
            super(Password, self).set(context, value)

        def validate(self, value):
            try:
                existing = bool(self.get(self.context))
            except AttributeError:
                existing = False
            if value is self.UNCHANGED_PASSWORD and existing:
                # Allow the UNCHANGED_PASSWORD value, if a password is set already
                return
            return super(Password, self).validate(value)
else:
    Password = schema.Password

class IAnalyticsCredentials(Interface):
    """
    This interface defines the configlet.
    """

    email = schema.TextLine(title=_(u"E-mail address"),
        description=_(u"Enter the e-mail address used to log in to Google Analytics."),
        required=True)
                                 
    password = Password(title=_(u"Password"),
        description=_(u"Enter the Google Analytics password for the e-mail address above."),
        required=True)

class IAnalyticsReportsAssignment(Interface):
    """
    An assignment that specifies a profile and one or more reports.
    """
    
    profile = schema.Choice(title=_(u"Profile"),
        vocabulary='collective.googleanalytics.Profiles',
        description=_(u"Choose the Web property profile from Google Analytics."),
        required=False)
        
    reports = schema.List(title=_(u"Reports"),
        value_type=schema.Choice(vocabulary='collective.googleanalytics.SiteWideReports'),
        default=[],
        description=_(u"Choose the reports to display."),
        required=False)

class IAnalyticsTracking(Interface):
    """
    Tracking settings for Google Analytics.
    """
    
    tracking_excluded_roles = schema.List(title=_(u"Excluded Roles"),
        value_type=schema.Choice(vocabulary='collective.googleanalytics.Roles'),
        default=[],
        description=_(u"Choose the roles that should be excluded from tracking."),
        required=False)

class IAnalyticsSettings(Interface):
    """
    Settings for the Analytics configlet.
    """
    
    cache_interval = schema.Int(title=_(u"Cache interval"),
        description=_(u"Enter the number of minutes for which report results should be cached."),
        default=60,
        required=True)

class IAnalytics(IAnalyticsCredentials, IAnalyticsReportsAssignment, IAnalyticsTracking, IAnalyticsSettings):
    """
    Analytics utility
    """
    
    report_categories = schema.List(title=_(u"Report Categories"),
        default=['Site Wide', 'Portlet'],
        required=False)
        
