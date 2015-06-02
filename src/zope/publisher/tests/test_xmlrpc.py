##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
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
"""Testing the XML-RPC Publisher code.
"""
import sys
import doctest
import zope.component.testing
from zope.publisher import xmlrpc
from zope.security.checker import defineChecker, Checker, CheckerPublic

if sys.version_info[0] == 2:
    import xmlrpclib
else:
    import xmlrpc.client as xmlrpclib

def setUp(test):
    zope.component.testing.setUp(test)
    zope.component.provideAdapter(xmlrpc.ListPreMarshaller)
    zope.component.provideAdapter(xmlrpc.TuplePreMarshaller)
    zope.component.provideAdapter(xmlrpc.BinaryPreMarshaller)
    zope.component.provideAdapter(xmlrpc.FaultPreMarshaller)
    zope.component.provideAdapter(xmlrpc.DateTimePreMarshaller)
    zope.component.provideAdapter(xmlrpc.PythonDateTimePreMarshaller)
    zope.component.provideAdapter(xmlrpc.DictPreMarshaller)

    defineChecker(xmlrpclib.Binary,
                  Checker({'data':CheckerPublic,
                           'decode':CheckerPublic,
                           'encode': CheckerPublic}, {}))
    defineChecker(xmlrpclib.Fault,
                  Checker({'faultCode':CheckerPublic,
                           'faultString': CheckerPublic}, {}))
    defineChecker(xmlrpclib.DateTime,
                  Checker({'value':CheckerPublic}, {}))

def test_suite():
    return doctest.DocFileSuite(
        "xmlrpc.txt", package="zope.publisher",
        setUp=setUp, tearDown=zope.component.testing.tearDown,
        optionflags=doctest.ELLIPSIS
        )

# Proper zope.component/zope.interface support requires PyPy 2.5.1+.
# Older versions fail to hash types correctly. This manifests itself here
# as being unable to find the marshlers registered as adapters for types
# like 'list' and 'dict'. As of Jun 1 2015, Travis CI is still using PyPy 2.5.0.
# All we can do is skip the test.
if hasattr(sys, 'pypy_version_info') and sys.pypy_version_info[:3] == (2,5,0):
    import unittest
    def test_suite():
        return unittest.TestSuite(())
