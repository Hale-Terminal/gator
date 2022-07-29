#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.provisioner.
==========================
"""
import logging
import os

from gator.plugins.provisioner.base import BaseProvisionerPlugin
from gator.util.linux import monitor_command, result_to_dict
from gator.util.metrics import cmdsucceeds, cmdfails, lapse

__all__ = ('YumProvisionerPlugin',)
log = logging.getLogger(__name__)


class YumProvisionerPlugin(BaseProvisionerPlugin):
    """
    YumProvisionerPlugin takes the majority of its behavior from BaseProvisionerPlugin
    See BaseProvisionerPlugin for details
    """
    _name = 'yum'

    def _refresh_repo_metadata(self):
        config = self._config.plugins[self.full_name]
        return yum_clean_metadata(config.get('clean_repos', []))

    @cmdsucceeds("gator.provisioner.yum.provision_package.count")
    @cmdfails("gator.provisioner.yum.provision_package.error")
    @lapse("gator.provisioner.yum.provision_package.duration")
    def _provision_package(self):
        result = self._refresh_repo_metadata()
        if not result.success:
            log.critical('Repo metadata refresh failed: {0.std_err}'.format(result.result))
            return result
        context = self._config.context
        if context.package.get('local_install', False):
            return yum_localinstall(context.package.arg)
        else:
            return yum_install(context.package.arg)

    def _store_package_metadata(self):
        context = self._config.context
        config = self._config.plugins[self.full_name]
        metadata = rpm_package_metadata(context.package.arg, config.get('pkg_query_format', ''), context.package.get('local_install', False))
        for x in config.pkg_attributes:
            metadata.setdefault(x, None)
        context.package.attributes = metadata


def yum_install(package):
    return monitor_command(['yum', '--nogpgcheck', '-y', 'install', package])


def yum_localinstall(path):
    if not os.path.isfile(path):
        log.critical('Package {0} not found'.format(path))
        return None
    return monitor_command(['yum', '--nogpgcheck', '-y', 'localinstall', path])


def yum_clean_metadata(repos=None):
    clean = ['yum', 'clean', 'metadata']
    if repos:
        clean.extend(['--disablerepo', '*', '--enablerepo', ','.join(repos)])
    return monitor_command(clean)


def rpm_query(package, queryformat, local=False):
    cmd = 'rpm -q --qf'.split()
    cmd.append(queryformat)
    if local:
        cmd.append('-p')
    cmd.append(package)
    return monitor_command(cmd)


def rpm_package_metadata(package, queryformat, local=False):
    return result_to_dict(rpm_query(package, queryformat, local))
