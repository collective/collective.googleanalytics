from zope.interface import implements
from zope.component import getMultiAdapter
from collective.googleanalytics.interfaces.adapters import IAnalyticsDateRangeChoices
from collective.googleanalytics.interfaces.plugins import IAnalyticsPlugin
import datetime

class AnalyticsBasePlugin(object):
    """
    A plugin for Analytics reports.
    """
    
    implements(IAnalyticsPlugin)
        
    def __init__(self, context, request, report):
        self.context = context
        self.request = request
        self.report = report
    
    name = 'Analytics Base Plugin'
        
    def processDimensionsChoices(self, choices):
        """
        Process the dimensions choices.
        """

        pass
        
    def processMetricsChoices(self, choices):
        """
        Process the metrics choices.
        """

        pass
    
    def processCacheArguments(self, cache_args):
        """
        Process the cache arguments.
        """
        
        pass
    
    def processQueryCriteria(self, criteria):
        """
        Process the query criteria.
        """
        
        pass
    
    def processExpressionContext(self, exp_context):
        """
        Process the expression context.
        """
        
        pass

class AnalyticsVariableDateRange(AnalyticsBasePlugin):
    """
    A plugin that allows date ranges to be selected dynamically when the report
    is evaluated.
    """
    
    name = 'Variable Date Range'
            
    def __init__(self, context, request, report):
        super(AnalyticsVariableDateRange, self).__init__(context, request, report)
        
        self.start_date = request.get('start_date', None)
        self.end_date = request.get('end_date', None)
        date_range = request.get('date_range', 'month')
        
        if not self.start_date or not self.end_date:
            self.start_date, self.end_date = self._getDateRange(date_range)
        
    def processDimensionsChoices(self, choices):
        """
        Process the dimensions choices.
        """

        choices.extend(['date_range_dimension', 'date_range_sort_dimension'])
    
    def processQueryCriteria(self, criteria):
        """
        Process the query criteria.
        """
        
        if self.start_date and self.end_date:
            criteria.update({
                'start_date': self.start_date,
                'end_date': self.end_date,
            })
            
    def processExpressionContext(self, exp_context):
        """
        Process the expression context.
        """
        
        date_context = self._getDateContext()
        exp_context.update(date_context)
        
    def _getDateRange(self, date_range='month'):
        """
        Given a number of days or a date range keyword, get the 
        appropriate start and end dates.
        """
        today = datetime.date.today()
        if type(date_range) == int and date_range > 0:
            return [today - datetime.timedelta(days=date_range), today]

        choices_provider = getMultiAdapter(
            (self.context, self.request, self.report),
            interface=IAnalyticsDateRangeChoices,
        )
        choices = choices_provider.getChoices()
        if date_range in choices.keys():
            return choices[date_range]
        else:
            return [today - datetime.timedelta(days=29), today]

    def _getDateContext(self):
        """
        Given date range arguments, return a dictionary containing the
        relevant expression context variables.
        """

        delta = self.end_date - self.start_date
        days = delta.days

        # Set the dimensions and sort based on the number of days.
        # We assume that the first dimension in the list is the date
        # range dimension that the report will use.
        date_range_choices = [
            (30, 'ga:day', 'ga:date', 'Day'),
            (210, 'ga:week', 'ga:year', 'Week'),
            (1160, 'ga:month', 'ga:year', 'Month'),
        ]

        date_range_max = ('ga:year', 'ga:year', 'Year'),

        date_range = None
        for choice in date_range_choices:
            if days <= choice[0]:
                date_range = choice[1:]
                break

        if not date_range:
            date_range = date_range_max

        dimension, sort_dimension, unit = date_range

        return {
            'date_range_unit': unit,
            'date_range_unit_plural': unit + 's',
            'date_range_dimension': dimension,
            'date_range_sort_dimension': sort_dimension,
        }
        
class AnalyticsContextualResults(AnalyticsBasePlugin):
    """
    A plugin that allows results of an Analytics report to be specific to the
    requested page.
    """
    
    name = 'Contextual Results'
    
    def __init__(self, context, request, report):
        super(AnalyticsContextualResults, self).__init__(context, request, report)
        
        # Get the relative URL of the request.
        absolute_url = request.get('request_url', request.ACTUAL_URL)
        self.relative_url = absolute_url.replace(request.SERVER_URL, '').strip()
        
        # Remove the trailing slash from the relative URL.
        if self.relative_url.endswith('/'):
            self.relative_url = self.relative_url[:-1]

    
    def processCacheArguments(self, cache_args):
        """
        Process the cache arguments.
        """

        cache_args.append(self.relative_url)

    def processExpressionContext(self, exp_context):
        """
        Process the expression context.
        """

        exp_context['page_url'] = self.relative_url
        url_pattern = '=~^%s/?$' % self.relative_url
        exp_context['page_filter'] = 'ga:pagePath%s' % url_pattern
        exp_context['nextpage_filter'] = 'ga:nextPagePath%s' % url_pattern
        exp_context['previouspage_filter'] = 'ga:previousPagePath%s' % url_pattern
