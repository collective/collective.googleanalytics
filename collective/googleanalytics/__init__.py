from Products.CMFCore import utils
from collective.googleanalytics.utility import Analytics
from collective.googleanalytics.report import AnalyticsReport

tools = (
    Analytics,
    )

def initialize(context):
    """
    Initializer called when used as a Zope 2 product.
    """

    utils.registerIcon(AnalyticsReport,
                       'browser/images/chart_bar.gif', globals())

    utils.ToolInit('Google Analytics Tool',
                   tools=tools,
                   icon='browser/images/chart_curve.gif',
                   ).initialize(context)
    

