##############################################################################
#
# From the cgi module in Python 3.8, licensed as follows:
#
# PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
# --------------------------------------------
#
# 1. This LICENSE AGREEMENT is between the Python Software Foundation
# ("PSF"), and the Individual or Organization ("Licensee") accessing and
# otherwise using this software ("Python") in source or binary form and
# its associated documentation.
#
# 2. Subject to the terms and conditions of this License Agreement, PSF
# hereby grants Licensee a nonexclusive, royalty-free, world-wide license to
# reproduce, analyze, test, perform and/or display publicly, prepare
# derivative works, distribute, and otherwise use Python alone or in any
# derivative version, provided, however, that PSF's License Agreement and
# PSF's notice of copyright, i.e., "Copyright (c) 2001, 2002, 2003, 2004,
# 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016,
# 2017, 2018, 2019, 2020 Python Software Foundation; All Rights Reserved"
# are retained in Python alone or in any derivative version prepared by
# Licensee.
#
# 3. In the event Licensee prepares a derivative work that is based on
# or incorporates Python or any part thereof, and wants to make
# the derivative work available to others as provided herein, then
# Licensee hereby agrees to include in any such work a brief summary of
# the changes made to Python.
#
# 4. PSF is making Python available to Licensee on an "AS IS"
# basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
# IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
# DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
# FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
# INFRINGE ANY THIRD PARTY RIGHTS.
#
# 5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
# FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
# A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
# OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.
#
# 6. This License Agreement will automatically terminate upon a material
# breach of its terms and conditions.
#
# 7. Nothing in this License Agreement shall be deemed to create any
# relationship of agency, partnership, or joint venture between PSF and
# Licensee.  This License Agreement does not grant permission to use PSF
# trademarks or trade name in a trademark sense to endorse or promote
# products or services of Licensee, or any third party.
#
# 8. By copying, installing or otherwise using Python, Licensee
# agrees to be bound by the terms and conditions of this License
# Agreement.
#
##############################################################################

from email.message import Message
from email.parser import FeedParser
from io import (
    BytesIO,
    StringIO,
    TextIOWrapper,
)
import locale
import os
import re
import sys
import tempfile

from six.moves.collections_abc import Mapping
from six.moves.urllib.parse import parse_qsl

from zope.publisher._compat import PYTHON2


# Maximum input we will accept when REQUEST_METHOD is POST
# 0 ==> unlimited input
maxlen = 0


def _parseparam(s):
    while s[:1] == ';':
        s = s[1:]
        end = s.find(';')
        while end > 0 and (s.count('"', 0, end) - s.count('\\"', 0, end)) % 2:
            end = s.find(';', end + 1)
        if end < 0:
            end = len(s)
        f = s[:end]
        yield f.strip()
        s = s[end:]


def parse_header(line):
    """Parse a Content-type like header.

    Return the main content-type and a dictionary of options.

    """
    parts = _parseparam(';' + line)
    key = next(parts)
    pdict = {}
    for p in parts:
        i = p.find('=')
        if i >= 0:
            name = p[:i].strip().lower()
            value = p[i+1:].strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
                value = value.replace('\\\\', '\\').replace('\\"', '"')
            pdict[name] = value
    return key, pdict


def valid_boundary(s):
    if isinstance(s, bytes):
        _vb_pattern = b"^[ -~]{0,200}[!-~]$"
    else:
        _vb_pattern = "^[ -~]{0,200}[!-~]$"
    return re.match(_vb_pattern, s)


# On Python 2, it isn't straightforward to wrap an ordinary file object in a
# TextIOWrapper.  This helps.
class _FileIOWrapper(object):
    def __init__(self, raw):
        self._raw = raw

    def readable(self):
        return not self.closed

    def seekable(self):
        return not self.closed

    def writable(self):
        return not self.closed

    def __getattr__(self, name):
        return getattr(self._raw, name)


class MiniFieldStorage(object):

    """Like FieldStorage, for use when no file uploads are possible."""

    # Dummy attributes
    filename = None
    list = None
    type = None
    file = None
    type_options = {}
    headers = {}

    def __init__(self, name, value):
        """Constructor from field name and value."""
        self.name = name
        self.value = value


class FieldStorage(object):

    """Store a sequence of fields, reading multipart/form-data.

    This class provides naming, typing, files stored on disk, and
    more.  At the top level, it is accessible like a dictionary, whose
    keys are the field names.  (Note: None can occur as a field name.)
    The items are either a Python list (if there's multiple values) or
    another FieldStorage or MiniFieldStorage object.  If it's a single
    object, it has the following attributes:

    name: the field name, if specified; otherwise None

    filename: the filename, if specified; otherwise None; this is the
        client side filename, *not* the file name on which it is
        stored (that's a temporary file you don't deal with)

    value: the value as a *string*; for file uploads, this
        transparently reads the file every time you request the value
        and returns *bytes*

    file: the file(-like) object from which you can read the data *as
        bytes* ; None if the data is stored a simple string

    headers: a dictionary(-like) object (sometimes email.message.Message or a
        subclass thereof) containing *all* headers

    The class is subclassable, mostly for the purpose of overriding
    the make_file() method, which is called internally to come up with
    a file open for reading and writing.  This makes it possible to
    override the default choice of storing all files in a temporary
    directory and unlinking them as soon as they have been opened.

    """
    def __init__(self, fp=None, headers=None, outerboundary=b'',
                 environ=os.environ, limit=None,
                 encoding='utf-8', errors='replace'):
        """Constructor.  Read multipart/* until last part.

        Arguments, all optional:

        fp              : file pointer; default: sys.stdin.buffer
            (not used when the request method is GET)
            Can be :
            1. a TextIOWrapper object
            2. an object whose read() and readline() methods return bytes

        headers         : header dictionary-like object; default:
            taken from environ as per CGI spec

        outerboundary   : terminating multipart boundary
            (for internal use only)

        environ         : environment dictionary; default: os.environ

        limit : used internally to read parts of multipart/form-data forms,
            to exit from the reading loop when reached. It is the difference
            between the form content-length and the number of bytes already
            read

        encoding, errors : the encoding and error handler used to decode the
            binary stream to strings. Must be the same as the charset defined
            for the page sending the form (content-type : meta http-equiv or
            header)

        """
        method = 'GET'
        if 'REQUEST_METHOD' in environ:
            method = environ['REQUEST_METHOD'].upper()
        self.qs_on_post = None
        if method == 'GET' or method == 'HEAD':
            if 'QUERY_STRING' in environ:
                qs = environ['QUERY_STRING']
            else:
                qs = ""
            if not PYTHON2:  # pragma: no cover
                qs = qs.encode(
                    locale.getpreferredencoding(), 'surrogateescape')
            fp = BytesIO(qs)
            if headers is None:
                headers = {'content-type':
                           "application/x-www-form-urlencoded"}
        if headers is None:
            headers = {}
            if method == 'POST':
                # Set default content-type for POST to what's traditional
                headers['content-type'] = "application/x-www-form-urlencoded"
            if 'CONTENT_TYPE' in environ:
                headers['content-type'] = environ['CONTENT_TYPE']
            if 'QUERY_STRING' in environ:
                self.qs_on_post = environ['QUERY_STRING']
            if 'CONTENT_LENGTH' in environ:
                headers['content-length'] = environ['CONTENT_LENGTH']
        else:
            if not (isinstance(headers, (Mapping, Message))):
                raise TypeError("headers must be mapping or an instance of "
                                "email.message.Message")
        self.headers = headers
        if fp is None:
            if PYTHON2:  # pragma: no cover
                self.fp = sys.stdin
            else:  # pragma: no cover
                self.fp = sys.stdin.buffer
        # self.fp.read() must return bytes
        elif isinstance(fp, TextIOWrapper):
            self.fp = fp.buffer
        else:
            if not (hasattr(fp, 'read') and hasattr(fp, 'readline')):
                raise TypeError("fp must be file pointer")
            self.fp = fp

        self.encoding = encoding
        self.errors = errors

        if not isinstance(outerboundary, bytes):
            raise TypeError('outerboundary must be bytes, not %s'
                            % type(outerboundary).__name__)
        self.outerboundary = outerboundary

        self.bytes_read = 0
        self.limit = limit

        # Process content-disposition header
        pdict = {}
        if 'content-disposition' in self.headers:
            _, pdict = parse_header(self.headers['content-disposition'])
        self.name = None
        if 'name' in pdict:
            self.name = pdict['name']
        self.filename = None
        if 'filename' in pdict:
            self.filename = pdict['filename']
        self._binary_file = self.filename is not None

        # Process content-type header
        #
        # Honor any existing content-type header.  But if there is no
        # content-type header, use some sensible defaults.  Assume
        # outerboundary is "" at the outer level, but something non-false
        # inside a multi-part.  The default for an inner part is text/plain,
        # but for an outer part it should be urlencoded.  This should catch
        # bogus clients which erroneously forget to include a content-type
        # header.
        #
        # See below for what we do if there does exist a content-type header,
        # but it happens to be something we don't understand.
        if 'content-type' in self.headers:
            ctype, pdict = parse_header(self.headers['content-type'])
        elif self.outerboundary or method != 'POST':
            ctype, pdict = "text/plain", {}
        else:
            ctype, pdict = 'application/x-www-form-urlencoded', {}
        if 'boundary' in pdict:
            self.innerboundary = pdict['boundary'].encode(self.encoding,
                                                          self.errors)
        else:
            self.innerboundary = b""

        clen = -1
        if 'content-length' in self.headers:
            try:
                clen = int(self.headers['content-length'])
            except ValueError:
                pass
            if maxlen and clen > maxlen:
                raise ValueError('Maximum content length exceeded')
        self.length = clen
        if self.limit is None and clen >= 0:
            self.limit = clen

        self.list = self.file = None
        self.done = 0
        if ctype == 'application/x-www-form-urlencoded':
            self.read_urlencoded()
        elif ctype[:10] == 'multipart/':
            self.read_multi(environ)
        else:
            self.read_single()

    def __del__(self):
        try:
            self.file.close()
        except AttributeError:
            pass

    def __getattr__(self, name):
        if name != 'value':
            raise AttributeError(name)
        if self.file:
            self.file.seek(0)
            value = self.file.read()
            self.file.seek(0)
        elif self.list is not None:
            value = self.list
        else:
            value = None
        return value

    def read_urlencoded(self):
        """Internal: read data in query string format."""
        qs = self.fp.read(self.length)
        if not isinstance(qs, bytes):
            raise ValueError("%s should return bytes, got %s"
                             % (self.fp, type(qs).__name__))
        if not PYTHON2:  # pragma: no cover
            qs = qs.decode(self.encoding, self.errors)
        if self.qs_on_post:
            qs += '&' + self.qs_on_post
        kwargs = {}
        if not PYTHON2:  # pragma: no cover
            kwargs['encoding'] = self.encoding
            kwargs['errors'] = self.errors
        query = parse_qsl(qs, keep_blank_values=True, **kwargs)
        self.list = [MiniFieldStorage(key, value) for key, value in query]
        self.skip_lines()

    def read_multi(self, environ):
        """Internal: read a part that is itself multipart."""
        ib = self.innerboundary
        if not valid_boundary(ib):
            raise ValueError('Invalid boundary in multipart form: %r' % (ib,))
        self.list = []
        if self.qs_on_post:
            kwargs = {}
            if not PYTHON2:  # pragma: no cover
                kwargs['encoding'] = self.encoding
                kwargs['errors'] = self.errors
            query = parse_qsl(
                self.qs_on_post, keep_blank_values=True, **kwargs)
            self.list.extend(
                MiniFieldStorage(key, value) for key, value in query)

        first_line = self.fp.readline()  # bytes
        if not isinstance(first_line, bytes):
            raise ValueError("%s should return bytes, got %s"
                             % (self.fp, type(first_line).__name__))
        self.bytes_read += len(first_line)

        # Ensure that we consume the file until we've hit our inner boundary
        while (first_line.strip() != (b"--" + self.innerboundary) and
                first_line):
            first_line = self.fp.readline()
            self.bytes_read += len(first_line)

        while True:
            parser = FeedParser()
            hdr_text = b""
            while True:
                data = self.fp.readline()
                hdr_text += data
                if not data.strip():
                    break
            if not hdr_text:
                break
            # parser takes strings, not bytes
            self.bytes_read += len(hdr_text)
            parser.feed(hdr_text.decode(self.encoding, self.errors))
            headers = parser.close()

            # Some clients add Content-Length for part headers, ignore them
            if 'content-length' in headers:
                del headers['content-length']

            limit = None if self.limit is None \
                else self.limit - self.bytes_read
            part = self.__class__(
                self.fp, headers, ib, environ, limit,
                self.encoding, self.errors)

            self.bytes_read += part.bytes_read
            self.list.append(part)
            if part.done or self.bytes_read >= self.length > 0:
                break
        self.skip_lines()

    def read_single(self):
        """Internal: read an atomic part."""
        if self.length >= 0:
            self.read_content()
            self.skip_lines()
        else:
            self.read_lines()
        self.file.seek(0)

    bufsize = 8*1024            # I/O buffering size for copy to file

    def read_content(self):
        """Internal: read data up until content-length len."""
        if self.length > 1000:
            self.file = self.make_file()
        else:
            self.file = self.io_object()
        self.__file = self.file
        todo = self.length
        if todo >= 0:
            while todo > 0:
                data = self.fp.read(min(todo, self.bufsize))  # bytes
                self.bytes_read += len(data)
                if not data:
                    self.done = -1
                    break
                self.__write(data)
                todo = todo - len(data)

    def read_lines(self):
        """Internal: read lines until EOF or outerboundary."""
        self.file = self.__file = self.io_object()
        if self.outerboundary:
            self.read_lines_to_outerboundary()
        elif self.length >= 0:
            self.read_content()
        else:
            self.read_lines_to_eof()

    def __write(self, line):
        """line is always bytes, not string"""
        if self.__file is not None:
            if self.__file.tell() + len(line) > 1000:
                self.file = self.make_file()
                data = self.__file.getvalue()
                self.file.write(data)
                self.__file = None
        if self._binary_file:
            # keep bytes
            self.file.write(line)
        else:
            # decode to string
            self.file.write(line.decode(self.encoding, self.errors))

    def read_lines_to_eof(self):
        """Internal: read lines until EOF."""
        while 1:
            line = self.fp.read(1 << 16)  # bytes
            self.bytes_read += len(line)
            if not line:
                self.done = -1
                break
            self.__write(line)

    def read_lines_to_outerboundary(self):
        """Internal: read lines until outerboundary.
        Data is read as bytes: boundaries and line ends must be converted
        to bytes for comparisons.
        """
        next_boundary = b"--" + self.outerboundary
        last_boundary = next_boundary + b"--"
        delim = b""
        last_line_lfend = True
        _read = 0
        while 1:
            if self.limit is not None and _read >= self.limit:
                break
            line = self.fp.readline(1 << 16)  # bytes
            self.bytes_read += len(line)
            _read += len(line)
            if not line:
                self.done = -1
                break
            if delim == b"\r":
                line = delim + line
                delim = b""
            if line.startswith(b"--") and last_line_lfend:
                strippedline = line.rstrip()
                if strippedline == next_boundary:
                    break
                if strippedline == last_boundary:
                    self.done = 1
                    break
            odelim = delim
            if line.endswith(b"\r\n"):
                delim = b"\r\n"
                line = line[:-2]
                last_line_lfend = True
            elif line.endswith(b"\n"):
                delim = b"\n"
                line = line[:-1]
                last_line_lfend = True
            elif line.endswith(b"\r"):
                # We may interrupt \r\n sequences if they span the 2**16
                # byte boundary
                delim = b"\r"
                line = line[:-1]
                last_line_lfend = False
            else:
                delim = b""
                last_line_lfend = False
            self.__write(odelim + line)

    def skip_lines(self):
        """Internal: skip lines until outer boundary if defined."""
        if not self.outerboundary or self.done:
            return
        next_boundary = b"--" + self.outerboundary
        last_boundary = next_boundary + b"--"
        last_line_lfend = True
        while True:
            line = self.fp.readline(1 << 16)
            self.bytes_read += len(line)
            if not line:
                self.done = -1
                break
            if line.endswith(b"--") and last_line_lfend:
                strippedline = line.strip()
                if strippedline == next_boundary:
                    break
                if strippedline == last_boundary:
                    self.done = 1
                    break
            last_line_lfend = line.endswith(b'\n')

    def make_file(self):
        """Overridable: return a readable & writable file.

        The file will be used as follows:
        - data is written to it
        - seek(0)
        - data is read from it

        The file is opened in binary mode for files, in text mode
        for other fields

        This version opens a temporary file for reading and writing,
        and immediately deletes (unlinks) it.  The trick (on Unix!) is
        that the file can still be used, but it can't be opened by
        another process, and it will automatically be deleted when it
        is closed or when the current process terminates.

        If you want a more permanent file, you derive a class which
        overrides this method.  If you want a visible temporary file
        that is nevertheless automatically deleted when the script
        terminates, try defining a __del__ method in a derived class
        which unlinks the temporary files you have created.

        """
        f = tempfile.TemporaryFile("wb+")
        if not self._binary_file:
            if PYTHON2:  # no cover
                f = _FileIOWrapper(f)
            f = TextIOWrapper(f, encoding=self.encoding, newline='\n')
        return f

    def io_object(self):
        if self._binary_file:
            return BytesIO() # store data as bytes for files
        else:
            return StringIO() # as strings for other fields
