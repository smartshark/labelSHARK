#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import logging
import re
import sys
import os

import pandas as pd
from pycoshark.mongomodels import Issue, FileAction, File, CodeEntityState, Hunk, Refactoring

from labelSHARK.approaches.vibscc.classifiers.direct_classifiers import Keyword_Classifier, Test_Classifier, \
    Documentation_Classifier,Refactoring_Classifier
from labelSHARK.approaches.vibscc.classifiers.ml_classifiers import ML_Classifiers_Exec
from labelSHARK.approaches.vibscc.utils.csv_utils import read_csv_df
from labelSHARK.approaches.vibscc.utils.mongo_pandas_utils import map_mongo_to_pandas
from labelSHARK.core import LabelSHARK, BaseLabelApproach


def remove_index(cls):
    tmp = copy.deepcopy(cls._meta)
    if 'indexes' in tmp.keys():
        del tmp['indexes']
    del tmp['index_specs']
    tmp['index_specs'] = None
    return tmp

FileAction._meta = remove_index(FileAction)
Issue._meta = remove_index(Issue)
File._meta = remove_index(File)
CodeEntityState._meta = remove_index(CodeEntityState)
Hunk._meta = remove_index(Hunk)
Refactoring._meta = remove_index(Refactoring)


@LabelSHARK.approach
class Vibscc_Main(BaseLabelApproach):
    """Run all classifiers and then perform voting between them to get final labels"""
    def set_commit(self, commit):

        commit_issue_files = pd.DataFrame({"_id": commit.pk,"message":commit.message},index=[0])

        #link commit to issues
        for its in self._config['itss']:
            if 'jira' in its.url:
                issues = self._find_jira_identifiers(commit.message)
            elif 'bugzilla' in its.url:
                issues = self._find_bugzilla_identifiers(commit.message)
            elif 'github' in its.url:
                issues = self._find_github_identifiers(commit.message)

        commit_issue_files["issue_type"] = ""
        if issues:
            issues_df = self._get_issues(its, issues)
            if (issues_df is not None) and ('issue_type' in issues_df):
                issues_type = issues_df.issue_type.str.cat(sep='||')
                commit_issue_files["issue_type"] = issues_type

        #append paths to commit
        commit_issue_files["paths"] = ""
        files_df = self._get_files_path(commit)
        if (files_df is not None) and ('path' in files_df):
                paths = files_df.path.str.cat(sep='||')
                commit_issue_files["paths"] = paths


        # code and keywrod based labeling
        code_test = self._test_classifier.classify_commit(commit_issue_files)
        code_documentation = self._documentation_classifier.classify_commit(commit_issue_files)
        code_refactoring = self._refactoring_classifier.classify_commit(commit_issue_files)
        keyword_df = self._keyword_classifier.classify_commit(commit_issue_files)

        # ml-labeling
        classifiers_labels = self._ml_classifiers_exec.get_all_labels(commit_issue_files)

        bugfix_labels = classifiers_labels["BugFix"]
        bugfix_labels.append(keyword_df.bugfix[0])
        refactoring_labels = classifiers_labels["Refactoring"]
        refactoring_labels.append(keyword_df.refactoring[0])
        test_labels = classifiers_labels["Test"]
        test_labels.append(keyword_df.test[0])
        feature_labels = classifiers_labels["Feature"]
        documentation_labels = classifiers_labels["Documentation"]
        documentation_labels.append(keyword_df.documentation[0])
        maintenance_labels = classifiers_labels["Maintainance"]
        maintenance_labels.append(keyword_df.maintainance[0])

        #voting
        bugfix_voting = self._get_hard_voting_label(bugfix_labels)
        refactoring_voting = self._get_hard_voting_label(refactoring_labels)
        test_voting = self._get_hard_voting_label(test_labels)
        feature_voting = self._get_hard_voting_label(feature_labels)
        documentation_voting = self._get_hard_voting_label(documentation_labels)
        maintenance_voting = self._get_hard_voting_label(maintenance_labels)

        #complementing
        label_name = "bugfix"
        if bugfix_voting:
            self._labels.append((label_name, True))
        else:
            self._labels.append((label_name, False))
        
        label_name = "refactoring"
        if refactoring_voting | code_refactoring :
            self._labels.append((label_name, True))
        else:
            self._labels.append((label_name, False))
            
        label_name = "test"
        if test_voting | code_test :
            self._labels.append((label_name, True))
        else:
            self._labels.append((label_name, False))
        
        label_name = "feature"
        if feature_voting:
            self._labels.append((label_name, True))
        else:
            self._labels.append((label_name, False))
            
        label_name = "documentation"
        if documentation_voting | code_documentation :
            self._labels.append((label_name, True))
        else:
            self._labels.append((label_name, False))

        label_name = "maintenance"
        if maintenance_voting:
            self._labels.append((label_name, True))
        else:
            self._labels.append((label_name, False))


    def configure(self, config):
        self._config = config
        self._log = logging.getLogger(self.__class__.__name__)
        self._log.setLevel(logging.INFO)
        i = logging.StreamHandler(sys.stdout)
        e = logging.StreamHandler(sys.stderr)
        i.setLevel(logging.INFO)
        e.setLevel(logging.ERROR)
        self._log.addHandler(i)
        self._log.addHandler(e)
        self._labels = []

        self._issue_pattern_jira = re.compile('(?P<ID>[A-Z][A-Z0-9_]+-[0-9]+)', re.M)
        self._issue_pattern_bugzilla = re.compile('((bug|issue|bugzilla)[s]*[#\s]*(?P<ID>[0-9]+))|(bugzilla\/show_bug\.cgi\?id=(?P<ID2>[0-9]+))', re.I | re.M)
        self._issue_pattern_github = re.compile('((bug|issue)[s]*[#\s]*(?P<ID>[0-9]+))|(issues\/(?P<ID2>[0-9]+))', re.I | re.M)


        #direct classifiers
        self._keyword_classifier = Keyword_Classifier()
        self._test_classifier = Test_Classifier(self._log)
        self._documentation_classifier = Documentation_Classifier(self._log)
        self._refactoring_classifier = Refactoring_Classifier(self._log)

        #ml-classifiers
        cur_dir = os.path.dirname(__file__)
        csv_file = os.path.join(cur_dir, 'vibscc/files', 'CCDataSet.csv')
        try:
            train_df = read_csv_df(csv_file)
            self._ml_classifiers_exec = ML_Classifiers_Exec(train_df)
            self._log.info("Starting ml-classifiers training")
            self._ml_classifiers_exec.train_classifiers()

        except Exception as exception:
            self._log.error(exception)
            sys.exit()



    def get_labels(self):
        return self._labels

    def _find_jira_identifiers(self, message):
        """Find issue-identifiers from commit message for jira"""
        identifiers = []
        for m in self._issue_pattern_jira.finditer(message):
            identifiers.append(m.group('ID').strip().upper())

        identifiers = set(identifiers)
        return identifiers

    def _find_bugzilla_identifiers(self, message):
        """Find issue-identifiers from commit message for bugzilla"""
        identifiers = []
        for m in self._issue_pattern_bugzilla.finditer(message):
            id = m.group('ID')
            id2 = m.group('ID2')
            if id is not None:
                identifiers.append(id)
            if id2 is not None:
                identifiers.append(id2)

        identifiers = set(identifiers)
        return identifiers

    def _find_github_identifiers(self, message):
        """Find issue-identifiers from commit message for github"""
        identifiers = []
        for m in self._issue_pattern_github.finditer(message):
            id = m.group('ID')
            id2 = m.group('ID2')
            if id is not None:
                identifiers.append(id)
            if id2 is not None:
                identifiers.append(id2)

        identifiers = set(identifiers)
        return identifiers

    def _get_issues(self, its, identifiers):
        """Get issue collection based on matched identifiers"""
        issues = Issue.objects(issue_system_id=its.id, external_id__in=identifiers).only("issue_type")
        if issues.count() > 0:
            issues_df = map_mongo_to_pandas(issues)
            return issues_df
        else:
            return None


    def _get_files_path(self, commit):
        """Get all file-actions and files associated with commit"""
        file_actions = FileAction.objects(commit_id=commit.id)
        file_actions_df = map_mongo_to_pandas(file_actions.only("file_id"))
        if (file_actions_df is not None) and ('file_id' in file_actions_df):
            file_ids = file_actions_df.file_id.values.tolist()
            files = File.objects(id__in=file_ids).only("path")
            if files.count() > 0:
                files_df = map_mongo_to_pandas(files)
                return files_df

        return None

    def _get_hard_voting_label(self, labels):
        """Performs hard voting between odd-classifiers"""
        if labels.count(1) > labels.count(0):
            return 1
        else:
            return 0