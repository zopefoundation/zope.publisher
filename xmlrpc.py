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
"""XML-RPC Publisher

This module contains the MethodPublisher, XMLRPCRequest and XMLRPCResponse

$Id$
"""
import sys
import xmlrpclib
from StringIO import StringIO

from zope.interface import implements
from zope.publisher.interfaces.xmlrpc import IXMLRPCPublisher
from zope.publisher.interfaces.xmlrpc import IXMLRPCRequest

from zope.publisher.http import HTTPRequest, HTTPResponse
from zope.publisher.http import DefaultPublisher
from zope.proxy import removeAllProxies


class MethodPublisher(DefaultPublisher):
    """Simple XML-RPC publisher that is identical to the HTTP Default Publisher
       except that it implements the IXMLRPCPublisher interface."""

    implements(IXMLRPCPublisher)

    def __init__(self, context, request):
        self.context = context
        self.request = request


class XMLRPCRequest(HTTPRequest):
    implements(IXMLRPCRequest)

    _args = ()

    def _createResponse(self, outstream):
        """Create a specific XML-RPC response object."""
        return XMLRPCResponse(outstream)

    def processInputs(self):
        'See IPublisherRequest'

        # Parse the request XML structure
        self._args, function = xmlrpclib.loads(self._body_instream.read())
        # Translate '.' to '/' in function to represent object traversal.
        function = function.split('.')

        if function:
            self.setPathSuffix(function)


class TestRequest(XMLRPCRequest):

    def __init__(self, body_instream=None, outstream=None, environ=None,
                 response=None, **kw):

        _testEnv =  {
            'SERVER_URL':         'http://127.0.0.1',
            'HTTP_HOST':          '127.0.0.1',
            'CONTENT_LENGTH':     '0',
            'GATEWAY_INTERFACE':  'TestFooInterface/1.0',
            }

        if environ:
            _testEnv.update(environ)
        if kw:
            _testEnv.update(kw)
        if body_instream is None:
            body_instream = StringIO('')

        if outstream is None:
            outstream = StringIO()

        super(TestRequest, self).__init__(
            body_instream, outstream, _testEnv, response)


class XMLRPCResponse(HTTPResponse):
    """XMLRPC response.

    This object is responsible for converting all output to valid XML-RPC.
    """

    def setBody(self, body):
        """Sets the body of the response

        Sets the return body equal to the (string) argument "body". Also
        updates the "content-length" return header.

        If the body is a 2-element tuple, then it will be treated
        as (title,body)

        If is_error is true then the HTML will be formatted as a Zope error
        message instead of a generic HTML page.
        """
        body = removeAllProxies(body)
        if isinstance(body, xmlrpclib.Fault):
            # Convert Fault object to XML-RPC response.
            body = xmlrpclib.dumps(body, methodresponse=1)
        else:
            # Marshall our body as an XML-RPC response. Strings will be sent
            # strings, integers as integers, etc. We do *not* convert
            # everything to a string first.
            if body is None:
                body = xmlrpclib.False # Argh, XML-RPC doesn't handle null
            try:
                body = xmlrpclib.dumps((body,), methodresponse=1)
            except:
                # We really want to catch all exceptions at this point!
                self.handleException(sys.exc_info())
                return
        # Set our body to the XML-RPC message, and fix our MIME type.
        self.setHeader('content-type', 'text/xml')

        self._body = body
        self._updateContentLength()

        if not self._status_set:
            self.setStatus(200)


    def handleException(self, exc_info):
        """Handle Errors during publsihing and wrap it in XML-RPC XML"""
        t, value = exc_info[:2]

        # Create an appropriate Fault object. Unfortunately, we throw away
        # most of the debugging information. More useful error reporting is
        # left as an exercise for the reader.
        Fault = xmlrpclib.Fault
        fault_text = None
        try:
            if isinstance(value, Fault):
                fault_text = value
            elif isinstance(value, Exception):
                fault_text = Fault(-1, "Unexpected Zope exception: " +
                                   str(value))
            else:
                fault_text = Fault(-2, "Unexpected Zope error value: " +
                                   str(value))
        except:
            fault_text = Fault(-3, "Unknown Zope fault type")

        # Do the damage.
        self.setBody(fault_text)
        self.setStatus(200)
