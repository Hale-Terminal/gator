#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator
======
Create images from packages for deployment in various cloud formations
"""
import logging
try:
    from logging import NullHandler
except ImportError:
    try:
        from logutils import NullHandler
    except ImportError:
        class NullHandler(logging.Handler):
            def emit(self, record):
                pass

__version__ = '1.0.0.dev'
__versioninfo__ = __version__.split('.')
__all__ = ()

logging.getLogger(__name__).addHandler(NullHandler())
