##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
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
"""XML-RPC Request Tests
"""
import unittest
from io import BytesIO

from zope.publisher.base import DefaultPublication
from zope.publisher.http import HTTPCharsets
from zope.publisher.xmlrpc import XMLRPCRequest


class Publication(DefaultPublication):

    require_docstrings = 0

    def getDefaultTraversal(self, request, ob):
        if hasattr(ob, 'browserDefault'):
            return ob.browserDefault(request)
        return ob, ()


class TestXMLRPCRequest(XMLRPCRequest, HTTPCharsets):
    """Make sure that our request also implements IHTTPCharsets, so that we do
    not need to register any adapters."""

    def __init__(self, *args, **kw):
        self.request = self
        XMLRPCRequest.__init__(self, *args, **kw)


xmlrpc_call = b'''<?xml version='1.0'?>
<methodCall>
  <methodName>action</methodName>
  <params>
    <param>
      <value><int>1</int></value>
    </param>
  </params>
</methodCall>
'''


class XMLRPCTests(unittest.TestCase):
    """The only thing different to HTTP is the input processing; so there
       is no need to redo all the HTTP tests again.
    """

    _testEnv = {
        'PATH_INFO': '/folder/item2/view/',
        'QUERY_STRING': '',
        'SERVER_URL': 'http://foobar.com',
        'HTTP_HOST': 'foobar.com',
        'CONTENT_LENGTH': '0',
        'REQUEST_METHOD': 'POST',
        'HTTP_AUTHORIZATION': 'Should be in accessible',
        'GATEWAY_INTERFACE': 'TestFooInterface/1.0',
        'HTTP_OFF_THE_WALL': "Spam 'n eggs",
        'HTTP_ACCEPT_CHARSET': 'ISO-8859-1, UTF-8;q=0.66, UTF-16;q=0.33',
    }

    def setUp(self):
        super().setUp()

        class AppRoot:
            pass

        class Folder:
            pass

        class Item:

            def __call__(self, a, b):
                return f"{a!r}, {b!r}"

            def doit(self, a, b):
                return f'do something {a} {b}'

        class View:

            def action(self, a):
                return "Parameter[type: {}; value: {}".format(
                    type(a).__name__, repr(a))

        class Item2:
            view = View()

        self.app = AppRoot()
        self.app.folder = Folder()
        self.app.folder.item = Item()
        self.app.folder.item2 = Item2()

    def _createRequest(self, extra_env={}, body=""):
        env = self._testEnv.copy()
        env.update(extra_env)
        if len(body):
            env['CONTENT_LENGTH'] = str(len(body))

        publication = Publication(self.app)
        instream = BytesIO(body)
        request = TestXMLRPCRequest(instream, env)
        request.setPublication(publication)
        return request

    def testProcessInput(self):
        req = self._createRequest({}, xmlrpc_call)
        req.processInputs()
        self.assertEqual(req.getPositionalArguments(), (1,))
        self.assertEqual(tuple(req._path_suffix), ('action',))

    def testTraversal(self):
        req = self._createRequest({}, xmlrpc_call)
        req.processInputs()
        action = req.traverse(self.app)
        self.assertEqual(action(*req.getPositionalArguments()),
                         "Parameter[type: int; value: 1")


def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(XMLRPCTests)
