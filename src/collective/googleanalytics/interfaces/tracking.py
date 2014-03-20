from zope.interface import Interface

class IAnalyticsTrackingPlugin(Interface):
    """
    A plugin for Analytics reports.
    """
    
    def __call__():
        """
        Renders the tracking plugin.
        """