##############################################################################
#
# From the test.test_cgi module in Python 3.8, licensed as follows:
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

from collections import defaultdict
from io import BytesIO
import tempfile
import unittest

from zope.publisher._fieldstorage import FieldStorage, parse_header


def gen_result(data, environ):
    encoding = 'latin-1'
    fake_stdin = BytesIO(data.encode(encoding))
    fake_stdin.seek(0)
    form = FieldStorage(fp=fake_stdin, environ=environ, encoding=encoding)

    result = defaultdict(list)
    for item in form.list:
        result[item.name].append(item.value)

    return result


class TestFieldStorage(unittest.TestCase):

    def test_fieldstorage_invalid(self):
        self.assertRaises(
            TypeError, FieldStorage, "not-a-file-obj",
            environ={"REQUEST_METHOD": "PUT"})
        self.assertRaises(TypeError, FieldStorage, "foo", "bar")

    def test_fieldstorage_read(self):
        # FieldStorage uses read, which has the capacity to read all contents
        # of the input file into memory; we use read's size argument to
        # prevent that for files that do not contain any newlines in
        # non-GET/HEAD requests
        class TestReadFile:
            def __init__(self, file):
                self.file = file
                self.numcalls = 0

            def read(self, size=None):
                self.numcalls += 1
                if size:
                    return self.file.read(size)
                else:
                    return self.file.read()

            def __getattr__(self, name):
                file = self.__dict__['file']
                a = getattr(file, name)
                if not isinstance(a, int):
                    setattr(self, name, a)
                return a

        f = TestReadFile(tempfile.TemporaryFile("wb+"))
        self.addCleanup(f.close)
        f.write(b'x' * 256 * 1024)
        f.seek(0)
        env = {'REQUEST_METHOD': 'PUT'}
        fs = FieldStorage(fp=f, environ=env)
        self.addCleanup(fs.file.close)
        # if we're not chunking properly, read is only called twice
        # (by read_binary); if we are chunking properly, it will be called 5
        # times as long as the chunksize is 1 << 16.
        self.assertGreater(f.numcalls, 2)
        f.close()

    def test_fieldstorage_multipart(self):
        # Test basic FieldStorage multipart parsing
        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'multipart/form-data; boundary={}'.format(
                BOUNDARY),
            'CONTENT_LENGTH': '558',
        }
        fp = BytesIO(POSTDATA.encode('latin-1'))
        fs = FieldStorage(fp, environ=env, encoding="latin-1")
        self.assertEqual(len(fs.list), 4)
        expect = [
            {'name': 'id', 'filename': None, 'value': '1234'},
            {'name': 'title', 'filename': None, 'value': ''},
            {'name': 'file', 'filename': 'test.txt',
             'value': b'Testing 123.\n'},
            {'name': 'submit', 'filename': None, 'value': ' Add '},
        ]
        for x in range(len(fs.list)):
            for k, exp in expect[x].items():
                got = getattr(fs.list[x], k)
                self.assertEqual(got, exp)

    def test_fieldstorage_multipart_leading_whitespace(self):
        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'multipart/form-data; boundary={}'.format(
                BOUNDARY),
            'CONTENT_LENGTH': '560',
        }
        # Add some leading whitespace to our post data that will cause the
        # first line to not be the innerboundary.
        fp = BytesIO(b"\r\n" + POSTDATA.encode('latin-1'))
        fs = FieldStorage(fp, environ=env, encoding="latin-1")
        self.assertEqual(len(fs.list), 4)
        expect = [
            {'name': 'id', 'filename': None, 'value': '1234'},
            {'name': 'title', 'filename': None, 'value': ''},
            {'name': 'file', 'filename': 'test.txt',
             'value': b'Testing 123.\n'},
            {'name': 'submit', 'filename': None, 'value': ' Add '}
        ]
        for x in range(len(fs.list)):
            for k, exp in expect[x].items():
                got = getattr(fs.list[x], k)
                self.assertEqual(got, exp)

    def test_fieldstorage_multipart_non_ascii(self):
        # Test basic FieldStorage multipart parsing
        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'multipart/form-data; boundary={}'.format(
                BOUNDARY),
            'CONTENT_LENGTH': '558',
        }
        for encoding in ['iso-8859-1', 'utf-8']:
            fp = BytesIO(POSTDATA_NON_ASCII.encode(encoding))
            fs = FieldStorage(fp, environ=env, encoding=encoding)
            self.assertEqual(len(fs.list), 1)
            expect = [
                {'name': 'id', 'filename': None, 'value': u'\xe7\xf1\x80'}
            ]
            for x in range(len(fs.list)):
                for k, exp in expect[x].items():
                    got = getattr(fs.list[x], k)
                    self.assertEqual(got, exp)

    def test_fieldstorage_multipart_maxline(self):
        # Issue #18167
        maxline = 1 << 16
        self.maxDiff = None

        def check(content):
            data = """---123
Content-Disposition: form-data; name="upload"; filename="fake.txt"
Content-Type: text/plain

%s
---123--
""".replace('\n', '\r\n') % content
            environ = {
                'CONTENT_LENGTH':   str(len(data)),
                'CONTENT_TYPE':     'multipart/form-data; boundary=-123',
                'REQUEST_METHOD':   'POST',
            }
            self.assertEqual(gen_result(data, environ),
                             {'upload': [content.encode('latin1')]})
        check('x' * (maxline - 1))
        check('x' * (maxline - 1) + '\r')
        check('x' * (maxline - 1) + '\r' + 'y' * (maxline - 1))

    def test_fieldstorage_multipart_w3c(self):
        # Test basic FieldStorage multipart parsing (W3C sample)
        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'multipart/form-data; boundary={}'.format(
                BOUNDARY_W3),
            'CONTENT_LENGTH': str(len(POSTDATA_W3)),
        }
        fp = BytesIO(POSTDATA_W3.encode('latin-1'))
        fs = FieldStorage(fp, environ=env, encoding="latin-1")
        self.assertEqual(len(fs.list), 2)
        self.assertEqual(fs.list[0].name, 'submit-name')
        self.assertEqual(fs.list[0].value, 'Larry')
        self.assertEqual(fs.list[1].name, 'files')
        files = fs.list[1].value
        self.assertEqual(len(files), 2)
        expect = [
            {'name': None, 'filename': 'file1.txt',
             'value': b'... contents of file1.txt ...'},
            {'name': None, 'filename': 'file2.gif',
             'value': b'...contents of file2.gif...'},
        ]
        for x in range(len(files)):
            for k, exp in expect[x].items():
                got = getattr(files[x], k)
                self.assertEqual(got, exp)

    def test_fieldstorage_part_content_length(self):
        BOUNDARY = "JfISa01"
        POSTDATA = """--JfISa01
Content-Disposition: form-data; name="submit-name"
Content-Length: 5

Larry
--JfISa01"""
        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'multipart/form-data; boundary={}'.format(
                BOUNDARY),
            'CONTENT_LENGTH': str(len(POSTDATA)),
        }
        fp = BytesIO(POSTDATA.encode('latin-1'))
        fs = FieldStorage(fp, environ=env, encoding="latin-1")
        self.assertEqual(len(fs.list), 1)
        self.assertEqual(fs.list[0].name, 'submit-name')
        self.assertEqual(fs.list[0].value, 'Larry')

    def test_content_length_no_content_disposition(self):
        body = b'{"test":123}'
        env = {
            'CONTENT_LENGTH': len(body),
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'application/json',
            'wsgi.input': BytesIO(body),
        }

        form = FieldStorage(fp=env['wsgi.input'], environ=env)
        self.assertEqual(form.file.read(), body.decode(form.encoding))

    def test_field_storage_multipart_no_content_length(self):
        fp = BytesIO(b"""--MyBoundary
Content-Disposition: form-data; name="my-arg"; filename="foo"

Test

--MyBoundary--
""")
        env = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": "multipart/form-data; boundary=MyBoundary",
            "wsgi.input": fp,
        }
        fs = FieldStorage(fp, environ=env)
        self.assertEqual(len(fs.list), 1)
        self.assertEqual(fs.list[0].name, "my-arg")
        self.assertEqual(len(fs.list[0].file.read()), 5)

    _qs_result = {
        'key1': ['value1'],
        'key2': ['value2x', 'value2y'],
        'key3': ['value3'],
        'key4': ['value4'],
    }

    def testQSAndUrlEncode(self):
        data = "key2=value2x&key3=value3&key4=value4"
        environ = {
            'CONTENT_LENGTH':   str(len(data)),
            'CONTENT_TYPE':     'application/x-www-form-urlencoded',
            'QUERY_STRING':     'key1=value1&key2=value2y',
            'REQUEST_METHOD':   'POST',
        }
        v = gen_result(data, environ)
        self.assertEqual(self._qs_result, v)

    def testQSAndFormData(self):
        data = """---123
Content-Disposition: form-data; name="key2"

value2y
---123
Content-Disposition: form-data; name="key3"

value3
---123
Content-Disposition: form-data; name="key4"

value4
---123--
"""
        environ = {
            'CONTENT_LENGTH':   str(len(data)),
            'CONTENT_TYPE':     'multipart/form-data; boundary=-123',
            'QUERY_STRING':     'key1=value1&key2=value2x',
            'REQUEST_METHOD':   'POST',
        }
        v = gen_result(data, environ)
        self.assertEqual(self._qs_result, v)

    def testQSAndFormDataFile(self):
        data = """---123
Content-Disposition: form-data; name="key2"

value2y
---123
Content-Disposition: form-data; name="key3"

value3
---123
Content-Disposition: form-data; name="key4"

value4
---123
Content-Disposition: form-data; name="upload"; filename="fake.txt"
Content-Type: text/plain

this is the content of the fake file

---123--
"""
        environ = {
            'CONTENT_LENGTH':   str(len(data)),
            'CONTENT_TYPE':     'multipart/form-data; boundary=-123',
            'QUERY_STRING':     'key1=value1&key2=value2x',
            'REQUEST_METHOD':   'POST',
        }
        result = self._qs_result.copy()
        result.update({
            'upload': [b'this is the content of the fake file\n'],
        })
        v = gen_result(data, environ)
        self.assertEqual(result, v)

    def test_parse_header(self):
        self.assertEqual(
            parse_header("text/plain"),
            ("text/plain", {}))
        self.assertEqual(
            parse_header("text/vnd.just.made.this.up ; "),
            ("text/vnd.just.made.this.up", {}))
        self.assertEqual(
            parse_header("text/plain;charset=us-ascii"),
            ("text/plain", {"charset": "us-ascii"}))
        self.assertEqual(
            parse_header('text/plain ; charset="us-ascii"'),
            ("text/plain", {"charset": "us-ascii"}))
        self.assertEqual(
            parse_header('text/plain ; charset="us-ascii"; another=opt'),
            ("text/plain", {"charset": "us-ascii", "another": "opt"}))
        self.assertEqual(
            parse_header('attachment; filename="silly.txt"'),
            ("attachment", {"filename": "silly.txt"}))
        self.assertEqual(
            parse_header('attachment; filename="strange;name"'),
            ("attachment", {"filename": "strange;name"}))
        self.assertEqual(
            parse_header('attachment; filename="strange;name";size=123;'),
            ("attachment", {"filename": "strange;name", "size": "123"}))
        self.assertEqual(
            parse_header('form-data; name="files"; filename="fo\\"o;bar"'),
            ("form-data", {"name": "files", "filename": 'fo"o;bar'}))


BOUNDARY = "---------------------------721837373350705526688164684"

POSTDATA = u"""-----------------------------721837373350705526688164684
Content-Disposition: form-data; name="id"

1234
-----------------------------721837373350705526688164684
Content-Disposition: form-data; name="title"


-----------------------------721837373350705526688164684
Content-Disposition: form-data; name="file"; filename="test.txt"
Content-Type: text/plain

Testing 123.

-----------------------------721837373350705526688164684
Content-Disposition: form-data; name="submit"

 Add\x20
-----------------------------721837373350705526688164684--
"""

POSTDATA_NON_ASCII = u"""-----------------------------721837373350705526688164684
Content-Disposition: form-data; name="id"

\xe7\xf1\x80
-----------------------------721837373350705526688164684
"""

# http://www.w3.org/TR/html401/interact/forms.html#h-17.13.4
BOUNDARY_W3 = "AaB03x"
POSTDATA_W3 = u"""--AaB03x
Content-Disposition: form-data; name="submit-name"

Larry
--AaB03x
Content-Disposition: form-data; name="files"
Content-Type: multipart/mixed; boundary=BbC04y

--BbC04y
Content-Disposition: file; filename="file1.txt"
Content-Type: text/plain

... contents of file1.txt ...
--BbC04y
Content-Disposition: file; filename="file2.gif"
Content-Type: image/gif
Content-Transfer-Encoding: binary

...contents of file2.gif...
--BbC04y--
--AaB03x--
"""
