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
import unittest

from zope.publisher.xmlrpc import MethodPublisher, TestRequest
from zope.publisher.interfaces.xmlrpc import IXMLRPCPublisher

from zope.interface.verify import verifyClass
from zope.interface import implementedBy

class ContentStub:
    pass

class Presentation(MethodPublisher):
    index = 'index'
    action = 'action'
    foo = 'foo'


class TestMethodPublisher(unittest.TestCase):
    def setUp(self):
        self.pres = Presentation(ContentStub(), TestRequest())

    def testImplementsIXMLRPCPublisher(self):
        self.failUnless(IXMLRPCPublisher.providedBy(self.pres))

    def testInterfacesVerify(self):
        for interface in implementedBy(Presentation):
            verifyClass(interface, Presentation)

    def testXMLRPCTraverseIndex(self):
        self.assertEquals(self.pres.publishTraverse(None, 'index'), 'index')

    def testXMLRPCTraverseAction(self):
        self.assertEquals(self.pres.publishTraverse(None, 'action'), 'action')

    def testXMLRPCTraverseNotFound(self):
        self.failUnlessRaises(AttributeError, self.pres.publishTraverse,
            None, 'bar')


def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestMethodPublisher)

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
