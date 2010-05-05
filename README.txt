Introduction
============
collective.googleanalytics is a Plone product used to pull statistics from Google 
Analytics and display them in a Plone site. It defines Analytics reports
that are used to query Google and display the results using Google
Visualizations. Reports are Zope objects that can be imported and exported
using GenericSetup XML and modified on a site-by-site basis. The product 
currently provides a portlet that can display results of reports as well
as a control panel for setting credentials and configuring settings.

Installation
============
To install collective.googleanalytics, add it to the eggs section of your buildout.
If you are using Plone 3.2 or earlier, you also need to add a ZCML slug. Then
re-run buildout and restart Zope.

Configuration
=============
When you install the product from the Plone Add-ons control panel, a new
control panel called Google Analytics will be added to your Plone site.
In this control panel, you can set the e-mail address and password that
Plone will use to access Google Analytics. You can also configure the
amount of time, in minutes, that report results will be cached, reducing
the need to query Google. Sixty minutes is the default caching interval.

Basic Use
=========
After you have set your credentials in the control panel, you can begin using
Analytics reports. First navigate to the page where you would like to display
the report results. Where you place the portlet depends on your goals and the
type of reports you are displaying. Even if you place a portlet on a public 
page, the portlet will only be visible to users who have the "View Google 
Analytics Reports" permission, which, by default is assigned to Managers.

Next, place the portlet as you normally would, using the manage portlets page
and selecting Google Analytics from the list of available portlets. In the
portlet add form, you can set the title of the portlet, the profile the portlet
will use and the reports it will display. Note that the title of the portlet is
not the same as the title of the report, which is displayed inside the portlet.
The profile is the Google property where the statistics that you want to access
live. Which profiles you can select within the portlet depends on which
profiles the Analytics account you provide to Plone can access. If you do not
see any profiles in the dropdown menu, check to be sure that you have
correctly set your Analytics e-mail address and password in the Google
Analytics control panel.

You can select more than one report to display within a single portlet. Each
report performs its own query to Google, however, so including many reports
on a single page may cause a decrease in performance. To change the order of
the reports within a portlet, see the section on `Managing Reports`_ below.

Once you have set the portlet title and profile and selected one or more
reports, click save to add the portlet. When you navigate to the page where
you assigned the portlet, you should see the results of your report.

Managing Reports
================
collective.googleanalytics ships with twelve default reports:

Site-Wide Reports
-----------------
* Site Visits: Line Chart
* Top 5 Pages: Table
* Top 5 Sources: Table
* Site Page Views: Line Chart
* Time on Site: Line Chart
* Site Unique Visitors: Line Chart

Page-Specific Reports
---------------------
* Page Views: Sparkline
* Time on Page: Sparkline
* Top 10 Page Sources: Table
* Top 10 Keywords: Table
* Top 5 Previous Pages: Table
* Top 5 Next Pages: Table

Reports live in a Plone tool called portal_analytics. To view and modify
reports, navigate to the root of the site in the ZMI and click on the
portal_analytics utility. Since they are standard Zope objects, reports can
be copied, pasted, renamed, deleted, imported and exported using the Zope
buttons beneath the list of reports. They can also be moved up and down in
the list using the up, down, top and bottom buttons. The order of reports
in portal_analytics controls the order that they will appear in portlets
throughout the site.

The Report Rendering Process
============================

By default, Analytics reports are rendered asynchronously using jQuery. This 
improves site performance by allowing the body of page to render without
waiting for a response from Google Analytics. The basic flow of a request
that renders an Analytics report might go as follows:

1. A user requests the content item front-page, which has a Google Analytics
   portlet assigned in the right column.
   
2. Plone renders front-page as usual. When it renders the Google Analytics
   portlet, it looks up a loader component.
   
3. Instead of requesting the actual results, the loader produces javascript
   that will load the results after the page has finished loading. It also
   produces javascript to load the visualization modules that the reports
   will require.
   
4. The javascript from the loader is included with front-page when it is
   rendered. As soon as the page has finished loading, the javascript produced
   by the loader is activated. It sends another request to the server that
   includes the requested reports and any options for evaluating them.
   
5. A browser view associated with the loader is called as part of the
   asynchronous request. (The context for this browser view is still
   front-page.) This browser view loads the specified reports.
   
6. For each report in the request, the browser view looks up a renderer,
   which is a multi-adapter on the current context (front-page), request 
   (the asynchronous request) and the report.
   
7. The renderer renders the report or returns a cached result if one exists.
   The browser view combines the results from all of the requested reports and
   returns them.
   
8. The results returned by the renderer are injected into the portlet. In the
   process, jQuery evaluates any javascript in the results, including the
   javascript that produces the visualization.

Report Properties
=================
Analytics reports are persistent Zope objects that store the arguments used to
query Google and the options needed to display the query result as a Google
Visualization. They store this information as properties on themselves. These
properties can be set using GenericSetup XML or through the web in the ZMI.

It may be helpful to think of Analytics reports as having five logical
sections, each of which has its own properties:

* `Report settings`_
* `Query criteria`_
* `Table builder`_
* `Visualization settings`_
* `Report body`_

Report settings
---------------

The report settings section consists of five properties that control the
display and behavior of the report. None of these properties accept
TAL or TALES.

Title
	The title of the report in the management interface. This is the title that
	that the user selects when assigning a portlet.

Description
	A brief description of the report. The description is mainly for developer
	reference and never appears in the Plone user interface.

I18n Domain
	The domain for translating the report.
	
Categories
    A list of categories to which the report belongs. Categories are used to
    determine where the report can be displayed.
    
Plugins
    Plugins are multi-adapters on the context, the request and the report
    that extend the default functionality of the report. Two plugins ship
    with collective.googleanalytics. See the sections on `Contextual Results
    Plugin`_ and `Variable Date Range Plugin`_ for more details.
    
    Note that some plugins add additional dimension, metric and visualization
    choices, which are not available until the report is saved. As a result,
    it is generally a good idea to save the report immediately after adding
    or removing any plugin.
	
Query criteria
--------------
	
The query criteria section of the report is made up of all the properties
that begin with the word query. These properties determine the query that is
sent to Google to retrieve Analytics data. All of these properties accept
TALES expressions. They have access to the TALES variables defined in the
section on `Using TAL and TALES in Reports`_ as well as any TALES objects
provided by the selected plugins.
	
Query Metrics
	A list of Google Analytics metrics to use in the query.
	
Query Dimensions
	A list of Google Analytics dimensions to return in the query. This list can
	include the special dimension variables date_range_dimension and
	date_range_sort_dimension. For more information on using these dimension,
	see the section on the `Variable Date Range Plugin`_.

Query Filters
	A list of filters to use in the query. Filters are defined as strings or
	TALES expressions that evaluate to strings in the format METRIC==VALUE,
	where METRIC is the name of a Google Analytics metric or dimension,
	VALUE is the desired value, and == is the appropriate logical operator.
	
Query Sort
	A list of metrics or dimensions on which to sort the query results. Sort
	parameters are defined using strings or TALES expressions that evaluate to
	strings containing the name of a Google Analytics dimension or metric. In
	addition, the name of the dimension or metric can be preceded by a minus
	sign (-) to change the sort order from ascending to descending.
	
Query Start Date
    The start date for query results. It must be a TALES expression that
    evaluates to a Python datetime.date object. In reports that use the
    `Variable Date Range Plugin`_, it is not necessary to specify the
    start date or end date.
    
Query End Date
    The end date for the query results. See Query Start Date above for more
    information.
	
Query Maximum Results
	The maximum number of results that the query can return. It must be a TALES
	expression that evaluates to a positive integer.

Table builder
-------------

The table builder section of the report includes three properties. Together
these properties are responsible for taking the query results returned by
Google and transforming them into a results table that can be used in as the
data source for a visualization or otherwise displayed in the report body.

In order to perform this transformation, these three properties use TALES
expressions that return Python lists. The TALES expressions have access to
three special functions that allow them to extract data from the data feed
returned by Google:

dimension(dimension, specified={}, aggregate=unique_list, default=[])
    Returns the value of the given dimension across the specified
    dimensions and metrics using the specified aggregation method
    (unique_list by default). If no values are found, the default value,
    an empty list by default, is returned.

    For example, the following TALES expression would return a list of all
    the browsers returned by the query::

        python:dimension('ga:browser')
            
metric(metric, specified={}, aggregate=sum, default=0)
    Returns the value of the given metric across the specified
    dimensions and metrics using the specified aggregation method (sum by
    default). If no values are found, the default value, 0 by default, is
    returned.

    To get the sum of the values of 'ga:visits' in records where
    'ga:browser' equals 'Mozilla,' we could use this expression::

        python:metric('ga:visits', {'ga:browser': 'Mozilla'})
    
    In reports that use the `Variable Date Range Plugin`_, the value
    of the specified argument is often set to an element in the list
    returned by the possible_dates method.

possible_dates(dimensions=[], aggregate=unique_list)
    Returns a list of dictionaries containing all possible values for
    the given date dimension in the current date range. If no dimensions
    are specified, all of the date dimensions in the query are used.

    This method is commonly used in place of the dimension method in
    reports that include date dimensions to ensure that the table contains
    one row for each date unit in the date range.
    
These three properties make up the table builder section of the report:

Table Columns Expression
	The titles for the table columns. It must be a TALES expression that evaluates
	to a Python list of strings. If and where these titles appear depends on
	the type of visualization. For the Table visualization, for example, they
	appear as the table column headings.
	
	In most reports, the table columns expression is a static Python list::
	    
	    python:['Visits']
	    
	It is, of course, possible to use TALES variables to populate the
	columns list::
	
	    python:[date_range_unit, 'Visits']
	    
	In complex tables, the number of columns may be determined by the results
	returned by the query. In this example, the first column is "Date" and the
	names of the remaining columns are the names of the browsers returned
	by the query::
	
	    python:['Date'] + dimension('ga:browser')
	
Table Row Repeat Expression
    The expression that produces the set of row keys used generate the rows in
    the results table. It is specified as a TALES expression that evaluates to
    a Python iterable with one element for each row in the final table.
    
    When the report renderer is asked for the results table rows, it first
    evaluates the row repeat expression. It then iterates over each element
    in the resulting list and evaluates the table rows expression with
    the current element assigned to the variable "row."
    
    Typically the values of the row repeat expression are generated using the
    dimension function or the possible_dates function::
    
        python:dimension('ga:pagePath')
        
    or::
    
        possible_dates
    
    See the section on `Using TAL and TALES in Reports`_ for more information
    about the use of these functions.
	
Table Rows Expression
    The contents of each table row. It is must be a TALES expression that
    evaluates to a Python list containing the value of the "cells" for that
    table row. The table rows expression has access to two special TALES
    varables:
    
    row
        The value of the row key for the row that is currently being evaluated.
        These values come from the list produced by evaluating the table row
        repeat expression.
        
    columns
        The list of table column headings produced by evaluating the table
        columns expression.
        
    In tables with only one column, the value of the rows expression is
    often the same as the value of the row key::
    
        python:[row]
        
    In two column tables, the value of one column is typically the row key,
    and the other is a metric value looked up using the row key::
    
        python:[row, metric('ga:visits', {'ga:browser': row})]
        
    In complex, multi-column tables, it may be necessary to iterate over the
    columns variable using a Python list comprehension::
    
        python:[row] + [metric('ga:visits', {'ga:browser': row, 'ga:operatingSystem': c}) for c in columns[1:]]

Visualization settings
----------------------

The visualizaiton settings section of the report consists of the
visualization type and visualization options properties. These properties
are used to create javascript that uses the Google Visualizations API
to render the data table produced by the table builder section above.

Visualization Type
	The type of Google Visualization to use to display the report results.
	This property can be set to the name of any of the default visualizations
	provided by Google.

Visualization Options
	A list of options and values, in the format of TAL defines, that specify
	the options for the visualization. The available options depend on the
	type of visualization selected. It is important that the option expressions
	evaluate to the data type that the visualization expects.

	For example, the height of a visualization that accepts an integer height
	option could be set as follows::

		height python:300

Report body
-----------

The report body consists of a single property that contains the TAL template
for the report. This block of TAL code is evaluated when the report is
rendered. TALES expressions within this code have access to the normal objects
described in the section on `Using TAL and TALES in Reports`_. They also
can access all of the public methods provided by the report renderer. In the
report body, these methods must be accessed using view/method_name or
python:view.method_name():

profile_ids()
    Returns a list of Google Analytics profiles for which the report
    is being evaluated.

query_criteria()
    Returns the evaluated query criteria.

data()
    Returns a list of dictionaries containing the values of the
    dimensions and metrics for each entry in the data feed returned
    by Google.

columns()
    Returns the evaluated table column headings.

rows()
    Returns the evaluated table rows.
    
visualization()
    Returns the rendered visualization.

dimension(dimension, specified={}, aggregate=unique_list, default=[])
    Returns the value of the given metric across the specified
    dimensions and metrics using the specified aggregation method. See
    the description in the `Table builder`_ section above.
                
metric(metric, specified={}, aggregate=sum, default=0)
    Returns the value of the given metric across the specified
    dimensions and metrics using the specified aggregation method. See
    the description in the `Table builder`_ section above.
    
possible_dates(dimensions=[], aggregate=unique_list)
    Returns a list of dictionaries containing all possible values for
    the given date dimension in the current date range. See the description
    in the `Table builder`_ section above.
    
Using TAL and TALES in Reports
==============================

Many of the properties of the Analytics report object accept TALES expressions
or TAL as their values. (For information about which properties accept TALES
and TAL, see the section on `Report Properties`_ above.) All of the TAL code
and TALES expressions have access to a standard set of Python objects and
variables:

context
	The object on which the current view is being called. In most cases, this
	is the content object next to which the report will be displayed.
	
request
	The current request object. Since Analytics reports are rendered
	asynchronously, this request object is the asynchronous report request,
	not the user's original request. The URL of the original request can be
	obtained by using request/request_url.

date
	An alias for the datetime.date function.
	
timedelta
	An alias for the datetime.timedelta function.
	
unique_list
    A helper function that takes a Python list and returns a corresponding
    list where all duplicated elements in the original list have been removed.
    It differs from the Python set type in that it preserves the order of the
    original list.

Contextual Results Plugin
=========================

This plugin provides tools to make reports page specific. It modifies the
default caching policy to cache report results on a per-page basis instead
of for the entire site. It also provides several helper TALES variables that
simplify the process of creating page-specific reports:

page_url
	The relative URL of the current request. This is most commonly used in
	the query filters property for creating page-specific reports.
	
page_filter
    A Google Analytics filter expression that matches records where the
    ga:pagePath record matches the current relative URL. It uses regular
    expression matching to match both URLs with and without the trailing
    slash.

nextpage_filter
    A Google Analytics filter expression that matches records where the
    ga:nextPagePath record matches the current relative URL. It uses regular
    expression matching to match both URLs with and without the trailing
    slash.

previouspage_filter
    A Google Analytics filter expression that matches records where the
    ga:previousPagePath record matches the current relative URL. It uses regular
    expression matching to match both URLs with and without the trailing
    slash.

Variable Date Range Plugin
==========================

Analytics reports can specify fixed start and end dates for their queries.
It is generally more useful, however, to allow the date range to be set when
the report is evaluated. The Variable Date Range Plugin provides this
functionality. In order to set the date range, it looks in the request for
one of these special keys:

start_date and end_date
    Dates in the form of YYYYMMDD.

date_range
    An integer specifying the number of days prior to the current date to use
    as the report start date. The end date is assumed to be the current date.
    The date_range argument can also accept a string keyword that evaluates 
    to a particular date range depending on the current context. Current 
    keywords include:

    week
        Last seven days.

    month
        Last 30 days.

    quarter
        Last 90 days.

    year
        Last 356 days.

    mtd
        Month-to-date.

    ytd
        Year-to-date.

    published
        Since the item was published.

Since Analytics reports are rendered asynchronously, these keys must be set
in the request sent by the asynchronous loader, not in the original request.

Since dates for reports are dynamic, the plugin also provides two special
dimensions that are date sensitive. This allows the granularity of the report
results to be set based on the date range selected. (For example, if you specify
a date range of a year, you probably don't want to segment your results by day.
Instead, viewing results by month would be a more appropriate choice.) The two 
special dimensions are:

date_range_dimension
    This is the dimension, selected based on the date range, that will be used
    to segment the results.

date_range_sort_dimension
    This is the date-related dimension that is used as a helper to ensure that
    results segmented by date_range_dimension can be sorted chronologically.
    For example, if date_range_dimension evaluates to ga:week,
    date_rage_sort_dimension would evalute to ga:year. Using
    date_range_sort_dimension (along with date_range_dimension) when sorting
    prevents a situation in which week 52 of 2009 gets sorted before week 1
    of 2010.

Note that that these two dimensions must be selected from the list of query
dimensions to be included in the query. If they are not available in the list
of possible dimensions, be sure to save the report after selecting the Variable
Date Range Plugin from the list of plugins.

The plugin also provides two helper variables that are useful in report
templates:

date_range_unit
    A string containing the human-readable name of the dimension specified
    by date_range_dimension (e.g. 'Day', 'Month', etc.)

date_range_unit_plural
    A convenience variable that contains date_range_unit with the letter
    's' appended.

Creating a New Report
=====================

Now that you are familiar with the properties that make up an Analytics report,
it's time to try creating a new report from scratch. In this example, we will
create a report that calculates and displays the site-wide bounce rate
over a period of time segmented by browser.

This example presents a fairly complex report. For examples of simpler reports,
consult the default reports in portal_analytics. In many cases, you can
probably modify one of these reports to suit your needs by substituting
dimensions and metrics. If, however, you find that you need to create a more
complicated multi-dimensional report, read on:

1. Navigate to the root of the site in the ZMI and click on the
   portal_analytics tool.

2. Click the Add Google Analytics Report button.

3. We'll give our new report the ID site-bounce-rate-browser-line,
   following the naming convention of the default reports. This naming 
   convention is optional, but it helps to keep things organized. Then 
   click the add button.

4. Click on the new report to edit it. Give it a title of Site Bounce Rate
   By Browser: Line Chart and this description:

   This report displays the site-wide bounce rate segmented by the user's 
   browser. It is useful for gauging how effective our site's new multimedia
   features are in each browser.

5. Leave the i18n domain as collective.googleanalytics, the default value. If we
   were going to translate this report, we might use the domain defined in our
   site's theme product.

6. From the list of categories, select Site Wide.

7. From the list of plugins, select Variable Date Range. After making your
   selection, click the Save button to populate the list of dimensions with
   the new options.

8. Now the difficult part: determining the arguments for our query. If we
   consult the common calculations page in the Google's Dimensions and Metrics
   Reference (see the section on `Where to Learn More`_ for the link), we see
   that bounce rate is calculated as follows::

		ga:bounces/ga:entrances
		
   So, set the query metrics to ga:bounces and ga:entrances.

9. We also know that we want to segment our results by browser, so we'll set
   our query dimension to ga:browser. Be sure to also select
   date_range_dimension and date_range_sort_dimension from the bottom
   of the dimensions list.

10. In the query filters enter::

        ga:entrances>10

    Strictly speaking, we wouldn't need this filter. But for a site with a lot
    of traffic, we probably don't care about the results browsers for that
    have fewer than 10 entrances in a given period of time. So, we use this
    filter to eliminate them from the results.

11. In the query sort box, enter the dimensions provided by the Variable Date
    Range Plugin::
    
        date_range_dimension
        date_range_sort_dimension
    
12. In query maximum results, leave the default value, python:1000.

13. Now that our query arguments are complete, we can work on our results
    table. Let's begin by drawing out what our table should look like:
    
    +-------+-----------+---------------------+----------+----------+
    | "Day" | "Firefox" | "Internet Explorer" | "Safari" | "Chrome" |
    +=======+===========+=====================+==========+==========+
    |   "5" |        60 |                  70 |       54 |       63 |
    +-------+-----------+---------------------+----------+----------+
    |   "6" |        64 |                  69 |       59 |       68 |
    +-------+-----------+---------------------+----------+----------+
    |   "7" |        63 |                  72 |       65 |       68 |
    +-------+-----------+---------------------+----------+----------+
    | Etc.                                                          |
    +-------+-----------+---------------------+----------+----------+
    
    Note that the day column contains strings, not integers. This is necessary
    so that the line chart visualization will treat these values as labels
    instead of data.
	
14. Great! Now we can write the expressions to generate the table. Enter this
    expression in the table columns expression field::
    
        python:[date_range_unit] + dimension('ga:browser')
        
    This expression combines the value of the date_range_unit, which is
    provided by the Variable Date Range Plugin, with all of the possible
    values of the ga:browser dimension.
    
15. For the table row repeat expression, enter::

        possible_dates    
    
    This expression will populate the row keys with dictionaries that contain
    the values of date_range_dimension and date_range_sort_dimension. We use
    possible_dates instead of dimension(date_range_dimension) because we want
    one entry for every period of time in the current date range, even if there
    aren't any results for that particular period of time.
    
16: In the table rows expression field, enter the following expression,
    removing the line breaks::
    
        python:[str(row[date_range_dimension])] + 
        [int(100*float(metric('ga:bounces', row))/(float(metric('ga:entrances', row)) + 0.0001))
            for c in columns[1:] if not row.update({'ga:browser': c})]
        
    Whoa! That looks complicated! If we break down the expression into its
    parts, however, it's easy to see what's going on::
    
        [str(row[date_range_dimension])]
        
    This part of the expression creates a list with a single element: the value
    of date_range_dimension as a string. Recall that, in this expression, row
    is a dictionary that contains key-value pairs for date_range_expression
    and date_range_sort_expression.
    
    Now let's skip to the end of the expression::
    
        for c in columns[1:]
        
    This code serves as the repeat expression in a Python list comprehension
    that generates the bounce rate for each browser for the specified date.
    columns[1:] represents the list of browser names generated by
    dimension('ga:browser')::
    
        if not row.update({'ga:browser': c})
        
    This tricky bit of code updates the row dictionary to include the value of
    the current browser as it iterates over the list of browsers. That way we
    can pass row to the metric() method to get value of the metric for the
    date and browser we are currently evaluating. We use 'if not' because
    the update method returns None, which evaluates to False.

    Finally, the rest of the expression is just the math used to calculate
    the bounce rate::
    
        int(100*float(metric('ga:bounces', row))/(float(metric('ga:entrances', row)) + 0.0001))
        
    We have to convert the values we get back from metric() into floating point
    numbers so that the division operates as we expect. We also add a tiny
    number to the denominator to avoid getting a divide by zero error if the
    value of ga:entrances is zero. Finally, we multiply the result by 100 to
    get a percentage and round the result to the nearest integer.

17. We're almost done! From the visualization type drop down menu, choose
    LineChart.
	
18. In the visualization options box, enter these option definitions, one
    per line::
    
        title string:Bounce Rate By Browser
        height python:250
        titleX python:date_range_unit
        titleY string:Bounce Rate (%)
        smoothLine python:True
		
    These options are all aesthetic. Once you become familiar with Google
    visualizations, you can adjust them to fit your personal preferences. For
    a full list of the options available for each visualization, visit the
    Google Visualization Gallery referenced in the section on `Where to Learn
    More`_.
	
19. In the report body field, enter this block of TAL code, which renders the
    line chart visualization::

        <div tal:replace="structure view/visualization"></div>
	
18. You're done! Click the save button in the ZMI. Then test out your new
    report on the site as described in the section about `Basic Use`_.

Defining Reports in a Filesystem Product
========================================

Any product that imports a GenericSetup profile can define Analytics reports.
These reports should be defined in a file called analytics.xml in the
product's GenericSetup profile directory. The easiest way to generate the XML
for a report is to create the report through the web and then export it. 

For example, after following the instructions above for creating a new report,
you could use the portal_setup tool in the ZMI to create a snapshot of the
site. Then you could navigate to the analytics.xml file in the snapshot and
copy and paste the appropriate XML into your product's analytics.xml file.

If you find that you need to write the GenericSetup XML for a report by hand,
consult the analytics.xml file in this product's profiles/default directory
for guidance. Keep in mind that any XML or XML reserved characters must be
properly escaped.

Where to Learn More
===================

Creating and managing Analytics reports requires knowledge of the Google
Analytics API, the Google Visualizations API, and Zope and Plone technologies
such as TAL and TALES.  These are resources that you may find helpful in
learning these technologies:

Google Analytics API
--------------------

* `Google Analytics Data Export API Documentation`__

  __ http://code.google.com/apis/analytics/docs/gdata/gdataDeveloperGuide.html

  This is the best place to start for learning the ins and outs of Google
  Analytics. Of particular interest are these pages:

  - `Data Feed Reference`__

    __ http://code.google.com/apis/analytics/docs/gdata/gdataReferenceDataFeed.html

    This reference describes the arguments used to query Google.

  - `Data Feed Query Explorer`__

    __ http://code.google.com/apis/analytics/docs/gdata/gdataExplorer.html

    This tool allows you to try out queries interactively, which can be
    extremely helpful in the process of creating and debugging reports.

  - `Dimensions and Metrics Reference`__

    __ http://code.google.com/apis/analytics/docs/gdata/gdataReferenceDimensionsMetrics.html

    This page describes each available dimension and metric. Also see the
    subpages on valid combinations and common calculations.

* gdata API Reference

  gdata is the Python module that interacts with the Google API. This
  documentation is most useful for developers who wish to contribute to or
  extend collective.googleanalytics. The relevant documentation is divided into 
  two sections:

  - `gdata.analtyics.service Reference`__

    __ http://gdata-python-client.googlecode.com/svn/trunk/pydocs/gdata.analytics.service.html

    This documentation describes the API for the analytics service objects
    that gdata provides. collective.googleanalytics uses both the AccountsService and
    the AnalyticsDataService.

  - `gdata.analytics Reference`__

    __ http://gdata-python-client.googlecode.com/svn/trunk/pydocs/gdata.analytics.html

    This reference documents the response objects returned by a query to Google
    Analytics.

Google Visualizations API
-------------------------

* `Google Visualizations API Documentation`__

  __ http://code.google.com/apis/visualization/documentation/index.html

  The visualizations API documentation provides an overview of what Google
  Visualizations are and how they work.

* `Google Visualizations Gallery`__

  __ http://code.google.com/apis/visualization/documentation/gallery.html

  This gallery provides examples of each type of visualization and documents
  the options the options that each accepts.

TAL and TALES
-------------

* `Using Zope Page Templates`__

  __ http://docs.zope.org/zope2/zope2book/ZPT.html

  This chapter from the Zope2 Book offers and introduction to TAL, TALES
  and related technologies.

* `Advanced Page Templates`__

  __ http://docs.zope.org/zope2/zope2book/AdvZPT.html

  This chapter from the Zope2 Book describes some of the more advanced
  features of the TAL specification.

* `Zope Page Template Reference`__

  __ http://docs.zope.org/zope2/zope2book/AppendixC.html
  
  This appendix from the Zope2 Book provides a comprehensive overview of
  TAL and TALES as they are used in Zope page templates.

Credits
=======

Development
-----------

* `Matt Yoder <mattyoder@groundwire.org>`_

Code Review
-----------

* `David Glick <davidglick@groundwire.org>`_

Other
-----

* Thanks to FamFamFam for the graph icons, which are part of the Silk_ set.

.. _Silk: http://www.famfamfam.com/lab/icons/silk/


