#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
import copy

from pycoshark.mongomodels import Issue

from core import LabelSHARK, BaseLabelApproach
from approaches.util import labelutils


def remove_index(cls):
    tmp = copy.deepcopy(cls._meta)
    if 'indexes' in tmp.keys():
        del tmp['indexes']
    del tmp['index_specs']
    tmp['index_specs'] = None
    return tmp


Issue._meta = remove_index(Issue)


@LabelSHARK.approach
class AdjustedSZZ(BaseLabelApproach):
    """This is basically SZZ [1] but not only for bugzilla and with regular expressions instead
    of flex.

    1: When Do Changes Induce Fixes? Jacek Śliwerski et al. 2005
    """

    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)
        self._labels = []
        # precompile regex
        self._keyword = re.compile('(\s|^)fix(e[ds])?|(\s|^)bugs?|(\s|^)defects?|(\s|^)patch|(\s|^)issue[s]{0,1}', re.I | re.M)

    def set_commit(self, commit):
        self._labels = []

        isbugfix = False
        if commit.linked_issue_ids is not None and len(commit.linked_issue_ids) > 0:
            for issue in Issue.objects(id__in=commit.linked_issue_ids):
                isbugfix |= labelutils.isbugfix(issue)
        else:
            isbugfix = self._keyword_label(commit.message)

        self._labels.append(('bugfix', isbugfix))

    def get_labels(self):
        return self._labels

    def _keyword_label(self, message):
        return self._keyword.match(message) is not None

    def _error(self, message):
        # we log to warn because error gets to stdout in servershark
        self._log.warning(message)
