#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.distro.debian
===========================
Basic debian distro
"""
import logging
import os.path

from gator.plugins.distro.linux import BaseLinuxDistroPlugin


__all__ = ('DebianDistroPlugin',)
log = logging.getLogger(__name__)


class DebianDistroPlugin(BaseLinuxDistroPlugin):
    """
    DebianDistroPlugin takes the majority of its behavior from BaseLinuxDistroPlugin
    See BaseLinuxDistroPlugin for details
    """
    _name = 'debian'

    def _deactivate_provisioning_service_block(self):
        """
        Prevent packages installing in the chroot from starting
        For debian based distros, we add /usr/sbin/policy-rc.d
        """
        if not super(DebianDistroPlugin, self)._deactivate_provisioning_service_block():
            return False

        config = self.plugin_config
        path = os.path.join(
            self.root_mountspec.mountpoint, config.get('policy_file_path', ''))
        filename = os.path.join(path, config.get('policy_file'))

        if not os.path.isdir(path):
            log.debug("creating %s", path)
            os.makedirs(path)
            log.debug("created %s", path)

        with open(filename, 'w') as f:
            log.debug("writing %s", filename)
            f.write(config.get('policy_file_content'))
            log.debug("wrote %s", filename)

        os.chmod(filename, config.get('policy_file_mode', ''))

        return True

    def _activate_provisioning_service_block(self):
        """
        Remove policy-rc.d file so that things start when the AMI launches
        """
        if not super(DebianDistroPlugin, self)._activate_provisioning_service_block():
            return False

        config = self.plugin_config

        policy_file = os.path.join(
            self.root_mountspec.mountpoint,
            config.get('policy_file_path', ''),
            config.get('policy_file', ''))

        if os.path.isfile(policy_file):
            log.debug("removing %s", policy_file)
            os.remove(policy_file)
        else:
            log.debug("The %s was missing, this is unexpected as the DebianDistroPlugin should manage this file", policy_file)

        return True
        