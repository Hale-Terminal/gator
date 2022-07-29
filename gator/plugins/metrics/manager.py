#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.metrics.manager
=============================
Metrics plugin manager(s) and utils
"""
import logging

from gator.plugins.manager import BasePluginManager


log = logging.getLogger(__name__)


class MetricsPluginManager(BasePluginManager):
    """ Metrics Plugin Manager """
    _entry_point = 'gator.plugins.metrics'

    @property
    def entry_point(self):
        return self._entry_point

    @staticmethod
    def check_func(plugin):  # pylint: disable=method-hidden
        return True
