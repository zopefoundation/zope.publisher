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
"""FTP Authentication Test

$Id$
"""
from unittest import TestCase, TestSuite, main, makeSuite
from zope.publisher.interfaces.ftp import IFTPCredentials
from zope.interface import implements

from zope.publisher.ftp import FTPAuth

class FTPCredentials(object):
    __doc__ = IFTPCredentials.__doc__

    implements(IFTPCredentials)

    def __init__(self, credentials):
        self.credentials = credentials

    def _authUserPW(self):
        return self.credentials

    unauth = 0
    def unauthorized(self, challenge):
        self.unauth += 1


class Test(TestCase):

    def test(self):
        request = FTPCredentials(('bob', '123'))
        auth = FTPAuth(request)
        self.assertEqual(auth.getLogin(), 'bob')
        self.assertEqual(auth.getPassword(), '123')

        unauth = request.unauth
        auth.needLogin('xxx')
        self.assertEqual(request.unauth, unauth+1)

        request = FTPCredentials(None)
        auth = FTPAuth(request)
        self.assertEqual(auth.getLogin(), None)
        self.assertEqual(auth.getPassword(), None)

def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
