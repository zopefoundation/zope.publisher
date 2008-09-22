##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import os
from setuptools import setup, find_packages

entry_points = """
[paste.app_factory]
main = zope.publisher.paste:Application

[zope.publisher.publication_factory]
sample = zope.publisher.tests.test_paste:SamplePublication
"""

setup(name='zope.publisher',
      version = '3.5.4',
      url='http://pypi.python.org/pypi/zope.publisher',
      license='ZPL 2.1',
      author='Zope Corporation and Contributors',
      author_email='zope-dev@zope.org',
      description="The Zope publisher publishes Python objects on the web.",
      long_description=(open('README.txt').read()
                        + '\n\n'
                        + open('CHANGES.txt').read()),

      entry_points = entry_points,

      packages=find_packages('src'),
      package_dir = {'': 'src'},

      namespace_packages=['zope',],
      install_requires=['setuptools',
                        'zope.component',
                        'zope.event',
                        'zope.exceptions',
                        'zope.i18n',
                        'zope.interface',
                        'zope.location',
                        'zope.proxy',
                        'zope.security',
                        'zope.deprecation',
                        'zope.deferredimport'],
      extras_require=dict(
          test = ['zope.testing',
                  'zope.app.testing'],
          ),
      include_package_data = True,

      zip_safe = False,
      )
