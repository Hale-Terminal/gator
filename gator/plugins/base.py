#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.base
==================
Base class(es) for plugin implementations
"""
import logging
import os

from gator.config import PluginConfig


__all__ = ()
log = logging.getLogger(__name__)


class BasePlugin(object):
    """
    Base class for plugins
    """
    _entry_point = None
    _name = None
    _enabled = True

    def __init__(self):
        if self._entry_point is None:
            raise AttributeError('Plugins must declare their entry point namespace in a _entry_point class attribute')
        if self._name is None:
            raise AttributeError('Plugins must declare their entry point name in a _name class attribute')

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enable):
        self._enabled = enable

    @property
    def entry_point(self):
        return self._entry_point

    @property
    def name(self):
        return self._name

    @property
    def full_name(self):
        return '{0}.{1}'.format(self.entry_point, self.name)

    @property
    def full_config(self):
        return self._config

    @property
    def plugin_config(self):
        config = self.full_config.get('plugins', {})
        plugin_config = config.get(self.full_name, {})
        return plugin_config

    @property
    def context(self):
        return self.full_config.get('context', {})

    def configure(self, config, parser):
        """
        Configure the plugin and contribute to command line args
        """
        log.debug('Configuring plugin {0} for entry point {1}'.format(self.name, self.entry_point))
        self._config = config
        self._parser = parser
        self.load_plugin_config()
        if self.enabled:
            self.add_plugin_args()

    def add_plugin_args(self):
        pass

    def load_plugin_config(self):
        entry_point = self.entry_point
        name = self.name
        key = self.full_name

        if self._config.plugins.config_root.startswith('~'):
            plugin_conf_dir = os.path.expanduser(self._config.plugins.config_root)

        elif self._config.plugins.config_root.startswith('/'):
            plugin_conf_dir = self._config.plugins.config_root

        else:
            plugin_conf_dir = os.path.join(self._config.config_root, self._config.plugins.config_root)

        plugin_conf_files = (
            os.path.join(plugin_conf_dir, '.'.join((key, 'yml'))),
        )

        self._config.plugins[key] = PluginConfig.from_defaults(entry_point, name)
        self._config.plugins[key] = PluginConfig.dict_merge(self._config.plugins[key], PluginConfig.from_files(plugin_conf_files))
        self.enabled = self._config.plugins[key].get('enabled', True)
