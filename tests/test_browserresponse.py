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
"""Browser response tests

$Id$
"""

from unittest import TestCase, TestSuite, main, makeSuite
from zope.publisher.browser import BrowserResponse
from StringIO import StringIO
from zope.interface.verify import verifyObject

# TODO: Waaa need more tests

class TestBrowserResponse(TestCase):

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

    def test_interface(self):
        from zope.publisher.interfaces.http import IHTTPResponse
        from zope.publisher.interfaces.http import IHTTPApplicationResponse
        from zope.publisher.interfaces import IResponse
        rp = BrowserResponse(StringIO())
        verifyObject(IHTTPResponse, rp)
        verifyObject(IHTTPApplicationResponse, rp)
        verifyObject(IResponse, rp)


def test_suite():
    return TestSuite((
        makeSuite(TestBrowserResponse),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
