from Products.CMFCore import utils as cmfutils
from Products.CMFCore.permissions import setDefaultRoles
from collective.googleanalytics.utility import Analytics
from collective.googleanalytics.report import AnalyticsReport
import gdata.gauth
from zope.i18nmessageid import MessageFactory
GoogleAnalyticsMessageFactory = MessageFactory('collective.googleanalytics')

# patch gdata scopes
gdata.gauth.AUTH_SCOPES['analytics'] += ('https://www.googleapis.com/auth/analytics.readonly',)


tools = (
    Analytics,
    )

setDefaultRoles( 'Google Analytics: View Analytics Results', 
                ( 'Site Administrator', ) )
setDefaultRoles( 'Google Analytics: Manage Analytics Reports', 
                ( 'Site Administrator', ) )

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
    

