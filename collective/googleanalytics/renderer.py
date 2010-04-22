from zope.interface import implements
from zope.component import getMultiAdapter
from Products.CMFCore.Expression import getEngine
from Products.CMFCore.utils import getToolByName
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from plone.memoize.volatile import cache, ATTR, CONTAINER_FACTORY
from plone.memoize.instance import memoize

from collective.googleanalytics.interfaces.adapters import IAnalyticsExpressionVars
from collective.googleanalytics.interfaces.report import IAnalyticsReportRenderer
from collective.googleanalytics.visualization import AnalyticsReportVisualization
from collective.googleanalytics.utils import evaluateTALES, extract_value

import datetime
import math
import time

import logging
logger = logging.getLogger("analytics")

def renderer_cache_key(method, instance):
    analytics_tool = getToolByName(instance.context, 'portal_analytics')
    cache_interval = analytics_tool.cache_interval
    cache_interval = (cache_interval > 0 and cache_interval * 60) or 1
    time_key = time.time() // cache_interval
    modification_time = str(instance.report.bobobase_modification_time())
    report_id = instance.report.id
    cache_vars = [time_key, modification_time, report_id, tuple(instance.profile_ids())]
    
    for plugin in instance.report.getPlugins(instance.context, instance.request):
        plugin.processCacheArguments(cache_vars)
    
    return hash(tuple(cache_vars))

def renderer_cache_storage(method, instance):
    return instance.report.__dict__.setdefault(ATTR, CONTAINER_FACTORY())

class AnalyticsReportRenderer(object):
    """
    The renderer for an Analytics report. It is a multiadapter on the context,
    the request and the report.
    """
    
    implements(IAnalyticsReportRenderer)    
    
    def __init__(self, context, request, report):
        self.context = context
        self.request = request
        self.report = report
    
    @cache(renderer_cache_key, renderer_cache_storage)
    def __call__(self):
        tal_context = self._getExpressionContext(
            extra={'view': self,},
            tal=True,
        )
        
        pt = ZopePageTemplate(id='__collective_googleanalytics__')
        pt.pt_edit(self.report.body, 'text/html')
        return pt.__of__(self.context).pt_render(extra_context=tal_context)
        
    @memoize
    def data_feed(self):
        """
        Returns a Google Analytics data feed.
        """
        
        analytics_tool = getToolByName(self.context, 'portal_analytics')
        query_args = self.query_arguments()
        data_feed = analytics_tool.makeClientRequest('data', 'GetData', **query_args)
        logger.info("Querying Google for report '%s' on context '%s'." % 
            (self.report.id, self.context.id))

        return data_feed
        
    @memoize
    def profile_ids(self):
        """
        Returns a list of Google Analytics profiles for which this report
        should be evaluated.
        """
        
        profile_ids = self.request.get('profile_ids', [])
        if type(profile_ids) is str:
            profile_ids = [profile_ids]
        return profile_ids
        
    @memoize
    def query_criteria(self):
        """
        Evaluates the query criteria provided by the report.
        """
        
        expressions = {
            'dimensions': list(self.report.dimensions),
            'metrics': list(self.report.metrics),
            'filters': list(self.report.filters),
            'sort': list(self.report.sort),
            'start_date': str(self.report.start_date),
            'end_date': str(self.report.end_date),
            'max_results': str(self.report.max_results),
        }
        
        criteria = evaluateTALES(expressions, self._getExpressionContext())
        criteria['ids'] = self.profile_ids()
        
        for plugin in self.report.getPlugins(self.context, self.request):
            plugin.processQueryCriteria(criteria)
        
        return criteria
        
    @memoize
    def query_arguments(self):
        """
        Returns the query arguments in the format that Google expects.
        """

        criteria = self.query_criteria()
        query_args = {
            'ids': ','.join(criteria['ids']),
            'dimensions': ','.join(criteria['dimensions']),
            'metrics': ','.join(criteria['metrics']),
            'filters': ','.join(criteria['filters']),
            'sort': ','.join(criteria['sort']),
            'start_date': criteria['start_date'],
            'end_date': criteria['end_date'],
            'max_results': criteria['max_results'],
        }
        return query_args
        
    @memoize
    def data(self):
        """
        Returns a generator of dictionaries containing the values of the
        dimensions and metrics for each data feed entry.
        """

        results = []
        for entry in self.data_feed().entry:
            results.append(dict([extract_value(row) for row in entry.dimension + entry.metric]))
        return results
        
    @memoize
    def columns(self):
        """
        Iterate through the data returned by Google and calcualte the value of the
        report columns.
        """
        
        values_context = {
            'value': self.value,
            'dimension': self.dimension,
            'metric': self.metric,
        }
        
        columns_context = self._getExpressionContext(values_context)
        return evaluateTALES(self.report.columns, columns_context)
        
    @memoize
    def rows(self):
        """
        Iterate through the data returned by Google and calcualte the value of the
        report columns.
        """
        
        values_vars = {
            'value': self.value,
            'dimension': self.dimension,
            'metric': self.metric,
        }
        
        repeat_context = self._getExpressionContext(values_vars)
        repeat = evaluateTALES(self.report.row_repeat, repeat_context)
        
        rows = []
        
        row_vars = values_vars.copy()
        row_vars.update({'columns': self.columns()})
        
        for row in repeat:
            row_vars['row'] = row
            row_context = self._getExpressionContext(row_vars)
            rows.append(evaluateTALES(self.report.rows, row_context))

        return rows
        
    @memoize
    def visualization(self):
        """
        Returns an AnalyticsReportVisualization for this report.
        """
        
        # Evaluate the visualization options.
        exp_context = self._getExpressionContext()
        options = evaluateTALES(dict([v.split(' ') for v in self.report.viz_options]), exp_context)

        return AnalyticsReportVisualization(self.report, self.columns(), self.rows(), options)
        
    def dimension(self, dimension, specified={}, aggregate=list, default=[]):
        """
        Returns the value of the given dimension across the specified
        metrics using the specified aggregation method.
        """
        
        return self.value(dimension, specified, aggregate, default)
                    
    def metric(self, metric, specified={}, aggregate=sum, default=0):
        """
        Returns the value of the given metic across the specified
        dimensions using the specified aggregation method.
        """

        return self.value(metric, specified, aggregate, default)
        
    def value(self, name, specified={}, aggregate=sum, default=0):
        """
        Returns the value of a dimension or metric from the data feed accross
        other specified dimensions or metrics.
        """
        
        values = [e[name] for e in self.data() if set(specified.items()) <= set(e.items())]
        if not values:
            return default
        return aggregate(values)
        
    def possible(self, name):
        """
        Returns all possible values for a date dimension given the current
        date range.
        """
        
        start = self.query_criteria()['start_date']
        end = self.query_criteria()['end_date']
        delta = end - start
        results = []
        previous = None
        
        for delta_days in range(0, delta.days):
            date = start + datetime.timedelta(days=delta_days)
            if name == 'ga:date':
                value = date
            elif name == 'ga:day':
                value = date.day
            elif name == 'ga:week':
                # According to Google, weeks start on Sunday, and week 1 of a
                # particular year begins on January 1 and ends on the first
                # possible Saturday (which may be January 1, making a 1-day
                # week).
                first = datetime.date(date.year, 1, 1)
                firstweek_days = 6 - first.weekday() or 7
                ytd = date - first
                ytd_days = ytd.days + 1
                
                value = int(math.ceil(float(ytd_days - firstweek_days)/7)) + 1
            elif name == 'ga:month':
                value = date.month
            elif name == 'ga:year':
                value = date.year
                
            if value and not value == previous:
                results.append(value)
                previous = value
            
        return results
        
    def _getExpressionContext(self, extra={}, tal=False):
        """
        Returns the context for rendering TALES or TAL. If the tal argument
        is true, a dictionary of variables is returned. Otherwise, an
        an expression context object is returned.
        """
        
        vars_provider = getMultiAdapter((self.context, self.request, self.report),interface=IAnalyticsExpressionVars)

        context_vars = vars_provider.getExpressionVars()
        context_vars.update(extra)

        for plugin in self.report.getPlugins(self.context, self.request):
            plugin.processExpressionContext(context_vars)

        if tal:
            return context_vars
        return getEngine().getContext(context_vars)