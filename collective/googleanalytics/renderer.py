try:
    from App.class_init import InitializeClass
except ImportError:
    from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from zope.interface import implements
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.Expression import getEngine
from Products.CMFCore.utils import getToolByName
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from plone.memoize.volatile import cache, ATTR, CONTAINER_FACTORY
from plone.memoize.instance import memoize

from collective.googleanalytics.interfaces.report import IAnalyticsReportRenderer
from collective.googleanalytics.visualization import AnalyticsReportVisualization
from collective.googleanalytics.utils import evaluateTALES, extract_value, \
    unique_list, getDate, getTimeDelta

import datetime
import math
import time
import sys

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
    
    for plugin in instance.plugins:
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
    
    security = ClassSecurityInfo()
    
    no_results = ViewPageTemplateFile('report_templates/noresults.pt')
    error = ViewPageTemplateFile('report_templates/error.pt')
    
    def __init__(self, context, request, report):
        self.context = context
        self.request = request
        self.report = report
        self.plugins = report.getPlugins(context, request)
        self._data_feed = None
    
    security.declarePrivate('__call__')
    @cache(renderer_cache_key, renderer_cache_storage)
    def __call__(self):
        """
        Renders the report.
        """
        
        if not self.data():
            return self.no_results()
            
        try:
            tal_context = self._getExpressionContext(
                extra={'view': self,},
                tal=True,
            )
        
            pt = ZopePageTemplate(id='__collective_googleanalytics__')
            pt.pt_edit(self.report.body, 'text/html')
            return pt.__of__(self.context).pt_render(extra_context=tal_context)
        except Exception:
            logger.exception('Error while rendering %r' % self.report.id)
            error_log = getToolByName(self.context, 'error_log')
            error_log.raising(sys.exc_info())
            return self.error()
        
    security.declarePublic('profile_ids')
    @memoize
    def profile_ids(self):
        """
        Returns a list of Google Analytics profiles for which the report
        is being evaluated.
        """
        
        profile_ids = self.request.get('profile_ids', [])
        if type(profile_ids) is str:
            profile_ids = [profile_ids]
        return profile_ids
        
    security.declarePublic('query_criteria')
    @memoize
    def query_criteria(self):
        """
        Returns the evaluated query criteria.
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
        
        for plugin in self.plugins:
            plugin.processQueryCriteria(criteria)
        
        return criteria
        
    security.declarePublic('data')
    @memoize
    def data(self):
        """
        Returns a list of dictionaries containing the values of the
        dimensions and metrics for each entry in the data feed returned
        by Google.
        """

        results = []
        for entry in self._getDataFeed().entry:
            results.append(dict([extract_value(row) for row in entry.dimension + entry.metric]))
        return results
        
    security.declarePublic('columns')
    @memoize
    def columns(self):
        """
        Returns the evaluated table column headings.
        """
        
        values_context = {
            'dimension': self.dimension,
            'metric': self.metric,
            'possible_dates': self.possible_dates,
        }
        
        columns_context = self._getExpressionContext(values_context)
        return evaluateTALES(self.report.columns, columns_context)
        
    security.declarePublic('rows')
    @memoize
    def rows(self):
        """
        Returns the evaluated table rows.
        """
        
        values_vars = {
            'dimension': self.dimension,
            'metric': self.metric,
            'possible_dates': self.possible_dates,
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
        
    security.declarePublic('visualization')
    @memoize
    def visualization(self):
        """
        Returns the rendered visualization.
        """
        
        return self._getVisualization().render()
        
    security.declarePublic('dimension')
    def dimension(self, dimension, specified={}, aggregate=unique_list, default=[]):
        """
        Returns the value of the given metric across the specified
        dimensions and metrics using the specified aggregation method.
        """
        
        return self._getValue(dimension, specified, aggregate, default)
                    
    security.declarePublic('metric')
    def metric(self, metric, specified={}, aggregate=sum, default=0):
        """
        Returns the value of the given metric across the specified
        dimensions and metrics using the specified aggregation method.
        """
        return self._getValue(metric, specified, aggregate, default)
        
    security.declarePublic('possible_dates')
    def possible_dates(self, dimensions=[], aggregate=list):
        """
        Returns a list of dictionaries containing all possible values for
        the given date dimension in the current date range.
        """
        
        start = self.query_criteria()['start_date']
        end = self.query_criteria()['end_date']
        delta = end - start
        
        if not dimensions:
            dimensions = self.query_criteria()['dimensions']
            
        DATE_DIMENSIONS = ['ga:date', 'ga:day', 'ga:week', 'ga:month', 'ga:year']
        date_dimensions = list(set(dimensions) & set(DATE_DIMENSIONS))
        results = []
        
        for delta_days in range(0, delta.days + 1):
            date = start + datetime.timedelta(days=delta_days)
            values = {}
            
            if 'ga:date' in date_dimensions:
                values['ga:date'] = date
            if 'ga:day' in date_dimensions:
                values['ga:day'] = date.day
            if 'ga:week' in date_dimensions:
                # According to Google, weeks start on Sunday, and week 1 of a
                # particular year begins on January 1 and ends on the first
                # possible Saturday (which may be January 1, making a 1-day
                # week).
                first = datetime.date(date.year, 1, 1)
                firstweek_days = 6 - first.weekday() or 7
                ytd = date - first
                ytd_days = ytd.days + 1
                
                values['ga:week'] = int(math.ceil(float(ytd_days - firstweek_days)/7)) + 1
            if 'ga:month' in date_dimensions:
                values['ga:month'] = date.month
            if 'ga:year' in date_dimensions:
                values['ga:year'] = date.year
                
            if values and not values in results:
                results.append(values)
            
        return aggregate(results)
        
    security.declarePrivate('_getQueryArguments')
    @memoize
    def _getQueryArguments(self):
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
    
    security.declarePrivate('_getDataFeed')
    @memoize
    def _getDataFeed(self):
        """
        Returns a Google Analytics data feed.
        """

        if self._data_feed:
            return self._data_feed

        analytics_tool = getToolByName(self.context, 'portal_analytics')
        query_args = self._getQueryArguments()
        data_feed = analytics_tool.makeClientRequest('data', 'GetData', **query_args)
        logger.info("Querying Google for report '%s' on context '%s'." % 
            (self.report.id, self.context.id))

        return data_feed
        
    security.declarePrivate('_getVisualization')
    @memoize
    def _getVisualization(self):
        """
        Returns an AnalyticsReportVisualization for this report.
        """

        # Evaluate the visualization options.
        exp_context = self._getExpressionContext()
        options = evaluateTALES(dict([v.split(' ', 1) for v in self.report.viz_options]), exp_context)

        return AnalyticsReportVisualization(self.report, self.columns(), self.rows(), options)
        
    security.declarePrivate('_getExpressionContext')
    def _getExpressionContext(self, extra={}, tal=False):
        """
        Returns the context for rendering TALES or TAL. If the tal argument
        is true, a dictionary of variables is returned. Otherwise, an
        an expression context object is returned.
        """
        
        context_vars = {
            'context': self.context,
            'request': self.request,
            'today': datetime.date.today(),
            'date': getDate,
            'timedelta': getTimeDelta,
            'unique_list': unique_list,
        }
        
        context_vars.update(extra)

        for plugin in self.plugins:
            plugin.processExpressionContext(context_vars)

        if tal:
            return context_vars
        return getEngine().getContext(context_vars)
        
    security.declarePrivate('_getValue')
    def _getValue(self, name, specified={}, aggregate=sum, default=0):
        """
        Returns the value of a dimension or metric from the data feed accross
        other specified dimensions or metrics.
        """

        values = [e[name] for e in self.data() if set(specified.items()) <= set(e.items())]
        if not values:
            return default
        return aggregate(values)
        
InitializeClass(AnalyticsReportRenderer)