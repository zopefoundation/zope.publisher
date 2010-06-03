##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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
"""Adapter:

Adapts zope.security.interfaces.IPrincipal to
zope.publisher.interfaces.logginginfo.ILoggingInfo.
"""
from zope.component import adapts
from zope.interface import implements
from zope.publisher.interfaces.logginginfo import ILoggingInfo
from zope.security.interfaces import IPrincipal


class PrincipalLogging(object):

    adapts(IPrincipal)
    implements(ILoggingInfo)

    def __init__(self, principal):
        self.principal = principal

    def getLogMessage(self):
        return self.principal.id.encode('ascii', 'backslashreplace')
