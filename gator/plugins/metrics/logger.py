#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.metrics.logger
============================
Basic logger metrics collector
"""
import logging
from time import time

from gator.plugins.metrics.base import BaseMetricsPlugin

__all__ = ('LoggerMetricsPlugin',)
log = logging.getLogger(__name__)


class LoggerMetricsPlugin(BaseMetricsPlugin):
    _name = 'logger'

    def __init__(self):
        super(LoggerMetricsPlugin, self).__init__()
        self.timers = {}

    def increment(self, name, value=1):
        log.debug("Metric {0}: increment {1}, tags: {2}".format(name, value, self.tags))

    def gauge(self, name, value):
        log.debug("Metric {0}: gauge set {1}, tags: {2}".format(name, value, self.tags))

    def timer(self, name, seconds):
        log.debug("Metric {0}: timer {1}s, tags: {2}".format(name, seconds, self.tags))

    def start_timer(self, name):
        log.debug("Metric {0}: start timer, tags: {1}".format(name, self.tags))
        self.timers[name] = time()

    def stop_timer(self, name):
        log.debug("Metric {0}: stop timer [{1}s], tags: {2}".format(name, time() - self.timers[name], self.tags))
        del self.timers[name]

    def flush(self):
        for name in self.timers:
            log.warning("Metric {0}: timer never stopped, started at {1}, tags: {2}".format(name, self.timers[name], self.tags))
