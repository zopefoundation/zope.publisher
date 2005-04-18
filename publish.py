##############################################################################
#
# Copyright (c) 2001, 2002, 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Python Object Publisher -- Publish Python objects on web servers

Provide an apply-like facility that works with any mapping object

$Id$
"""
import sys
from zope.publisher.interfaces import Retry
from zope.proxy import removeAllProxies

_marker = []  # Create a new marker object.


def unwrapMethod(object):
    """object -> (unwrapped, wrapperCount)

    Unwrap 'object' until we get to a real function, counting the number of
    unwrappings.

    Bail if we find a class or something we can't identify as callable.
    """
    wrapperCount = 0
    unwrapped = object
    for i in range(10):
        bases = getattr(unwrapped, '__bases__', None)
        if bases is not None:
            raise TypeError, "mapply() can not call class constructors"

        im_func = getattr(unwrapped, 'im_func', None)
        if im_func is not None:
            unwrapped = im_func
            wrapperCount += 1
            continue

        func_code = getattr(unwrapped, 'func_code', None)
        if func_code is not None:
            break

        __call__ = getattr(unwrapped, '__call__' , None)
        if __call__ is not None:
            unwrapped = unwrapped.__call__
        else:
            raise TypeError, "mapply() can not call %s" % `object`

    else:
        raise TypeError(
            "couldn't find callable metadata, mapply() error on %s"%`object`
        )

    return unwrapped, wrapperCount


def mapply(object, positional=(), request={}):
    __traceback_info__ = object

    # we need deep access for introspection. Waaa.
    unwrapped = removeAllProxies(object)

    unwrapped, wrapperCount = unwrapMethod(unwrapped)

    code = unwrapped.func_code
    defaults = unwrapped.func_defaults
    names = code.co_varnames[wrapperCount:code.co_argcount]

    nargs = len(names)
    if positional:
        args = list(positional)
        if len(args) > nargs:
            given = len(args)
            if wrapperCount:
                given = given + wrapperCount
            raise TypeError, (
                '%s() takes at most %d argument%s(%d given)' % (
                getattr(unwrapped, '__name__', repr(object)), code.co_argcount,
                (code.co_argcount > 1 and 's ' or ' '), given))
    else:
        args = []

    get = request.get
    if defaults:
        nrequired = len(names) - (len(defaults))
    else:
        nrequired = len(names)
    for index in range(len(args), nargs):
        name = names[index]
        v = get(name, _marker)
        if v is _marker:
            if name == 'REQUEST':
                v = request
            elif index < nrequired:
                raise TypeError, 'Missing argument to %s(): %s' % (
                    getattr(unwrapped, '__name__', repr(object)), name)
            else:
                v = defaults[index-nrequired]
        args.append(v)

    args = tuple(args)

    if __debug__:
        return debug_call(object, args)

    return object(*args)

def debug_call(object, args):
    # The presence of this function allows us to set a pdb breakpoint
    return object(*args)

def publish(request, handle_errors=True):
    try: # finally to clean up to_raise and close request
        to_raise = None
        while True:
            publication = request.publication
            try:
                try:
                    object = None
                    try:
                        try:
                            request.processInputs()
                            publication.beforeTraversal(request)

                            object = publication.getApplication(request)
                            object = request.traverse(object)
                            publication.afterTraversal(request, object)

                            result = publication.callObject(request, object)
                            response = request.response
                            if result is not response:
                                response.setBody(result)

                            publication.afterCall(request, object)

                        except:
                            publication.handleException(
                                object, request, sys.exc_info(), True)

                            if not handle_errors:
                                raise
                    finally:
                        publication.endRequest(request, object)

                    break # Successful.

                except Retry, retryException:
                    if request.supportsRetry():
                        # Create a copy of the request and use it.
                        newrequest = request.retry()
                        request.close()
                        request = newrequest
                    elif handle_errors:
                        # Output the original exception.
                        publication = request.publication
                        publication.handleException(
                            object, request,
                            retryException.getOriginalException(), False)
                        break
                    else:
                        raise

            except:
                # Bad exception handler or retry method.
                # Re-raise after outputting the response.
                if handle_errors:
                    request.response.internalError()
                    to_raise = sys.exc_info()
                    break
                else:
                    raise

        response = request.response
        response.outputBody()
        if to_raise is not None:
            raise to_raise[0], to_raise[1], to_raise[2]

    finally:
        to_raise = None  # Avoid circ. ref.
        request.close()  # Close database connections, etc.
