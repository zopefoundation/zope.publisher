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

Revision information: $Id: views.py,v 1.2 2002/12/25 14:15:19 jim Exp $
"""

from zope.interface import Interface
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces.browser import IBrowserPresentation

class IC(Interface): pass

class V1(BrowserView): pass

class VZMI(V1): pass

class R1:
    __implements__ = IBrowserPresentation
    def __init__(self, request): self.request = request

class RZMI(R1):
    pass
