from setuptools import setup, find_packages

version = '1.0b1'

setup(name='collective.googleanalytics',
      version=version,
      description="Tools for pulling statistics from Google Analytics.",
      long_description=open("README.txt").read() + "\n" +
                       open("CHANGES.txt").read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: Log Analysis",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "Development Status :: 3 - Alpha",
        ],
      keywords='Google Analytics Plone statistics portlet integration',
      author='Matt Yoder',
      author_email='mattyoder@onenw.org',
      url='http://svn.plone.org/svn/collective/collective.googleanalytics/trunk',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'gdata>=2.0.4',
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """
      )
