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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""FTP Publisher

$Id$
"""
from zope.authentication.loginpassword import LoginPassword
from zope.component import adapts
from zope.interface import implements
from zope.publisher.interfaces.ftp import IFTPCredentials, IFTPRequest
from zope.publisher.base import BaseResponse, BaseRequest


class FTPResponse(BaseResponse):
    __slots__ = '_exc', # Saved exception

    def outputBody(self):
        # Nothing to do
        pass

    def getResult(self):
        if getattr(self, '_exc', None) is not None:
            raise self._exc[0], self._exc[1], self._exc[2]
        return self._result

    def handleException(self, exc_info):
        self._exc = exc_info


class FTPRequest(BaseRequest):
    implements(IFTPCredentials, IFTPRequest)

    __slots__ = '_auth'

    def __init__(self, body_instream, environ, response=None):
        self._auth = environ.get('credentials')

        del environ['credentials']

        super(FTPRequest, self).__init__(body_instream, environ, response)

        path = environ['path']
        if path.startswith('/'):
            path = path[1:]
        if path:
            path = path.split('/')
            path.reverse()
            self.setTraversalStack(path)


    def _createResponse(self):
        """Create a specific FTP response object."""
        return FTPResponse()

    def _authUserPW(self):
        'See IFTPCredentials'
        return self._auth

    def unauthorized(self, challenge):
        'See IFTPCredentials'


class FTPAuth(LoginPassword):
    """ILoginPassword adapter for handling common FTP authentication."""

    # This was moved from zope.app.security as a part of refactoring process,
    # see http://mail.zope.org/pipermail/zope-dev/2009-March/035325.html for
    # the reasoning.

    adapts(IFTPCredentials)

    def __init__(self, request):
        self.__request = request
        lpw = request._authUserPW()
        if lpw is None:
            login, password = None, None
        else:
            login, password = lpw
        super(FTPAuth, self).__init__(login, password)

    def needLogin(self, realm):
        self.__request.unauthorized("Did not work")
