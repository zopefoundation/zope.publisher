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

Revision information: $Id: views.py,v 1.4 2003/11/21 17:12:41 jim Exp $
"""

from zope.interface import Interface, implements
from zope.publisher.browser import BrowserView

class IC(Interface): pass

class V1(BrowserView): pass

class VZMI(V1): pass

class R1:
    def __init__(self, request): self.request = request

class RZMI(R1):
    pass
