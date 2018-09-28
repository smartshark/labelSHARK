import logging
import re

from pycoshark.mongomodels import Refactoring

from core import LabelSHARK, BaseLabelApproach


@LabelSHARK.approach
class RefactoringLabels(BaseLabelApproach):
    """This labels commits as refactorings based on keywords and detected refactorings
    """

    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)
        self._labels = []
        self._keywords = re.compile(
            r"\b(refact|refactor|refactored|migrated|refactoring|restructure|encapsulate|param|parameters|abstract|rename\s+(method|variable|class)|(method|variable|class)\s+name|extract\s+(method|class|interface|code)|(moved|move)(?!.*(icon|icons|version))|getter|setter|checkstyle|pmd|typo.*(variable|method|class|code)|pull up|push down|merge.*(method|funcation|class)|convention|simple|simplify|replace|nest|inline|(remove|delete)\s+duplicate|split|wrapper|private|protect|delegate)\b")

    def set_commit(self, commit):
        self._labels = []

        has_refactoring_keywords = self._keywords.match(commit.message.lower()) is not None
        has_code_refactoring = Refactoring.objects(commit_id=commit.id).count() > 0
        self._labels.append(('keyword', has_refactoring_keywords))
        self._labels.append(('codebased', has_code_refactoring))

    def get_labels(self):
        return self._labels

    def _error(self, message):
        # we log to warn because error gets to stdout in servershark
        self._log.warning(message)
