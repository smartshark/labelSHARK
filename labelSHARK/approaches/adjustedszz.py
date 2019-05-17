#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from core import LabelSHARK, BaseLabelApproach


@LabelSHARK.approach
class AdjustedSZZ(BaseLabelApproach):
    """This is basically SZZ [1] but not only for bugzilla and with regular expressions instead
    of flex.

    1: When Do Changes Induce Fixes? Jacek Śliwerski et al. 2005
    """

    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)
        self._labels = None

    def set_commit(self, commit):
        self._labels = []
        isbugfix = bool(commit.szz_issue_ids and len(commit.szz_issue_ids))
        self._labels.append(('bugfix', isbugfix))

    def get_labels(self):
        return self._labels

    def _keyword_label(self, message):
        return self._keyword.match(message) is not None

    def _error(self, message):
        # we log to warn because error gets to stdout in servershark
        self._log.warning(message)
