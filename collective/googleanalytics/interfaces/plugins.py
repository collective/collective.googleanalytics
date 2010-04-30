from zope.interface import Interface, Attribute

# General plugin interfaces

class IAnalyticsPlugin(Interface):
    """
    A plugin for Analytics reports.
    """
    
    name = Attribute('Plugin name')
        
    def processDimensionsChoices(choices):
        """
        Process the dimensions choices.
        """

    def processMetricsChoices(choices):
        """
        Process the metrics choices.
        """
        
    def processVisualizationChoices(choices):
        """
        Process the visualization choices.
        """
    
    def processCacheArguments(cache_args):
        """
        Process the cache arguments.
        """
    
    def processQueryCriteria(criteria):
        """
        Process the query criteria.
        """
    
    def processExpressionContext(exp_context):
        """
        Process the expression context.
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