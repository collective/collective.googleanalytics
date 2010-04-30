from zope.interface import Interface, Attribute

class IAnalyticsReport(Interface):
    """
    A report that can be used to gather information from Google Analytics.
    """
    
    title = Attribute('Title')
    description = Attribute('Description')
    i18n_domain = Attribute('I18n Domain')
    categories = Attribute('Categories')
    metrics = Attribute('Query Metrics')
    dimensions = Attribute('Query Dimensions')
    filters = Attribute('Query Filters')
    sort = Attribute('Query Sort')
    start_date = Attribute('Query Start Date')
    end_date = Attribute('Query End Date')
    max_results = Attribute('Query Maximum Results')
    columns = Attribute('Table Columns Expression')
    row_repeat = Attribute('Table Row Repeat Expression')
    rows = Attribute('Table Rows Expression')
    viz_type = Attribute('Visualization Type')
    viz_options = Attribute('Visualization Options')
    body = Attribute('Report Body')
    
    def getPlugins(context, request):
        """
        Returns the plugin adapters for this report.
        """
    
class IAnalyticsReportRenderer(Interface):
    """
    A report that can be used to gather information from Google Analytics.
    """
    
    def __call__():
        """
        Renders the report.
        """
        
    def data_feed(self):
        """
        Returns a Google Analytics data feed.
        """

    def profile_ids():
        """
        Returns a list of Google Analytics profiles for which this report
        should be evaluated.
        """

    def query_criteria():
        """
        Evaluates the query criteria provided by the report.
        """
        
    def query_arguments():
        """
        Returns the query arguments in the format that Google expects.
        """

    def data():
        """
        Returns a list of dictionaries containing the values of the
        dimensions and metrics for each data feed entry.
        """

    def columns():
        """
        Iterate through the data returned by Google and calcualte the value of the
        report columns.
        """

    def rows():
        """
        Iterate through the data returned by Google and calcualte the value of the
        report columns.
        """
        
    def visualization():
        """
        Returns an AnalyticsReportVisualization for this report.
        """

    def dimension(dimension, specified, aggregate, default):
        """
        Returns the value of the given dimension across the specified
        metrics using the specified aggregation method.
        """
                    
    def metric(metric, specified, aggregate, default):
        """
        Returns the value of the given metic across the specified
        dimensions using the specified aggregation method.
        """
        
    def value(name, specified, aggregate, default):
        """
        Returns the value of a dimension or metric from the data feed accross
        other specified dimensions or metrics.
        """
        
    def possible_dates(dimensions, aggregate):
        """
        Returns a list of dictionaries containing all possible values for the given
        date dimension in the current date range.
        """