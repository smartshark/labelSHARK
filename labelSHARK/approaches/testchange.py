import logging
import re

from pycoshark.mongomodels import CodeEntityState, Hunk, File, FileAction
from core import LabelSHARK, BaseLabelApproach


@LabelSHARK.approach
class TestChangeLabel(BaseLabelApproach):
    """This labels commits as test changes based on the file actions
    """

    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)
        self._labels = []
        self._test_import_pattern_java = re.compile(
            'org\.junit|junit\.framework|android\.test|android\.support\.test|com\.jayway\.android\.robotium|org\.easymock|org\.mockejb|org\.mockito|org\.powermock')
        self._test_filename_pattern_java = re.compile('((.*(Test|test))|((Test|test).*))\.(java)')

        self._empty_line_regex = re.compile("\+(\s*)\n")
        self._streamed_comments = re.compile("/\*.*?\*/", re.DOTALL)
        self._single_line_comments = re.compile("//.*?\n")
        self._start_plus_minus = re.compile("^(\+|-)", re.MULTILINE)

    def set_commit(self, commit):
        self._labels = []
        self._labels.append(('javacode', self._is_java_test_change(commit)))

    def get_labels(self):
        return self._labels

    def _error(self, message):
        # we log to warn because error gets to stdout in servershark
        self._log.warning(message)

    def _is_java_test_change(self, commit):
        if commit.code_entity_states is None or len(commit.code_entity_states) == 0:
            code_entities = CodeEntityState.objects(commit_id=commit.id, ce_type='file').only('id', 'long_name',
                                                                                              'imports')
        else:
            code_entities = CodeEntityState.objects(id__in=commit.code_entity_states, ce_type='file').only('id',
                                                                                                           'long_name',
                                                                                                           'imports')
        for file_action in FileAction.objects(commit_id=commit.id):
            file = File.objects(id=file_action.file_id).get()
            if code_entities.filter(long_name=file.path).count() > 0:
                code_entity = code_entities.filter(long_name=file.path).get()
            else:
                code_entity = None
            is_filename_match = self._test_filename_pattern_java.match(file.path) is not None
            is_import_match = False
            if code_entity is not None and code_entity.imports is not None:
                for package in code_entity.imports:
                    if self._test_import_pattern_java.match(package) is not None:
                        is_import_match = True
                        break
            if is_filename_match or is_import_match:
                for hunk in Hunk.objects(file_action_id=file_action.id):
                    # check if hunk is logical change
                    content = hunk.content
                    content = re.sub(self._streamed_comments, "", content)
                    content = re.sub(self._single_line_comments, "", content)
                    content = re.sub(self._start_plus_minus, "", content)
                    content = re.sub(self._empty_line_regex, "", content)
                    if len(content) > 0:
                        return True
        return False
