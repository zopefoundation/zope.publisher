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
"""Virtual File System interfaces for the publisher.

$Id: vfs.py,v 1.2 2002/12/25 14:15:18 jim Exp $
"""

from zope.interface import Interface

from zope.component.interfaces import IPresentation
from zope.component.interfaces import IView

from zope.publisher.interfaces import IPublishTraverse


class IVFSCredentials(Interface):

    # XXX Eventually this will be a different method
    def _authUserPW():
        """Return (login, password) if there are basic credentials;
        return None if there aren't."""

    def unauthorized(challenge):
        """Cause a FTP-based unautorized error message"""


class IVFSPresentation(IPresentation):
    """VFS presentations"""


class IVFSView(IVFSPresentation, IView):
    "VFS View"


class IVFSPublisher(IPublishTraverse):
    """VFS Publisher"""


class IVFSObjectPublisher(IVFSPublisher):
    """ """

    def isdir():
        """Returns true, if the object is a container, namely implements
           IContainer. For all other cases it returns false.
        """

    def isfile():
        """Returns always the oposite of isdir() for the same reasons.
        """

    def stat():
        """This method should return the typical file stat information:
           (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime)
        """


class IVFSDirectoryPublisher(IVFSObjectPublisher):

    def exists(name):
        """Checks whether the name exists.
        """

    def listdir(with_stats=0, pattern='*'):
        """Returns a sequence of names ot (name, stat)
        """

    def mkdir(name, mode=0777):
        """Create a container with name in this object.
        """

    def remove(name):
        """Remove file with naem from this container.
        """

    def rmdir(name):
        """Remove the container name from this container.
        """

    def rename(old, new):
        """Rename an object from old name to new name.
        """

    def writefile(name, mode, instream, start=0):
        """Write a file to the container. If the object does not exist,
           inspect the content and the file name to create the right object
           type.
        """

    def check_writable(name):
        """Check whether we can write to a subobject.
        """


class IVFSFilePublisher(IVFSObjectPublisher):
    """This interface describes the necessary methods a VFS view has to
       implement in order to be used by teh VFS.
    """

    def read(mode, outstream, start=0, end=-1):
        """Read the content of this object.
        """

    def write(mode, instream, start=0):
        """Write data specified in instream to object.
        """
