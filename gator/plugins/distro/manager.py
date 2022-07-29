#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.distro.manager
============================
Provisioner plugin manager(s) and utils
"""
import logging

from gator.plugins.manager import BasePluginManager


log = logging.getLogger(__name__)


class DistroPluginManager(BasePluginManager):
    """
    OS Distribution Plugin Manager
    """
    _entry_point = 'gator.plugins.distro'

    @property
    def entry_point(self):
        return self._entry_point

    @staticmethod
    def check_func(plugin):
        return True
