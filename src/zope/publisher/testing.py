#############################################################################
#
# Copyright (c) 2011 Zope Foundation and Contributors.
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

import sys
import re
import contextlib
import zope.publisher.browser
import zope.security.management
import zope.security.testing
from zope.testing import renormalizing

PY2 = sys.version_info[0] == 2

if PY2:
    _u = unicode
    import doctest
    rules = [(re.compile("b('.*?')"), r"\1"),
             (re.compile('b(".*?")'), r"\1"),
            ]
    output_checker = renormalizing.RENormalizing(rules)
else:
    _u = str
    rules = [(re.compile("u('.*?')"), r"\1"),
             (re.compile('u(".*?")'), r"\1"),
             (re.compile("b('.*?')"), r"\1"),
             (re.compile('b(".*?")'), r"\1"),
            ]
    output_checker = renormalizing.RENormalizing(rules)


# These are enhanced versions of the ones in zope.security.testing,
# they use a TestRequest instead of a TestParticipation.

def create_interaction(principal_id, **kw):
    principal = zope.security.testing.Principal(principal_id, **kw)
    request = zope.publisher.browser.TestRequest()
    request.setPrincipal(principal)
    zope.security.management.newInteraction(request)
    return principal


@contextlib.contextmanager
def interaction(principal_id, **kw):
    if zope.security.management.queryInteraction():
        # There already is an interaction. Great. Leave it alone.
        yield
    else:
        principal = create_interaction(principal_id, **kw)
        try:
            yield principal
        finally:
            zope.security.management.endInteraction()
