##############################################################################
#
# Copyright (c) 2006--2008 Zope Corporation and Contributors.
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
"""Setup for zope.publisher package

$Id$
"""

from setuptools import setup, find_packages


long_description = (open('README.txt').read() +
                    '\n\n' +
                    open('CHANGES.txt').read())


setup(name='zope.publisher',
      version='3.4.6dev',
      url='http://pypi.python.org/pypi/zope.publisher',
      license='ZPL 2.1',
      author='Zope Corporation and Contributors',
      author_email='zope-dev@zope.org',
      description="The Zope publisher publishes Python objects on the web.",
      long_description=long_description,

      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['zope',],
      tests_require=['zope.testing'],
      install_requires=['setuptools',
                        'zope.component',
                        'zope.event',
                        'zope.exceptions',
                        'zope.i18n',
                        'zope.interface',
                        'zope.location',
                        'zope.proxy',
                        'zope.security',
                        'zope.testing',
                        'zope.app.testing',
                        'zope.deprecation',
                        'zope.deferredimport'],
      include_package_data=True,
      zip_safe=False,
      )
