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

from zope.component.tests.placelesssetup import PlacelessSetup
from zope.component.adapter import provideAdapter

from zope.i18n.interfaces import IUserPreferredCharsets

from zope.publisher.http import IHTTPRequest
from zope.publisher.http import HTTPCharsets
from zope.publisher.browser import BrowserRequest
from zope.publisher.interfaces import NotFound

from zope.publisher.base import DefaultPublication
from zope.publisher.interfaces.browser \
    import IBrowserPresentation, IBrowserRequest, IBrowserApplicationRequest
from zope.interface.verify import verifyObject

from StringIO import StringIO

from zope.publisher.tests.test_http import HTTPTests

from zope.publisher.publish import publish as publish_
def publish(request):
    publish_(request, handle_errors=0)

class Publication(DefaultPublication):

    def getDefaultTraversal(self, request, ob):
        if hasattr(ob, 'browserDefault'):
            return ob.browserDefault(request)
        return ob, ()



class BrowserTests(HTTPTests, PlacelessSetup):

    _testEnv =  {
        'PATH_INFO':           '/folder/item',
        'QUERY_STRING':        'a=5&b:int=6',
        'SERVER_URL':          'http://foobar.com',
        'HTTP_HOST':           'foobar.com',
        'CONTENT_LENGTH':      '0',
        'HTTP_AUTHORIZATION':  'Should be in accessible',
        'GATEWAY_INTERFACE':   'TestFooInterface/1.0',
        'HTTP_OFF_THE_WALL':   "Spam 'n eggs",
        'HTTP_ACCEPT_CHARSET': 'ISO-8859-1, UTF-8;q=0.66, UTF-16;q=0.33',
    }

    def setUp(self):
        PlacelessSetup.setUp(self)
        provideAdapter(IHTTPRequest, IUserPreferredCharsets, HTTPCharsets)

        class AppRoot:
            " "

        class Folder:
            " "

        class Item:
            " "
            def __call__(self, a, b):
                return "%s, %s" % (`a`, `b`)

        class Item3:
            " "
            def __call__(self, *args):
                return "..."

        class View:
            " "
            def browserDefault(self, request):
                return self, ['index']

            def index(self, a, b):
                " "
                return "%s, %s" % (`a`, `b`)

        class Item2:
            " "
            view = View()

            def browserDefault(self, request):
                return self, ['view']


        self.app = AppRoot()
        self.app.folder = Folder()
        self.app.folder.item = Item()
        self.app.folder.item2 = Item2()
        self.app.folder.item3 = Item3()

    def _createRequest(self, extra_env={}, body="", outstream=None):
        env = self._testEnv.copy()
        env.update(extra_env)
        if len(body):
            env['CONTENT_LENGTH'] = str(len(body))

        publication = Publication(self.app)
        if outstream is None:
            outstream = StringIO()
        instream = StringIO(body)
        request = BrowserRequest(instream, outstream, env)
        request.setPublication(publication)
        return request

    def testTraversalToItem(self):
        res = self._publisherResults()
        self.failUnlessEqual(
            res,
            "Status: 200 Ok\r\n"
            "Content-Length: 7\r\n"
            "Content-Type: text/plain;charset=utf-8\r\n"
            "X-Powered-By: Zope (www.zope.org), Python (www.python.org)\r\n"
            "\r\n"
            "u'5', 6")

    def testIPresentationRequest(self):
        # test the IView request
        r = self._createRequest()

        self.failUnless(r.getPresentationType() is IBrowserPresentation)
        self.assertEqual(r.getPresentationSkin(), '')
        r.setPresentationSkin('morefoo')
        self.assertEqual(r.getPresentationSkin(), 'morefoo')

    def testNoDefault(self):
        request = self._createRequest()
        response = request.response
        publish(request)
        self.failIf(response.getBase())

    def testDefault(self):
        extra = {'PATH_INFO': '/folder/item2'}
        request = self._createRequest(extra)
        response = request.response
        publish(request)
        self.assertEqual(response.getBase(),
                         'http://foobar.com/folder/item2/view/index')

    def testDefaultPOST(self):
        extra = {'PATH_INFO': '/folder/item2', "REQUEST_METHOD": "POST"}
        request = self._createRequest(extra, body='a=5&b:int=6')
        response = request.response
        publish(request)
        self.assertEqual(response.getBase(),
                         'http://foobar.com/folder/item2/view/index')

    def testDefault2(self):
        extra = {'PATH_INFO': '/folder/item2/view'}
        request = self._createRequest(extra)
        response = request.response
        publish(request)
        self.assertEqual(response.getBase(),
                         'http://foobar.com/folder/item2/view/index')

    def testDefault3(self):
        extra = {'PATH_INFO': '/folder/item2/view/index'}
        request = self._createRequest(extra)
        response = request.response
        publish(request)
        self.failIf(response.getBase())

    def testDefault4(self):
        extra = {'PATH_INFO': '/folder/item2/view/'}
        request = self._createRequest(extra)
        response = request.response
        publish(request)
        self.failIf(response.getBase())

    def testDefault6(self):
        extra = {'PATH_INFO': '/folder/item2/'}
        request = self._createRequest(extra)
        response = request.response
        publish(request)
        self.assertEqual(response.getBase(),
                         'http://foobar.com/folder/item2/view/index')

    def testBadPath(self):
        extra = {'PATH_INFO': '/folder/nothere/'}
        request = self._createRequest(extra)
        self.assertRaises(NotFound, publish, request)

    def testBadPath2(self):
        extra = {'PATH_INFO': '/folder%2Fitem2/'}
        request = self._createRequest(extra)
        self.assertRaises(NotFound, publish, request)

    def testForm(self):
        request = self._createRequest()
        publish(request)
        self.assertEqual(request.form,
                         {u'a':u'5', u'b':6})

    def testFormListTypes(self):
        #extra = {'QUERY_STRING':'x.a:list:record=5&x.a:list:record=6'}
        extra = {'QUERY_STRING':'a:list=5&a:list=6&b=1'}
        request = self._createRequest(extra)
        publish(request)
        self.assertEqual(request.form, {u'a':[u'5',u'6'], u'b':u'1'})

    def testFormListRecordTypes(self):
        extra = {'QUERY_STRING':'a.x:list:record=5&a.x:list:record=6&b=1'}
        request = self._createRequest(extra)
        publish(request)
        keys = request.form.keys()
        keys.sort()
        self.assertEqual(keys, [u'a',u'b'])
        self.assertEqual(request.form[u'b'], u'1')
        self.assertEqual(request.form[u'a'].keys(), [u'x'])
        self.assertEqual(request.form[u'a'][u'x'], [u'5',u'6'])
        self.assertEqual(str(request.form[u'a']), "x: [u'5', u'6']")
        self.assertEqual(repr(request.form[u'a']), "x: [u'5', u'6']")

    def testFormListTypes2(self):
        extra = {'QUERY_STRING':'a=5&a=6&b=1'}
        request = self._createRequest(extra)
        publish(request)
        self.assertEqual(request.form, {'a':[u'5',u'6'], 'b':u'1'})

    def testFormDefaults(self):
        extra = {'QUERY_STRING':'a:default=10&a=6&b=1'}
        request = self._createRequest(extra)
        publish(request)
        self.assertEqual(request.form, {u'a':u'6', u'b':u'1'})

    def testFormDefaults2(self):
        extra = {'QUERY_STRING':'a:default=10&b=1'}
        request = self._createRequest(extra)
        publish(request)
        self.assertEqual(request.form, {u'a':u'10', u'b':u'1'})

    def testFormFieldName(self):
        extra = {'QUERY_STRING':'c+%2B%2F%3D%26c%3Aint=6',
                 'PATH_INFO': '/folder/item3/'}
        request = self._createRequest(extra)
        publish(request)
        self.assertEqual(request.form, {u'c +/=&c': 6})

    def testFormFieldValue(self):
        extra = {'QUERY_STRING':'a=b+%2B%2F%3D%26b%3Aint',
                 'PATH_INFO': '/folder/item3/'}
        request = self._createRequest(extra)
        publish(request)
        self.assertEqual(request.form, {u'a':u'b +/=&b:int'})

    def testInterface(self):
        request = self._createRequest()
        verifyObject(IBrowserRequest, request)
        verifyObject(IBrowserApplicationRequest, request)

def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(BrowserTests)


if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
