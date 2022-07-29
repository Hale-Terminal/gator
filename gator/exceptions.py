#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.exceptions
================
gator's exceptions
"""


class GatorException(Exception):
    """ Base Gator Exception """
    pass


class DeviceException(GatorException):
    """ Errors during device allocation """
    pass


class VolumeException(GatorException):
    """ Errors during volume allocation """
    pass


class ArgumentError(GatorException):
    """ Errors during argument parsing """


class ProvisionException(GatorException):
    """ Errors during provisioning """


class FinalizerException(GatorException):
    """ Errors during finalizing """
