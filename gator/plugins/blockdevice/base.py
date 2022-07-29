#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.blockdevice.base
==============================
Base class(es) for block device manager plugins
"""
import abc
import logging

from gator.plugins.base import BasePlugin


__all__ = ('BaseBlockDevicePlugin',)
log = logging.getLogger(__name__)


class BaseBlockDevicePlugin(BasePlugin):
    """
    BlockDevicePlugins are context managers and as such, need to implement the context manager protocol
    """
    __metaclass__ = abc.ABCMeta
    _entry_point = 'gator.plugins.blockdevice'

    def __init__(self, *args, **kwargs):
        super(BaseBlockDevicePlugin, self).__init__(*args, **kwargs)
        self.partition = None

    @abc.abstractmethod
    def __enter__(self):
        return self

    @abc.abstractmethod
    def __exit__(self, typ, val, trc):
        if typ:
            log.debug('Exception encountered in block device plugin', exc_info=(typ, val, trc))
        return False

    def __call__(self, cloud):
        """
        By default, BlockDevicePlugins are called using
        with blockdeviceplugin(cloud) as device:
            pass
        Override if need be
        """
        self.cloud = cloud
        return self
