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

    def test_writeDataDirectlyToResponse(self):
        # In this test we are going to simulate the behavior of a view that
        # writes its data directly to the output pipe, instead of going
        # through the entire machinery. This is particularly interesting for
        # views returning large amount of binary data. 
        output = StringIO()
        response = BrowserResponse(output)
        data = 'My special data.'

        # If you write the data yourself directly, then you are responsible
        # for setting the status and any other HTTP header yourself as well.
        response.setHeader('content-type', 'text/plain')
        response.setHeader('content-length', str(len(data)))
        response.setStatus(200)
        
        # Write the data directly to the output stream from the view
        response.write(data)

        # Then the view returns `None` and the publisher calls
        response.setBody(None)

        # Now, if we got here already everything should be fine. The `None`
        # value for the body should have been ignored and our putput value
        # should just be our data:
        self.assertEqual(
            output.getvalue(),
            'Status: 200 Ok\r\nContent-Length: 16\r\n'
            'Content-Type: text/plain;charset=utf-8\r\n'
            'X-Powered-By: Zope (www.zope.org), Python (www.python.org)\r\n'
            '\r\n'
            'My special data.')

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
