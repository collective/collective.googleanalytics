from zope.interface import Interface, Attribute

# General plugin interfaces

class IAnalyticsPlugin(Interface):
    """
    A plugin for Analytics reports.
    """
    
    name = Attribute('Plugin name')
    
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
