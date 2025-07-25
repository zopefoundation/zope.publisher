=========
 Changes
=========

7.4 (unreleased)
================

- Nothing changed yet.

7.3 (2025-03-05)
================

- Replace `pkg_resources` with `importlib.metadata`.

7.2 (2024-12-19)
================

- Drop support for Python 3.8.

- Replace deprecated multipart argument ``memfile_limit`` with ``spool_limit``

- Increase the default value of ``part_limit`` for ``multipart`` to 1024 as 128
  is too low for some use cases.

7.1 (2024-09-27)
================

- Drop support for Python 3.7.

- Add support for Python 3.12, 3.13.

- Fix test suite to use proper line endings (``\r\n``) in raw multipart/form-data
  HTTP requests, because multipart 1.0.0 is stricter about line endings.
  Fixes `issue #74 <https://github.com/zopefoundation/zope.publisher/issues/74>`_.

- ``FileUpload`` objects now implement a fallback ``seekable()`` method on
  Python 3.7 through 3.10, where tempfile.SpooledTemporaryFile lacks it.
  Fixes `issue 44 <https://github.com/zopefoundation/zope.publisher/issues/44>`_
  again, which had regressed due to certain assumptions that were no longer
  true after the multipart 1.0.0 release.


7.0 (2023-08-29)
================

- Drop support for Python 2.7, 3.5, 3.6.

- Drop support for ``im_func`` and ``func_code``.

- Add support for Python 3.11.


6.1.0 (2022-03-15)
==================

- Revamp handling of query string and form decoding in ``BrowserRequest``.

  The previous approach was to tell underlying libraries to decode inputs
  using ISO-8859-1, then re-encode as ISO-8859-1 and decode using an
  encoding deduced from the ``Accept-Charset`` request header.  However,
  this didn't make much conceptual sense (since ``Accept-Charset`` defines
  the preferred *response* encoding), and it made it impossible to handle
  cases where the encoding was specified as something other than ISO-8859-1
  in the request (which might even be on a per-item basis, in the case of
  ``multipart/form-data`` input).

  We now only perform the dubious ``Accept-Charset`` guessing for query
  strings; in other cases we let ``multipart`` determine the encoding,
  defaulting to UTF-8 as per the HTML specification.  For cases where
  applications need to specify some other default form encoding,
  ``BrowserRequest`` subclasses can now set ``default_form_charset``.

  See `issue 65
  <https://github.com/zopefoundation/zope.publisher/issues/65>`_.

- Add support for Python 3.10.


6.0.2 (2021-06-07)
==================

- Avoid traceback reference cycle in ``zope.publisher.publish.publish``.
- Handle empty Content-Type environment variable gracefully.


6.0.1 (2021-04-15)
==================

- Fix test compatibility with zope.interface 5.4.


6.0.0 (2021-01-20)
==================

- Port form data parsing to ``multipart``, which is a new dependency.  See
  `issue 39 <https://github.com/zopefoundation/zope.publisher/issues/39>`_.
  Note that as a result ``FileUpload`` objects no longer have a ``name``
  attribute: the ``name`` attribute couldn't be used in portable code in any
  case, and the usual methods on open files should be used instead.

- Add support for Python 3.9.


5.2.1 (2020-06-15)
==================

- Fix text/bytes handling on Python 3 for some response edge cases. See
  `pull request 51
  <https://github.com/zopefoundation/zope.publisher/pull/51>`_.


5.2.0 (2020-03-30)
==================

- Add support for Python 3.8.

- Ensure all objects have a consistent interface resolution order. See
  `issue 49
  <https://github.com/zopefoundation/zope.publisher/issues/49>`_.

- Drop support for the deprecated ``python setup.py test`` command.

5.1.1 (2019-08-08)
==================

- Avoid using ``urllib.parse.splitport()`` which was deprecated in Python 3.8.
  See `issue 38 <https://github.com/zopefoundation/zope.publisher/issues/38>`_


5.1.0 (2019-07-12)
==================

- Drop support for Python 3.4.

- ``FileUpload`` objects now support the ``seekable()`` method on Python 3.
  Fixes `issue 44 <https://github.com/zopefoundation/zope.publisher/issues/44>`_.

- Character set handling was rather comprehensively broken on Python 3.
  It should be fixed now.  See `issue 41
  <https://github.com/zopefoundation/zope.publisher/issues/41>`_.


5.0.1 (2018-10-19)
==================

- Fix a ``DeprecationWarning``.


5.0.0 (2018-10-10)
===================

- Backwards incompatible change: Remove ``zope.publisher.tests.httprequest``.
  It is not used inside this package and was never ported to Python 3.
  Fixes https://github.com/zopefoundation/zope.publisher/issues/4.

- Add support for Python 3.7 and PyPy3.

- Drop support for Python 3.3.

- Fix ``XMLRPCResponse`` having a str body (instead of a bytes body)
  which could lead to ``TypeError`` on Python 3. See `issue 26
  <https://github.com/zopefoundation/zope.publisher/issues/26>`_.


4.3.2 (2017-05-23)
==================

- Fix instances of ``BaseRequest`` (including ``BrowserRequest``)
  being unexpectedly ``False`` on Python 3 by defining ``__bool__``.
  Such instances were always ``True`` on Python 2. See `issue 18
  <https://github.com/zopefoundation/zope.publisher/issues/18>`_.


4.3.1 (2017-04-24)
==================

- Add support for Python 3.6.

- Accept both new and old locations for ``__code__`` in
  ``zope.publisher.publisher.unwrapMethod``. This restores compatibility with
  Products.PythonScripts, where parameters were not extracted.
  [maurits, thet, MatthewWilkes]

- Fix file uploads on python 3.4 and up. cgi.FieldStorage explicitly
  closes files when it is garbage collected. For details, see:

  * http://bugs.python.org/issue18394
  * https://hg.python.org/cpython/rev/c0e9ba7b26d5
  * https://github.com/zopefoundation/zope.publisher/pull/13

  We now keep a reference to the FieldStorage till we are finished
  processing the request.

- Fix POST with large values on Python 3. Related to cgi.FieldStorage
  doing the decoding in Python 3. See `pull 16
  <https://github.com/zopefoundation/zope.publisher/pull/16>`_.

4.3.0 (2016-07-04)
==================

- Add support for Python 3.5.

- Drop support for Python 2.6 and 3.2.


4.2.2 (2015-11-16)
==================

- Emit HTTP response headers in a deterministic order (GH #8).

4.2.1 (2015-06-05)
==================

- Add support for Python 3.2.

4.2.0 (2015-06-02)
==================

- Add support for PyPy and PyPy3.

4.1.0 (2014-12-27)
==================

- Add support for Python 3.4.

4.0.0 (2014-12-22)
==================

- Add ``__traceback_info__`` to ``response.redirect()`` to ease debugging
  untrusted redirects.

- Add ``trusted`` support for ``Redirect`` exception

4.0.0a4 (2013-03-12)
====================

- Support UTF-8-encoding application/json responses returned as Unicode.

4.0.0a3 (2013-02-28)
====================

- Return bytes from ``PrincipalLogging.getLogMessage`` instead of unicode.

4.0.0a2 (2013-02-22)
====================

- Use BytesIO in ``zope.publisher.xmlrpc.TestRequest``.

4.0.0a1 (2013-02-21)
====================

- Replace deprecated ``zope.component.adapts`` usage with equivalent
  ``zope.component.adapter`` decorator.

- Replace deprecated ``zope.interface.implements`` usage with equivalent
  ``zope.interface.implementer`` decorator.

- Drop support for Python 2.4, 2.5 and pypy.

- Add support for Python 3.3.

- Wrap ``with interaction()`` in try/finally.

- Don't guess the content type with 304 responses which MUST NOT /
  SHOULD NOT include it according to:
  http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.3.5

  Unfortunately, the content type will still be guessed if the result is
  set before the status.

3.13.0 (2011-11-17)
===================

- Fix error when no charset matches form data and HTTP_ACCEPT_CHARSET contains a ``*``.

- Add test convenience helper ``create_interaction`` and ``with interaction()``.


3.12.6 (2010-12-17)
===================

- Upload a non-CRLF version to pypi.


3.12.5 (2010-12-14)
===================

- Rename the ``tests`` extra to ``test``.

- Add a test for our own configure.zcml.

- Use UTF-8 as the charset if the browser does not set a header,
  per W3C spec.

3.12.4 (2010-07-15)
===================

- LP #131460: Make principal logging unicode safe.

- Remove use of string exceptions in tests, http://bugs.debian.org/585343

- Add ``IStartRequestEvent`` and ``StartRequestEvent`` for use in
  ``zope.app.publication`` (matching up with ``IEndRequestEvent`` and
  ``EndRequestEvent``).  Includes refactoring to produce one definition of
  'event with a request' - IRequestEvent.

3.12.3 (2010-04-30)
===================

- LP #209440: Don't obscure original exception when handling retries
  in ``publish.publish()`` with ``handleErrors == False``.   This change
  makes debugging such exception in unit tests easier.
  Thanks to James Henstridge for the patch.

- LP #98395: allow unicode output of XML content whose mimetype does not
  begin with ``text/``, per RFC 3023 as well as for content types ending
  in ``+xml`` such as Mozilla XUL's ``application/vnd+xml``.  Thanks to
  Justin Ryan for the patch.

3.12.2 (2010-04-16)
===================

- Remove use of ``zope.testing.doctestunit`` in favor of stdlib's ``doctest``.

- Fix bug where xml-rpc requests would hang when served using
  ``paster.httpserver``.

3.12.1 (2010-02-21)
===================

- Ensure that ``BaseRequest.traverse`` does not call traversal hooks on
  elements previously traversed but wrapped in a security proxy.

3.12.0 (2009-12-31)
===================

- Revert change done in 3.6.2, removing the ``zope.authentication``
  dependency again. Move the ``BasicAuthAdapter`` and ``FTPAuth`` adapters
  to the new ``zope.login`` package.

3.11.0 (2009-12-15)
===================

- Move ``EndRequestEvent`` and ``IEndRequestEvent`` here from
  ``zope.app.publication``.

3.10.1 (2009-11-28)
===================

- Declare minimum dependency on ``zope.contenttype`` 3.5 (omitted in 3.10).

3.10.0 (2009-10-22)
===================

- Move the implementation of ``zope.publisher.contenttype`` to
  ``zope.contenttype.parse``, leaving BBB imports and moving tests along.
  ``zope.contenttype`` is a new but light-weight dependency of this package.

- Support Python 2.6 by keeping QUERY_STRING out of request.form if
  the method is a POST.  The original QUERY_STRING is still available if
  further processing is needed.

- Better support the zcml ``defaultSkin`` directive's behavior (registering
  an interface as a default skin) in the ``setDefaultSkin`` function.

3.9.3 (2009-10-08)
==================

- Fix the check for untrusted redirects introduced in 3.9.0 so it works with
  virtual hosting.

3.9.2 (2009-10-07)
==================

- Make redirect validation works without HTTP_HOST variable.

- Add DoNotReRaiseException adapter that can be registered
  for exceptions to flag that they should not be re-raised by
  publisher when ``handle_errors`` parameter of the ``publish``
  method is False.

3.9.1 (2009-09-01)
==================

- Convert a location, passed to a redirect method of HTTPRequest to
  string before checking for trusted host redirection, because a
  location object may be some non-string convertable to string, like
  URLGetter.

3.9.0 (2009-08-27)
==================

- Move some parts of ``zope.app.publisher`` into this package
  during ``zope.app.publisher`` refactoring:

   * ``IModifiableUserPreferredLanguages`` adapter for requests
   * ``browser:defaultView`` and ``browser:defaultSkin`` ZCML directives
   * ``IHTTPView``, ``IXMLRPCView`` and like interfaces
   * security ZCML declarations for some of ``zope.publisher`` classes

- Introduce ``IReRaiseException`` interface. If during publishing an
  exception occurs and for this exception an adapter is available that
  returns ``False`` on being called, the exception won't be reraised
  by the publisher. This happens only if ``handle_errors`` parameter
  of the ``publish()`` method is set to ``False``. Fixes problems when
  acting in a WSGI pipeline with a debugger middleware enabled.

  See https://bugs.launchpad.net/grok/+bug/332061 for details.

- Fix #98471: Restrict redirects to current host. This causes a ValueError to
  be raised in the case of redirecting to a different host. If this is
  intentional, the parameter `trusted` can be given.

- Move dependency on ``zope.testing`` from ``install_requires`` to
  ``tests_require``.

- Remove ``time.sleep`` in the ``supportsRetry`` http request.

- Add a fix for Internet Explorer versions which upload files with full
  filesystem paths as filenames.

3.8.0 (2009-05-23)
==================

- Move ``IHTTPException``, ``IMethodNotAllowed``, and ``MethodNotAllowed``
  here from ``zope.app.http``, fixing dependency cycles involving
  ``zope.app.http``.

- Move the ``DefaultViewName`` API here from ``zope.app.publisher.browser``,
  making it accessible to other packages that need it.

3.7.0 (2009-05-13)
==================

- Move ``IView`` and ``IBrowserView`` interfaces into
  ``zope.browser.interfaces``, leaving BBB imports.

3.6.4 (2009-04-26)
==================

- Add some BBB code to setDefaultSkin to allow IBrowserRequest's to continue
  to work without configuring any special adapter for IDefaultSkin.

- Move `getDefaultSkin` to the skinnable module next to the `setDefaultSkin`
  method, leaving a BBB import in place. Mark `IDefaultBrowserLayer` as a
  `IBrowserSkinType` in code instead of relying on the ZCML to be loaded.

3.6.3 (2009-03-18)
==================

- Mark HTTPRequest as IAttributeAnnotatable if ``zope.annotation`` is
  available, this was previously done by ``zope.app.i18n``.

- Register `IHTTPRequest` -> `IUserPreferredCharsets` adapter in ZCML
  configuration. This was also previously done by ``zope.app.i18n``.

3.6.2 (2009-03-14)
==================

- Add an adapter from ``zope.security.interfaces.IPrincipal`` to
  ``zope.publisher.interfaces.logginginfo.ILoggingInfo``. It was moved
  from ``zope.app.security`` as a part of refactoring process.

- Add adapters from HTTP and FTP request to
  ``zope.authentication.ILoginPassword`` interface. They are moved from
  ``zope.app.security`` as a part of refactoring process. This change adds a
  dependency on the ``zope.authentication`` package, but it's okay, since it's
  a tiny contract definition-only package.

  See http://mail.zope.org/pipermail/zope-dev/2009-March/035325.html for
  reasoning.

3.6.1 (2009-03-09)
==================

- Fix: remove IBrowserRequest dependency in http implementation based on
  condition for setDefaultSkin. Use ISkinnable instead of IBrowserRequest.

3.6.0 (2009-03-08)
==================

- Clean-up: Move skin related code from zope.publisher.interfaces.browser and
  zope.publisher.browser to zope.publihser.interfaces and
  zope.publisher.skinnable and provide BBB imports. See skinnable.txt for more
  information.

- Fix: ensure that we only apply skin interface in setDefaultSkin which also
  provide IBrowserSkinType. This will ensure that we find a skin if the
  applySkin method will lookup for a skin based on this type interface.

- Fix: Make it possible to use adapters and not only interfaces as skins from
  the adapter registry. Right now the defaultSkin directive registers simple
  interfaces as skin adapters which will run into a TypeError if someone tries
  to adapter such a skin adapter. Probably we should change the defaultSkin
  directive and register real adapters instead of using the interfaces as fake
  adapters where we expect adapter factories.

- Feature: allow use of ``applySkinof`` with different skin types using the
  optional ``skinType`` argument, which is by default set to
  ``IBrowserSkinType``.

- Feature: implement the default skin pattern within adapters. This allows
  us to register default skins for other requests then only
  ``IBrowserRequest`` using ``IDefaultSkin`` adapters.

  Note, ``ISkinnable`` and ``ISkinType`` and the skin implementation should
  be moved out of the browser request modules. Packages like ``z3c.jsonrpc``
  do not depend on ``IBrowserRequest`` but they are skinnable.

- Feature: add ``ISkinnable`` interface which allows us to implement the apply
  skin pattern not only for ``IBrowserRequest``.

- Fix: Don't cause warnings on Python 2.6

- Fix: Make ``IBrowserPage`` inherit ``IBrowserView``.

- Move ``IView`` and ``IDefaultViewName`` here from
  ``zope.component.interfaces``. Stop inheriting from deprecated (for years)
  interfaces defined in ``zope.component``.

- Remove deprecated code.

- Clean-up: Move ``zope.testing`` from extras to dependencies, per Zope
  Framework policy.  Remove ``zope.app.testing`` as a dependency: tests run
  fine without it.

3.5.6 (2009-02-14)
==================

- Fix an untested code path that incorrectly attempted to construct a
  ``NotFound``, adding a test.


3.5.5 (2009-02-04)
==================

- LP #322486: ``setStatus()`` now allows any ``int()``-able status value.


3.5.4 (2008-09-22)
==================


- LP #98440: interfaces lost on retried request

- LP #273296: dealing more nicely with malformed HTTP_ACCEPT_LANGUAGE headers
  within getPreferredLanguages().

- LP #253362: dealing more nicely with malformed HTTP_ACCEPT_CHARSET headers
  within getPreferredCharsets().

- LP #98284: Pass the ``size`` argument to readline, as the version of
  twisted used in zope.app.twisted supports it.

- Fix the LP #98284 fix: do not pass ``size`` argument of None that causes
  cStringIO objects to barf with a TypeError.


3.5.3 (2008-06-20)
==================

- It turns out that some Web servers (Paste for example) do not send the EOF
  character after the data has been transmitted and the read() of the cached
  stream simply hangs if no expected content length has been specified.


3.5.2 (2008-04-06)
==================

- A previous fix to handle posting of non-form data broke handling of
  form data with extra information in the content type, as in::

    application/x-www-form-urlencoded; charset=UTF-8

3.5.1 (2008-03-23)
==================

- When posting non-form (and non-multipart) data, the request body was
  consumed and discarded. This makes it impossible to deal with other
  post types, like xml-rpc or json without resorting to overly complex
  "request factory" contortions.

- https://bugs.launchpad.net/zope2/+bug/143873

  ``zope.publisher.http.HTTPCharsets`` was confused by the Zope 2
  publisher, which gives misleading information about which headers
  it has.

3.5.0 (2008-03-02)
==================

- Added a PasteDeploy app_factory implementation.  This should make
  it easier to integrate Zope 3 applications with PasteDeploy.  It
  also makes it easier to control the publication used, giving far
  greater control over application policies (e.g. whether or not to
  use the ZODB).

3.4.2 (2007-12-07)
==================

- Made segmentation of URLs not strip (trailing) whitespace from path segments
  to allow URLs ending in %20 to be handled correctly. (#172742)

3.4.1 (2007-09-29)
==================

No changes since 3.4.1b2.

3.4.1b2 (2007-08-02)
====================

- Add support for Python 2.5.

- Fix a problem with ``request.get()`` when the object that's to be
  retrieved is the request itself.


3.4.1b1 (2007-07-13)
====================

No changes.


3.4.0b2 (2007-07-05)
====================

- LP #122054: ``HTTPInputStream`` understands both the CONTENT_LENGTH and
  HTTP_CONTENT_LENGTH environment variables. It is also now tolerant
  of empty strings and will treat those as if the variable were
  absent.


3.4.0b1 (2007-07-05)
====================

- Fix caching issue. The input stream never got cached in a temp file
  because of a wrong content-length header lookup. Added CONTENT_LENGTH
  header check in addition to the previous used HTTP_CONTENT_LENGTH. The
  ``HTTP_`` prefix is sometimes added by some CGI proxies, but CONTENT_LENGTH
  is the right header info for the size.

- LP #98413: ``HTTPResponse.handleException`` should set the content type


3.4.0a1 (2007-04-22)
====================

Initial release as a separate project, corresponds to zope.publisher
from Zope 3.4.0a1
