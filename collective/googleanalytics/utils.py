from Products.CMFCore.Expression import Expression, getEngine
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zope.tales.tales import CompilerError
import datetime

def getTimeDelta(**kwargs):
    """
    Return a python timedelta for use in TALES expressions.
    """
    return datetime.timedelta(**kwargs)
    
def getDate(year, month, day):
    """
    Return a python date for use in TALES expressions.
    """
    return datetime.date(year, month, day)
    
def getExpressionContextDict(context):
    """
    Return the dictonary used to form the expression context.
    """
    
    request = context.REQUEST
    absolute_url = request.get('request_url', request.ACTUAL_URL)
    return {
        'context': context,
        'request': request,
        'today': datetime.date.today(),
        'date': getDate,
        'timedelta': getTimeDelta,
        'page_url': absolute_url.replace(request.SERVER_URL, ''),
    }

def getExpressionContext(context, extra={}):
    """
    Return the context for evaluating TALES expressions.
    """
    
    context_dict = getExpressionContextDict(context)
    context_dict.update(extra)
    return getEngine().getContext(context_dict)

def evaluateExpression(expression, exp_context):
    """
    Evalute a TALES expression using the given context.
    """
    try:
        return Expression(str(expression))(exp_context)
    except (KeyError, CompilerError):
        return expression

def evaluateList(parent, exp_context):
    """
    Evaluate each TALES expression in a list.
    """
    results = []
    if hasattr(parent, '__iter__'):
        for child in parent:
            results.append(evaluateList(child, exp_context))
        return results
    return evaluateExpression(parent, exp_context)
    
def evaluateTAL(tal, context, extra={}):
    """
    Evalute HTML containing TAL.
    """
    
    pt = ZopePageTemplate(id='__collective_googleanalytics__')
    pt.pt_edit(tal, 'text/html')
    return pt.__of__(context).pt_render(extra_context=extra)