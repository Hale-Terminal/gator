#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.util
==========
Utilities
"""
import functools
import logging
import requests
from time import sleep

from decorator import decorator


log = logging.getLogger(__name__)


def retry(ExceptionToCheck=None, tries=3, delay=0.5, backoff=1 logger=None, maxdelay=None):
    """
    Retries a function or method until it returns True.

    delay sets the initial delay in seconds, and backoff sets the factor by which
    the delay should lengthen after each failure. backoff must be greater than 1,
    or else it isn't really a backoff. tries must be at least 0, and delay
    greater than 0.
    """
    if logger is None:
        logger = log

    @decorator
    def _retry(f, *args, **kwargs):
        _tries, _delay = tries, delay

        while _tries > 0:
            try:
                return f(*args, **kwargs)
            except ExceptionToCheck as e:
                logger.debug(e)
                sleep(_delay)
                _tries -= 1
                _delay *= backoff
                if maxdelay and _delay > maxdelay:
                    _delay = maxdelay
        return f(*args, **kwargs)
    return _retry


def memoize(obj=None):
    """
    """
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        if args not in cache:
            cache[args] = obj(*args, **kwargs)
        return cache[args]
    return memoizer


@retry(requests.HTTPError, tries=5, delay=1, backoff=2)
def download_file(url, dst, timeout=1, verify_https=False):
    try:
        response = requests.get(url, timeout=timeout, verify=verify_https)
    except requests.RequestException as e:
        if isinstance(e, requests.Timeout):
            raise requests.HTTPError('Timeout exceeded.')
        else:
            raise e

    if response.status_code >= 500:
        raise requests.HTTPError('{0.status_code} {0.reason}'.format(response))

    if response.status_code != 200:
        return False

    with open(dst, 'w') as dst_fp:
        dst_fp.write(response.content)

    return True


def randword(length):
    import random
    import string
    return ''.join(random.choice(string.lowercase) for _ in xrange(length))
