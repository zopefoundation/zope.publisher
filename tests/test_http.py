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

from zope.publisher.http import HTTPRequest

from zope.publisher.publish import publish
from zope.publisher.base import DefaultPublication
from zope.publisher.interfaces.http import IHTTPPresentation, IHTTPRequest

from zope.i18n.interfaces import ILocale

from zope.interface.verify import verifyObject

from StringIO import StringIO


class HTTPTests(unittest.TestCase):

    _testEnv =  {
        'PATH_INFO':          '/folder/item',
        'a':                  '5',
        'b':                  6,
        'SERVER_URL':         'http://foobar.com',
        'HTTP_HOST':          'foobar.com',
        'CONTENT_LENGTH':     '0',
        'HTTP_AUTHORIZATION': 'Should be in accessible',
        'GATEWAY_INTERFACE':  'TestFooInterface/1.0',
        'HTTP_OFF_THE_WALL':  "Spam 'n eggs",
        'HTTP_ACCEPT_CHARSET': 'ISO-8859-1, UTF-8;q=0.66, UTF-16;q=0.33',
    }

    def setUp(self):
        class AppRoot:
            " "

        class Folder:
            " "

        class Item:
            " "
            def __call__(self, a, b):
                return "%s, %s" % (`a`, `b`)

        self.app = AppRoot()
        self.app.folder = Folder()
        self.app.folder.item = Item()

    def _createRequest(self, extra_env={}, body="", outstream=None):
        env = self._testEnv.copy()
        env.update(extra_env)
        if len(body):
            env['CONTENT_LENGTH'] = str(len(body))

        publication = DefaultPublication(self.app)
        if outstream is None:
            outstream = StringIO()
        instream = StringIO(body)
        request = HTTPRequest(instream, outstream, env)
        request.setPublication(publication)
        return request

    def _publisherResults(self, extra_env={}, body=""):
        outstream = StringIO()
        request = self._createRequest(extra_env, body, outstream=outstream)
        publish(request, handle_errors=0)
        return outstream.getvalue()

    def testTraversalToItem(self):
        res = self._publisherResults()
        self.failUnlessEqual(
            res,
            "Status: 200 Ok\r\n"
            "Content-Length: 6\r\n"
            "X-Powered-By: Zope (www.zope.org), Python (www.python.org)\r\n"
            "\r\n"
            "'5', 6")

    def testRequestEnvironment(self):
        req = self._createRequest()
        publish(req, handle_errors=0) # Force expansion of URL variables

        self.assertEquals(str(req.URL), 'http://foobar.com/folder/item')
        self.assertEquals(req.URL['-1'], 'http://foobar.com/folder')
        self.assertEquals(req.URL['-2'], 'http://foobar.com')
        self.assertRaises(KeyError, req.URL.__getitem__, '-3')

        self.assertEquals(req.URL['0'], 'http://foobar.com')
        self.assertEquals(req.URL['1'], 'http://foobar.com/folder')
        self.assertEquals(req.URL['2'], 'http://foobar.com/folder/item')
        self.assertRaises(KeyError, req.URL.__getitem__, '3')

        self.assertEquals(req['SERVER_URL'], 'http://foobar.com')
        self.assertEquals(req['HTTP_HOST'], 'foobar.com')
        self.assertEquals(req['PATH_INFO'], '/folder/item')
        self.assertEquals(req['CONTENT_LENGTH'], '0')
        self.assertRaises(KeyError, req.__getitem__, 'HTTP_AUTHORIZATION')
        self.assertEquals(req['GATEWAY_INTERFACE'], 'TestFooInterface/1.0')
        self.assertEquals(req['HTTP_OFF_THE_WALL'], "Spam 'n eggs")

        self.assertRaises(KeyError, req.__getitem__,
                          'HTTP_WE_DID_NOT_PROVIDE_THIS')

    def testRequestLocale(self):
        eq = self.assertEqual
        unless = self.failUnless
        for httplang in ('it', 'it-ch', 'it-CH', 'IT', 'IT-CH', 'IT-ch'):
            req = self._createRequest({'HTTP_ACCEPT_LANGUAGE': httplang})
            locale = req.locale
            unless(ILocale.isImplementedBy(locale))
            parts = httplang.split('-')
            lang = parts.pop(0).lower()
            country = variant = None
            if parts:
                country = parts.pop(0).upper()
            if parts:
                variant = parts.pop(0).upper()
            eq(locale.id.language, lang)
            eq(locale.id.country, country)
            eq(locale.id.variant, variant)
        # Now test for non-existant locale fallback
        req = self._createRequest({'HTTP_ACCEPT_LANGUAGE': 'xx'})
        locale = req.locale
        unless(ILocale.isImplementedBy(locale))
        eq(locale.id.language, None)
        eq(locale.id.country, None)
        eq(locale.id.variant, None)

        # If the first language is not available we should try others
        req = self._createRequest({'HTTP_ACCEPT_LANGUAGE': 'xx,en;q=0.5'})
        locale = req.locale
        unless(ILocale.isImplementedBy(locale))
        eq(locale.id.language, 'en')
        eq(locale.id.country, None)
        eq(locale.id.variant, None)

        # Regression test: there was a bug where country and variant were
        # not reset
        req = self._createRequest({'HTTP_ACCEPT_LANGUAGE': 'xx-YY,en;q=0.5'})
        locale = req.locale
        unless(ILocale.isImplementedBy(locale))
        eq(locale.id.language, 'en')
        eq(locale.id.country, None)
        eq(locale.id.variant, None)

    def testCookies(self):
        cookies = {
            'HTTP_COOKIE': 'foo=bar; spam="eggs", this="Should be accepted"'
        }
        req = self._createRequest(extra_env=cookies)

        self.assertEquals(req.cookies[u'foo'], u'bar')
        self.assertEquals(req[u'foo'], u'bar')

        self.assertEquals(req.cookies[u'spam'], u'eggs')
        self.assertEquals(req[u'spam'], u'eggs')

        self.assertEquals(req.cookies[u'this'], u'Should be accepted')
        self.assertEquals(req[u'this'], u'Should be accepted')

    def testHeaders(self):
        headers = {
            'TEST_HEADER': 'test',
            'Another-Test': 'another',
        }
        req = self._createRequest(extra_env=headers)
        self.assertEquals(req.headers[u'TEST_HEADER'], u'test')
        self.assertEquals(req.headers[u'TEST-HEADER'], u'test')
        self.assertEquals(req.headers[u'test_header'], u'test')
        self.assertEquals(req.getHeader('TEST_HEADER', literal=True), u'test')
        self.assertEquals(req.getHeader('TEST-HEADER', literal=True), None)
        self.assertEquals(req.getHeader('test_header', literal=True), None)
        self.assertEquals(req.getHeader('Another-Test', literal=True), 'another')

    def testBasicAuth(self):
        from zope.publisher.interfaces.http import IHTTPCredentials
        import base64
        req = self._createRequest()
        verifyObject(IHTTPCredentials, req)
        lpq = req._authUserPW()
        self.assertEquals(lpq, None)
        env = {}
        login, password = ("tim", "123")
        s = base64.encodestring("%s:%s" % (login, password)).rstrip()
        env['HTTP_AUTHORIZATION'] = "Basic %s" % s
        req = self._createRequest(env)
        lpw = req._authUserPW()
        self.assertEquals(lpw, (login, password))

    def testIPresentationRequest(self):
        # test the IView request
        r = self._createRequest()

        self.assertEquals(r.getPresentationType(), IHTTPPresentation)
        self.assertEqual(r.getPresentationSkin(), '')
        r.setViewSkin('morefoo')
        self.assertEqual(r.getPresentationSkin(), 'morefoo')

    def test_method(self):
        r = self._createRequest(extra_env={'REQUEST_METHOD':'SPAM'})
        self.assertEqual(r.method, 'SPAM')
        r = self._createRequest(extra_env={'REQUEST_METHOD':'eggs'})
        self.assertEqual(r.method, 'EGGS')

    def test_setApplicationServer(self):
        req = self._createRequest()
        req.setApplicationServer('foo')
        self.assertEquals(req._app_server, 'http://foo')
        req.setApplicationServer('foo', proto='https')
        self.assertEquals(req._app_server, 'https://foo')
        req.setApplicationServer('foo', proto='https', port=8080)
        self.assertEquals(req._app_server, 'https://foo:8080')
        req.setApplicationServer('foo', proto='http', port='9673')
        self.assertEquals(req._app_server, 'http://foo:9673')
        req.setApplicationServer('foo', proto='https', port=443)
        self.assertEquals(req._app_server, 'https://foo')
        req.setApplicationServer('foo', proto='https', port='443')
        self.assertEquals(req._app_server, 'https://foo')
        req.setApplicationServer('foo', port=80)
        self.assertEquals(req._app_server, 'http://foo')
        req.setApplicationServer('foo', proto='telnet', port=80)
        self.assertEquals(req._app_server, 'telnet://foo:80')

    def test_setApplicationNames(self):
        req = self._createRequest()
        names = ['x', 'y', 'z']
        req.setApplicationNames(names)
        self.assertEquals(req._app_names, ['x', 'y', 'z'])
        names[0] = 'muahahahaha'
        self.assertEquals(req._app_names, ['x', 'y', 'z'])

    def test_setVirtualHostRoot(self):
        req = self._createRequest()
        req._traversed_names = ['x', 'y']
        req.setVirtualHostRoot()
        self.assertEquals(req._vh_trunc, 3)

    def test_traverse(self):
        # setting _vh_trunc *before* traversal is a no-op
        req = self._createRequest()
        req._vh_trunc = 1
        req.traverse(self.app)
        self.assertEquals(req._traversed_names, ['folder', 'item'])

        # setting it during traversal matters
        req = self._createRequest()
        def hook(self, object, req=req):
            req._vh_trunc = 1
        req.publication.callTraversalHooks = hook
        req.traverse(self.app)
        self.assertEquals(req._traversed_names, ['item'])

    def testInterface(self):
        from zope.publisher.interfaces.http import IHTTPCredentials
        from zope.publisher.interfaces.http import IHTTPApplicationRequest
        rq = self._createRequest()
        verifyObject(IHTTPRequest, rq)
        verifyObject(IHTTPCredentials, rq)
        verifyObject(IHTTPApplicationRequest, rq)

    def testDeduceServerURL(self):
        req = self._createRequest()
        deduceServerURL = req._HTTPRequest__deduceServerURL
        req._environ = {'HTTP_HOST': 'example.com:80'}
        self.assertEquals(deduceServerURL(), 'http://example.com')
        req._environ = {'HTTP_HOST': 'example.com:8080'}
        self.assertEquals(deduceServerURL(), 'http://example.com:8080')
        req._environ = {'HTTP_HOST': 'example.com:443', 'HTTPS': 'on'}
        self.assertEquals(deduceServerURL(), 'https://example.com')
        req._environ = {'HTTP_HOST': 'example.com:80', 'HTTPS': 'ON'}
        self.assertEquals(deduceServerURL(), 'https://example.com:80')
        req._environ = {'HTTP_HOST': 'example.com:8080',
                        'SERVER_PORT_SECURE': '1'}
        self.assertEquals(deduceServerURL(), 'https://example.com:8080')
        req._environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT':'8080',
                        'SERVER_PORT_SECURE': '0'}
        self.assertEquals(deduceServerURL(), 'http://example.com:8080')
        req._environ = {'SERVER_NAME': 'example.com'}
        self.assertEquals(deduceServerURL(), 'http://example.com')


def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(HTTPTests)


if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
