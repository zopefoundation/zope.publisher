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

$Id: http.py,v 1.23 2003/04/25 10:36:38 ryzaja Exp $
"""

import re, time, random
from urllib import quote, splitport
from types import StringTypes, UnicodeType, ClassType
from cgi import escape

from zope.publisher.interfaces.http import IHTTPCredentials
from zope.publisher.interfaces.http import IHTTPRequest
from zope.publisher.interfaces.http import IHTTPApplicationRequest
from zope.publisher.interfaces.http import IHTTPPublisher
from zope.publisher.interfaces.http import IHTTPPresentation

from zope.publisher.interfaces import Redirect
from zope.publisher.interfaces.http import IHTTPResponse
from zope.publisher.interfaces.http import IHTTPApplicationResponse
from zope.i18n.interfaces import IUserPreferredCharsets
from zope.i18n.locales import locales, LoadLocaleError

from zope.component import queryAdapter
from zope.publisher.base import BaseRequest, BaseResponse
from zope.publisher.base \
     import RequestDataProperty, RequestDataMapper, RequestDataGetter


# Default Encoding
ENCODING = 'UTF-8'

class CookieMapper(RequestDataMapper):
    _mapname = '_cookies'

class HeaderGetter(RequestDataGetter):
    _gettrname = 'getHeader'

_marker = object()

base64 = None

def sane_environment(env):
    # return an environment mapping which has been cleaned of
    # funny business such as REDIRECT_ prefixes added by Apache
    # or HTTP_CGI_AUTHORIZATION hacks.
    dict={}
    for key, val in env.items():
        while key.startswith('REDIRECT_'):
            key=key[9:]
        dict[key]=val
    if 'HTTP_CGI_AUTHORIZATION' in dict:
        dict['HTTP_AUTHORIZATION']=dict['HTTP_CGI_AUTHORIZATION']
        try: del dict['HTTP_CGI_AUTHORIZATION']
        except: pass
    return dict


def parse_cookie(
    text,
    result=None,
    qparmre=re.compile(
    '([\x00- ]*([^\x00- ;,="]+)="([^"]*)"([\x00- ]*[;,])?[\x00- ]*)'),
    parmre=re.compile(
    '([\x00- ]*([^\x00- ;,="]+)=([^\x00- ;,"]*)([\x00- ]*[;,])?[\x00- ]*)'),
    ):

    if result is None: result={}
    already_have=result.has_key

    mo_q = qparmre.match(text)

    if mo_q:
        # Match quoted correct cookies

        l     = len(mo_q.group(1))
        name  = unicode(mo_q.group(2), ENCODING)
        value = unicode(mo_q.group(3), ENCODING)

    else:
        # Match evil MSIE cookies ;)

        mo_p = parmre.match(text)

        if mo_p:
            l     = len(mo_p.group(1))
            name  = unicode(mo_p.group(2), ENCODING)
            value = unicode(mo_p.group(3), ENCODING)

        else:
            return result

    if not already_have(name): result[name]=value

    return apply(parse_cookie,(text[l:],result))


# Possible HTTP status responses
status_reasons = {
100: 'Continue',
101: 'Switching Protocols',
102: 'Processing',
200: 'OK',
201: 'Created',
202: 'Accepted',
203: 'Non-Authoritative Information',
204: 'No Content',
205: 'Reset Content',
206: 'Partial Content',
207: 'Multi-Status',
300: 'Multiple Choices',
301: 'Moved Permanently',
302: 'Moved Temporarily',
303: 'See Other',
304: 'Not Modified',
305: 'Use Proxy',
307: 'Temporary Redirect',
400: 'Bad Request',
401: 'Unauthorized',
402: 'Payment Required',
403: 'Forbidden',
404: 'Not Found',
405: 'Method Not Allowed',
406: 'Not Acceptable',
407: 'Proxy Authentication Required',
408: 'Request Time-out',
409: 'Conflict',
410: 'Gone',
411: 'Length Required',
412: 'Precondition Failed',
413: 'Request Entity Too Large',
414: 'Request-URI Too Large',
415: 'Unsupported Media Type',
416: 'Requested range not satisfiable',
417: 'Expectation Failed',
422: 'Unprocessable Entity',
423: 'Locked',
424: 'Failed Dependency',
500: 'Internal Server Error',
501: 'Not Implemented',
502: 'Bad Gateway',
503: 'Service Unavailable',
504: 'Gateway Time-out',
505: 'HTTP Version not supported',
507: 'Insufficient Storage',
}

status_codes={}

def init_status_codes():
    # Add mappings for builtin exceptions and
    # provide text -> error code lookups.
    for key, val in status_reasons.items():
        status_codes[val.replace(' ', '').lower()] = key
        status_codes[val.lower()] = key
        status_codes[key] = key
        status_codes[str(key)] = key

    en = [n.lower() for n in dir(__builtins__) if n.endswith('Error')]

    for name in en:
        status_codes[name] = 500

init_status_codes()

accumulate_header = {'set-cookie': 1}.has_key


class URLGetter:

    def __init__(self, request):
        self.__request = request

    def __str__(self):
        return self.__request.getURL()

    def __getitem__(self, name):
        i = int(name)
        try:
            if i < 0:
                i = -i
                return self.__request.getURL(i)
            else:
                return self.__request.getApplicationURL(i)
        except IndexError, v:
            if v[0] == i:
                raise KeyError, name
            raise

    def get(self, name, default=None):
        i = int(name)
        try:
            if i < 0:
                return self.__request.getURL(-i)
            else:
                return self.__request.getApplicationURL(i)
        except IndexError, v:
            if v == i:
                return default
            raise

DEFAULT_PORTS = {'http': '80', 'https': '443'}
STAGGER_RETRIES = True

class HTTPRequest(BaseRequest):
    """
    Model HTTP request data.

    This object provides access to request data.  This includes, the
    input headers, form data, server data, and cookies.

    Request objects are created by the object publisher and will be
    passed to published objects through the argument name, REQUEST.

    The request object is a mapping object that represents a
    collection of variable to value mappings.  In addition, variables
    are divided into four categories:

      - Environment variables

        These variables include input headers, server data, and other
        request-related data.  The variable names are as <a
        href="http://hoohoo.ncsa.uiuc.edu/cgi/env.html">specified</a>
        in the <a
        href="http://hoohoo.ncsa.uiuc.edu/cgi/interface.html">CGI
        specification</a>

      - Form data

        These are data extracted from either a URL-encoded query
        string or body, if present.

      - Cookies

        These are the cookie data, if present.

      - Other

        Data that may be set by an application object.

    The form attribute of a request is actually a Field Storage
    object.  When file uploads are used, this provides a richer and
    more complex interface than is provided by accessing form data as
    items of the request.  See the FieldStorage class documentation
    for more details.

    The request object may be used as a mapping object, in which case
    values will be looked up in the order: environment variables,
    other variables, form data, and then cookies.
    """

    _presentation_type = IHTTPPresentation


    __implements__ = (BaseRequest.__implements__,
                      IHTTPCredentials, IHTTPRequest, IHTTPApplicationRequest,
                      )

    __slots__ = (
        '_auth',          # The value of the HTTP_AUTHORIZATION header.
        '_cookies',       # The request cookies
        '_path_suffix',   # Extra traversal steps after normal traversal
        '_retry_count',   # How many times the request has been retried
        '_app_names',     # The application path as a sequence
        '_app_server',    # The server path of the application url
        '_orig_env',      # The original environment
        '_endswithslash', # Does the given path end with /
        'method',         # The upper-cased request method (REQUEST_METHOD)
        '_locale',        # The locale for the request
        '_vh_trunc',      # The number of path elements to be removed
                          # from _traversed_names
        )

    retry_max_count = 3    # How many times we're willing to retry

    def __init__(self, body_instream, outstream, environ, response=None):
        # Import here to break import loops
        from zope.publisher.browser import BrowserLanguages

        super(HTTPRequest, self).__init__(
            body_instream, outstream, environ, response)

        self._orig_env = environ
        environ = sane_environment(environ)

        if 'HTTP_AUTHORIZATION' in environ:
            self._auth = environ['HTTP_AUTHORIZATION']
            del environ['HTTP_AUTHORIZATION']
        else:
            self._auth = None

        self.method = environ.get("REQUEST_METHOD", 'GET').upper()

        self._environ = environ

        self.__setupCookies()
        self.__setupPath()
        self.__setupURLBase()
        self._vh_trunc = 0

        self.response.setCharsetUsingRequest(self)
        langs = BrowserLanguages(self).getPreferredLanguages()
        for httplang in langs:
            language = country = variant = None
            parts = httplang.split('-')
            if parts:
                language = parts.pop(0)
            if parts:
                country = parts.pop(0)
            if parts:
                variant = parts.pop(0)
            try:
                self._locale = locales.getLocale(language, country, variant)
                return
            except LoadLocaleError:
                # Just try the next combination
                pass
        else:
            # No combination gave us an existing locale, so use the default,
            # which is guaranteed to exist
            self._locale = locales.getLocale(None, None, None)

    def _getLocale(self):
        return self._locale
    locale = property(_getLocale)

    def __setupURLBase(self):

        get_env = self._environ.get

        ################################################################
        # Get base info first. This isn't likely to cause
        # errors and might be useful to error handlers.
        script = get_env('SCRIPT_NAME','').strip()

        # _script and the other _names are meant for URL construction
        self._app_names = app_names = filter(None, script.split('/'))

        # get server URL and store it too, since we are already looking it up
        server_url = get_env('SERVER_URL', None)
        if server_url is not None:
            self._app_server = server_url = server_url.strip()
        else:
            server_url = self.__deduceServerURL()

        if server_url.endswith('/'):
            server_url = server_url[:-1]


        # strip off leading /'s of script
        while script.startswith('/'):
            script = script[1:]

        self._app_server = server_url

    def __deduceServerURL(self):
        environ = self._environ

        if (environ.get('HTTPS', '').lower() == "on" or
            environ.get('SERVER_PORT_SECURE') == "1"):
            protocol = 'https'
        else:
            protocol = 'http'

        if environ.has_key('HTTP_HOST'):
            host = environ['HTTP_HOST'].strip()
            hostname, port = splitport(host)
        else:
            hostname = environ.get('SERVER_NAME', '').strip()
            port = environ.get('SERVER_PORT', '')

        if port and port != DEFAULT_PORTS.get(protocol):
            host = hostname + ':' + port
        else:
            host = hostname

        return '%s://%s' % (protocol, host)

    def __setupCookies(self):

        ################################################################
        # Cookie values should *not* be appended to existing form
        # vars with the same name - they are more like default values
        # for names not otherwise specified in the form.
        cookies={}
        cookie_header = self._environ.get('HTTP_COOKIE','')
        if cookie_header:
            parse_cookie(cookie_header, cookies)

        self._cookies = cookies

    def __setupPath(self):
        self._setupPath_helper("PATH_INFO")

    def supportsRetry(self):
        'See IPublisherRequest'
        count = getattr(self, '_retry_count', 0)
        if count < self.retry_max_count:
            if STAGGER_RETRIES:
                time.sleep(random.uniform(0, 2**(count)))
            return True

    def retry(self):
        'See IPublisherRequest'
        count = getattr(self, '_retry_count', 0)
        self._retry_count = count + 1
        self._body_instream.seek(0)
        new_response = self.response.retry()
        request = self.__class__(
            body_instream=self._body_instream,
            outstream=None,
            environ=self._orig_env,
            response=new_response,
            )
        request.setPublication(self.publication)
        request._retry_count = self._retry_count
        return request

    def traverse(self, object):
        'See IPublisherRequest'

        self._vh_trunc = 0
        ob = super(HTTPRequest, self).traverse(object)
        if self._path_suffix:
            self._traversal_stack = self._path_suffix
            ob = super(HTTPRequest, self).traverse(ob)

        if self._vh_trunc:
            del self._traversed_names[:self._vh_trunc]

        return ob

    # This method is not part of the interface.
    def _splitPath(self, path):
        # Split and clean up the path.
        if path.startswith('/'):
            path = path[1:]

        if path.endswith('/'):
            path = path[:-1]

        clean = []
        for item in path.split('/'):
            if not item or item == '.':
                continue
            elif item == '..':
                del clean[-1]
            else: clean.append(item)

        return clean

    def getHeader(self, name, default=None, literal=False):
        'See IHTTPRequest'
        environ = self._environ
        if not literal:
            name = name.replace('-', '_').upper()
        val = environ.get(name, None)
        if val is not None:
            return val
        if not name.startswith('HTTP_'):
            name='HTTP_%s' % name
        return environ.get(name, default)

    headers = RequestDataProperty(HeaderGetter)

    def getCookies(self):
        'See IHTTPRequest'
        return self._cookies

    cookies = RequestDataProperty(CookieMapper)

    def setPathSuffix(self, steps):
        'See IHTTPRequest'
        steps = list(steps)
        steps.reverse()
        self._path_suffix = steps

    def _authUserPW(self):
        'See IHTTPCredentials'
        global base64
        auth=self._auth
        if auth:
            if auth.lower().startswith('basic '):
                if base64 is None: import base64
                name, password = base64.decodestring(
                    auth.split()[-1]).split(':')
                return name, password

    def unauthorized(self, challenge):
        'See IHTTPCredentials'
        self._response.setHeader("WWW-Authenticate", challenge, True)
        self._response.setStatus(401)

    #
    ############################################################

    def _createResponse(self, outstream):
        # Should be overridden by subclasses
        return HTTPResponse(outstream)


    def getURL(self, level=0, path_only=False):
        names = self._app_names + self._traversed_names
        if level:
            if level > len(names):
                raise IndexError, level
            names = names[:-level]
        names = [quote(name, safe='/+@') for name in names]

        if path_only:
            if not names: return '/'
            return '/' + '/'.join(names)
        else:
            if not names: return self._app_server
            return "%s/%s" % (self._app_server, '/'.join(names))

    def getApplicationURL(self, depth=0, path_only=False):
        """See IHTTPApplicationRequest"""
        if depth:
            names = self._traversed_names
            if depth > len(names):
                raise IndexError, depth
            names = self._app_names + names[:depth]
        else:
            names = self._app_names

        names =  [quote(name, safe='/+@') for name in names]

        if path_only:
            return names and ('/' + '/'.join(names)) or '/'
        else:
            return (names and ("%s/%s" % (self._app_server, '/'.join(names)))
                    or self._app_server)

    def setApplicationServer(self, host, proto='http', port=None):
        if port and str(port) != DEFAULT_PORTS.get(proto):
            host = '%s:%s' % (host, port)
        self._app_server = '%s://%s' % (proto, host)

    def setApplicationNames(self, names):
        self._app_names = list(names)

    def setVirtualHostRoot(self):
        self._vh_trunc = len(self._traversed_names) + 1

    URL = RequestDataProperty(URLGetter)

    def __repr__(self):
        # Returns a *short* string.
        return '<%s instance at 0x%x, URL=%s>' % (
            str(self.__class__), id(self), `self.URL`)

    def get(self, key, default=None):
        'See Interface.Common.Mapping.IReadMapping'

        result = self._cookies.get(key, self)
        if result is not self: return result

        result = self._environ.get(key, self)
        if result is not self: return result

        return default

    def keys(self):
        'See Interface.Common.Mapping.IEnumerableMapping'
        d = {}
        d.update(self._environ)
        d.update(self._cookies)
        return d.keys()


class HTTPResponse (BaseResponse):

    __implements__ = (IHTTPResponse, IHTTPApplicationResponse,
                      BaseResponse.__implements__)

    __slots__ = (
        '_header_output',       # Hook object to collaborate with a server
                                # for header generation.
        '_headers',
        '_cookies',
        '_accumulated_headers', # Headers that can have multiples
        '_wrote_headers',
        '_streaming',
        '_status',              # The response status (usually an integer)
        '_reason',              # The reason that goes with the status
        '_status_set',          # Boolean: status explicitly set
        '_charset',             # String: character set for the output
        )


    def __init__(self, outstream, header_output=None):
        self._header_output = header_output

        super(HTTPResponse, self).__init__(outstream)
        self.reset()

    def reset(self):
        'See IResponse'
        super(HTTPResponse, self).reset()
        self._headers = {}
        self._cookies = {}
        self._accumulated_headers = []
        self._wrote_headers = False
        self._streaming = False
        self._status = 599
        self._reason = 'No status set'
        self._status_set = False
        self._charset = None

    def setHeaderOutput(self, header_output):
        self._header_output = header_output

    def setStatus(self, status, reason=None):
        'See IHTTPResponse'
        if status is None:
            status = 200
        else:
            if type(status) in StringTypes:
                status = status.lower()
            if status in status_codes:
                status = status_codes[status]
            else:
                status = 500
        self._status = status

        if reason is None:
            if status == 200:
                reason = 'Ok'
            elif status in status_reasons:
                reason = status_reasons[status]
            else:
                reason = 'Unknown'
        self._reason = reason
        self._status_set = True


    def getStatus(self):
        'See IHTTPResponse'
        return self._status


    def setHeader(self, name, value, literal=False):
        'See IHTTPResponse'

        name = str(name)
        value = str(value)

        key = name.lower()
        if accumulate_header(key):
            self.addHeader(name, value)
        else:
            name = literal and name or key
            self._headers[name]=value


    def addHeader(self, name, value):
        'See IHTTPResponse'
        accum = self._accumulated_headers
        accum.append('%s: %s' % (name, value))


    def getHeader(self, name, default=None, literal=False):
        'See IHTTPResponse'
        key = name.lower()
        name = literal and name or key
        return self._headers.get(name, default)

    def getHeaders(self):
        'See IHTTPResponse'
        result = {}
        headers = self._headers

        if (not self._streaming and not ('content-length' in headers)
            and not ('transfer-encoding' in headers)):
            self._updateContentLength()

        result["X-Powered-By"] = "Zope (www.zope.org), Python (www.python.org)"

        for key, val in headers.items():
            if key.lower() == key:
                # only change non-literal header names
                key = key.capitalize()
                start = 0
                location = key.find('-', start)
                while location >= start:
                    key = "%s-%s" % (key[:location],
                                     key[location+1:].capitalize())
                    start = location + 1
                    location = key.find('-', start)
            result[key] = val

        return result


    def appendToHeader(self, name, value, delimiter=','):
        'See IHTTPResponse'
        headers = self._headers
        if name in headers:
            h = self._header[name]
            h = "%s%s\r\n\t%s" % (h, delimiter, value)
        else:
            h = value
        self.setHeader(name, h)


    def appendToCookie(self, name, value):
        'See IHTTPResponse'
        cookies = self._cookies
        if name in cookies:
            cookie = cookies[name]
        else:
            cookie = cookies[name] = {}
        if 'value' in cookie:
            cookie['value'] = '%s:%s' % (cookie['value'], value)
        else:
            cookie['value'] = value


    def expireCookie(self, name, **kw):
        'See IHTTPResponse'
        dict = {'max_age':0, 'expires':'Wed, 31-Dec-97 23:59:59 GMT'}
        for k, v in kw.items():
            if v is not None:
                dict[k] = v
        cookies = self._cookies
        if name in cookies:
            # Cancel previous setCookie().
            del cookies[name]
        self.setCookie(name, 'deleted', **dict)


    def setCookie(self, name, value, **kw):
        'See IHTTPResponse'
        cookies = self._cookies
        cookie = cookies.setdefault(name, {})

        for k, v in kw.items():
            if v is not None:
                cookie[k] = v

        cookie['value'] = value


    def getCookie(self, name, default=None):
        'See IHTTPResponse'
        return self._cookies.get(name, default)


    def setCharset(self, charset=None):
        'See IHTTPResponse'
        self._charset = charset


    def setCharsetUsingRequest(self, request):
        'See IHTTPResponse'
        envadapter = queryAdapter(request, IUserPreferredCharsets)
        if envadapter is None:
            return

        # XXX This try/except looks rather suspicious :(
        try:
            charset = envadapter.getPreferredCharsets()[0]
        except:
            charset = 'UTF-8'
        self.setCharset(charset)

    def setBody(self, body):
        self._body = unicode(body)
        if not self._status_set:
            self.setStatus(200)

    def handleException(self, exc_info):
        """
        Calls self.setBody() with an error response.
        """
        t, v = exc_info[:2]
        if isinstance(t, ClassType):
            title = tname = t.__name__
            if issubclass(t, Redirect):
                self.redirect(v.getLocation())
                return
        else:
            title = tname = unicode(t)

        # Throwing non-protocol-specific exceptions is a good way
        # for apps to control the status code.
        self.setStatus(tname)

        status = self.getStatus()
        body = self._html(title, "A server error occurred." )
        self.setBody(body)


    def internalError(self):
        'See IPublisherResponse'
        self.setStatus(500, u"The engines can't take any more, Jim!")


    def _html(self, title, content):
        t = escape(title)
        return (
            u"<html><head><title>%s</title></head>\n"
            u"<body><h2>%s</h2>\n"
            u"%s\n"
            u"</body></html>\n" %
            (t, t, content)
            )


    def retry(self):
        """
        Returns a response object to be used in a retry attempt
        """
        return self.__class__(self._outstream,
                              self._header_output)

    def _updateContentLength(self):
        blen = str(len(self._body))
        if blen.endswith('L'):
            blen = blen[:-1]
        self.setHeader('content-length', blen)

    def redirect(self, location, status=302):
        """Causes a redirection without raising an error"""
        self.setStatus(status)
        self.setHeader('Location', location)
        return location

    def _cookie_list(self):
        cookie_list = []
        for name, attrs in self._cookies.items():

            # Note that as of May 98, IE4 ignores cookies with
            # quoted cookie attr values, so only the value part
            # of name=value pairs may be quoted.

            cookie='Set-Cookie: %s="%s"' % (name, attrs['value'])
            for name, value in attrs.items():
                name = name.lower()
                if name == 'expires':
                    cookie = '%s; Expires=%s' % (cookie,value)
                elif name == 'domain':
                    cookie = '%s; Domain=%s' % (cookie,value)
                elif name == 'path':
                    cookie = '%s; Path=%s' % (cookie,value)
                elif name == 'max_age':
                    cookie = '%s; Max-Age=%s' % (cookie,value)
                elif name == 'comment':
                    cookie = '%s; Comment=%s' % (cookie,value)
                elif name == 'secure' and value:
                    cookie = '%s; Secure' % cookie
            cookie_list.append(cookie)

        # XXX: Should really check size of cookies here!

        return cookie_list


    def getHeaderText(self, m):
        lst = ['Status: %s %s' % (self._status, self._reason)]
        items = m.items()
        items.sort()
        lst.extend(map(lambda x: '%s: %s' % x, items))
        lst.extend(self._cookie_list())
        lst.extend(self._accumulated_headers)
        return ('%s\r\n\r\n' % '\r\n'.join(lst))


    def outputHeaders(self):
        headers = self.getHeaders()
        header_output = self._header_output
        if header_output is not None:
            # Use the IHeaderOutput interface.
            header_output.setResponseStatus(self._status, self._reason)
            header_output.setResponseHeaders(headers)
            header_output.appendResponseHeaders(self._cookie_list())
            header_output.appendResponseHeaders(self._accumulated_headers)
        else:
            # Write directly to outstream.
            headers_text = self.getHeaderText(headers)
            self._outstream.write(headers_text)


    def write(self, string):
        """See IApplicationResponse

        Return data as a stream

        HTML data may be returned using a stream-oriented interface.
        This allows the browser to display partial results while
        computation of a response to proceed.

        The published object should first set any output headers or
        cookies on the response object.

        Note that published objects must not generate any errors
        after beginning stream-oriented output.

        """
        self.output(string)

    def output(self, data):
        if not self._wrote_headers:
            self.outputHeaders()
            self._wrote_headers = True

        if (self.getHeader('content-type', '').startswith('text') and
               self._charset is not None and type(data) is UnicodeType):
            data = data.encode(self._charset)

        self._outstream.write(data)


    def outputBody(self):
        """
        Outputs the response body.
        """
        self.output(self._body)


class DefaultPublisher:

    __implements__ =  IHTTPPublisher

    def publishTraverse(self, request, name):
        'See IHTTPPublisher'

        return getattr(self, name)

def sort_charsets(x, y):
    if y[1] == 'utf-8':
        return 1
    if x[1] == 'utf-8':
        return -1
    return cmp(y, x)


class HTTPCharsets:

    __implements__ =  IUserPreferredCharsets

    def __init__(self, request):
        self.request = request

    def getPreferredCharsets(self):
        '''See interface IUserPreferredCharsets'''
        charsets = []
        sawstar = sawiso88591 = 0
        for charset in self.request.get('HTTP_ACCEPT_CHARSET', '').split(','):
            charset = charset.strip().lower()
            if charset:
                if ';' in charset:
                    charset, quality = charset.split(';')
                    if not quality.startswith('q='):
                        # not a quality parameter
                        quality = 1.0
                    else:
                        try:
                            quality = float(quality[2:])
                        except ValueError:
                            continue
                else:
                    quality = 1.0
                if quality == 0.0:
                    continue
                if charset == '*':
                    sawstar = 1
                if charset == 'iso-8859-1':
                    sawiso88591 = 1
                charsets.append((quality, charset))
        # Quoting RFC 2616, $14.2: If no "*" is present in an Accept-Charset
        # field, then all character sets not explicitly mentioned get a
        # quality value of 0, except for ISO-8859-1, which gets a quality
        # value of 1 if not explicitly mentioned.
        if not sawstar and not sawiso88591:
            charsets.append((1.0, 'iso-8859-1'))
        # UTF-8 is **always** preferred over anything else.
        # XXX Please give more details as to why!
        charsets.sort(sort_charsets)
        return [c[1] for c in charsets]
