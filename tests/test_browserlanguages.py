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
import unittest

class Test(unittest.TestCase):

    def test(self):
        request = {'HTTP_ACCEPT_LANGUAGE': 'da, en-gb;q=0.8, en;q=0.7'}

        from zope.publisher.browser import BrowserLanguages

        browser_languages = BrowserLanguages(request)

        self.assertEqual(list(browser_languages.getPreferredLanguages()),
                         ['da', 'en-gb', 'en'])

    # XXX Add support for quality statements




def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
