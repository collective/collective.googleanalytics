from Products.GenericSetup.browser.utils import AddWithPresettingsViewBase

from collective.googleanalytics.report import AnalyticsReport

class AnalyticsReportAddView(AddWithPresettingsViewBase):
    """
    Add view for AnalyticsReport
    """

    klass = AnalyticsReport

    description = \
            u'An Analytics Report pulls information from Google Analytics.'

    def getProfileInfos(self):
        return []

    def _initSettings(self, obj, profile_id, obj_path):
        pass