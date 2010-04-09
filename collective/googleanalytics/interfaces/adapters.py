from zope.interface import Interface

class IAnalyticsExpressionVars(Interface):
    """
    Adapter to provide the default variables for the TALES expression context.
    """
        
    def getExpressionVars():
        """
        Returns a dictionary containing the expression variables.
        """

class IAnalyticsDateRangeChoices(Interface):
    """
    A utility to get the date range choices for a particular report,
    request and context.
    """
    
    def getChoices():
        """
        Returns the appropriate date range choices.
        """