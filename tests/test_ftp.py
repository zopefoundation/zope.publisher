##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""FTP Publisher Tests

$Id$
"""
import sys
from cStringIO import StringIO
from unittest import TestCase, TestSuite, main, makeSuite
import zope.publisher.ftp

class Test(TestCase):

    def setUp(self):
        self.__input = StringIO('')
        self.__output = StringIO()
        env = {'credentials': ('bob', '123'),
               'path': '/a/b/c',
               'command': 'foo',
               }
        self.__request = zope.publisher.ftp.FTPRequest(
            self.__input, self.__output, env)

    def test_response(self):
        response = self.__request.response
        response.setBody(123.456)
        response.outputBody()
        self.assertEqual(response.getResult(), 123.456)
        self.failIf(self.__output.getvalue())

        try:
            raise ValueError('spam')
        except:
            info = sys.exc_info()
            response.handleException(info)

        try:
            response.getResult()
        except:
            self.assertEqual(sys.exc_info()[:2], info[:2])

    def test_request(self):
        self.assertEqual(self.__request.getTraversalStack(),
                         ['c', 'b', 'a'])
        self.assertEqual(self.__request._authUserPW(),
                         ('bob', '123'))



def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
