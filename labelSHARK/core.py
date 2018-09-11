#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The core module contains the abstract base class for labeling approaches
and the LabelSHARK class which provides the rough plugin structure for approaches.
"""

import abc
import logging


class BaseLabelApproach(metaclass=abc.ABCMeta):
    """Abstract base class for labeling approaches."""

    @abc.abstractmethod
    def set_commit(self, commit):
        pass

    @abc.abstractmethod
    def get_labels(self):
        pass


class LabelSHARK(object):
    """LabelSHARK plugin structure.

    This class calls every registered labeling approach plugin.
    """
    approaches = []

    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)

    def set_commit(self, commit):
        """Passes the current commit model to the approach class.

        :param obj commit: A Commit object from pycoshark models.
        """

        for app in self.approaches:
            app_name = app.__module__.replace('approaches.', '')
            self._log.debug('setting commit for {}'.format(app_name))
            try:
                app.set_commit(commit)
            except Exception as e:
                self._log.exception('error setting commit in {}'.format(app_name))

    def get_labels(self):
        """Calls every registered commit labeling approach to collect the labels.

        Every collected label is prefixed with the name of the approach.
        """

        ret = []
        for app in self.approaches:
            # we want the module name without the approaches package as prefix
            app_name = app.__module__.replace('approaches.', '')
            self._log.debug('getting labels from {}'.format(app_name))

            # every plugin should return a list of tuples
            # this hould result in a list of: (approach_key, value)
            try:
                for k, v in app.get_labels():
                    ret.append(('{}_{}'.format(app_name, k), v))
            except Exception as e:
                self._log.error('error getting labels from {}'.format(app_name))
                self._log.exception(e)
        return ret

    @classmethod
    def approach(cls, approach):
        """Registers an approach with LabelSHARK.

        Should be used with the @LabelSHARk.approach decorator on the class implementing the approach.
        """

        if approach not in cls.approaches:
            if not issubclass(approach, BaseLabelApproach):
                raise Exception('approach: {} not of type BaseLabelApproach'.format(approach))
            cls.approaches.append(approach())
            return approach
