zope.publisher allows you to publish Python objects on the web.  It
has support for plain HTTP/WebDAV clients, web browsers as well as
XML-RPC and FTP clients.  Input and output streams are represented by
request and response objects which allow for easy client interaction
from Python.  The behaviour of the publisher is geared towards WSGI
compatibility.

Changes
=======

Next Version
------------

- zope.publisher now works on Python2.5

3.4.1b1 (2007-07-13)
--------------------

No changes.

3.4.0b2 (2007-07-05)
--------------------

* Fix https://bugs.launchpad.net/zope3/+bug/122054:  
  HTTPInputStream understands both the CONTENT_LENGTH and
  HTTP_CONTENT_LENGTH environment variables. It is also now tolerant
  of empty strings and will treat those as if the variable were
  absent.

3.4.0b1 (2007-07-05)
--------------------

* Fix caching issue. The input stream never got cached in a temp file 
  because of a wrong content-length header lookup. Added CONTENT_LENGTH 
  header check in addition to the previous used HTTP_CONTENT_LENGTH. The 
  HTTP_ prefix is sometimes added by some CGI proxies, but CONTENT_LENGTH
  is the right header info for the size.

* Fix https://bugs.launchpad.net/zope3/+bug/98413:
  HTTPResponse.handleException should set the content type

3.4.0a1 (2007-04-22)
--------------------

Initial release as a separate project, corresponds to zope.publisher
from Zope 3.4.0a1
