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
"""Setup for zope.publisher package

$Id$
"""
import os
from setuptools import setup, find_packages

setup(name='zope.publisher',
      version = '3.5dev',
      url='http://cheeseshop.python.org/pypi/zope.publisher',
      license='ZPL 2.1',
      author='Zope Corporation and Contributors',
      author_email='zope3-dev@zope.org',
      description="The Zope publisher publishes Python objects on the web.",
      long_description=open('README.txt').read(),

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
