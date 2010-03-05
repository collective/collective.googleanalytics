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
type of report you are displaying. For site-wide reports, your user dashboard
may be the most appropriate place. For reports that monitor a specific page
or section of the site, it may makes sense to place the portlet on the page
that it references. Even if you place a portlet on a public page, the portlet
will only be visible to users who have the "View Google Analytics Reports"
permission, which, by default is assigned to Managers.

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

Report Properties
=================
Analytics reports are persistent Zope objects that store the arguments used to
query Google and the options needed to display the query result as a Google
Visualization. They store this information as properties on themselves. These
properties can be set using GenericSetup XML or through the web in the ZMI.

These are the properties that the report object defines:

Title
	The title of the report in the management interface. This is the title that
	that the user selects when assigning a portlet.

Description
	A brief description of the report. The description is mainly for developer
	reference and never appears in the Plone user interface.

I18n Domain
	The domain for translating the report.
	
Page Specific
	A boolean value for whether the report results change based on the page
	where the report is displayed. This value is used to determine whether
	the report results should be cached for the entire site or on a 
	page-by-page basis.
	
Query Metrics
	A list of Google Analytics metrics to use in the query.
	
Query Dimensions
	A list of Google Analytics dimensions to return in the query. This list can
	include the special dimension variables date_range_dimension and
	date_range_sort_dimension. For more information on using these dimension,
	see the section on `Using TAL and TALES in Reports`_.

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
	
Query Maximum Results
	The maximum number of records that the query should return. It must be
	a positive integer, and 1000 is the default value.
	
Report Column Labels
	The labels for the report columns. These are defined using strings or TALES
	expressions that evaluate to strings. Where they appear depends on type of
	visualization. For the Table visualization, for example, they appear as the
	table column headings.
	
Report Column Expressions
	A list of TALES expressions used to calculate the values of the report based
	on the data returned by Google. After the query is performed, the report
	iterates over the rows of data returned and calculates the value of each
	column. Naturally the values available in these calculations depend on the
	dimensions and metrics found in the query. Each dimension and metric is
	converted to a variable name by replacing the colon with an underscore.
	For example, the value of ga:uniquePageviews is stored in the variable
	ga_uniquePageviews.
	
	When writing column expressions, it is important to convert value of the
	variable to the appropriate type before attempting to perform calculations.
	Google returns all data, including numbers, as strings, so expressions must
	use the appropriate Python functions (int(), bool(), etc.) to convert to
	the correct type. Similarly, the result of the expression must be returned
	as the type that the selected visualization expects.
	
Report Introduction
	A block of TAL code that precedes the visualization containing the report
	results. TALES expressions within this code have access to the normal
	objects described in the section on `Using TAL and TALES in Reports`_. They
	also get two special Python lists called data_rows and data_columns.
	data_rows contains lists of the the evaluated column expression for each
	row of query data. data_columns is a convenience list that reformats the
	data in data_rows by column instead of row.
	
	As an example, take a report that defines these columns::
	
		python:str(ga_city)
		python:int(ga_visits)
	
	data_rows and data_columns might evaluate to the following python lists::
	
		data_rows = [
			['Seattle', 50],
			['Portland', 25],
			['San Francisco', 15]
		]
		data_columns = [
			['Seattle', 'Portland', 'San Francisco'],
			[50, 25, 15]
		]
	
	If you wanted to display the total number of visits in the title, you could
	includes this TAL in the report introduction::
	
		<h3>
			<span tal:replace="python:sum(data_columns[0])">
				[Total visits]
			</span>
			Visits
		</h3>
	
Report Conclusion
	A block of TAL code that follows the visualization containing the report
	results. See Report Introduction above for instructions on writing the
	TAL for this property.

Visualization Type
	The type of Google Visualization to use to display the report results.
	This property can be set to the name of any of the default visualizations
	provided by Google.

Visualization Options
	A list of options and values, in the format of TAL defines, that specify
	the options for the visualization. The available options depend on the
	type of visualization selected. As with the report column expressions,
	it is important that the option expressions evaluate to the data type
	that the visualization expects.
	
	For example, the height of a visualization that accepts an integer height
	option could be set as follows::
	
		height python:300

It may be helpful to think of Analytics reports as having four logical
sections:

* Metadata about the report
* Query criteria
* Report definition
* Visulization settings

The first four properties--title, description, i18n domain and page
specific--make up the metadata section of the report. These properties
do not affect the results of the report or its presentation. Instead, they
determine how it is listed and cached.

The query criteria section of the report is made up of all the properties
that begin with the word query. These properties determine the query that is
sent to Google to retrieve Analytics data. As a result, TALES expressions in
this section of the report do not have access to the variables and objects
that store the returned Analytics data.

The report definition is composed on the four properties that begin with the
word report. This section of the report takes the data returned by Google and
does the necessary processing and calculations. In other words, it takes the
columns of data that Google provides, which correspond to dimensions and
metrics, and maps them to the columns of data that the report defines. As a
result, the report column expressions property has access to the metric and
dimension variables, like ga_day or ga_visits, that represent the results of
the query. The report introduction and conclusion have access to the data
produces by evaluating the report column expressions in the form of data_rows
and data_columns.

Finally the visualizaiton settings section of the report consists of the
visualization type and visualization options properties. These properties
are used to produce javascript that uses the Google Visualizations API
to render the report data.

Dates and Reports
=================

Analytics reports do not specify start and end dates for their queries.
Instead, they accecpt date range arguments when they are evaluated. (This
dynamic selection of date ranges is not currently exposed in the user
interface.) These date range arguments are passed to the report's getResults
method. getResults can accept these date-related keyword arguments:

start_date and end_date
    Python start and end dates.

date_range
    An integer specifying the number of days prior to the current date use
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
        
Since dates for reports are dynamic, Analytics reports implement two special
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
    
For more information about using these dimensions in reports, see the section
on `Using TAL and TALES in Reports`_.
    
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
	The current request object.

date
	An alias for the datetime.date function.
	
timedelta
	An alias for the datetime.timedelta function.
	
page_url
	The relative URL of the current request. This is most commonly used in
	the query filters property for creating page-specific reports.
		
date_range_dimension
    The temporal dimension used to segment the results. In report column
    expressions, this variable evaluates to the value of the dimension for
    the selected row. In all other fields, it evaluates to the name of the
    dimension. See the section on `Dates and Reports`_ for more information
    about how this dimension is selected.
    
date_range_sort_dimension
    The name of the dimension used to sort the results chronologically (along
    with date_range_dimension). See the section on `Dates and Reports`_ for
    more information.
    
date_range_unit
    A string containing the human-readable name of the dimension specified
    by date_range_dimension (e.g. 'Day', 'Month', etc.)
    
date_range_unit_plural
    A convenience variable that contains date_range_unit with the letter
    's' appended.

In addition to these objects, some properties have access to special objects
and variables that represent the data returned by the query:

Report Column Expressions
	These TALES expressions have access to variables that represent the values
	of each dimension and metric used in the query. The names of these
	variables are found by taking the name of the dimension or metric and
	replacing the colon with an underscore. For example, ga:exitPagePath
	becomes ga_exitPagePath. For more information about using these variables,
	see the section on `Report Properties`_ above.
	
Report Introduction and Report Conclusion
	These TAL blocks have access to two special data structures--data_rows
	and data_columns--that contain the results of the evaluated report
	column expressions. For more information about using these data structures
	to perform calculations, see the section on `Report Properties`_ above.

Creating a New Report
=====================

Now that you are familiar with the properties that make up an Analytics report,
it's time to try creating a new report from scratch. In this example, we will
first create a report that calculates and displays the site-wide bounce rate
segmented by browser. After we get that working, we'll create a second report
that displays the same information for any given page on the site. Let's get 
started!

1. Navigate to the root of the site in the ZMI and click on the
   portal_analytics tool.

2. Click the Add Google Analytics Report button.

3. We'll give our new report the ID site-bounce-rate-browser-column,
   following the naming convention of the default reports. This naming 
   convention is optional, but it helps to keep things organized. Then 
   click the add button.

4. Click on the new report to edit it. Give it a title of Site Bounce Rate
   By Browser: Column Chart and this description:

   This report displays the site-wide bounce rate segmented by the user's 
   browser. It is useful for gauging how effective our site's new multimedia
   features are in each browser.

5. Leave the i18n domain as analytics, the default value. If we were going
   to translate this report, we might use the domain defined in our site's
   theme product.

6. Leave the page specific box unchecked. This report is site-wide, so
   we don't need to calculate the result for each individual page.

7. Now the difficult part: determining the arguments for our query. If we
   consult the common calculations page in the Google's Dimensions and Metrics
   Reference (see the section on `Where to Learn More`_ for the link), we see
   that bounce rate is calculated as follows::

		ga:bounces/ga:entrances
		
   So, set the query metrics to ga:bounces and ga:entrances. 

8. We also know that we want to segment our results by browser, so we'll se
   our query dimension to ga:browser.

9. Leave query filters blank. We don't need to filter the query results.

10. In the query sort box, type -ga:entrances. We want to sort by entrances
    so that we'll be guaranteed to be shown the most popular browsers. The
    minus sign preceding the metric indicates that the sort should be in
    descending order.

11. In query maximum results, enter 5. Since we set ga:entrances as the sort
    value, this will show us results for the top five browsers based on
    entrances. We could, of course, increase this number if we wanted to see
    results for more browsers.

12. Now that our query arguments are complete, we can work on our report
    definition. We want our report to show us two things: the name of the
    browser and the bounce rate as a percentage. So, we'll define two report
    columns. In the report column labels, enter these values on separate
    lines::

        string:Browser Name
        string:Bounce Rate (%)
	
13. In the report column expressions field, enter these TALES expressions on
    separate lines::

        python:str(ga_browser)
        python:int(100*float(ga_bounces)/float(ga_entrances))
		
    The first expression is fairly self-explanatory; it returns then name of
    the browser as a string. In the second expression, however, we have to
    do some calculations. Since Google returns all values as strings, our first
    task is converting the values to the appropriate format, in this case,
    floats. (Even though these values are always integers, we want to convert
    them to floating point numbers. Otherwise, Python will round down the
    result of the division.) Once we have our values in the correct format, we
    can divide them according to the formula provided by Google
	
    This division will yield a number between 0 and 1. To make the result
    easier to read, we'll multiply the decimal by 100 to get a percentage and
    round it off to the nearest integer.
	
14. Leave the report introduction property blank. We're going to display the
    title of the report as part of the visualization, so we don't have to do
    it here.

15. In the report conclusion, we want to list the browsers with the lowest and
    highest bounce rates among the ones we are displaying. In the report
    conclusion field enter this TAL code::

        <div tal:define="browsers python:data_columns[0];
                bounces python:data_columns[1];">
            <p>
                Highest bounce rate:
                <strong tal:define="max_bounces python:max(bounces);
                    max_bounces_index python:bounces.index(max_bounces);"
                    tal:content="python:browsers[max_bounces_index]">
                    Browser
                </strong>
            </p>
            <p>
                Lowest bounce rate:
                <strong tal:define="min_bounces python:min(bounces);
                        min_bounces_index python:bounces.index(min_bounces);"
                    tal:content="python:browsers[min_bounces_index]">
                    Browser
                </strong>
            </p>
        </div>
		
    In the first tal:define, we extract the browsers and bounces columns
    from the data_columns list. Then in the subsequent tal:defines, we
    determine the highest or lowest value in the bounces column and find
    the index of that value. Finally we set the value of the strong element
    to the value in browsers column that corresponds with the index we have
    determined.
	
16. Finally, we will set the visualization options for the report. In the
    visualization type dropdown, select ColumnChart.

17. In the visualization options field, enter these options in the format
    of TAL defines, one per line::

        height python:250
        is3D python:True
        legend string:top
        legendFontSize python:10
        title string:Site Bounce Rate
		
    These options are all aesthetic. Once you become familiar with Google
    visualizations, you can adjust them to fit your personal preferences. For
    a full list of the options available for each visualization, visit the
    Google Visualization Gallery referenced in the section on `Where to Learn
    More`_.
	
18. You're done! Click the save button in the ZMI. Then test out your new
    report on the site as described in the section about `Basic Use`_.

Now that we've created a site-wide report for bounce rate, it's easy to create
a related report that displays the same statistics for a particular page.

1. To begin, navigate to the portal_analytics tool in the ZMI.

2. Check the box next to the report you just created. Then press the copy
   button at the bottom of the list.

3. Press the paste button. A new copy of the report is created with the ID
   copy_of_site-bounce-rate-browser-column.

4. Check next to the newly pasted report and click the rename button.

5. Change the ID of the new report to page-bounce-rate-browser-column and
   press Ok.

6. Click on the new report to edit it. In the title, replace the word Site with
   Page, and edit the description accordingly.

7. Check the box next to page specific. This will tell Plone to evaluate the
   the report for each page instead of caching it for the entire site.

8. In the query metrics list, deselect ga:entrances and select
   ga:uniquePageviews. Also, leave ga:bounces selected. If you're not sure why
   we need to use ga:uniquePageviews instead of ga:entrances, consult the
   Google page about common calculations referenced above.

9. In the list of query dimensions, select ga:pagePath, and leave ga:browser
   selected. We'll use ga:pagePath to filter the results of the query to just
   the current page.

10. In the query sort field, replace -ga:entrances with -ga:uniquePageviews to
    reflect the change in metrics.

11. Similarly, in the report column expressions, replace ga_entrances with
    ga_uniquePageviews.

12. In the query filters field, enter this TALES expression::

        string:ga:pagePath==${page_url}
		
    Recall that page_url is a convenience variable that is set to the relative
    URL of the current request.
	
13. In the visualization options property, edit the title of the visualization
    to read Page Bounce Rate.

14. You're done! Save your changes and try out your new report on your site. If
    you assign the report in a portlet at the root of the site and then navigate
    to interior pages, you should see the results change.

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


