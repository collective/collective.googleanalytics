try:
    from App.class_init import InitializeClass
except ImportError:
    from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from zope.interface import implements
from zope.tales.tales import CompilerError

from OFS.PropertyManager import PropertyManager
from OFS.SimpleItem import SimpleItem

from Products.CMFCore.Expression import Expression, getEngine
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate

from plone.memoize.volatile import cache

from collective.googleanalytics.interfaces.report import IAnalyticsReport
from collective.googleanalytics.config import METRICS_CHOICES, DIMENSIONS_CHOICES, VISUALIZATION_CHOICES

from string import Template

from DateTime import DateTime
import datetime
import time
import os

import logging
logger = logging.getLogger("analytics")

def report_results_cache_key(method, instance, context, profile, start_date, end_date, data_feed=None):
    analytics_tool = instance.aq_parent
    cache_interval = analytics_tool.cache_interval
    cache_interval = (cache_interval > 0 and cache_interval * 60) or 1
    time_key = time.time() // cache_interval
    modification_time = str(instance.bobobase_modification_time())
    cache_vars = [time_key, modification_time, profile, start_date, end_date]
    if instance.is_page_specific:
        cache_vars.append(context.request.ACTUAL_URL)
    return hash(tuple(cache_vars))

def getDateRangeChoices(context):
    """
    Return a list of possible date ranges for this content.
    """

    today = datetime.date.today()
    timedelta = datetime.timedelta

    mtd_days = today.day - 1
    ytd_days = today.replace(year=1).toordinal() - 1

    date_ranges = {
        'week': [today - timedelta(days=6), today],
        'month': [today - timedelta(days=29), today],
        'quarter': [today - timedelta(days=89), today],
        'year': [today - timedelta(days=364), today],
        'mdt': [today - timedelta(days=mtd_days), today],
        'ytd': [today - timedelta(days=ytd_days), today],
    }

    if hasattr(context, 'Date') and context.Date() is not 'None':
        pub_dt = DateTime(context.Date())
        published_date = datetime.date(pub_dt.year(), pub_dt.month(), pub_dt.day())
        date_ranges.update({
            'published': [published_date, today],
        })

    return date_ranges

class AnalyticsReport(PropertyManager, SimpleItem):
    """
    A Google Analytics report. The AnalyticsReport object defines all of the parameters
    used to query Google and format the result into a report.
    """
    
    implements(IAnalyticsReport)

    i18n_domain = 'analytics'
    
    security = ClassSecurityInfo()
    
    security.declarePrivate('title')
    security.declarePrivate('description')
    security.declarePrivate('i18n_domain')
    security.declarePrivate('metrics')
    security.declarePrivate('dimensions')
    security.declarePrivate('filters')
    security.declarePrivate('sort')
    security.declarePrivate('max_results')
    security.declarePrivate('is_page_specific')
    security.declarePrivate('categories')
    security.declarePrivate('column_labels')
    security.declarePrivate('column_exps')
    security.declarePrivate('viz_type')
    security.declarePrivate('viz_options')
    security.declarePrivate('introduction')
    security.declarePrivate('conclusion')
    
    _properties = (
        {'id': 'title', 'type': 'string', 'mode': 'w',
        'label': 'Title'},
        {'id': 'description', 'type': 'text', 'mode': 'w',
        'label': 'Description'},
        {'id':'i18n_domain', 'type': 'string', 'mode':'w',
         'label':'I18n Domain'},
        {'id':'is_page_specific', 'type': 'boolean', 'mode':'w',
         'label':'Page Specific'},
        {'id':'categories', 'type': 'multiple selection', 'mode':'w',
         'label':'Categories', 'select_variable': 'getCategoriesChoices'},
        {'id':'metrics', 'type': 'multiple selection', 'mode':'w',
        'label':'Query Metrics', 'select_variable': 'getMetricsChoices'},
        {'id':'dimensions', 'type': 'multiple selection', 'mode':'w',
        'label':'Query Dimensions', 'select_variable': 'getDimensionsChoices'},
        {'id':'filters', 'type': 'lines', 'mode':'w',
        'label':'Query Filters'},
        {'id':'sort', 'type': 'lines', 'mode':'w',
        'label':'Query Sort'},
        {'id':'max_results', 'type': 'int', 'mode':'w',
        'label':'Query Maximum Results'},
        {'id':'column_labels', 'type': 'lines', 'mode':'w',
        'label':'Report Column Labels'},
        {'id':'column_exps', 'type': 'lines', 'mode':'w',
        'label':'Report Column Expressions'},
        {'id':'introduction', 'type': 'text', 'mode':'w',
        'label':'Report Introduction'},
        {'id':'conclusion', 'type': 'text', 'mode':'w',
        'label':'Report Conclusion'},
        {'id':'viz_type', 'type': 'selection', 'mode':'w',
        'label':'Visualization Type', 'select_variable': 'getVisualizationChoices'},
        {'id':'viz_options', 'type': 'lines', 'mode':'w',
        'label':'Visualization Options'},
    )

    manage_options = (
        PropertyManager.manage_options
        + SimpleItem.manage_options)
    
    security.declarePrivate('__init__')
    def __init__(self, id, **kwargs):
        self.id = id
        self.title = kwargs.get('title', '')
        self.description = kwargs.get('description', '')
        self.i18n_domain = kwargs.get('i18n_domain', 'analytics')
        self.viz_type = kwargs.get('viz_type', 'Table')
        self.viz_options = kwargs.get('viz_options', [])
        self.column_labels = kwargs.get('column_labels', [])
        self.column_exps = kwargs.get('column_exps', [])
        self.metrics = kwargs.get('metrics', [])
        self.dimensions = kwargs.get('dimensions', [])
        self.filters = kwargs.get('filters', [])
        self.sort = kwargs.get('sort', [])
        self.introduction = kwargs.get('introduction', '')
        self.conclusion = kwargs.get('conclusion', '')
        self.max_results = kwargs.get('max_results', 1000)
        self.is_page_specific = kwargs.get('is_page_specific', False)
        self.categories = kwargs.get('categories', [])
        
    security.declarePrivate('getMetricsChoices')
    def getMetricsChoices(self):
        """
        Return the list of possible metrics.
        """
        return METRICS_CHOICES

    security.declarePrivate('getDimensionsChoices')
    def getDimensionsChoices(self):
        """
        Return the list of possible dimensions.
        """
        return DIMENSIONS_CHOICES
        
    security.declarePrivate('getVisualizationChoices')
    def getVisualizationChoices(self):
        """
        Return the list of visualization types.
        """
        return VISUALIZATION_CHOICES
        
    security.declarePublic('_getTimeDelta')
    def _getTimeDelta(self, **kwargs):
        """
        Return a python timedelta for use in TALES expressions.
        """
        return datetime.timedelta(**kwargs)
        
    security.declarePublic('_getDate')
    def _getDate(self, year, month, day):
        """
        Return a python date for use in TALES expressions.
        """
        return datetime.date(year, month, day)
        
    security.declarePrivate('_getExpressionContextDict')
    def _getExpressionContextDict(self, context):
        """
        Return the dictonary used to form the expression context.
        """
        
        request = context.REQUEST
        absolute_url = request.get('request_url', request.ACTUAL_URL)
        return {
            'context': context,
            'request': request,
            'today': datetime.date.today(),
            'date': self._getDate,
            'timedelta': self._getTimeDelta,
            'page_url': absolute_url.replace(request.SERVER_URL, ''),
        }
    
    security.declarePrivate('_getExpressionContext')
    def _getExpressionContext(self, context, extra={}):
        """
        Return the context for evaluating TALES expressions.
        """
        
        context_dict = self._getExpressionContextDict(context)
        context_dict.update(extra)
        return getEngine().getContext(context_dict)

    security.declarePrivate('_evaluateExpression')
    def _evaluateExpression(self, expression, exp_context):
        """
        Evalute a TALES expression using the given context.
        """
        try:
            return Expression(str(expression))(exp_context)
        except (KeyError, CompilerError):
            return expression

    security.declarePrivate('_evaluateList')
    def _evaluateList(self, parent, exp_context):
        """
        Evaluate each TALES expression in a list.
        """
        results = []
        if hasattr(parent, '__iter__'):
            for child in parent:
                results.append(self._evaluateList(child, exp_context))
            return results
        return self._evaluateExpression(parent, exp_context)
        
    security.declarePrivate('_evaluateTAL')
    def _evaluateTAL(self, tal, context, extra={}):
        """
        Evalute HTML containing TAL.
        """
        
        pt = ZopePageTemplate(id='__collective_googleanalytics__')
        pt.pt_edit(tal, 'text/html')
        return pt.__of__(context).pt_render(extra_context=extra)
        
    security.declarePrivate('_getDateRange')
    def _getDateRange(self, context, date_range='month'):
        """
        Given a number of days or a date range keyword, get the 
        appropriate start and end dates.
        """
        today = datetime.date.today()
        if type(date_range) == int and date_range > 0:
            return [today - datetime.timedelta(days=date_range), today]
        
        choices = getDateRangeChoices(context)
        if date_range in choices.keys():
            return choices[date_range]
        else:
            return [today - datetime.timedelta(days=29), today]
        
    security.declarePrivate('_getDateContext')
    def _getDateContext(self, start_date, end_date):
        """
        Given date range arguments, return a dictionary containing the
        relevant expression context variables.
        """

        delta = end_date - start_date
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

    security.declarePrivate('_getQueryCriteria')
    def _getQueryCriteria(self, context, profiles, start_date, end_date):
        """
        Get the criteria for the query (i.e. resolve the variables that need to be
        evaluted before the query can be performed).
        """
        
        date_context = self._getDateContext(start_date, end_date)
        exp_context = self._getExpressionContext(context, date_context)
        criteria = {
            'ids': profiles,
            'dimensions': self._evaluateList(self.dimensions, exp_context),
            'metrics': self._evaluateList(self.metrics, exp_context),
            'filters': self._evaluateList(self.filters, exp_context),
            'sort': self._evaluateList(self.sort, exp_context),
            'start_date': start_date,
            'end_date': end_date,
            'max_results': self.max_results,
        }
        return criteria

    security.declarePrivate('_makeDate')
    def _makeDate(self, date_stamp):
        """
        Given a date string returned by Google, return the corresponding python
        date object.
        """
        date_string = str(date_stamp)
        year = int(date_string[0:4])
        month = int(date_string[4:6])
        day = int(date_string[6:8])
        return datetime.date(year, month, day)
        
    security.declarePrivate('_makeGoogleVarName')
    def _makeGoogleVarName(self, google_name):
        """
        Determine if the given name is a Google dimension or metric.  If it is,
        return the corresponding variable name (i.e. replace the colon with an
        underscore). Otherwise, return the variable name as is.
        """
        
        if len(google_name) > 3 and google_name[:3] == 'ga:':
            return 'ga_' + google_name[3:]
        return google_name

    security.declarePrivate('_evaluateData')
    def _evaluateData(self, context, criteria, data):
        """
        Iterate through the data returned by Google and calcualte the value of the
        report columns.
        """
        column_vars = criteria['dimensions'] + criteria['metrics']
        column_exps = self.column_exps
        rows = []
        date_context = self._getDateContext(criteria['start_date'], criteria['end_date'])
        for entry in data.entry:
            extra_context = date_context.copy()
            for column in entry.dimension + entry.metric:
                if column.name in column_vars:
                    value = column.value
                    if column.name == 'ga:date':
                        value = self._makeDate(column)
                    extra_context.update({self._makeGoogleVarName(column.name): value})
                    for date_var in date_context.keys():
                        if column.name == date_context[date_var]:
                            extra_context.update({date_var: value})
            exp_context = self._getExpressionContext(context, extra_context)
            row = self._evaluateList(column_exps, exp_context)
            rows.append(row)
        return rows
    
    security.declarePrivate('_getReportDefinition')
    def _getReportDefinition(self, context, criteria, data):
        """
        Returns the definition for the report.
        """
        
        date_context = self._getDateContext(criteria['start_date'], criteria['end_date'])
        exp_context = self._getExpressionContext(context, date_context)
        viz_options = {}
        for option in self.viz_options:
            try:
                option_key, option_value = option.split(' ', 1)
            except ValueError:
                continue
            viz_options.update({option_key: self._evaluateExpression(option_value, exp_context)})
        tal_dict = self._getExpressionContextDict(context)
        tal_dict.update({
            'data_length': len(data),
            'data_rows': data, 
            'data_columns': zip(*data),
        })
        tal_dict.update(date_context)
        definition = {
            'introduction': self._evaluateTAL(self.introduction, context, tal_dict),
            'conclusion': self._evaluateTAL(self.conclusion, context, tal_dict),
            'viz_type': self.viz_type,
            'viz_options': viz_options,
            'column_labels': self._evaluateList(self.column_labels, exp_context),
        }
        return definition
        
    security.declarePrivate('getResults')
    def getResults(self, context, profile, **kwargs):
        """
        Return a results object that encapsulates the results of the query.
        This function is a wrapper for _getResultsForDates because the
        cache decorator can't accept keyword arguments.
        """
        
        start_date = kwargs.get('start_date', None)
        end_date = kwargs.get('end_date', None)
        date_range = kwargs.get('date_range', 'month')
        data_feed = kwargs.get('data_feed', None)
        
        if not start_date and not end_date:
            start_date, end_date = self._getDateRange(context, date_range)
            
        return self._getResultsForDates(context, profile, start_date, end_date, data_feed)
        
    security.declarePrivate('_getResultsForDates')
    @cache(report_results_cache_key)
    def _getResultsForDates(self, context, profile, start_date, end_date, data_feed=None):
        """
        Return a results object that encapsulates the results of the query.
        """
        
        criteria = self._getQueryCriteria(context, [profile], start_date, end_date)

        if not data_feed:
            analytics_tool = self.aq_parent
            query_args = self._getQueryArgs(criteria)
            data_feed = analytics_tool.makeClientRequest('data', 'GetData', **query_args)
            
        data = self._evaluateData(context, criteria, data_feed)
        definition = self._getReportDefinition(context, criteria, data)
        logger.info("Querying Google for report '%s' on context '%s'." % 
            (self.id, context.id))
        return AnalyticsReportResults(self.id, definition, data)

    security.declarePrivate('_getQueryArgs')
    def _getQueryArgs(self, criteria):
        """
        Given the query criteria from _getQueryCriteria, form the query arguments in the format
        that Google expects.
        """
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

InitializeClass(AnalyticsReport)

class AnalyticsReportResults(object):
    """
    The results for an Analytics report. This object is generated by the getResults method
    of the AnalyticsReport object. It encapsulates all of the logic for turning the report
    results in to javascript configuration for Google Visualizations.
    """
    def __init__(self, report_id, definition, data):
        self.definition = definition
        self.data = data
        self.id = report_id
        self.time_stamp = str(time.time())
        
    def getJSValue(self, value):
        """
        Given a python value, return the corresponding javascript value.
        """
        # A date
        if isinstance(value, datetime.date):
            return 'new Date(%i, %i, %i)' % (value.year, value.month, value.day)
        # A boolean
        if isinstance(value, bool):
            return str(value).lower()
        # A string
        if isinstance(value, str):
            return '"%s"' % (value.replace('"', '\\"').replace("'", "\\'"))
        # A number
        return str(value)

    def getVizData(self):
        """
        Return a javascript array that describes the data. It is used by Google
        Visualizations to populate the DataTable.
        """
        js_rows = []
        for row in self.data:
            js_row = []
            for value in row:
                js_row.append(self.getJSValue(value))
            js_rows.append('[%s]' % (', '.join(js_row)))
        return '[\n%s\n]' % (',\n'.join(js_rows))

    def getVizColumns(self):
        """
        Return javascript that adds the appropriate columns to the DataTable.
        """
        column_labels = self.definition['column_labels']
        column_types = []
        if self.data:
            for value in self.data[0]:
                if isinstance(value, datetime.date):
                    col_type = 'date'
                elif isinstance(value, str):
                    col_type = 'string'
                else:
                    col_type = 'number'
                column_types.append(col_type)
            js = []
            for col_type, label in zip(column_types, column_labels):
                js.append('data.addColumn("%s", "%s");' % (col_type, label))
            return '\n'.join(js)
        return ''

    def getVizPackage(self):
        """
        Return the name of the package that contains the selected visualization.
        """
        return self.definition['viz_type'].lower()

    def getVizChartType(self):
        """
        Return the javascript class used to generate the visualization.
        """
        return self.definition['viz_type']

    def getVizID(self):
        """
        Create a unique ID that we can use for the div that will hold the visualization.
        """
        try:
            import hashlib
            viz_id = hashlib.md5(self.id + self.time_stamp).hexdigest()
        except ImportError:
            import md5
            viz_id = md5.new(self.id + self.time_stamp).hexdigest()
        
        return 'analytics-' + viz_id

    def getVizOptions(self):
        """
        Return a javascript object containing the options for the visualization.
        """
        js_options = []
        for option, value in self.definition['viz_options'].items():
            js_options.append('%s: %s' % (option, self.getJSValue(value)))
        # Set the width of the visualization to the container width if it
        # if not already set.
        if not 'width' in self.definition['viz_options'].keys():
            js_options.append('width: container_width')
        if js_options:
            return '{%s}' % (', '.join(js_options))
        return 'null'
        
    def getVizHeight(self):
        """
        Return the height of the visualization if it is set, or False if it is not.
        """
        
        if 'height' in self.definition['viz_options'].keys():
            return int(self.definition['viz_options']['height'])
        return False
        
    def getVizIntroduction(self):
        """
        Return the HTML for the report introduction.
        """
        return self.definition['introduction']
        
    def getVizConclusion(self):
        """
        Return the HTML for the report conclusion.
        """
        return self.definition['conclusion']

    def getVizJS(self):
        """
        Return the javascript to create the visualization.
        """
        template_file = os.path.join(os.path.dirname(__file__), 'visualization.js.tpl')
        template = Template(open(template_file).read())
        
        template_vars = {
            'package_name': self.getVizPackage(), 
            'columns': self.getVizColumns(), 
            'data': self.getVizData(), 
            'chart_type': self.getVizChartType(), 
            'id': self.getVizID(),
            'options': self.getVizOptions()
        }
        
        return template.substitute(template_vars)