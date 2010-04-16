# -*- coding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""HTTP Publisher Tests

$Id: test_http.py 96537 2009-02-14 15:13:58Z benji_york $
"""
import unittest
import doctest
import zope.testing


def cleanUp(test):
    zope.testing.cleanup.cleanUp()


def test_suite():
    return unittest.TestSuite(
        doctest.DocFileSuite('../skinnable.txt',
            setUp=cleanUp, tearDown=cleanUp))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
