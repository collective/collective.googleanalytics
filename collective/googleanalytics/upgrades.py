from Products.CMFPlone.migrations.migration_util import loadMigrationProfile

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
    