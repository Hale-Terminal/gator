#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""

"""
import abc
import logging

from gator.plugins.base import BasePlugin


__all__ = ('BaseVolumePlugin',)
log = logging.getLogger(__name__)


class BaseVolumePlugin(BasePlugin):
    """
    Volume plugins ask blockdevice for an os block device, the cloud for a volume at
    that block device, mount it, and return the mount point for the provisioner. How they go about it
    is up to the implementor.
    The are context managers to ensure they unmount and clean up resources
    """
    __metaclass__ = abc.ABCMeta
    _entry_point = 'gator.plugins.volume'

    @abc.abstractmethod
    def __enter__(self):
        return self

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, trace):
        if exc_type:
            log.debug('Exception encountered in volume plugin context manager',
                      exc_info=(exc_type, exc_value, trace))
        return False

    def __call__(self, cloud, blockdevice):
        self._cloud = cloud
        self._blockdevice = blockdevice
        return self
