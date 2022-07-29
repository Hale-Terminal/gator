#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.blockdevice.null
==============================
null block device manager
"""
import logging

from gator.plugins.blockdevice.base import BaseBlockDevicePlugin

__all__ = ('NullBlockDevicePlugin',)
log = logging.getLogger(__name__)


class NullBlockDevicePlugin(BaseBlockDevicePlugin):
    _name = 'null'

    def __enter__(self):
        return '/dev/null'

    def __exit__(self, typ, val, trc):
        if typ:
            log.debug('Exception encountered in Null block device plugin',
                exc_info=(typ, val, trc))
        return False
