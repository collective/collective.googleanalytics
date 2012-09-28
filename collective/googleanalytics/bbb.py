# BBB
try:
    from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
    from zope.component.hooks import getSite
    from zope.browser.interfaces import IAdding
except:
    from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
    from zope.app.component.hooks import getSite
    from zope.app.container.interfaces import IAdding
