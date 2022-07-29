#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.distro.redhat
===========================
Basic redhat distro
"""
import logging

from gator.plugins.distro.linux import BaseLinuxDistroPlugin

__all__ = ('RedHatDistroPlugin',)
log = logging.getLogger(__name__)


class RedHatDistroPlugin(BaseLinuxDistroPlugin):
    """
    RedHatDistroPlugin takes the majority of its behavior from BaseLinuxDistroPlugin
    See BaseLinuxDistroPlugin for details
    """
    _name = 'redhat'
