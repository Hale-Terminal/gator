#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.distro.base
=========================
Base class(es) for OS distributions plugins
"""
import abc
import logging

from gator.plugins.base import BasePlugin

__all__ = ('BaseDistroPlugin',)
log = logging.getLogger(__name__)


class BaseDistroPlugin(BasePlugin):
    """
    Distribution plugins take a volume and prepare it for provisioning.
    They are context managers to ensure resource cleanup
    """

    __metaclass__ = abc.ABCMeta
    _entry_point = 'gator.plugins.distro'

    @abc.abstractmethod
    def __enter__(self):
        return self

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, trace):
        if exc_type:
            log.debug('Exception encountered in distro plugin context manager',
                      exc_info=(exc_type, exc_value, trace))
        return False
