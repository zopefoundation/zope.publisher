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
"""

Revision information:
$Id: browser.py,v 1.2 2002/12/25 14:15:18 jim Exp $
"""

from zope.interface import Interface
from zope.interface import Attribute

from zope.component.interfaces import IPresentation
from zope.component.interfaces import IResource
from zope.component.interfaces import IView

from zope.publisher.interfaces import IPublication
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces.http import IHTTPApplicationRequest
from zope.publisher.interfaces.http import IHTTPRequest


class IBrowserPresentation(IPresentation):
    """Browser presentations are for interaction with user's using Web Browsers
    """


class IBrowserApplicationRequest(IHTTPApplicationRequest):
    """Browser-specific requests
    """

    def __getitem__(key):
        """Return Browser request data

        Request data sre retrieved from one of:

        - Environment variables

          These variables include input headers, server data, and other
          request-related data.  The variable names are as <a
          href="http://hoohoo.ncsa.uiuc.edu/cgi/env.html">specified</a>
          in the <a
          href="http://hoohoo.ncsa.uiuc.edu/cgi/interface.html">CGI
          specification</a>

        - Cookies

          These are the cookie data, if present.

        - Form data

        Form data are searched before cookies, which are searched
        before environmental data.
        """

    form = Attribute(
        """Form data

        This is a read-only mapping from name to form value for the name.
        """)


class IBrowserResource(IBrowserPresentation, IResource):
    """Browser View
    """

    def __call__():
        """Return a URL for getting the resource

        This URL should not be context dependent. Typically, the URL
        will be based on the service that defined the resource.
        """


class IBrowserPublication(IPublication):
    """Object publication framework.
    """

    def getDefaultTraversal(request, ob):
        """Get the default published object for the request

        Allows a default view to be added to traversal.
        Returns (ob, steps_reversed).
        """


class IVirtualHostRequest(Interface):
    """The support for virtual hosts in Zope is very important.

    In order to make virtual hosts working, we need to support several
    methods in our Request object. This interface defines the required
    methods.
    """

    def setVirtualRoot(path, hard=0):
        """Treat the current publishing object as a VirtualRoot.
        """


    def convertPhysicalPathToVirtualPath(path):
        """Remove the path to the VirtualRoot from a physical path.
        """


    def convertPhysicalPathToURL(path, relative=0):
        """Convert a physical path into a URL in the current context.
        """


    def getPhysicalPathFromURL(URL):
        """Convert a URL into a physical path in the current context.

        If the URL makes no sense in light of the current virtual
        hosting context, a ValueError is raised.
        """

    def getEffectiveURL(self):
        """Return the effective URL.
        """


class IBrowserRequest(IHTTPRequest, IVirtualHostRequest):
    """Browser-specific Request functionality.

    Note that the browser is special in many ways, since it exposes
    the Request object to the end-developer.
    """


class IBrowserPublisher(IPublishTraverse):

    def browserDefault(request):
        """Provide the default object

        The default object is expressed as a (possibly different)
        object and/or additional traversal steps.

        Returns an object and a sequence of names.  If the sequence of
        names is not empty, then a traversal step is made for each name.
        After the publisher gets to the end of the sequence, it will
        call browserDefault on the last traversed object.

        Normal usage is to return self for object and a default view name.

        The publisher calls this method at the end of each traversal path. If
        a non-empty sequence of names is returned, the publisher will traverse
        those names and call browserDefault again at the end.

        Note that if additional traversal steps are indicated (via a
        nonempty sequence of names), then the publisher will try to adjust
        the base href.
        """


class IBrowserView(IBrowserPresentation, IView):
    "Browser View"
