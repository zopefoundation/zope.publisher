=====================
Zope WSGI Application
=====================

About
-----
This package contains a WSGI application for Zope.

WSGI is the Python Web Server Gateway Interface, an
upcoming PEP to standardize the interface between web servers
and python applications to promote portability.

For more information, refer to the WSGI specification: http://www.python.org/peps/pep-0333.html

Usage
-----
To use Zope as a WSGI application, the following steps must be taken

* configure and setup Zope

* create an instance of ``zope.app.wsgi.PublisherApp`` must be created
  with a refernce to an open database

* This instance must be set as the WSGI servers application object


Example::

    from zope.app.server.main import setup, load_options
    from zope.app.wsgi import PublisherApp

    args = ["-C/path/to/zope.conf"]
    db = setup(load_options(args))

    my_app = PublisherApp(db)

    wsgi_server.set_app(my_app)

This assumes, that Zope is available on the ``PYTHONPATH``.
Note that you may have to edit ``zope.conf`` to provide
an absolute path for ``site.zcml``.


