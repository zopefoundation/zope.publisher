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
"""Interfaces for the XMLRPC publisher.

$Id: xmlrpc.py,v 1.2 2002/12/25 14:15:18 jim Exp $
"""

from zope.component.interfaces import IView

from zope.component.interfaces import IPresentation
from zope.publisher.interfaces import IPublication
from zope.publisher.interfaces import IPublishTraverse


class IXMLRPCPresentation(IPresentation):
    """XMLRPC presentations are for interaction with user's
    """


class IXMLRPCPublisher(IPublishTraverse):
    """XML-RPC Publisher"""


class IXMLRPCPublication (IPublication):
    """Object publication framework."""

    def getDefaultTraversal(request, ob):
        """Get the default published object for the request

        Allows a default view to be added to traversal.
        Returns (ob, steps_reversed).
        """


class IXMLRPCView(IXMLRPCPresentation, IView):
    "XMLRPC View"
