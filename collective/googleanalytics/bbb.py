# BBB
try:  # XXX OK to combine these?
    from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
    from zope.component.hooks import getSite
except:
    from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
    from zope.app.component.hooks import getSite
