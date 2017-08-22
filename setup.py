from setuptools import setup, find_packages
import sys

version = '1.6.1'


setup(name='collective.googleanalytics',
      version=version,
      description="Tools for pulling statistics from Google Analytics.",
      long_description=open("README.rst").read() + "\n" +
                       open("CHANGES.rst").read(),
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Framework :: Plone",
          "Framework :: Plone :: 4.3",
          "Framework :: Plone :: 5.0",
          "Framework :: Plone :: 5.1",
          "Intended Audience :: System Administrators",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Operating System :: OS Independent",
          "Programming Language :: JavaScript",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Topic :: Internet :: Log Analysis",
          "Topic :: Internet :: WWW/HTTP :: Site Management",
          "Topic :: Software Development :: Libraries :: Python Modules",
      ],
      keywords='Google Analytics Plone statistics portlet integration',
      author='Matt Yoder',
      author_email='mattyoder@groundwire.org',
      url='https://github.com/collective/collective.googleanalytics',
      license='GPL',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'gdata>=2.0.18',
          'plone.api',
      ],
      extras_require={
          'test': [
              'plone.app.testing',
          ],
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """
      )
