#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.blockdevice.manager
=================================
Block device plugin manager(s) and utils
"""
import logging

from gator.plugins.manager import BasePluginManager


log = logging.getLogger(__name__)


class BlockDevicePluginManager(BasePluginManager):
    """
    BlockDevice Plugin Manager
    """
    _entry_point = 'gator.plugins.blockdevice'

    @property
    def entry_point(self):
        return self._entry_point
        