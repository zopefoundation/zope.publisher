##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Browser response tests

XXX longer description goes here.

$Id: test_browserresponse.py,v 1.3 2003/03/02 18:09:03 stevea Exp $
"""

from unittest import TestCase, TestSuite, main, makeSuite
from zope.publisher.browser import BrowserResponse
from StringIO import StringIO

# XXX Waaa need more tests

class Test(TestCase):

    def test_contentType_DWIM_in_setBody(self):
        response = BrowserResponse(StringIO())
        response.setBody(
            """<html>
            <blah>
            </html>
            """)
        self.assert_(response.getHeader('content-type').startswith("text/html")
                     )

        response = BrowserResponse(StringIO())
        response.setBody(
            """<html foo="1"
            bar="x">
            <blah>
            </html>
            """)
        self.assert_(response.getHeader('content-type').startswith("text/html")
                     )

        response = BrowserResponse(StringIO())
        response.setBody(
            """<html foo="1"
            bar="x">
            <blah>
            </html>
            """)
        self.assert_(response.getHeader('content-type').startswith("text/html")
                     )

        response = BrowserResponse(StringIO())
        response.setBody(
            """<!doctype html>
            <html foo="1"
            bar="x">
            <blah>
            </html>
            """)
        self.assert_(response.getHeader('content-type').startswith("text/html")
                     )

        response = BrowserResponse(StringIO())
        response.setBody(
            """Hello world
            """)
        self.assert_(response.getHeader('content-type').startswith(
            "text/plain")
                     )

        response = BrowserResponse(StringIO())
        response.setBody(
            """<p>Hello world
            """)
        self.assert_(response.getHeader('content-type').startswith(
            "text/plain")
                     )


def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
