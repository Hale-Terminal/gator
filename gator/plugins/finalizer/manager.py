#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.finalizer.manager
================================
Finalizer plugin manager(s) and utils
"""
import logging

from gator.plugins.manager import BasePluginManager


log = logging.getLogger(__name__)


class FinalizerPluginManager(BasePluginManager):
    """ Finalizer Plugin Manager """
    _entry_point = 'gator.plugins.finalizer'

    @property
    def entry_point(self):
        return self._entry_point