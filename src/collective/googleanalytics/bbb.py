# BBB  # flake8: noqa
try:
    from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
except:
    from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
try:
    from zope.component.hooks import getSite
except:
    from zope.app.component.hooks import getSite
try:
    from zope.browser.interfaces import IAdding
except:
    from zope.app.container.interfaces import IAdding
