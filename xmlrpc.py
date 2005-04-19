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

This module contains the XMLRPCRequest and XMLRPCResponse

$Id$
"""
import sys
import xmlrpclib
from StringIO import StringIO

from zope.interface import implements
from zope.publisher.interfaces.xmlrpc import IXMLRPCPublisher
from zope.publisher.interfaces.xmlrpc import IXMLRPCRequest

from zope.publisher.http import HTTPRequest, HTTPResponse

from zope.security.proxy import isinstance

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
        body = premarshal(body)
        if isinstance(body, xmlrpclib.Fault):
            # Convert Fault object to XML-RPC response.
            body = xmlrpclib.dumps(body, methodresponse=True)
        else:
            # Marshall our body as an XML-RPC response. Strings will be sent
            # as strings, integers as integers, etc.  We do *not* convert
            # everything to a string first.
            try:
                body = xmlrpclib.dumps((body,), methodresponse=True,
                                       allow_none=True)
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
        """Handle Errors during publsihing and wrap it in XML-RPC XML

        >>> import sys
        >>> from StringIO import StringIO
        >>> output = StringIO()
        >>> resp = XMLRPCResponse(output)
        >>> try:
        ...     raise AttributeError('xyz')
        ... except:
        ...     exc_info = sys.exc_info()
        ...     resp.handleException(exc_info)
        ...     resp.outputBody()
        ...     lines = output.getvalue().split('\\n')
        ...     for line in lines:
        ...         if 'Status:' in line or 'Content-Type:' in line:
        ...             print line.strip()
        ...         if '<value><string>' in line:
        ...             print line[:61].strip()
        Status: 200 Ok
        Content-Type: text/xml;charset=utf-8
        <value><string>Unexpected Zope exception: AttributeError: xyz
        """
        t, value = exc_info[:2]
        s = '%s: %s' % (getattr(t, '__name__', t), value)

        # Create an appropriate Fault object. Unfortunately, we throw away
        # most of the debugging information. More useful error reporting is
        # left as an exercise for the reader.
        Fault = xmlrpclib.Fault
        fault_text = None
        try:
            if isinstance(value, Fault):
                fault_text = value
            elif isinstance(value, Exception):
                fault_text = Fault(-1, "Unexpected Zope exception: " + s)
            else:
                fault_text = Fault(-2, "Unexpected Zope error value: " + s)
        except:
            fault_text = Fault(-3, "Unknown Zope fault type")

        # Do the damage.
        self.setBody(fault_text)
        # XML-RPC prefers a status of 200 ("ok") even when reporting errors.
        self.setStatus(200)


def premarshal_dict(data):
    return dict([(premarshal(k), premarshal(v))
                 for (k, v) in data.items()])

def premarshal_list(data):
    return map(premarshal, data)

def premarshal_fault(data):
    return xmlrpclib.Fault(
        premarshal(data.faultCode),
        premarshal(data.faultString),
        )

def premarshal_datetime(data):
    return xmlrpclib.DateTime(data.value)

premarshal_dispatch_table = {
    dict: premarshal_dict,
    list: premarshal_list,
    tuple: premarshal_list,
    xmlrpclib.Fault: premarshal_fault,
    xmlrpclib.DateTime: premarshal_datetime,
    }
premarshal_dispatch = premarshal_dispatch_table.get

def premarshal(data):
    """Premarshal data before handing it to xmlrpclib for marhalling

    The initial purpose of this function is to remove security proxies
    without resorting to removeSecurityProxy.   This way, we can avoid
    inadvertently providing access to data that should be protected.

    Suppose we have a sample data structure:

      >>> sample = {'foo': (1, ['x', 'y', 1.2])}

    if we put the sample in a security proxy:

      >>> from zope.security.checker import ProxyFactory
      >>> proxied_sample = ProxyFactory(sample)

    We can still get to the data, but the non-rock data is proxied:

      >>> from zope.security.proxy import Proxy
      >>> proxied_sample['foo']
      (1, ['x', 'y', 1.2])
      
      >>> type(proxied_sample['foo']) is Proxy
      True
      >>> type(proxied_sample['foo'][1]) is Proxy
      True

    But we can strip the proxies using premarshal:

      >>> stripped = premarshal(proxied_sample)
      >>> stripped
      {'foo': [1, ['x', 'y', 1.2]]}

      >>> type(stripped['foo']) is Proxy
      False
      >>> type(stripped['foo'][1]) is Proxy
      False

    So xmlrpclib will be happy. :)

    We can also use premarshal to strip proxies off of Fault objects.
    We have to make a security declaration first though:

      >>> from zope.security.checker import NamesChecker, defineChecker
      >>> defineChecker(xmlrpclib.Fault,
      ...               NamesChecker(['faultCode', 'faultString']))
    
      >>> fault = xmlrpclib.Fault(1, 'waaa')
      >>> proxied_fault = ProxyFactory(fault)
      >>> stripped_fault = premarshal(proxied_fault)
      >>> type(stripped_fault) is Proxy
      False
    """
    premarshaller = premarshal_dispatch(data.__class__)
    if premarshaller is not None:
        return premarshaller(data)
    return data
