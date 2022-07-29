#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.finalizer.base
============================
Base class(es) for finalizer plugins
"""
import abc
import logging

from gator.plugins.base import BasePlugin


__all__ = ('BaseFinalizerPlugin',)
log = logging.getLogger(__name__)


class BaseFinalizerPlugin(BasePlugin):
    """
    Finalizers handle administrivia post-package-provisioning. Think: registration, tagging, snapshotting, etc.
    They are context managers to ensure resource cleanup
    """

    __metaclass__ = abc.ABCMeta
    _entry_point = 'gator.plugins.finalizer'

    @abc.abstractmethod
    def finalize(self):
        """ finalize an image """

    def __enter__(self):
        return self

    def __exit__(self, typ, val, trc):
        if typ:
            log.debug('Exception encountered in Finalizer plugin context manager',
                      exc_info=(typ, val, trc))
        return False

    def __call__(self, cloud):
        self._cloud = cloud