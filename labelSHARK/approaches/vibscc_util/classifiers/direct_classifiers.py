import re
import sys
from abc import ABCMeta, abstractmethod

import pandas as pd
from pycoshark.mongomodels import CodeEntityState, Hunk, File, FileAction, Commit, Refactoring

from ..utils.mongo_pandas_utils import map_mongo_to_pandas
from ..utils.pre_process_utils import stemmer_tokenize


class IDirectClassifier(metaclass=ABCMeta):
    """Interface for classifiers which do not require training beforehand"""

    @abstractmethod
    def classify_commit(self, data_frame):
        pass



class Keyword_Classifier(IDirectClassifier):
    """Classify commit using keywords"""

    def _classify_bugfix(self, df):
        bug_fix_pattern = r"\b(bug|fix|error|fail|repair|fixup)\b"
        df["bugfix"] = df.message.str.contains(bug_fix_pattern, case=False)
        df.bugfix = df.bugfix.map({True: 1, False: 0})
        for row in df.itertuples():
            if (("nan" != row.issue_type) & ("Bug" in row.issue_type)):
                df.set_value(row.Index, "bugfix", 1)
            elif (("nan" != row.issue_type) & (row.bugfix == 1)):
                df.set_value(row.Index, "bugfix", 0)

    def _classify_refactoring(self, df):
        refact_pattern = r"\b(refact|refactor|refactored|migrated|refactoring|restructure|encapsulate|param|parameters|abstract|rename\s+(method|variable|class)|(method|variable|class)\s+name|extract\s+(method|class|interface|code)|(moved|move)(?!.*(icon|icons|version))|getter|setter|checkstyle|pmd|typo.*(variable|method|class|code)|pull up|push down|merge.*(method|funcation|class)|convention|simple|simplify|replace|nest|inline|(remove|delete)\s+duplicate|split|wrapper|private|protect|delegate)\b"
        df["refactoring"] = df.message.str.contains(refact_pattern, case=False)
        df.refactoring = df.refactoring.map({True: 1, False: 0})

    def _classify_test(self, df):
        test_message_pattern = r"\b(test|tests|junit)\b"
        df["test"] = df.message.str.contains(test_message_pattern, case=False)
        df.test = df.test.map({True: 1, False: 0})
        test_file_pattern = r"\b(test|tests)\b"
        df["test"] = df.paths.str.contains(test_file_pattern, case=False)
        df.test = df.test.map({True: 1, False: 0})

    def _classify_documentation(self, df):
        doc_message_pattern = r"\b(doc|xdoc|xdocs|userguide|documentation|javadoc)\b"
        df["P_Documentation1"] = df.message.str.contains(doc_message_pattern, case=False)
        df.P_Documentation1 = df.P_Documentation1.map({True: 1, False: 0})
        documentation_file_pattern = r"\b(doc|xdoc|xdocs|userguide|changes|documentation|readme|license)\b"
        df["P_Documentation2"] = df.paths.str.contains(documentation_file_pattern, case=False)
        df.P_Documentation2 = df.P_Documentation2.map({True: 1, False: 0})
        df["documentation"] = 0
        for row in df.itertuples():
            if ((row.P_Documentation1 == 1) | (row.P_Documentation2 == 1)):
                df.set_value(row.Index, "documentation", 1)

    def _classify_feature(self, df):
        feature_pattern = r"\b((add|added).*(class|method|png|logo)|new|feature|import|^(no|not|never).*use|support|Synchronize)\b"
        df["feature"] = df.message.str.contains(feature_pattern, case=False)
        df.feature = df.feature.map({True: 1, False: 0})
        for row in df.itertuples():
            if (("nan" != row.issue_type) & ("Feature" in row.issue_type)):
                df.set_value(row.Index, "feature", 1)

    def _classify_maintainance(self, df):
        # maintainance_pattern_message = r"\b(clean|cleaning|cleanup|cleaned up|reordered|configuration|remove|upgrade|format|update|version|pom|dead|unused|api|library|cosmetic|organize|tabs|spaces|whitespace)\b"
        maintainance_pattern_message = r"\b(clean|cleaning|cleanup|cleaned up|reordered|(remove)?(.)*(unused|import|dead|whitespace|whitespaces|spaces|tabs)|((update|upgrade|set)+(.)*(version))|format|cosmetic|organize)\b"
        df["P_Maintain_Message"] = df.message.str.contains(maintainance_pattern_message, case=False)
        df.P_Maintain_Message = df.P_Maintain_Message.map({True: 1, False: 0})

        maintainance_pattern_files = r"\b(build|pom|properties|project|gitignore|cvsignore|maven|travis|classpath|AndroidManifest)\b"
        df["P_Maintain_files"] = df.paths.str.contains(maintainance_pattern_files, case=False)
        df.P_Maintain_files = df.P_Maintain_files.map({True: 1, False: 0})
        df["maintainance"] = 0
        for row in df.itertuples():
            if ((row.P_Maintain_Message == 1) | (row.P_Maintain_files == 1)):
                df.set_value(row.Index, "maintainance", 1)

    def classify_commit(self, commit_issue_df):
        df = commit_issue_df.copy()
        df.issue_type = df.issue_type.apply(str)
        df.paths = df.paths.apply(str)
        df.message = df.message.apply(stemmer_tokenize)
        self._classify_bugfix(df)
        self._classify_refactoring(df)
        self._classify_feature(df)
        self._classify_test(df)
        self._classify_documentation(df)
        self._classify_maintainance(df)
        return df


class Refactoring_Classifier(IDirectClassifier):
    """Classify commit into Refactoring/Non-Refactoring"""

    def __init__(self, log):
        self._log = log

    def classify_commit(self, commit_issue_df):
        """Returns 1 if any refactoring present in refactoring collection otherwise 0"""
        try:
            refactoring = Refactoring.objects(commit_id=commit_issue_df._id[0])
            if refactoring.count() > 0:
                return 1
            else:
                return 0
        except Exception as exception:
            self._log.error(exception)
            return 0




class Test_Classifier(IDirectClassifier):
    """Classify commit into Test/No-Test based on Imports"""

    def __init__(self, log):
        self._log = log

    def _remove_comments_blanklines(self, row):
        if row.candidate_test == 1:
            row.content = re.sub(re.compile("\+(\s*)\n"), "", row.content)  # remove empty lines
            row.content = re.sub(re.compile("/\*.*?\*/", re.DOTALL), "",
                                 row.content)  # remove all occurance streamed comments (/*COMMENT */) from string
            row.content = re.sub(re.compile("//.*?\n"), "",
                                 row.content)  # remove all occurance singleline comments (//COMMENT\n ) from string
            row.content = re.sub(re.compile("\+(\s*)\n"), "", row.content)  # remove empty lines
            row.content = re.sub(re.compile("\+|\-"), "", row.content)  # remove plus and minus
            if (len(row.content) > 0):
                row.test = 1

        elif (row.candidate_test == 2) or (row.candidate_test == 3):
            row.test = 1

        return row

    def classify_commit(self, commit_issue_df):

        try:
            actions_files_df = self._get_actions_files(commit_issue_df)

            commit_files = commit_issue_df.merge(actions_files_df, how="left", left_on="_id", right_on="commit_id")

            code_entity_df = self._get_code_entity_states(commit_files)

            commit_entities_df = commit_files.merge(code_entity_df, how="left", left_on=["_id", "file_id"],
                                                    right_on=["commit_id", "file_id"])
            
            commit_entities_df["candidate_test"] = 0
            test_pattern = "org\.junit|junit\.framework|android\.test|android\.support\.test|com\.jayway\.android\.robotium|org\.easymock|org\.mockejb|org\.mockito|org\.powermock"
            test_pattern_python = "unittest"
            file_pattern = "((.*(Test|test))|((Test|test).*))\.(java|c|cc|cpp)"
            file_pattern_python = "((.*(Test|test))|((Test|test).*))\.(py)"
            file_pattern_other = "((.*(Test|test))|((Test|test).*))\.[a-z]+"
            directory_pattern = ".*(Test|Tests|test|tests).*"

            for row in commit_entities_df.itertuples():
                if (isinstance(row.imports, (list))):
                    for file_import in row.imports:
                        if re.search(test_pattern, file_import):
                            commit_entities_df.set_value(row.Index, "candidate_test", 1)
                        elif re.search(test_pattern_python, file_import):
                            commit_entities_df.set_value(row.Index, "candidate_test", 2)
                elif pd.notnull(row.path):
                    path_file = row.path.rsplit('/', 1)
                    path = path_file[0]
                    file_name = path_file[-1]
                    if re.search(directory_pattern, path) and re.search(file_pattern, file_name):
                        commit_entities_df.set_value(row.Index, "candidate_test", 1)
                    if re.search(directory_pattern, path) and re.search(file_pattern_python, file_name):
                        commit_entities_df.set_value(row.Index, "candidate_test", 2)
                    elif re.search(directory_pattern, path) and re.search(file_pattern_other, file_name):
                        commit_entities_df.set_value(row.Index, "candidate_test", 3)

            hunks = Hunk.objects(file_action_id__in=commit_entities_df[(commit_entities_df.candidate_test == 1)].
                                 file_action_id.values.tolist())

            hunks_df = map_mongo_to_pandas(hunks)

            commit_entities_hunks = commit_entities_df.merge(hunks_df, how="left", left_on="file_action_id",
                                                             right_on="file_action_id")

            # check if hunks contain actual code rather than comments and blank lines for candidate test
            commit_entities_hunks["test"] = 0
            commit_entities_hunks = commit_entities_hunks.apply(self._remove_comments_blanklines, axis=1)
            commit_entities_hunks = commit_entities_hunks.loc[:, ("_id", "test")]
            commit_entities_hunks = commit_entities_hunks.groupby("_id").sum().reset_index()
            commit_entities_hunks.loc[commit_entities_hunks.test != 0, ("test")] = 1

            if commit_entities_hunks.test[0] == 1:
                return 1
            else:
                return 0

        except Exception as exception:
            self._log.error(exception)
            return 0





    def _get_actions_files(self, commit_issue_df):

        file_actions = FileAction.objects(commit_id=commit_issue_df._id[0])
        file_actions_df = map_mongo_to_pandas(file_actions.only("id","file_id", "commit_id"))
        file_actions_df.rename(columns={'_id': 'file_action_id'}, inplace=True)
        file_ids = file_actions_df.file_id.values.tolist()
        files = File.objects(id__in=file_ids).only("id","path")
        files_df = map_mongo_to_pandas(files)
        file_action_files = file_actions_df.merge(files_df, left_on="file_id", right_on="_id")
        file_action_files.drop("_id", axis=1, inplace=True)
        return file_action_files

    def _get_code_entity_states(self, commit_issue_df):
        current_commits_files = [{'file_id': file_id, 'commit_id': commit_issue_df._id[0], 'ce_type': 'file'}
                                 for file_id in commit_issue_df.file_id.values.tolist()]
        code_entity_states = CodeEntityState.objects(__raw__= {'$or': current_commits_files})
        code_entity_df = map_mongo_to_pandas(code_entity_states)
        return code_entity_df




class Documentation_Classifier(IDirectClassifier):
    """Classify commit into Documentation/No-Documentation based on Hunks/DLOC"""

    def __init__(self, log):
        self._log = log

    def classify_commit(self, commit_issue_df):
        try:
            documention_metric_df = commit_issue_df.copy()
            documention_metric_df = self._classify_metric_documentation(documention_metric_df)

            documention_hunk_df = commit_issue_df.copy()
            documention_hunk_df = self._classify_hunk_documentation(documention_hunk_df)

            if (documention_metric_df.delta_DLOC[0] == 1) | (documention_hunk_df.c_documentation[0] == 1):
                return 1
            else:
                return 0

        except Exception as exception:
            self._log.error("Unexpected error: {}".format(exception))
            return 0


    def _classify_metric_documentation(self, commit_issue_df):
        commit = Commit.objects(id = commit_issue_df._id[0])
        commit_df = map_mongo_to_pandas(commit)
        commit_hash_df = commit_df.apply(lambda x: pd.Series(x['parents']), axis=1).stack().reset_index(level=1, drop=True)
        commit_hash_df.name = 'parents'
        commit_hash_df = commit_df.drop("parents", axis=1).join(commit_hash_df)
        commit_hash_df = commit_hash_df.loc[:,("_id","revision_hash")]
        commit_hash_df.columns = ['commit_id', 'revision_hash']
        # read previous revisions
        parent_commits = Commit.objects(revision_hash__in = commit_hash_df.revision_hash.values.tolist())
        prev_df = map_mongo_to_pandas(parent_commits)

        prev_df = prev_df.loc[:, ("_id", "revision_hash")]
        prev_df.columns = ["parent_commit_id", "parent_revision_hash"]
        current_previous_commits_df = commit_hash_df.merge(prev_df, left_on="revision_hash",
                                                           right_on="parent_revision_hash")
        current_previous_commits_df.drop("revision_hash", axis=1, inplace=True)

        # read changed files
        file_action_files = self._get_actions_files(current_previous_commits_df)
        file_action_files = file_action_files.loc[:, ("commit_id", "path", "file_id")]
        file_action_files = file_action_files[file_action_files.path.str.contains("(\.java)") == True]
        commit_prev_files = current_previous_commits_df.merge(file_action_files)

        current_commits = [{'commit_id': commit_id} for commit_id in
                           commit_prev_files.commit_id.values.tolist()]
        parent_commits = [{'commit_id': commit_id} for commit_id in
                          commit_prev_files.parent_commit_id.values.tolist()]
        file_ids = [{'file_id': file_id} for file_id in commit_prev_files.file_id.values.tolist()]

        # supported types by sourcemeter for java
        code_entity_types = [{'ce_type': 'annotation'}, {'ce_type': 'class'}, {'ce_type': 'enum'},
                             {'ce_type': 'interface'},
                             {'ce_type': 'method'}]

        current_commits_files = []
        for i in range(len(current_commits)):
            current_commits_files_dict = dict(list(current_commits[i].items()) + list(file_ids[i].items()))
            current_commits_files_dict['$or'] = code_entity_types
            current_commits_files.append(current_commits_files_dict)

        parent_commits_files = []
        for i in range(len(parent_commits)):
            parent_commits_files_dict = dict(list(parent_commits[i].items()) + list(file_ids[i].items()))
            parent_commits_files_dict['$or'] = code_entity_types
            parent_commits_files.append(parent_commits_files_dict)

        # read metrics realted to commit
        current_code_entity_states = CodeEntityState.objects(__raw__={'$or': current_commits_files})
        current_metrics = map_mongo_to_pandas(current_code_entity_states)
        current_metrics = current_metrics.loc[:, ("commit_id", "long_name", "metrics", "file_id")]
        current_metrics.rename(columns={'commit_id': 'commit_id_x'}, inplace=True)

        parent_code_entity_states = CodeEntityState.objects(__raw__={'$or': parent_commits_files})
        parent_metrics = map_mongo_to_pandas(parent_code_entity_states)
        parent_metrics = parent_metrics.loc[:, ("commit_id", "long_name", "metrics", "file_id")]
        parent_metrics.rename(columns={'commit_id': 'commit_id_y'}, inplace=True)

        commit_prev_files_cpy = commit_prev_files.copy()
        commit_metrices_current = pd.merge(commit_prev_files, current_metrics, how='left',
                                           left_on=['commit_id', 'file_id'],
                                           right_on=['commit_id_x', 'file_id'])
        commit_metrices_current = commit_metrices_current.loc[:,
                                  ("commit_id", "parent_commit_id", "file_id", "long_name", "metrics")]
        commit_metrices_parent = pd.merge(commit_prev_files_cpy, parent_metrics, how='left',
                                          left_on=['parent_commit_id', 'file_id'],
                                          right_on=['commit_id_y', 'file_id'])
        commit_metrices_parent = commit_metrices_parent.loc[:,
                                 ("commit_id", "parent_commit_id", "file_id", "long_name", "metrics")]
        commit_metrics = pd.merge(commit_metrices_current, commit_metrices_parent, how='outer',
                                  left_on=['commit_id', 'parent_commit_id', 'file_id', 'long_name'],
                                  right_on=['commit_id', 'parent_commit_id', 'file_id', 'long_name'])

        commit_metrics["delta_DLOC"] = 0
        commit_metrics = commit_metrics.apply(self._calculate_dloc_metric, axis=1)
        commit_metrics = commit_metrics.loc[:, ("commit_id", "delta_DLOC")]
        commit_metrics = commit_metrics.groupby("commit_id").sum().reset_index()
        commit_metrics.loc[commit_metrics.delta_DLOC != 0, ("delta_DLOC")] = 1
        return commit_metrics

    def _get_actions_files(self, commit_issue_df):

        file_actions = FileAction.objects(commit_id=commit_issue_df.commit_id[0])
        file_actions_df = map_mongo_to_pandas(file_actions.only("id", "file_id", "commit_id"))
        file_actions_df.rename(columns={'_id': 'file_action_id'}, inplace=True)
        file_ids = file_actions_df.file_id.values.tolist()
        files = File.objects(id__in=file_ids).only("id","path")
        files_df = map_mongo_to_pandas(files)
        file_action_files = file_actions_df.merge(files_df, left_on="file_id", right_on="_id")
        file_action_files.drop("_id", axis=1, inplace=True)
        return file_action_files

    def _calculate_dloc_metric(self, row):
        if (pd.notnull(row.metrics_x) & pd.notnull(row.metrics_y)):
            row.delta_DLOC = abs(row.metrics_x['DLOC'] - row.metrics_y['DLOC'])
        elif (pd.notnull(row.metrics_x)):
            row.delta_DLOC = row.metrics_x['DLOC']
        elif (pd.notnull(row.metrics_y)):
            row.delta_DLOC = row.metrics_y['DLOC']
        else:
            row.delta_DLOC = 0
        return row

    def _classify_hunk_documentation(self, commit_issue_df):
        commit = Commit.objects(id=commit_issue_df._id[0])
        commit_df = map_mongo_to_pandas(commit)
        commit_df.rename(columns={'_id': 'commit_id'}, inplace=True)
        # read changed files
        file_action_files = self._get_actions_files(commit_df)
        file_action_files = file_action_files.loc[:, ("commit_id", "path", "file_id", "file_action_id")]
        file_action_files = file_action_files[
            file_action_files.path.str.contains("(\.java$)|(\.c$)|(\.cpp$)|(\.py$)|(\.h$)|(\.cc$)") == True]
        commit_files = commit_df.merge(file_action_files, how="left")
        hunks = Hunk.objects(file_action_id__in=commit_files.file_action_id.values.tolist())
        hunks_df = map_mongo_to_pandas(hunks)

        commit_files_hunk = commit_files.merge(hunks_df, how="left", left_on="file_action_id",
                                               right_on="file_action_id")

        # check if hunks contain actual code rather than comments and blank lines for candidate test
        commit_files_hunk["c_documentation"] = 0
        commit_files_hunk = commit_files_hunk.apply(self._find_documentation_hunk, axis=1)
        commit_files_hunk = commit_files_hunk.loc[:, ("commit_id", "c_documentation")]
        commit_files_hunk = commit_files_hunk.groupby("commit_id").sum().reset_index()
        commit_files_hunk.loc[commit_files_hunk.c_documentation != 0, ("c_documentation")] = 1
        commit_files_hunk = commit_files_hunk.loc[:, ("commit_id", "c_documentation")]
        return commit_files_hunk

    def _find_documentation_hunk(self, row):
        if (pd.notnull(row.content)):
            python_pattern = "(\"\"\")|(\'\'\')"
            java_c_cpp_pattern = "(/\*\*)|((-|\+)(\s*)\*)"
            if re.search(python_pattern, row.content) or re.search(java_c_cpp_pattern, row.content):
                row.c_documentation = 1
        return row
