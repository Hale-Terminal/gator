#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.cloud.manager
===========================
Cloud plugin manager(s) and utils
"""
import logging

from gator.plugins.manager import BasePluginManager


log = logging.getLogger(__name__)


class CloudPluginManager(BasePluginManager):
    """
    Cloud Plugin Manager
    """
    _entry_point = 'gator.plugins.cloud'

    @property
    def entry_point(self):
        return self._entry_point
