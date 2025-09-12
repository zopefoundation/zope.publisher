##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
# This package is developed by the Zope Toolkit project, documented here:
# http://docs.zope.org/zopetoolkit
# When developing and releasing this package, please follow the documented
# Zope Toolkit policies as described by this documentation.
##############################################################################
import os

from setuptools import setup


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()


entry_points = '''
[paste.app_factory]
main = zope.publisher.paste:Application

[zope.publisher.publication_factory]
sample = zope.publisher.tests.test_paste:SamplePublication
'''

tests_require = [
    'zope.testing',
    'zope.testrunner >= 6.4',
]

setup(
    name='zope.publisher',
    version='8.0',
    url='https://github.com/zopefoundation/zope.publisher',
    license='ZPL 2.1',
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.dev',
    description='The Zope publisher publishes Python objects on the web.',
    long_description=read('README.rst') + '\n\n' + read('CHANGES.rst'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
    ],
    install_requires=[
        'multipart>=1.1.0',
        'setuptools',
        'zope.browser',
        'zope.component',
        'zope.configuration',
        'zope.contenttype>=4.0.0',
        'zope.event',
        'zope.exceptions',
        'zope.i18n>=4.0.0',
        'zope.interface>=4.0.1',
        'zope.location',
        'zope.proxy',
        'zope.security>=4.0.0',
    ],
    extras_require={
        'test': tests_require,
        'docs': [
            'Sphinx',
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],
    },
    entry_points=entry_points,
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.9',
)
