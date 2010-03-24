from zope.interface import Interface

class IAnalyticsAsyncLoader(Interface):
    """
    Generates the javascript for loading Analytics report results
    asynchronously.
    """
    
    def getContainerId():
        """
        Creates a unique HTML id for the target element into which the report
        result will be loaded.
        """
    
    def getJavascript(report_ids, date_range, container_id=None):
        """
        Returns the javascript for loading the results of the given reports IDs
        and date range keyword into the HTML element specified by the container
        ID. If a container ID is omitted, it is obtained using getContainerId.
        """