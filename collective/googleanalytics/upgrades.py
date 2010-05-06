from Products.CMFCore.utils import getToolByName

def null_upgrade_step(setup_tool):
    """
    This is a null upgrade, use it when nothing happens
    """
    pass

def upgrade_10a2_to_10a3(setup_tool):
    """
    Remove external javascript from the registry and use a viewlet instead.
    Import new reports.
    """
    
    name = 'profile-collective.googleanalytics:upgrade_10a2_10a3'
    setup_tool.runAllImportStepsFromProfile(name)
    
def upgrade_10a4_to_10b1(setup_tool):
    """
    Update reports to use new attributes and reimport default reports.
    """

    analytics_tool = getToolByName(setup_tool, 'portal_analytics')
    reports = analytics_tool.getReports()
    
    BODY_TEMPLATE = """<!--
    %s
    <div tal:replace="structure view/visualization"></div>
    %s
    -->
    This report needs to be updated to use the new table building fields
    introduced in collective.googleanalytics 1.0b1.
    """
    
    COLUMNS_TEMPLATE = """<!--
    COLUMN LABELS:
    %s
    
    COLUMN EXPRESSIONS:
    %s
    -->
    """
    
    def map_filter(old_filter):
        """
        Maps an old filter expression to a new one.
        """
                
        if old_filter == 'string:ga:pagePath==${page_url}':
            return 'page_filter'
        if old_filter == 'string:ga:nextPagePath==${page_url}':
            return 'nextpage_filter'
        if old_filter == 'string:ga:previousPagePath==${page_url}':
            return 'previouspage_filter'
        return old_filter

    for report in reports:
        if not hasattr(report, 'plugin_names'):
            report.plugin_names = []
            
            if hasattr(report, 'is_page_specific') and report.is_page_specific:
                report.plugin_names.append(u'Contextual Results')
                
            if hasattr(report, 'is_page_specific'):
                del report.is_page_specific
        
            report.plugin_names.append(u'Variable Date Range')
            
        if hasattr(report, 'filters'):
            report.filters = [map_filter(f) for f in report.filters]
        
        if not hasattr(report, 'start_date'):
            report.start_date = u''
            
        if not hasattr(report, 'end_date'):
            report.end_date = u''
        
        if type(report.max_results) is int:
            report.max_results = u'python:%i' % report.max_results
        
        if hasattr(report, 'introduction') and hasattr(report, 'conclusion'):
            report.body = BODY_TEMPLATE % (
                report.introduction,
                report.conclusion,
            )
        
            del report.introduction
            del report.conclusion
            
        if hasattr(report, 'column_labels') and hasattr(report, 'column_exps'):
            report.columns = report.row_repeat = report.rows = ''
            
            report.body += COLUMNS_TEMPLATE % (
                report.column_labels,
                report.column_exps,
            )

            del report.column_labels
            del report.column_exps
            
        if report.i18n_domain == 'analytics':
            report.i18n_domain = 'collective.googleanalytics'

    profile_id = 'profile-collective.googleanalytics:upgrade_10a4_10b1'
    step_id = 'analytics'
    setup_tool.runImportStepFromProfile(profile_id, step_id)
