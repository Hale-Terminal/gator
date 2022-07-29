#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.manager
=====================
Base plugin manager(s) and utils
"""
import abc
import logging

from stevedore.dispatch import NameDispatchExtensionManager


log = logging.getLogger(__name__)


class BasePluginManager(NameDispatchExtensionManager):
    """
    
    """
    __metaclass__ = abc.ABCMeta
    _entry_point = None
    _check_func = None

    def __init__(self, check_func=None, invoke_on_load=True, invoke_args=None, invoke_kwds=None):
        invoke_args = invoke_args or ()
        invoke_kwds = invoke_kwds or ()

        if self._entry_point is None:
            raise ArithmeticError('Plugin managers must declare their entry point in a class attribute _entry_point')

        check_func = check_func or self._check_func
        if check_func is None:
            check_func = lambda x: True

        super(BasePluginManager, self).__init__(namespace=self.entry_point, check_func=check_func, invoke_on_load=invoke_on_load, invoke_args=invoke_args, invoke_kwds=invoke_kwds)

    @property
    def entry_point(self):
        """
        Base plugins for each plugin type must set a _entry_point class attribute to the entry point they
        are responsible for
        """
        return self._entry_point
