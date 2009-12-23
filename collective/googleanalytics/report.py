from App.class_init import InitializeClass
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

import datetime
import time
import os

import logging
logger = logging.getLogger("analytics")

def report_results_cache_key(method, instance, context, profile, data_feed=None):
    analytics_tool = instance.aq_parent
    cache_interval = analytics_tool.cache_interval
    cache_interval = (cache_interval > 0 and cache_interval * 60) or 1
    time_key = time.time() // cache_interval
    modification_time = str(instance.bobobase_modification_time())
    cache_vars = [profile, time_key, modification_time]
    if instance.is_page_specific:
        cache_vars.append(context.request.ACTUAL_URL)
    return hash(tuple(cache_vars))

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
    security.declarePrivate('start_date')
    security.declarePrivate('end_date')
    security.declarePrivate('max_results')
    security.declarePrivate('is_page_specific')
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
        {'id':'metrics', 'type': 'multiple selection', 'mode':'w',
        'label':'Query Metrics', 'select_variable': 'getMetricsChoices'},
        {'id':'dimensions', 'type': 'multiple selection', 'mode':'w',
        'label':'Query Dimensions', 'select_variable': 'getDimensionsChoices'},
        {'id':'filters', 'type': 'lines', 'mode':'w',
        'label':'Query Filters'},
        {'id':'sort', 'type': 'lines', 'mode':'w',
        'label':'Query Sort'},
        {'id':'start_date', 'type': 'string', 'mode':'w',
        'label':'Query Start Date'},
        {'id':'end_date', 'type': 'string', 'mode':'w',
        'label':'Query End Date'},
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
        self.start_date = kwargs.get('start_date', 'today')
        self.end_date = kwargs.get('end_date', 'today')
        self.metrics = kwargs.get('metrics', [])
        self.dimensions = kwargs.get('dimensions', [])
        self.filters = kwargs.get('filters', [])
        self.sort = kwargs.get('sort', [])
        self.introduction = kwargs.get('introduction', '')
        self.conclusion = kwargs.get('conclusion', '')
        self.max_results = kwargs.get('max_results', 1000)
        self.is_page_specific = kwargs.get('is_page_specific', False)
        
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
        return {
            'context': context,
            'request': request,
            'today': datetime.date.today(),
            'date': self._getDate,
            'timedelta': self._getTimeDelta,
            'page_url': request.ACTUAL_URL.replace(request.SERVER_URL, ''),
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

    security.declarePrivate('_getQueryCriteria')
    def _getQueryCriteria(self, context, profiles):
        """
        Get the criteria for the query (i.e. resolve the variables that need to be
        evaluted before the query can be performed).
        """
        exp_context = self._getExpressionContext(context)
        criteria = {
            'ids': profiles,
            'dimensions': self._evaluateList(self.dimensions, exp_context),
            'metrics': self._evaluateList(self.metrics, exp_context),
            'filters': self._evaluateList(self.filters, exp_context),
            'sort': self._evaluateList(self.sort, exp_context),
            'start_date': self._evaluateExpression(self.start_date, exp_context),
            'end_date': self._evaluateExpression(self.end_date, exp_context),
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
        for entry in data.entry:
            extra_context = {}
            for column in entry.dimension + entry.metric:
                if column.name in column_vars:
                    value = column.value
                    if column.name == 'ga:date':
                        value = self._makeDate(column)
                    extra_context.update({self._makeGoogleVarName(column.name): value})
            exp_context = self._getExpressionContext(context, extra_context)
            row = self._evaluateList(column_exps, exp_context)
            rows.append(row)
        return rows
        
    security.declarePrivate('_getReportDefinition')
    def _getReportDefinition(self, context, data):
        """
        Returns the definition for the report.
        """
        exp_context = self._getExpressionContext(context)
        viz_options = {}
        for option in self.viz_options:
            try:
                option_key, option_value = option.split(' ', 1)
            except ValueError:
                continue
            viz_options.update({option_key: self._evaluateExpression(option_value, exp_context)})
        tal_dict = self._getExpressionContextDict(context)
        tal_dict.update({'data_rows': data, 'data_columns': zip(*data)})
        definition = {
            'introduction': self._evaluateTAL(self.introduction, context, tal_dict),
            'conclusion': self._evaluateTAL(self.conclusion, context, tal_dict),
            'viz_type': self.viz_type,
            'viz_options': viz_options,
            'column_exps': self._evaluateList(self.column_labels, exp_context),
        }
        return definition
        
    security.declarePrivate('getResults')
    @cache(report_results_cache_key)
    def getResults(self, context, profile, data_feed=None):
        """
        Return a results object that encapsulates the results of the query.
        """
        
        criteria = self._getQueryCriteria(context, [profile])

        if not data_feed:
            analytics_tool = self.aq_parent
            client = analytics_tool.getAuthenticatedClient()
            query_args = self._getQueryArgs(criteria)
            data_feed = client.GetData(**query_args)
            
        data = self._evaluateData(context, criteria, data_feed)
        definition = self._getReportDefinition(context, data)
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
        column_labels = self.definition['column_exps']
        column_types = []
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
            viz_id = hashlib.md5(self.id).hexdigest()
        except ImportError:
            import md5
            viz_id = md5.new(self.id).hexdigest()
        
        return 'analytics-' + viz_id

    def getVizOptions(self):
        """
        Return a javascript object containing the options for the visualization.
        """
        js_options = []
        for option, value in self.definition['viz_options'].items():
            js_options.append('%s: %s' % (option, self.getJSValue(value)))
        if js_options:
            return '{%s}' % (', '.join(js_options))
        return 'null'
        
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