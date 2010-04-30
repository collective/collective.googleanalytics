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

def json_serialize(parent):
    """
    Given a Python list, tuple or dictionary, return the corresponding
    json object.
    """
    json_parts = []
    if type(parent) in [list, tuple]:
        for child in parent:
            json_parts.append(json_serialize(child))
        return '[%s]' % ', '.join(json_parts)
    if type(parent) is dict:
        for (key, value) in parent.items():
            json_parts.append('%s: %s' % (json_serialize(key), json_serialize(value)))
        return '{%s}' % ', '.join(json_parts)
    return js_value(parent)

class js_literal(str):
    """
    Marks a Python string object as a literal so that it is not enclosed
    in quotes when it is passed through js_value.
    """

def js_value(value):
    """
    Given a python value, return the corresponding javascript value.
    """
    
    # A javascript literal
    if isinstance(value, js_literal):
        return str(value)
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
    
def extract_value(column):
    """
    Returns a tuple containing the diimension or metric name and value value
    for an entry from a Google Analytics data feed.
    """
    
    value = column.value
    if column.name == 'ga:date':
        value = makeDate(column)
    elif column.name in ['ga:day', 'ga:week', 'ga:month', 'ga:year']:
        value = int(value)
    elif column.type == 'integer':
        value = int(value)
    elif column.type in ['float', 'percent', 'time', 'currency', 'us_currency']:
        value = float(value)
    return (column.name, value)
    
def unique_list(original):
    """
    Returns a list of unique items while preserving the order of the
    original list.
    """
    
    used = set()
    return [x for x in original if x not in used and not used.add(x)]
    