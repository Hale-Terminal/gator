#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.util.metrics
==================
Metrics utility functions
"""
from time import time


def timer(metric_name, context_obj=None):
    def func_1(func):
        def func_2(obj, *args, **kwargs):
            start = time()
            try:
                retval = func(obj, *args, **kwargs)
                (context_obj or obj)._config.metrics.timer(metric_name, time() - start)
            except:
                (context_obj or obj)._config.metrics.timer(metric_name, time() - start)
                raise
            return retval
        return func_2
    return func_1


def lapse(metric_name, context_obj=None):
    def func_1(func):
        def func_2(obj, *args, **kwargs):
            (context_obj or obj)._config.metrics.start_timer(metric_name)
            try:
                retval = func(obj, *args, **kwargs)
                (context_obj or obj)._config.metrics.stop_timer(metric_name)
            except:
                (context_obj or obj)._config.metrics.stop_timer(metric_name)
                raise
            return retval
        return func_2
    return func_1


def fails(metric_name, context_obj=None):
    def func_1(func):
        def func_2(obj, *args, **kwargs):
            try:
                retval = func(obj, *args, **kwargs)
            except:
                (context_obj or obj)._config.metrics.increment(metric_name)
                raise
            if not retval:
                (context_obj or obj)._config.metrics.increment(metric_name)
            return retval
        return func_2
    return func_1


def cmdfails(metric_name, context_obj=None):
    def func_1(func):
        def func_2(obj, *args, **kwargs):
            try:
                retval = func(obj, *args, **kwargs)
            except:
                (context_obj or obj)._config.metrics.increment(metric_name)
                raise
            if not retval or not retval.success:
                (context_obj or obj)._config.metrics.increment(metric_name)
            return retval
        return func_2
    return func_1


def cmdsucceeds(metric_name, context_obj=None):
    def func_1(func):
        def func_2(obj, *args, **kwargs):
            retval = func(obj, *args, **kwargs)
            if retval and retval.success:
                (context_obj or obj)._config.metrics.increment(metric_name)
            return retval
        return func_2
    return func_1


def succeeds(metric_name, context_obj=None):
    def func_1(func):
        def func_2(obj, *args, **kwargs):
            retval = func(obj, *args, **kwargs)
            if retval:
                (context_obj or obj)._config.metrics.increment(metric_name)
            return retval
        return func_2
    return func_1


def raises(metric_name, context_obj=None):
    def func_1(func):
        def func_2(obj, *args, **kwargs):
            try:
                return func(obj, *args, **kwargs)
            except:
                (context_obj or obj)._config.metrics.increment(metric_name)
                raise
        return func_2
    return func_1
