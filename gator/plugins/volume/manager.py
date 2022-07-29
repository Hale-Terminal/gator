#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""

"""
import logging

from gator.plugins.manager import BasePluginManager


log = logging.getLogger(__name__)


class VolumePluginManager(BasePluginManager):
    """ Volume Plugin Manager """
    _entry_point = 'gator.plugins.volume'

    @property
    def entry_point(self):
        return self._entry_point

    @staticmethod
    def check_func(plugin):  # pylint: disable=method-hidden
        return True
