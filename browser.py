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

$Id: browser.py,v 1.18 2003/05/22 22:48:34 jim Exp $
"""

import re
from types import ListType, TupleType, StringType, StringTypes
from cgi import FieldStorage, escape

from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.interfaces import IUserPreferredCharsets
from zope.publisher.interfaces.browser import IBrowserPresentation
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.browser import IBrowserApplicationRequest

from zope.publisher.interfaces.browser import IBrowserView
from zope.component import getAdapter
from zope.publisher.http import HTTPRequest, HTTPResponse

__metaclass__ = type # All classes are new style when run with Python 2.2+

__ArrayTypes = (ListType, TupleType)

search_type = re.compile('(:[a-zA-Z][a-zA-Z0-9_]+|\\.[xy])$').search
start_of_header_search=re.compile('(<head[^>]*>)', re.IGNORECASE).search
base_re_search=re.compile('(<base.*?>)',re.I).search
isRelative = re.compile("[-_.!~*a-zA-z0-9'()@&=+$,]+(/|$)").match
newline_search = re.compile('\r\n|\n\r').search


def is_text_html(content_type):
    return content_type.startswith('text/html')

# Flas Constants
SEQUENCE = 1
DEFAULT = 2
RECORD = 4
RECORDS = 8
REC = 12 # RECORD|RECORDS
EMPTY = 16
CONVERTED = 32
DEFAULTABLE_METHODS = 'GET', 'POST', 'HEAD'


def field2string(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    return v

def field2text(v, nl=newline_search):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    mo = nl(v)
    if mo is None: return v
    l = mo.start(0)
    r=[]
    s=0
    while l >= s:
        r.append(v[s:l])
        s=l+2
        mo=nl(v,s)
        if mo is None: l=-1
        else:          l=mo.start(0)

    r.append(v[s:])

    return '\n'.join(r)

def field2required(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    if v.strip(): return v
    raise ValueError, 'No input for required field<p>'

def field2int(v):
    if isinstance(v, __ArrayTypes):
        return map(field2int, v)
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    if v:
        try: return int(v)
        except ValueError:
            raise ValueError, (
                "An integer was expected in the value '%s'" % v
                )
    raise ValueError, 'Empty entry when <strong>integer</strong> expected'

def field2float(v):
    if isinstance(v, __ArrayTypes):
        return map(field2float, v)
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    if v:
        try: return float(v)
        except ValueError:
            raise ValueError, (
                "A floating-point number was expected in the value '%s'" % v
                )
    raise ValueError, (
        'Empty entry when <strong>floating-point number</strong> expected')

def field2long(v):
    if isinstance(v, __ArrayTypes):
        return map(field2long, v)
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)

    # handle trailing 'L' if present.
    if v.lower().endswith('l'):
        v = v[:-1]
    if v:
        try: return long(v)
        except ValueError:
            raise ValueError, (
                "A long integer was expected in the value '%s'" % v
                )
    raise ValueError, 'Empty entry when <strong>integer</strong> expected'

def field2tokens(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    return v.split()

def field2lines(v):
    if isinstance(v, __ArrayTypes):
        result=[]
        for item in v:
            result.append(str(item))
        return result
    return field2text(v).split('\n')

def field2boolean(v):
    return v

type_converters = {
    'float':    field2float,
    'int':      field2int,
    'long':     field2long,
    'string':   field2string,
    'required': field2required,
    'tokens':   field2tokens,
    'lines':    field2lines,
    'text':     field2text,
    'boolean':     field2boolean,
    }

get_converter=type_converters.get

def registerTypeConverter(field_type, converter, replace=False):
    """Add a custom type converter to the registry.

    o If 'replace' is not true, raise a KeyError if a converter is
      already registered for 'field_type'.
    """
    existing = type_converters.get(field_type)

    if existing is not None and not replace:
        raise KeyError, 'Existing converter for field_type: %s' % field_type

    type_converters[field_type] = converter


isCGI_NAME = {
    # These fields are placed in request.environ instead of request.form.
    'SERVER_SOFTWARE' : 1,
    'SERVER_NAME' : 1,
    'GATEWAY_INTERFACE' : 1,
    'SERVER_PROTOCOL' : 1,
    'SERVER_PORT' : 1,
    'REQUEST_METHOD' : 1,
    'PATH_INFO' : 1,
    'PATH_TRANSLATED' : 1,
    'SCRIPT_NAME' : 1,
    'QUERY_STRING' : 1,
    'REMOTE_HOST' : 1,
    'REMOTE_ADDR' : 1,
    'AUTH_TYPE' : 1,
    'REMOTE_USER' : 1,
    'REMOTE_IDENT' : 1,
    'CONTENT_TYPE' : 1,
    'CONTENT_LENGTH' : 1,
    'SERVER_URL': 1,
    }.has_key

hide_key={
    'HTTP_AUTHORIZATION':1,
    'HTTP_CGI_AUTHORIZATION': 1,
    }.has_key


class record:

    def __getattr__(self, key, default=None):
        if key in ('get', 'keys', 'items', 'values', 'copy',
                   'has_key', '__contains__'):
            return getattr(self.__dict__, key)
        raise AttributeError, key

    def __getitem__(self, key):
        return self.__dict__[key]

    def __str__(self):
        L1 = self.__dict__.items()
        L1.sort()
        return ", ".join(["%s: %s" % item for item in L1])

    def __repr__(self):
        L1 = self.__dict__.items()
        L1.sort()
        return ', '.join(["%s: %s" % (key, repr(value)) for key, value in L1])


class BrowserRequest(HTTPRequest):

    __implements__ = (HTTPRequest.__implements__,
                      IBrowserRequest,
                      IBrowserApplicationRequest,
                      )

    __slots__ = (
        'form',   # Form data
        'charsets', # helper attribute
        )

    use_redirect = 0 # Set this to 1 in a subclass to redirect GET
                     # requests when the effective and actual URLs differ.

    # _presentation_type is overridden from the BaseRequest
    #  to implement IBrowserPresentation
    _presentation_type = IBrowserPresentation



    def __init__(self, body_instream, outstream, environ, response=None):
        self.form = {}
        self.charsets = None
        super(BrowserRequest, self).__init__(
            body_instream, outstream, environ, response)


    def _createResponse(self, outstream):
        # Should be overridden by subclasses
        return BrowserResponse(outstream)

    def _decode(self, text):
        """Try to decode the text using one of the available charsets."""
        if self.charsets is None:
            envadapter = getAdapter(self, IUserPreferredCharsets)
            self.charsets = envadapter.getPreferredCharsets()
        for charset in self.charsets:
            try:
                text = unicode(text, charset)
                break
            except UnicodeError:
                pass
        return text

    def processInputs(self):
        'See IPublisherRequest'

        environ = self._environ
        form = self.form

        if self.method != 'GET':
            # Process form if not a GET request.
            fp = self._body_instream
        else:
            fp = None

        fs = FieldStorage(fp = fp,
                          environ = environ,
                          keep_blank_values = 1)

        meth = None
        fslist = getattr(fs, 'list', None)
        if fslist is not None:
            tuple_items = {}
            CGI_name = isCGI_NAME
            defaults = {}
            converter = seqf = None

            # process all entries in the field storage (form)
            for item in fslist:

                # Check whether this field is a file upload object
                key = item.name
                if (hasattr(item, 'file') and hasattr(item, 'filename')
                    and hasattr(item,'headers')):
                    if (item.file and
                        (item.filename is not None
                         # RFC 1867 says that all fields get a content-type.
                         # or 'content-type' in map(lower, item.headers.keys())
                         )):
                        item = FileUpload(item)
                    else:
                        item = item.value

                flags = 0

                # Loop through the different types and set
                # the appropriate flags
                # Syntax: var_name:type_name

                # We'll search from the back to the front.
                # We'll do the search in two steps.  First, we'll
                # do a string search, and then we'll check it with
                # a re search.

                # Get the location of the name type splitter
                loc = key.rfind(':')
                if loc >= 0:
                    mo = search_type(key,loc)
                    if mo: loc = mo.start(0)
                    else:  loc = -1

                    while loc >= 0:
                        type_name = key[loc+1:]
                        key = key[:loc]
                        # find the right type converter
                        c = get_converter(type_name, None)

                        if c is not None:
                            converter = c
                            flags=flags|CONVERTED
                        elif type_name == 'list':
                            seqf=list
                            flags=flags|SEQUENCE
                        elif type_name == 'tuple':
                            seqf=tuple
                            tuple_items[key]=1
                            flags=flags|SEQUENCE
                        elif (type_name == 'method' or type_name == 'action'):
                            if loc: meth=key
                            else: meth=item
                        elif (type_name == 'default_method' or type_name == \
                              'default_action'):
                            if not meth:
                                if loc: meth=key
                                else: meth=item
                        elif type_name == 'default':
                            flags=flags|DEFAULT
                        elif type_name == 'record':
                            flags=flags|RECORD
                        elif type_name == 'records':
                            flags=flags|RECORDS
                        elif type_name == 'ignore_empty':
                            if not item: flags=flags|EMPTY

                        loc = key.rfind(':')
                        if loc < 0:
                            break
                        mo = search_type(key, loc)
                        if mo:
                            loc = mo.start(0)
                        else:
                            loc = -1


                # Filter out special names from form:
                if CGI_name(key) or key.startswith('HTTP_'):
                    continue

                # Make it unicode
                key = self._decode(key)
                if type(item) == StringType:
                    item = self._decode(item)

                if flags:

                    # skip over empty fields
                    if flags & EMPTY: continue

                    #Split the key and its attribute
                    if flags & REC:
                        key = key.split(".")
                        key, attr = ".".join(key[:-1]), key[-1]

                    # defer conversion
                    if flags & CONVERTED:
                        try:
                            item=converter(item)
                        except:
                            if (not item and not (flags&DEFAULT) and
                                (key in defaults)):
                                item = defaults[key]
                                if flags&RECORD:
                                    item=getattr(item,attr)
                                if flags&RECORDS:
                                    item.reverse()
                                    item = item[0]
                                    item=getattr(item,attr)
                            else:
                                raise

                    # Determine which dictionary to use
                    if flags & DEFAULT:
                        mapping_object = defaults
                    else:
                        mapping_object = form

                    # Insert in dictionary
                    if key in mapping_object:
                        if flags & RECORDS:
                            #Get the list and the last record
                            #in the list
                            reclist = mapping_object[key]
                            reclist.reverse()
                            x=reclist[0]
                            reclist.reverse()
                            if not hasattr(x,attr):
                                #If the attribute does not
                                #exist, setit
                                if flags&SEQUENCE: item=[item]
                                reclist.remove(x)
                                setattr(x,attr,item)
                                reclist.append(x)
                                mapping_object[key] = reclist
                            else:
                                if flags&SEQUENCE:
                                    # If the attribute is a
                                    # sequence, append the item
                                    # to the existing attribute
                                    reclist.remove(x)
                                    y = getattr(x, attr)
                                    y.append(item)
                                    setattr(x, attr, y)
                                    reclist.append(x)
                                    mapping_object[key] = reclist
                                else:
                                    # Create a new record and add
                                    # it to the list
                                    n=record()
                                    setattr(n,attr,item)
                                    reclist.append(n)
                                    mapping_object[key]=reclist
                        elif flags&RECORD:
                            b=mapping_object[key]
                            if flags&SEQUENCE:
                                item=[item]
                                if not hasattr(b,attr):
                                    # if it does not have the
                                    # attribute, set it
                                    setattr(b,attr,item)
                                else:
                                    # it has the attribute so
                                    # append the item to it
                                    setattr(b,attr,getattr(b,attr)+item)
                            else:
                                # it is not a sequence so
                                # set the attribute
                                setattr(b,attr,item)
                        else:
                            # it is not a record or list of records
                            found=mapping_object[key]
                            if isinstance(found, list):
                                found.append(item)
                            else:
                                found=[found,item]
                                mapping_object[key]=found
                    else:
                        # The dictionary does not have the key
                        if flags&RECORDS:
                            # Create a new record, set its attribute
                            # and put it in the dictionary as a list
                            a = record()
                            if flags&SEQUENCE: item=[item]
                            setattr(a,attr,item)
                            mapping_object[key]=[a]
                        elif flags&RECORD:
                            # Create a new record, set its attribute
                            # and put it in the dictionary
                            if flags&SEQUENCE: item=[item]
                            r = mapping_object[key]=record()
                            setattr(r,attr,item)
                        else:
                            # it is not a record or list of records
                            if flags&SEQUENCE: item=[item]
                            mapping_object[key]=item

                else:
                    # This branch is for case when no type was specified.
                    mapping_object = form

                    #Insert in dictionary
                    if key in mapping_object:
                        # it is not a record or list of records
                        found=mapping_object[key]
                        if isinstance(found, list):
                            found.append(item)
                        else:
                            found=[found,item]
                            mapping_object[key]=found
                    else:
                        mapping_object[key]=item

            #insert defaults into form dictionary
            if defaults:
                for keys, values in defaults.items():
                    if not (keys in form):
                        # if the form does not have the key,
                        # set the default
                        form[keys]=values
                    else:
                        #The form has the key
                        if isinstance(values, record):
                            # if the key is mapped to a record, get the
                            # record
                            r = form[keys]
                            for k, v in values.__dict__.items():
                                # loop through the attributes and values
                                # in the default dictionary
                                if not hasattr(r, k):
                                    # if the form dictionary doesn't have
                                    # the attribute, set it to the default
                                    setattr(r,k,v)
                                    form[keys] = r

                        elif isinstance(values, list):
                            # the key is mapped to a list
                            lst = form[keys]
                            for val in values:
                                # for each val in the list
                                if isinstance(val, record):
                                    # if the val is a record
                                    for k, v in val.__dict__.items():

                                        # loop through each
                                        # attribute and value in
                                        # the record

                                        for y in lst:

                                            # loop through each
                                            # record in the form
                                            # list if it doesn't
                                            # have the attributes
                                            # in the default
                                            # dictionary, set them

                                            if not hasattr(y, k):
                                                setattr(y, k, v)
                                else:
                                    # val is not a record
                                    if not a in lst:
                                        lst.append(a)
                            form[keys] = lst
                        else:
                            # The form has the key, the key is not mapped
                            # to a record or sequence so do nothing
                            pass

            # Convert to tuples
            if tuple_items:
                for key in tuple_items.keys():
                    # Split the key and get the attr
                    k=key.split(".")
                    k, attr=".".join(k[:-1]), k[-1]

                    # remove any type_names in the attr
                    while not attr == '':
                        attr = attr.split(":")
                        attr, new = ":".join(attr[:-1]), attr[-1]
                    attr = new

                    if k in form:
                        # If the form has the split key get its value
                        item = form[k]
                        if isinstance(item, record):
                            # if the value is mapped to a record, check if it
                            # has the attribute, if it has it, convert it to
                            # a tuple and set it
                            if hasattr(item, attr):
                                value = tuple(getattr(item, attr))
                                setattr(item, attr, value)
                        else:
                            # It is mapped to a list of  records
                            for x in item:
                                # loop through the records
                                if hasattr(x, attr):
                                    # If the record has the attribute
                                    # convert it to a tuple and set it
                                    value = tuple(getattr(x, attr))
                                    setattr(x, attr, value)
                    else:
                        # the form does not have the split key
                        if key in form:
                            # if it has the original key, get the item
                            # convert it to a tuple
                            item = form[key]
                            item = tuple(form[key])
                            form[key] = item

        if meth:
            self.setPathSuffix((meth,))


    def traverse(self, object):
        'See IPublisherRequest'

        ob = super(BrowserRequest, self).traverse(object)
        method = self.method

        base_needed = 0
        if self._path_suffix:
            # We had a :method variable, so we need to set the base,
            # but we don't look for default documents any more.
            base_needed = 1
            redirect = 0
        elif method in DEFAULTABLE_METHODS:
            # We need to check for default documents
            publication = self.publication

            nsteps = 0
            ob, add_steps = publication.getDefaultTraversal(self, ob)
            while add_steps:
                nsteps += len(add_steps)
                add_steps = list(add_steps)
                add_steps.reverse()
                self.setTraversalStack(add_steps)
                ob = super(BrowserRequest, self).traverse(ob)
                ob, add_steps = publication.getDefaultTraversal(self, ob)

            if nsteps > self._endswithslash:
                base_needed = 1
                redirect = self.use_redirect and method == 'GET'


        if base_needed:
            url = self.getURL()
            response = self.response
            if redirect:
                response.redirect(url)
                return ''
            elif not response.getBase():
                response.setBase(url)

        return ob

    def keys(self):
        'See Interface.Common.Mapping.IEnumerableMapping'
        d = {}
        d.update(self._environ)
        d.update(self._cookies)
        d.update(self.form)
        return d.keys()


    def get(self, key, default=None):
        'See Interface.Common.Mapping.IReadMapping'

        result = self.form.get(key, self)
        if result is not self: return result

        result = self._cookies.get(key, self)
        if result is not self: return result

        result = self._environ.get(key, self)
        if result is not self: return result

        return default


class FileUpload(object):
    '''File upload objects

    File upload objects are used to represent file-uploaded data.

    File upload objects can be used just like files.

    In addition, they have a 'headers' attribute that is a dictionary
    containing the file-upload headers, and a 'filename' attribute
    containing the name of the uploaded file.
    '''

    def __init__(self, aFieldStorage):

        file=aFieldStorage.file
        if hasattr(file, '__methods__'): methods=file.__methods__
        else: methods= ['close', 'fileno', 'flush', 'isatty',
                        'read', 'readline', 'readlines', 'seek',
                        'tell', 'truncate', 'write', 'writelines']

        d=self.__dict__
        for m in methods:
            if hasattr(file,m): d[m]=getattr(file,m)

        self.headers=aFieldStorage.headers
        self.filename=aFieldStorage.filename

class RedirectingBrowserRequest(BrowserRequest):
    """Browser requests that redirect when the actual and effective URLs differ
    """

    use_redirect = 1

class TestRequest(BrowserRequest):
    """Browser request with a constructor convenient for testing
    """

    def __init__(self,
                 body_instream=None, outstream=None, environ=None, form=None,
                 **kw):

        _testEnv =  {
            'SERVER_URL':         'http://127.0.0.1',
            'HTTP_HOST':          '127.0.0.1',
            'CONTENT_LENGTH':     '0',
            'GATEWAY_INTERFACE':  'TestFooInterface/1.0',
            }

        if environ:
            _testEnv.update(environ)
        if kw:
            _testEnv.update(kw)
        if body_instream is None:
            from StringIO import StringIO
            body_instream = StringIO('')

        if outstream is None:
            from StringIO import StringIO
            outstream = StringIO()

        super(TestRequest, self).__init__(body_instream, outstream, _testEnv)
        if form:
            self.form.update(form)

class BrowserResponse(HTTPResponse):
    """Browser response
    """

    __slots__ = (
        '_base', # The base href
        )

    def setBody(self, body):
        """Sets the body of the response

        Sets the return body equal to the (string) argument "body". Also
        updates the "content-length" return header and sets the status to
        200 if it has not already been set.
        """
        if not isinstance(body, StringTypes):
            body = unicode(body)

        if 'content-type' not in self._headers:
            c = (self.__isHTML(body) and 'text/html' or 'text/plain')
            if self._charset is not None:
                c += ';charset=' + self._charset
            self.setHeader('content-type', c)

        body = self.__insertBase(body)
        self._body = body
        self._updateContentLength()
        if not self._status_set:
            self.setStatus(200)

    def __isHTML(self, str):
        s = str.strip().lower()
        return ((s.startswith('<html') and (s[5:6] in ' >'))
                 or s.startswith('<!doctype html'))


    def __wrapInHTML(self, title, content):
        t = escape(title)
        return (
            "<html><head><title>%s</title></head>\n"
            "<body><h2>%s</h2>\n"
            "%s\n"
            "</body></html>\n" %
            (t, t, content)
            )


    def __insertBase(self, body):
        # Only insert a base tag if content appears to be html.
        content_type = self.getHeader('content-type', '')
        if content_type and not is_text_html(content_type):
            return body

        if getattr(self, '_base', ''):
            if body:
                match = start_of_header_search(body)
                if match is not None:
                    index = match.start(0) + len(match.group(0))
                    ibase = base_re_search(body)
                    if ibase is None:
                        body = ('%s\n<base href="%s" />\n%s' %
                                (body[:index], self._base, body[index:]))
        return body

    def getBase(self):
        return getattr(self, '_base', '')

    def setBase(self, base):
        self._base = base

    def redirect(self, location, status=302):
        base = getattr(self, '_base', '')
        if base and isRelative(str(location)):
            l = base.rfind('/')
            if l >= 0:
                base = base[:l+1]
            else:
                base += '/'
            location = base + location

        # XXX: HTTP redirects must provide an absolute location, see
        #      http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.30
        #      So, what if location is relative and base is unknown?  Uncomment
        #      the following and you'll see that it actually happens.
        #
        # if isRelative(str(location)):
        #     raise AssertionError('Cannot determine absolute location')

        super(BrowserResponse, self).redirect(location, status)

    def reset(self):
        super(BrowserResponse, self).reset()
        self._base = ''


class BrowserLanguages:

    __implements__ =  IUserPreferredLanguages

    def __init__(self, request):
        self.request = request

    def getPreferredLanguages(self):
        '''See interface IUserPreferredLanguages'''
        langs = []
        for lang in self.request.get('HTTP_ACCEPT_LANGUAGE', '').split(','):
            lang = lang.strip()
            if lang:
                langs.append(lang.split(';')[0])
        return langs


class BrowserView:

    __implements__ = IBrowserView

    def __init__(self, context, request):
        self.context = context
        self.request = request

