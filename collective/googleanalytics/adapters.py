from zope.interface import implements
from DateTime import DateTime
from collective.googleanalytics.utils import getDate, getTimeDelta, unique_list
from collective.googleanalytics.interfaces.adapters import IAnalyticsExpressionVars, \
    IAnalyticsDateRangeChoices
import datetime

class AnalyticsBaseAdapter(object):
    """
    A base adapter for Analytics reports.
    """
    
    def __init__(self, context, request, report):
        self.context = context
        self.request = request
        self.report = report

class AnalyticsDefaultExpressionVars(AnalyticsBaseAdapter):
    """
    Adapter to provide the default variables for the TALES expression context.
    """
    
    implements(IAnalyticsExpressionVars)
        
    def getExpressionVars(self):
        """
        Returns a dictionary containing the expression variables.
        """
        
        return {
            'context': self.context,
            'request': self.request,
            'today': datetime.date.today(),
            'date': getDate,
            'timedelta': getTimeDelta,
            'unique_list': unique_list,
        }

class DefaultDateRangeChoices(AnalyticsBaseAdapter):
    """
    An adapter to list the possible date ranges for this report, request
    and content.
    """
    
    implements(IAnalyticsDateRangeChoices)
        
    def getChoices(self):
        """
        Returns the appropriate date range choices.
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

        if hasattr(self.context, 'Date') and self.context.Date() is not 'None':
            pub_dt = DateTime(self.context.Date())
            published_date = datetime.date(pub_dt.year(), pub_dt.month(), pub_dt.day())
            date_ranges.update({
                'published': [published_date, today],
            })

        return date_ranges