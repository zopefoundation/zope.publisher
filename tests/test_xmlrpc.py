##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Testing the XML-RPC Publisher code.

$Id$
"""
import unittest
from zope.testing.doctest import DocTestSuite
from zope.testing.cleanup import CleanUp


def test_suite():
    return unittest.TestSuite((
        DocTestSuite('zope.publisher.xmlrpc',
                     tearDown=lambda ignored=None: CleanUp().cleanUp()),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

