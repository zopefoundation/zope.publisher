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

$Id: vfs.py,v 1.3 2002/12/27 16:40:25 k_vertigo Exp $
"""

import datetime

from zope.component import queryAdapter
from zope.publisher.interfaces.vfs import IVFSFilePublisher
from zope.publisher.interfaces.vfs import IVFSView
from zope.publisher.interfaces.vfs import IVFSCredentials
from zope.app.interfaces.dublincore import IZopeDublinCore
from zope.publisher.base import BaseResponse, BaseRequest

zerotime = datetime.datetime.fromtimestamp(0)

__metaclass__ = type # All classes are new style when run with Python 2.2+


class VFSResponse(BaseResponse):
    """VFS response
    """
    __slots__ = (
        '_exc',
        )

    def setBody(self, body):
        """Sets the body of the response

           It is very important to note that in this case the body may
           not be just a astring, but any Python object.
        """

        self._body = body


    def outputBody(self):
        'See IPublisherResponse'
        pass


    def getResult(self):
        if getattr(self, '_exc', None) is not None:
            raise self._exc[0], self._exc[1]
        return self._getBody()


    def handleException(self, exc_info):
        self._exc = exc_info[:2]
        # import traceback
        # traceback.print_exc()

class VFSRequest(BaseRequest):

    __implements__ = BaseRequest.__implements__, IVFSCredentials

    # _presentation_type is overridden from the BaseRequest
    # to implement IVFSView
    _presentation_type = IVFSView


    def __init__(self, body_instream, outstream, environ, response=None):
        """ """
        super(VFSRequest, self).__init__(
            body_instream, outstream, environ, response)

        self._environ = environ
        self.method = ''
        self.__setupPath()


    def _createResponse(self, outstream):
        """Create a specific XML-RPC response object."""
        return VFSResponse(outstream)

    def _authUserPW(self):
        'See IVFSCredentials'
        # XXX This is wrong.  Instead of _authUserPW() there should
        # be a method of all requests called getCredentials() which
        # returns an ICredentials instance.
        credentials = self._environ['credentials']
        return credentials.getUserName(), credentials.getPassword()

    def unauthorized(self, challenge):
        'See IVFSCredentials'
        pass

    def processInputs(self):
        'See IPublisherRequest'

        if 'command' in self._environ:
            self.method = self._environ['command']

    def __setupPath(self):
        self._setupPath_helper("path")

    def __repr__(self):
        # Returns a *short* string.
        return '<%s instance at 0x%x, path=%s>' % (
            str(self.__class__), id(self), '/'.join(self._traversal_stack))


class VFSView:

    __implements__ = IVFSView

    def __init__(self, context, request):
        self.context = context
        self.request = request


class VFSFileView(VFSView):
    """Abstract class providing the infrastructure for a basic VFS view
    for basic file-like content object."""

    __implements__ = IVFSFilePublisher, VFSView.__implements__


    # These methods need to be implmented by the real view class

    def _setData(self, data):
        raise NotImplemented

    def _getData(self):
        raise NotImplemented

    def _getSize(self):
        return len(self._getData())

    def read(self, mode, outstream, start = 0, end = -1):
        """See IVFSFilePublisher"""

        data = self._getData()
        try:
            if end != -1: data = data[:end]
            if start != 0: data = data[start:]
        except TypeError:
            pass
        outstream.write(data)


    def write(self, mode, instream, start = 0):
        """See IVFSFilePublisher"""
        try:
            instream.seek(start)
        except:
            pass
        self._setData(instream.read())


    def check_writable(self, mode):
        """See IVFSFilePublisher"""
        return 1

    def isdir(self):
        """See IVFSObjectPublisher"""
        return 0


    def isfile(self):
        """See IVFSObjectPublisher"""
        return 1


    def stat(self):
        """See IVFSObjectPublisher"""
        dc = queryAdapter(self, IZopeDublinCore)
        if dc is not None:
            modified = dc.modified
            created = dc.created
        else:
            created = zerotime
            modified = zerotime

        if created is None:
            created = zerotime

        if modified is None:
            modified = created

        size = self._getSize()
        uid = "nouser"
        gid = "nogroup"
        return (504, 0, 0, 0, uid, gid, size, modified, modified, created)


    def publishTraverse(self, request, name):
        """See IVFSPublisher"""
        # Traversing always stops here.
        return None
