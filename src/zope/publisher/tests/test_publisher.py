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
"""Test Publisher

$Id$
"""
import unittest

from zope import component
from zope.publisher.publish import publish
from zope.publisher.base import TestRequest
from zope.publisher.base import DefaultPublication
from zope.publisher.interfaces import Unauthorized, NotFound, DebugError
from zope.publisher.interfaces import IPublication, IReRaiseException

from zope.interface.verify import verifyClass
from zope.interface import implementedBy, Interface

from StringIO import StringIO


class PublisherTests(unittest.TestCase):
    def setUp(self):
        class AppRoot(object):
            """Required docstring for the publisher."""

        class Folder(object):
            """Required docstring for the publisher."""

        class Item(object):
            """Required docstring for the publisher."""
            def __call__(self):
                return "item"

        class NoDocstringItem:
            def __call__(self):
                return "Yo! No docstring!"

        self.app = AppRoot()
        self.app.folder = Folder()
        self.app.folder.item = Item()

        self.app._item = Item()
        self.app.noDocString = NoDocstringItem()

    def _createRequest(self, path, **kw):
        publication = DefaultPublication(self.app)
        path = path.split('/')
        path.reverse()
        request = TestRequest(StringIO(''), **kw)
        request.setTraversalStack(path)
        request.setPublication(publication)
        return request

    def _publisherResults(self, path, **kw):
        request = self._createRequest(path, **kw)
        response = request.response
        publish(request, handle_errors=False)
        return response._result

    def _registerExcAdapter(self, factory):
        component.provideAdapter(factory, (Unauthorized,), IReRaiseException)

    def _unregisterExcAdapter(self, factory):
        gsm = component.getGlobalSiteManager()
        gsm.unregisterAdapter(
            factory=factory, required=(Unauthorized,),
            provided=IReRaiseException)

    def testImplementsIPublication(self):
        self.failUnless(IPublication.providedBy(
                            DefaultPublication(self.app)))

    def testInterfacesVerify(self):
        for interface in implementedBy(DefaultPublication):
            verifyClass(interface, DefaultPublication)

    def testTraversalToItem(self):
        res = self._publisherResults('/folder/item')
        self.failUnlessEqual(res, 'item')
        res = self._publisherResults('/folder/item/')
        self.failUnlessEqual(res, 'item')
        res = self._publisherResults('folder/item')
        self.failUnlessEqual(res, 'item')

    def testUnderscoreUnauthorizedException(self):
        self.assertRaises(Unauthorized, self._publisherResults, '/_item')

    def testNotFoundException(self):
        self.assertRaises(NotFound, self._publisherResults, '/foo')

    def testDebugError(self):
        self.assertRaises(DebugError, self._publisherResults, '/noDocString')

    def testIReRaiseExceptionAdapters(self):

        def dontReRaiseAdapter(context):
            def shouldBeReRaised():
                return False
            return shouldBeReRaised

        self._registerExcAdapter(dontReRaiseAdapter)
        try:
            self._publisherResults('/_item')
        except Unauthorized:
            raise self.fail('Unauthorized raised though this should '
                            'not happen')
        finally:
            self._unregisterExcAdapter(dontReRaiseAdapter)

        def doReRaiseAdapter(context):
            def shouldBeReRaised():
                return True
            return shouldBeReRaised

        self._registerExcAdapter(doReRaiseAdapter)
        self.failUnlessRaises(Unauthorized, self._publisherResults, '/_item')
        self._unregisterExcAdapter(doReRaiseAdapter)
            
def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(PublisherTests)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
