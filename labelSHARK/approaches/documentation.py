import logging
import re

from pycoshark.mongomodels import Hunk, File, FileAction

from core import LabelSHARK, BaseLabelApproach


@LabelSHARK.approach
class DocumentationChangeLabel(BaseLabelApproach):
    """This labels commits as documentation changes based on hunks
    """

    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)
        self._labels = []
        self._filename_pattern_java = re.compile('.*\.java$')
        self._java_string = re.compile(r"(\"(?:[^\"\\]|\\\"|\\)*\")")
        self._mutliline_comment = re.compile(r"^(-|\+)\s*((/\*)|(\*)).*$", re.MULTILINE)
        self._java_inlinecomment = re.compile(r"^(-|\+).*//.*$", re.MULTILINE)
        self._java_inlinetechnicaldept_add = re.compile(r"^\+.*//\s*(TODO|XXX|FIXME).*$", re.MULTILINE)
        self._java_inlinetechnicaldept_remove = re.compile(r"^-.*//\s*(TODO|XXX|FIXME).*$", re.MULTILINE)

    def set_commit(self, commit):
        self._labels = []
        has_javadoc_change = False
        has_inline_change = False
        has_technical_dept_add = False
        has_technical_dept_remove = False
        if len(commit.parents)>0:
            file_actions = FileAction.objects(commit_id=commit.id, parent_revision_hash=commit.parents[0])
        else:
            file_actions = FileAction.objects(commit_id=commit.id)
        for file_action in file_actions:
            file = File.objects(id=file_action.file_id).get()
            is_filename_match = self._filename_pattern_java.match(file.path) is not None
            if is_filename_match:
                for hunk in Hunk.objects(file_action_id=file_action.id):
                    content = hunk.content
                    # First drop all Java strings from the code
                    content = re.sub(self._java_string, "", content)
                    has_javadoc_change |= self._ismatch(self._mutliline_comment, content)
                    # drop multiline comments
                    content = re.sub(self._mutliline_comment, "", content)
                    has_inline_change |= self._ismatch(self._java_inlinecomment, content)
                    has_technical_dept_add |= self._ismatch(self._java_inlinetechnicaldept_add, content)
                    has_technical_dept_remove |= self._ismatch(self._java_inlinetechnicaldept_remove, content)

        self._labels.append(('javadoc', has_javadoc_change))
        self._labels.append(('javainline', has_javadoc_change))
        self._labels.append(('technicaldept_add', has_technical_dept_add))
        self._labels.append(('technicaldept_remove', has_technical_dept_remove))

    def get_labels(self):
        return self._labels

    def _error(self, message):
        # we log to warn because error gets to stdout in servershark
        self._log.warning(message)

    @staticmethod
    def _ismatch(regex, string):
        matches = regex.finditer(string)
        match_num = 0
        for match in matches:
            match_num = match_num + 1
        return match_num > 0
