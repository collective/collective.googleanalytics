from Products.CMFCore import utils as cmfutils
from collective.googleanalytics.utility import Analytics
from collective.googleanalytics.report import AnalyticsReport

tools = (
    Analytics,
    )

def initialize(context):
    """
    Initializer called when used as a Zope 2 product.
    """

    cmfutils.registerIcon(AnalyticsReport,
                       'browser/images/chart_bar.gif', globals())

    cmfutils.ToolInit('Google Analytics Tool',
                   tools=tools,
                   icon='browser/images/chart_curve.gif',
                   ).initialize(context)
    

