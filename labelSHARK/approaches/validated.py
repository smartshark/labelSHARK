import logging

from pycoshark.mongomodels import Issue
from pycoshark.utils import jira_is_resolved_and_fixed

from core import LabelSHARK, BaseLabelApproach
from approaches.util import labelutils


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
        if commit.fixed_issue_ids is not None and len(commit.fixed_issue_ids) > 0:
            for issue in Issue.objects(id__in=commit.fixed_issue_ids):
                if issue.issue_type_verified and issue.issue_type_verified.lower() == 'bug':
                    isbugfix |= jira_is_resolved_and_fixed(issue)
                if issue.parent_issue_id:
                    parent_issue = Issue.objects(id=issue.parent_issue_id).get()
                    if parent_issue.issue_type_verified and parent_issue.issue_type_verified.lower() == 'bug':
                        isbugfix |= jira_is_resolved_and_fixed(parent_issue)
        self._labels.append(('bugfix', isbugfix))

    def get_labels(self):
        return self._labels

    def _error(self, message):
        # we log to warn because error gets to stdout in servershark
        self._log.warning(message)
