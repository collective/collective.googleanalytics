Changelog
=========

1.7 (unreleased)
----------------

- Additional plugin for server-side download virtual page hits so direct download links get counted
  [djay]
- Ensure download handler works even on links loaded from AJAX such as the quicksearch.
  [ivanteoh]
- Fix exception thrown with external link plugin
  [nngu6036]
- upgrade to google api v3 and deprecate gdata library usage
  [djay]
- allow setting client secrets ahead of user authentication
  [djay]
- switched to https://www.googleapis.com/auth/analytics.readonly scope as it's all we need
  [djay]  
- Fix bug where every page view is register twice
  [djay]
- fix bug where views without "__name__" cause an error

1.6.1 (2017-08-22)
------------------

- Log virtual error page views based on HTTP response status
  rather than Python exc_info (which is set even for handled
  exceptions).
  [davisagli]

- Use jQuery global instead of jq.
  [davisagli]

- Plone 5.1 compatibility
  [alecm]

- Port to plone.app.testing
  [tomgross]

- Remove unused egg dependencies
  [tomgross]

- implements -> implementer
  [tomgross]

1.6.0 (2017-02-21)
------------------

- Plone 5 compatibility
  [enfold-josh, tomgross]


1.5.0 (2016-07-27)
------------------

- Add virtual page views for search and error pages [tomgross]
 
- Use Python json instead of custom one [tomgross]

- Updated Spanish translations [macagua]

- Added more improvements about i18n [macagua]

- Move to OAuth2 credential authentication [frapell]


1.4.4 (2014-10-15)
------------------

- Added more improvements about i18n [macagua]

- Added Spanish translations [macagua]

- Updated the core GA code with the latest snippet from Google [spanktar]

- Prepend "Copy of" if copy&paste a report. [frapell]

- Use SimpleTerm when creating the reports vocabulary. [frapell]

- Crop overlong profile names [tomgross]
  
- Pass viewlet view and manager [tomgross]


1.4.3 (2013-05-28)
------------------

- french translations [kiorky]


1.4.2 (2013-05-28)
------------------

- Fix release, add .mo [kiorky]


1.4.1 (2013-05-28)
------------------

* Add dependency on unittest2 to support advance testing features under
  Python 2.6.
  [2013-04-06 - hvelarde]

* Add dependency on plone.app.testing and some tests for the control panel
  configlet.
  [2013-04-05 - hvelarde]

* Package distribution refactoring: package classifiers were updated;
  documentation files were renamed as .rst; MANIFEST.in was fixed and some
  missing testing dependencies were added.
  [2013-04-05 - hvelarde]

* Add .docx, .pptx, and .xlsx to extensions tracked by the file
  download plugin.
  [2013-03-28 - davisagli]

* Improve i18n and include first version of the pt-br translation.
  [2012-10-19 - tcurvelo]

* Improve handling of unicode values in vocabularies
  [2012-10-23 - kiorky]

* Release & QA Stuff
  [2013-05-28 - kiorky]

1.4.1 - 2012-08-29
------------------

* Avoid calling Google to retrieve vocabularies if there's no valid auth_token.
  This should help avoid conflict errors on the analytics tool.
  [2012-08-29 - davisagli]

1.4 - 2012-08-27
----------------

* Update to continue working with Google's new Management API and some bugs
  in their backwards-compatibility for the Data Export API.
  [2012-08-27 - davisagli]

* Avoid trying to look up the list of available web properties when simply
  rendering the tracking code.
  [2012-08-23 - davisagli]

* When a Forbidden exception is encountered and the stored access_token is
  removed, also be sure to clear the reports_profile so that a new
  authorization won't encounter the same Forbidden exception immediately.
  [2012-08-23 - davisagli]

1.3 - 2012-04-09
----------------

* Add Plone 4.1 compatibility
  [2012-03-28 - encolpe]

* Fixed leap day bug in date range calculation.
  [2012-03-01 - yomatters]

* Updated file download tracking plugin to track at_download links.
  [2011-07-26 - yomatters]

1.2 - 2011-05-31
----------------

* Escaped CDATA tags to keep Chameleon happy.
  [2011-05-27 - yomatters]

* Reject AuthSub tokens that generate a forbidden response.
  [2011-04-27 - yomatters]

* Moved page view tracking after plugins so that custom variables get sent
  along with the page view.
  [2011-04-04 - yomatters]

* Added a plugin for tracking user type in a custom variable.
  [2011-04-04 - yomatters]

* Update tracking code
  [2011-04-15 - garbas]

* Added a plugin for tracking page load time.
  [2011-05-05 - toutpt]

1.1 - 2011-03-24
----------------

* Documented the domain registration process.
  [2011-03-24 - yomatters]

* Made vocabularies safe for profiles containing non-ASCII characters.
  [2010-12-23 - yomatters]

1.0 - 2010-12-07
----------------

* Added icon expression for control panel in Plone 4.
  [2010-12-07 - yomatters]

* Fixed permission bug so that the Google Analytics portlet can be made visible
  to non-managers.
  [2010-12-07 - yomatters]

* Allowed requesting Google API javascript over HTTPS if the current page is
  being served securely.
  [2010-11-04 - yomatters]

* Reduced logging level for query messages.
  [2010-08-13 - yomatters]

* wrap inline javascript in CDATA, making it easier to use with Deliverance.
  [2010-08-13 - garbas]

1.0b3 - 2010-06-30
------------------

* Stored connections to Google Analytics on the ZODB connection instead
  of the Analytics tool.
  [2010-06-30 - yomatters]

* Resolved conflict between Analytics tools on multiple Plone sites on the
  same Zope instance.
  [2010-06-30 - yomatters]

1.0b2 - 2010-06-18
------------------

* Changed to comma-separated strings in asynchronous loader for Plone 4
  compatibility.
  [2010-06-18 - yomatters]

* Fixed divide by zero error in Time on Site: Line Chart report.
  [2010-06-18 - yomatters]

* Added basic timeout handling so that a request to Google can't tie up a Zope
  thread indefinitely.
  [2010-06-15 - yomatters]

* Limited regular expressions generated by the contextual results plugin to
  128 characters to conform to Google API restrictions.
  [2010-06-07 - yomatters]

* Added upgrade step to 1.0b2.
  [2010-06-07 - yomatters]

* Changed to AuthSub authentication.
  [2010-06-04 - yomatters]

* Add tracking functionality, including external links, e-mail addresses,
  comments and file downloads.
  [2010-05-11 - yomatters]

* @@analytics-controlpanel failing to display under Plone 4 because of trying to
  access self.context.request which for some reason is not availiable. Accesing
  self.context.REQUEST works for for Plone 3.3.5 and Plone 4b2. Didn't have time
  to investigate this further, but I made it work.
  [2010-05-07 garbas]

1.0b1 - 2010-05-05
------------------

Note: 1.0b1 changes the syntax for the table-building section of the report
(previously the report column labels and expressions) and the report body. The
upgrade step overwrites these properties for the default reports that ship with
the product. If you have customized these properties on the default reports, be
sure to rename the customized reports in portal_analytics before running the
upgrade step to avoid losing your changes.

* Changed loader to call @@analytics_async on the current context.
  [2010-05-05 - yomatters]

* Added a link to Google Analytics in the control panel.
  [2010-05-04 - yomatters]

* Standardized i18n domain to collective.googleanalytics.
  [2010-04-30 - yomatters]

* Added possible_dates helper function to solve the problem where date-based
  reports do not have results for every date in the range.
  [2010-04-28 - yomatters]

* Make it Plone4 compatible.
  [2010-04-26 - garbas]

* Changed table building interface so that rows are not directly tied to
  results returned by Google. Added dimension and metric value-getter
  functions.
  [2010-04-22 - yomatters]

* Improved reporting when there is no data.
  [2010-04-09 - yomatters]

* Refactored monolithic report into pluggable components.
  [2010-04-09 - yomatters]

* Moved utility functions off of report class.
  [2010-04-01 - yomatters]

1.0a4 - 2010-03-24
------------------

* Only show the portlet on the context's view template.
  [2010-03-24 - yomatters]

* Add an upgrade step from 1.0a3 to 1.0a4.
  [2010-03-24 - yomatters]

* Modify tests to match asynchronous javascript.
  [2010-03-24 - yomatters]

* Use asynchronous view for the site-wide analytics viewlet.
  [2010-03-24 - yomatters]

* Add a view for asynchronous results, and modify the portlet to use it.
  [2010-03-19 - yomatters]

1.0a3 - 2010-03-05
------------------

* Add upgrade step from 1.0a2 to 1.0a3.
  [2010-03-05 - yomatters]

* Modify javascript registration and configuration javascript to be compatible
  with Plone 3.1.
  [2010-03-05 - yomatters]

* Add more default reports.
  [2010-03-05 - yomatters]

* Load external javascript through a viewlet instead of through the
  registry to add support for Plone < 3.3.
  [2010-03-05 - yomatters]

1.0a2 - 2010-02-10
------------------

* Add security assertions for report categories.
  [2010-02-10 - yomatters]

* Update documentation to reflect date range changes.
  [2010-02-10 - yomatters]

* Make date range independent of report and update tests and default reports
  to reflect the new reality; add javascript to set the width of the
  visualization based on the width of the container; add categories to reports
  and adjust vocabularies to be category-specific; handle auth token expiration
  error.
  [2010-02-03 - yomatters]

* Make report IDs unique so that the same page can contain multiple copies
  of the same report.
  [2010-01-19 - yomatters]

* Fix a bug that caused an error if the query returned no results.
  [2010-01-19 - yomatters]

* Fix bug in older Zopes that required the user to reenter the password every
  time the configlet form was saved.
  [2010-01-14 - yomatters]

* Add fallback for importing InitializeClass in Zopes prior to 2.12.
  [2010-01-05 - yomatters]

1.0a1 - 2009-12-23
------------------

* Initial release

