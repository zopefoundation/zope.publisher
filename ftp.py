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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""

$Id: ftp.py,v 1.1 2003/02/03 15:08:51 jim Exp $
"""

from zope.publisher.interfaces.ftp import IFTPView
from zope.publisher.interfaces.ftp import IFTPCredentials
from zope.publisher.base import BaseResponse, BaseRequest

class FTPResponse(BaseResponse):
    __slots__ = '_exc', # Saved exception

    def outputBody(self):
        # Nothing to do
        pass

    def getResult(self):
        if getattr(self, '_exc', None) is not None:
            raise self._exc[0], self._exc[1], self._exc[2]
        return self._getBody()

    def handleException(self, exc_info):
        self._exc = exc_info

class FTPRequest(BaseRequest):
    __implements__ = BaseRequest.__implements__, IFTPCredentials

    _presentation_type = IFTPView

    __slots__ = '_auth'

    def __init__(self, body_instream, outstream, environ, response=None):
        self._auth = environ.get('credentials')
        del environ['credentials']
         
        super(FTPRequest, self).__init__(
            body_instream, outstream, environ, response)

        path = environ['path']
        if path.startswith('/'):
            path = path[1:]
        if path:
            path = path.split('/')
            path.reverse()
            self.setTraversalStack(path)
        

    def _createResponse(self, outstream):
        """Create a specific XML-RPC response object."""
        return FTPResponse(outstream)

    def _authUserPW(self):
        'See IFTPCredentials'
        return self._auth

    def unauthorized(self, challenge):
        'See IFTPCredentials'

