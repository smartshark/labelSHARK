import logging
import pickle
import pandas as pd

from pycoshark.mongomodels import Issue

from core import LabelSHARK, BaseLabelApproach
from approaches.util import labelutils



@LabelSHARK.approach
class IssueFasttext(BaseLabelApproach):
    """
    This labels commits as bugfix based on issue links and predictions is the issues are bugs with the fastText
    classifier
    """

    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)
        self._labels = []
        try:
            self._text_clf = pickle.load(open('classifier/ft_text_clf.p', 'rb'))
            self._title_clf = pickle.load(open('classifier/ft_title_clf.p', 'rb'))
        except:
            self._text_clf = None
            self._title_clf = None
            self._log.warning('Approach issuefasttext not working. could not load ft classifiers. '
                              'You need to download the classifiers () and place them in the labelSHARK/classifiers '
                              'folder.')
            pass

    def set_commit(self, commit):
        if self._text_clf is None or self._title_clf is None:
            return # do nothing without the classifiers

        self._labels = []

        isbugfix = False
        if commit.linked_issue_ids is not None and len(commit.linked_issue_ids) > 0:
            for issue in Issue.objects(id__in=commit.linked_issue_ids):
                isbugfix |= labelutils.isbugfix(issue) and self._validate_bugfix(issue)
                if issue.parent_issue_id:
                    parent_issue = Issue.objects(id=issue.parent_issue_id).get()
                    isbugfix |= labelutils.isbugfix(parent_issue) and self._validate_bugfix(issue)

        self._labels.append(('bugfix', isbugfix))

    def _validate_bugfix(self, issue):
        desc = issue.desc
        title = issue.title
        if desc is None:
            desc = ''
        if title is None:
            title = ''
        X = pd.DataFrame({'description': [desc.replace('\n', '')], 'title': [title.replace('\n', '')]})
        proba_text = self._text_clf.predict_proba(X)
        proba_title = self._title_clf.predict_proba(X)
        proba_total = (proba_text+proba_title)/2
        return proba_total[0, 1]>0.5


    def get_labels(self):
        return self._labels

    def _error(self, message):
        # we log to warn because error gets to stdout in servershark
        self._log.warning(message)
