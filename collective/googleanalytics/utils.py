from Products.CMFCore.Expression import Expression
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

def evaluateTALES(parent, exp_context, evaluate_keys=False):
    """
    Evaluates each TALES expression in a list, set, tuple, dictionary
    or string.
    """
    
    if type(parent) in [list, set, tuple]:
        results = []
        for child in parent:
            results.append(evaluateTALES(child, exp_context))
        return type(parent)(results)
    if type(parent) is dict:
        results = {}
        for key, value in parent.items():
            if evaluate_keys:
                results[evaluateTALES(key, exp_context)] = evaluateTALES(value, exp_context)
            else:
                results[key] = evaluateTALES(value, exp_context)
        return results
    try:
        return Expression(str(parent))(exp_context)
    except (KeyError, CompilerError):
        return parent
    
def makeDate(date_stamp):
    """
    Given a date string returned by Google, return the corresponding python
    date object.
    """
    date_string = str(date_stamp)
    year = int(date_string[0:4])
    month = int(date_string[4:6])
    day = int(date_string[6:8])
    return datetime.date(year, month, day)
    
def makeGoogleVarName(google_name):
    """
    Determine if the given name is a Google dimension or metric.  If it is,
    return the corresponding variable name (i.e. replace the colon with an
    underscore). Otherwise, return the variable name as is.
    """
    
    if len(google_name) > 3 and google_name[:3] == 'ga:':
        return 'ga_' + google_name[3:]
    return google_name
    
def getJSValue(value):
    """
    Given a python value, return the corresponding javascript value.
    """
    # A date
    if isinstance(value, datetime.date):
        return 'new Date(%i, %i, %i)' % (value.year, value.month, value.day)
    # A boolean
    if isinstance(value, bool):
        return str(value).lower()
    # A string
    if isinstance(value, str):
        return '"%s"' % (value.replace('"', '\\"').replace("'", "\\'"))
    # A number
    return str(value)