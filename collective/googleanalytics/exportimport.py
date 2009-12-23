from zope.component import adapts

from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import I18NURI
from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import NodeAdapterBase
from Products.GenericSetup.utils import ObjectManagerHelpers
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.GenericSetup.utils import XMLAdapterBase

from Products.CMFCore.utils import getToolByName

from collective.googleanalytics.interfaces.utility import IAnalytics
from collective.googleanalytics.interfaces.report import IAnalyticsReport


class AnalyticsReportNodeAdapter(NodeAdapterBase, PropertyManagerHelpers):
    """
    Node importer and exporter for Analytics Report.
    """

    adapts(IAnalyticsReport, ISetupEnviron)

    def _exportNode(self):
        """
        Export the report as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())
        return node

    def _importNode(self, node):
        """
        Import the report from the DOM node.
        """
        purge = self.environ.shouldPurge()
        if node.getAttribute('purge'):
            purge = self._convertToBoolean(node.getAttribute('purge'))
        if purge:
            self._purgeProperties()

        self._initProperties(node)

    node = property(_exportNode, _importNode)
    

class AnalyticsToolXMLAdapter(XMLAdapterBase, ObjectManagerHelpers):
    """
    XML importer and exporter for Analytics tool.
    """

    adapts(IAnalytics, ISetupEnviron)

    _LOGGER_ID = 'analytics'

    name = 'analytics'
    
    def _exportNode(self):
        """
        Export the Analytics tool as a DOM node.
        """
        node = self._getObjectNode('object')
        node.setAttribute('xmlns:i18n', I18NURI)
        node.appendChild(self._extractObjects())

        self._logger.info('Analytics tool exported.')
        return node

    def _importNode(self, node):
        """
        Import the Analytics tool from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeObjects()

        self._initObjects(node)

        self._logger.info('Analytics tool imported.')
        
def importAnalyticsReports(context):
    """
    Import Analytics tool.
    """
    site = context.getSite()
    tool = getToolByName(site, 'portal_analytics', None)
    if tool is None:
        return

    importObjects(tool, '', context)

def exportAnalyticsReports(context):
    """
    Export Analytics tool.
    """
    site = context.getSite()
    tool = getToolByName(site, 'portal_analytics', None)
    if tool is None:
        logger = context.getLogger('analytics')
        logger.info('Nothing to export.')
        return

    exportObjects(tool, '', context)