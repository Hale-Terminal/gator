#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.metrics.base
======================
Base class(es) for metrics plugins
"""
import abc
import logging

from gator.plugins.base import BasePlugin


__all__ = ('BaseMetricsPlugin',)
log = logging.getLogger(__name__)


class BaseMetricsPlugin(BasePlugin):
    """
    """
    __metaclass__ = abc.ABCMeta
    _entry_point = 'gator.plugins.metrics'

    @abc.abstractmethod
    def increment(self, name, value=1):
        pass

    @abc.abstractmethod
    def gauge(self, name, value):
        pass

    @abc.abstractmethod
    def timer(self, name, seconds):
        pass

    @abc.abstractmethod
    def start_timer(self, name):
        pass

    @abc.abstractmethod
    def stop_timer(self, name):
        pass

    @abc.abstractmethod
    def flush(self):
        pass

    def add_tag(self, name, value):
        self.tags[name] = value

    def __init__(self):
        super(BaseMetricsPlugin, self).__init__()
        self.tags = {}

    def __enter__(self):
        setattr(self._config, "metrics", self)
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.flush()
        if exc_type:
            log.debug('Exception encountered in metrics plugin context manager',
                      exc_info=(exc_type, exc_value, trace))
        return False
