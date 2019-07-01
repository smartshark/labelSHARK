import logging
import copy

from pycoshark.mongomodels import Issue, Event

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
Event._meta = remove_index(Event)


@LabelSHARK.approach
class IssueOnly(BaseLabelApproach):
    """This labels commits as bugfix only based on linked issues.
    """

    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)
        self._labels = []

    def set_commit(self, commit):
        self._labels = []

        isbugfix = False
        isfeatureadd = False
        if commit.linked_issue_ids is not None and len(commit.linked_issue_ids) > 0:
            for issue in Issue.objects(id__in=commit.linked_issue_ids):
                isbugfix |= labelutils.isbugfix(issue)
                isfeatureadd |= labelutils.isfeatureadd(issue)
                if issue.parent_issue_id:
                    parent_issue = Issue.objects(id=issue.parent_issue_id).get()
                    isbugfix |= labelutils.isbugfix(parent_issue)
                    isfeatureadd |= labelutils.isfeatureadd(parent_issue)

        self._labels.append(('bugfix', isbugfix))
        self._labels.append(('featureadd', isbugfix))

    def get_labels(self):
        return self._labels

    def _error(self, message):
        # we log to warn because error gets to stdout in servershark
        self._log.warning(message)
