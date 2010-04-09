try:
    from App.class_init import InitializeClass
except ImportError:
    from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from zope.interface import implements
from zope.component import queryMultiAdapter, getMultiAdapter
from zope.app.component.hooks import getSite
from zope.component import getGlobalSiteManager
from OFS.PropertyManager import PropertyManager
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.Expression import getEngine
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from plone.memoize.volatile import cache
from plone.memoize.instance import memoize, memoizedproperty
from collective.googleanalytics.interfaces.adapters import IAnalyticsExpressionVars
from collective.googleanalytics.interfaces.report import IAnalyticsReport, IAnalyticsReportRenderer
from collective.googleanalytics.interfaces.plugins import IAnalyticsPlugin
from collective.googleanalytics.utils import getJSValue, evaluateTALES, makeDate, makeGoogleVarName
from collective.googleanalytics.config import METRICS_CHOICES, \
    DIMENSIONS_CHOICES, VISUALIZATION_CHOICES

from string import Template

import datetime
import time
import os

import logging
logger = logging.getLogger("analytics")

# def report_results_cache_key(method, instance, profiles, options):
#     analytics_tool = instance.report.aq_parent
#     cache_interval = analytics_tool.cache_interval
#     cache_interval = (cache_interval > 0 and cache_interval * 60) or 1
#     time_key = time.time() // cache_interval
#     modification_time = str(instance.bobobase_modification_time())
#     cache_vars = [time_key, modification_time, profiles]
#     
#     for plugin in instance.getPlugins():
#         plugin.processCacheArguments(cache_vars)
#         
#     return hash(tuple(cache_vars))

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
        {'id':'categories', 'type': 'multiple selection', 'mode':'w',
         'label':'Categories', 'select_variable': 'getCategoriesChoices'},
        {'id':'plugin_names', 'type': 'multiple selection', 'mode':'w',
         'label':'Plugins', 'select_variable': 'getPluginNameChoices'},
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
        {'id':'max_results', 'type': 'string', 'mode':'w',
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
        self.start_date = kwargs.get('start_date', '')
        self.end_date = kwargs.get('end_date', '')
        self.introduction = kwargs.get('introduction', '')
        self.conclusion = kwargs.get('conclusion', '')
        self.max_results = kwargs.get('max_results', 'python:1000')
        self.plugin_names = kwargs.get('plugin_names', [])
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
        
    security.declarePrivate('getPluginInterfaceChoices')
    def getPluginNameChoices(self):
        """
        Return the list of plugin names.
        """
        
        gsm = getGlobalSiteManager()
        global_plugins = set([p.name for p in gsm.registeredAdapters() if p.provided == IAnalyticsPlugin])
        
        lsm = getSite().getSiteManager()
        local_plugins = set([p.name for p in lsm.registeredAdapters() if p.provided == IAnalyticsPlugin])
        
        return sorted(list(global_plugins | local_plugins))

InitializeClass(AnalyticsReport)

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
    
    __call__ = ViewPageTemplateFile('async.pt')
    
    @memoizedproperty
    def data_feed(self):
        """
        Returns a Google Analytics data feed.
        """
        
        analytics_tool = self.report.aq_parent
        query_args = self.query_arguments
        data_feed = analytics_tool.makeClientRequest('data', 'GetData', **query_args)
        logger.info("Querying Google for report '%s' on context '%s'." % 
            (self.report.id, self.context.id))

        return data_feed
    
    @memoizedproperty
    def plugins(self):
        """
        Returns the instantiated plugin adapters used by this report.
        """
        
        results = []
        for plugin_name in self.report.plugin_names:
            plugin = queryMultiAdapter(
                (self.context, self.request, self.report),
                interface=IAnalyticsPlugin,
                name=plugin_name,
                default=None,
            )
            if plugin:
                results.append(plugin)
        return results
        
    @memoizedproperty
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
        
        profile_ids = self.request.get('profile_ids')
        if type(profile_ids) is str:
              profile_ids = [profile_ids]
              
        criteria['ids'] = profile_ids
        
        for plugin in self.plugins:
            plugin.processQueryCriteria(criteria)
        
        return criteria
        
    @memoizedproperty
    def query_arguments(self):
        """
        Returns the query arguments in the format that Google expects.
        """

        criteria = self.query_criteria
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
        
    @memoizedproperty
    def data(self):
        """
        Iterate through the data returned by Google and calcualte the value of the
        report columns.
        """
        criteria = self.query_criteria
        data = self.data_feed
        
        column_vars = list(criteria['dimensions']) + list(criteria['metrics'])
        column_exps = self.report.column_exps
        rows = []
        for entry in data.entry:
            extra_context = {}
            for column in (entry.dimension or []) + (entry.metric or []):
                if column.name in column_vars:
                    value = column.value
                    if column.name == 'ga:date':
                        value = makeDate(column)
                    extra_context.update({makeGoogleVarName(column.name): value})
            exp_context = self._getExpressionContext(extra_context)
            row = evaluateTALES(column_exps, exp_context)
            rows.append(row)
        return rows
        
    @memoizedproperty
    def visualization(self):
        """
        Returns an AnalyticsReportVisualization for this report.
        """
        
        # Evaluate the visualization options.
        exp_context = self._getExpressionContext()
        options = evaluateTALES(dict([v.split(' ') for v in self.report.viz_options]), exp_context)
        column_labels = evaluateTALES(self.report.column_labels, exp_context)

        return AnalyticsReportVisualization(self.report, self.data, options, column_labels)
        
    @memoizedproperty
    def introduction(self):
        """
        Returns the rendered report introduction.
        """
        
        return self._renderTALField('introduction')
        
    @memoizedproperty
    def conclusion(self):
        """
        Returns the rendered report conclusion.
        """
        
        return self._renderTALField('conclusion')
        
    def _getExpressionContext(self, extra={}, tal=False):
        """
        Returns the context for rendering TALES or TAL. If the tal argument
        is true, a dictionary of variables is returned. Otherwise, an
        an expression context object is returned.
        """
        
        vars_provider = getMultiAdapter((self.context, self.request, self.report),interface=IAnalyticsExpressionVars)

        context_vars = vars_provider.getExpressionVars()
        context_vars.update(extra)

        for plugin in self.plugins:
            plugin.processExpressionContext(context_vars)

        if tal:
            return context_vars
        return getEngine().getContext(context_vars)

    def _renderTALField(self, field):
        """
        Renders and returns the result of the introduction or conclusion
        field.
        """

        tal_context = self._getExpressionContext(
            extra={
                'data_length': len(self.data),
                'data_rows': self.data, 
                'data_columns': zip(*self.data),
            },
            tal=True,
        )

        return self._evaluateTAL(getattr(self.report, field), tal_context)    
    
    def _evaluateTAL(self, tal, extra={}):
        """
        Evalutes HTML containing TAL.
        """

        pt = ZopePageTemplate(id='__collective_googleanalytics__')
        pt.pt_edit(tal, 'text/html')
        return pt.__of__(self.context).pt_render(extra_context=extra)

class AnalyticsReportVisualization(object):
    """
    The visualization for an Analytics report. This object is generated by the
    visualization method of the AnalyticsReportRenderer object. It encapsulates
    all of the logic for turning the report results in to javascript
    configuration for Google Visualizations.
    """

    def __init__(self, report, data, options, column_labels):
        self.report = report
        self.data = data
        self.options = options
        self.column_labels = column_labels
            
    @memoize
    def id(self):
        """
        Creates a unique ID that we can use for the div that will hold the
        visualization.
        """
        try:
            import hashlib
            viz_id = hashlib.md5(self.report.id + str(time.time())).hexdigest()
        except ImportError:
            import md5
            viz_id = md5.new(self.report.id + str(time.time())).hexdigest()

        return 'analytics-' + viz_id
    
    @memoize
    def javascript(self):
        """
        Returns the javascript to create the visualization.
        """

        js_template_file = os.path.join(os.path.dirname(__file__), 'visualization.js.tpl')
        js_template = Template(open(js_template_file).read())

        js_template_vars = {
            'package_name': self.report.viz_type.lower(), 
            'columns': self._getColumns(), 
            'data': self._getData(), 
            'chart_type': self.report.viz_type, 
            'id': self.id(),
            'options': self._getOptions()
        }

        return js_template.substitute(js_template_vars)

    @memoize
    def height(self):
        """
        Returns the height of the visualization if it is set, or False
        if it is not.
        """

        if 'height' in self.options.keys():
            return int(self.options['height'])
        return False

    @memoize
    def _getData(self):
        """
        Returns a javascript array that describes the data. It is used by Google
        Visualizations to populate the DataTable.
        """
        js_rows = []
        for row in self.data:
            js_row = []
            for value in row:
                js_row.append(getJSValue(value))
            js_rows.append('[%s]' % (', '.join(js_row)))
        return '[\n%s\n]' % (',\n'.join(js_rows))

    @memoize
    def _getColumns(self):
        """
        Returns javascript that adds the appropriate columns to the DataTable.
        """
        column_labels = self.column_labels
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

    @memoize
    def _getOptions(self):
        """
        Returns a javascript object containing the options for the visualization.
        """
        js_options = []
        for option, value in self.options.items():
            js_options.append('%s: %s' % (option, getJSValue(value)))
        # Set the width of the visualization to the container width if it
        # if not already set.
        if not 'width' in self.options.keys():
            js_options.append('width: container_width')
        if js_options:
            return '{%s}' % (', '.join(js_options))
        return 'null'